#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_DIR}/.." && pwd)"

ENVIRONMENT="env-zjlab"
IMAGE_REPO=""
TAG=""
ARGOCD_APP="euclid-catalog-mcp"
ARGOCD_SERVER="${ARGOCD_SERVER:-}"
ARGOCD_USERNAME="${ARGOCD_USERNAME:-admin}"
ARGOCD_PASSWORD="${ARGOCD_PASSWORD:-}"
ARGOCD_AUTO_LOGIN="true"
ARGOCD_CHECK_PATH="true"
SKIP_BUILD="false"
SKIP_PUSH="false"
SKIP_SYNC="false"
COMMIT_CHANGES="false"
PUSH_GIT="false"

usage() {
  cat <<'EOF'
Usage:
  ./ops/release.sh [options]

Options:
  --env <env-zjlab|env-72602>   Target overlay environment (default: env-zjlab)
  --image <repo/image>          Image repository (defaults by environment)
  --tag <tag>                   Image tag (default: vYYYYMMDDHHMMSS-<gitsha>)
  --argocd-app <name>           Argo CD app name (default: euclid-catalog-mcp)
  --argocd-server <host:port>   Argo CD server (default: auto-detect via kubectl)
  --argocd-username <name>      Argo CD username (default: admin)
  --argocd-password <pass>      Argo CD password (default: empty; auto-detect if possible)
  --no-argocd-auto-login        Disable automatic Argo CD re-login on auth failure
  --no-argocd-path-check        Disable Argo CD app source.path validation
  --skip-build                  Skip podman build
  --skip-push                   Skip podman push
  --skip-sync                   Skip Argo CD sync trigger
  --commit                      Commit overlay image update
  --push-git                    Push git commit (implies --commit)
  -h, --help                    Show this help

Examples:
  ./ops/release.sh --env env-zjlab
  ./ops/release.sh --env env-zjlab --commit --push-git
  ./ops/release.sh --env env-72602 --tag v2026041301 --skip-sync
  ./ops/release.sh --env env-zjlab --argocd-server 10.0.0.5:30443
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command not found: $1" >&2
    exit 1
  fi
}

registry_from_image_repo() {
  local image_repo="$1"
  echo "${image_repo%%/*}"
}

check_registry_login() {
  local registry="$1"
  if podman login --get-login "$registry" >/dev/null 2>&1; then
    return 0
  fi

  echo "Error: not logged in to registry: ${registry}" >&2
  echo "Please run: podman login ${registry}" >&2
  return 1
}

detect_argocd_server_from_cluster() {
  local master_ip
  master_ip="$(kubectl get nodes --selector=node-role.kubernetes.io/control-plane -o jsonpath='{$.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || true)"
  if [[ -z "$master_ip" ]]; then
    master_ip="$(kubectl get nodes --selector=node-role.kubernetes.io/master -o jsonpath='{$.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || true)"
  fi
  if [[ -z "$master_ip" ]]; then
    return 1
  fi
  echo "${master_ip}:30443"
}

detect_argocd_password_from_cluster() {
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' 2>/dev/null | base64 -d
}

try_argocd_login() {
  require_cmd argocd

  local server="$ARGOCD_SERVER"
  local username="$ARGOCD_USERNAME"
  local password="$ARGOCD_PASSWORD"

  if [[ -z "$server" ]] && command -v kubectl >/dev/null 2>&1; then
    server="$(detect_argocd_server_from_cluster || true)"
  fi

  if [[ -z "$password" ]] && command -v kubectl >/dev/null 2>&1; then
    password="$(detect_argocd_password_from_cluster || true)"
  fi

  if [[ -z "$server" || -z "$password" ]]; then
    return 1
  fi

  echo "==> Argo CD login: ${username}@${server}"
  argocd login --insecure --username "$username" "$server" --password "$password" >/dev/null
}

run_argocd_sync() {
  local sync_out
  if sync_out="$(argocd app sync "$ARGOCD_APP" --prune 2>&1)"; then
    printf '%s\n' "$sync_out"
    argocd app wait "$ARGOCD_APP" --health --sync --timeout 300
    return 0
  fi

  printf '%s\n' "$sync_out" >&2
  if [[ "$ARGOCD_AUTO_LOGIN" == "true" ]] && [[ "$sync_out" == *"Unauthenticated"* || "$sync_out" == *"token is expired"* || "$sync_out" == *"invalid session"* ]]; then
    echo "Argo CD session expired, trying auto-login..."
    if try_argocd_login; then
      argocd app sync "$ARGOCD_APP" --prune
      argocd app wait "$ARGOCD_APP" --health --sync --timeout 300
      return 0
    fi
  fi

  return 1
}

check_argocd_source_path() {
  local expected_path="$1"

  if [[ "$ARGOCD_CHECK_PATH" != "true" ]]; then
    return 0
  fi

  if ! command -v kubectl >/dev/null 2>&1; then
    return 0
  fi

  local actual_path
  actual_path="$(kubectl -n argocd get application "$ARGOCD_APP" -o jsonpath='{.spec.source.path}' 2>/dev/null || true)"
  if [[ -z "$actual_path" ]]; then
    return 0
  fi

  if [[ "$actual_path" != "$expected_path" ]]; then
    echo "Error: Argo CD app source path mismatch." >&2
    echo "  app:      ${ARGOCD_APP}" >&2
    echo "  actual:   ${actual_path}" >&2
    echo "  expected: ${expected_path}" >&2
    echo "Fix with one of:" >&2
    echo "  kubectl -n argocd patch application ${ARGOCD_APP} --type merge -p '{\"spec\":{\"source\":{\"path\":\"${expected_path}\"}}}'" >&2
    echo "  argocd app set ${ARGOCD_APP} --path ${expected_path}" >&2
    return 22
  fi
}

normalize_git_url() {
  local url="$1"
  if [[ "$url" =~ ^git@([^:]+):(.+)$ ]]; then
    url="https://${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  fi
  url="${url%.git}"
  echo "$url"
}

find_remote_by_url() {
  local repo_url="$1"
  local target_norm
  target_norm="$(normalize_git_url "$repo_url")"

  local remote
  for remote in $(git -C "$REPO_ROOT" remote); do
    local rurl
    rurl="$(git -C "$REPO_ROOT" remote get-url "$remote" 2>/dev/null || true)"
    if [[ -n "$rurl" ]] && [[ "$(normalize_git_url "$rurl")" == "$target_norm" ]]; then
      echo "$remote"
      return 0
    fi
  done
  return 1
}

check_argocd_repo_state() {
  if ! command -v kubectl >/dev/null 2>&1; then
    return 0
  fi

  local repo_url target_rev remote_name
  repo_url="$(kubectl -n argocd get application "$ARGOCD_APP" -o jsonpath='{.spec.source.repoURL}' 2>/dev/null || true)"
  target_rev="$(kubectl -n argocd get application "$ARGOCD_APP" -o jsonpath='{.spec.source.targetRevision}' 2>/dev/null || true)"
  if [[ -z "$repo_url" ]]; then
    return 0
  fi
  if [[ -z "$target_rev" ]]; then
    target_rev="main"
  fi

  remote_name="$(find_remote_by_url "$repo_url" || true)"
  if [[ -z "$remote_name" ]]; then
    echo "Warning: cannot map Argo CD repoURL to local git remote, skip remote-state check." >&2
    return 0
  fi

  git -C "$REPO_ROOT" fetch "$remote_name" "$target_rev" --quiet || true

  if ! git -C "$REPO_ROOT" cat-file -e "$remote_name/$target_rev:$EXPECTED_ARGO_PATH" 2>/dev/null; then
    echo "Error: Argo CD repo branch does not contain expected path." >&2
    echo "  repoURL:   ${repo_url}" >&2
    echo "  revision:  ${target_rev}" >&2
    echo "  path:      ${EXPECTED_ARGO_PATH}" >&2
    echo "Fix: push the branch containing overlays to Argo CD repo, or adjust app repoURL/path." >&2
    return 24
  fi

  if ! git -C "$REPO_ROOT" merge-base --is-ancestor HEAD "$remote_name/$target_rev"; then
    echo "Error: local HEAD is not on Argo CD tracked branch yet." >&2
    echo "Argo CD sync will not include your latest overlay change." >&2
    echo "Run: git -C "$REPO_ROOT" push ${remote_name} HEAD:${target_rev}" >&2
    return 23
  fi
}

default_image_for_env() {
  case "$1" in
    env-zjlab)
      echo "harbor.zhejianglab.com/ay-dev/euclid-catalog-mcp"
      ;;
    env-72602)
      echo "crpi-wixjy6gci86ms14e.cn-hongkong.personal.cr.aliyuncs.com/ay-dev/euclid-catalog-mcp"
      ;;
    *)
      echo ""
      ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --image)
      IMAGE_REPO="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --argocd-app)
      ARGOCD_APP="$2"
      shift 2
      ;;
    --argocd-server)
      ARGOCD_SERVER="$2"
      shift 2
      ;;
    --argocd-username)
      ARGOCD_USERNAME="$2"
      shift 2
      ;;
    --argocd-password)
      ARGOCD_PASSWORD="$2"
      shift 2
      ;;
    --no-argocd-auto-login)
      ARGOCD_AUTO_LOGIN="false"
      shift
      ;;
    --no-argocd-path-check)
      ARGOCD_CHECK_PATH="false"
      shift
      ;;
    --skip-build)
      SKIP_BUILD="true"
      shift
      ;;
    --skip-push)
      SKIP_PUSH="true"
      shift
      ;;
    --skip-sync)
      SKIP_SYNC="true"
      shift
      ;;
    --commit)
      COMMIT_CHANGES="true"
      shift
      ;;
    --push-git)
      PUSH_GIT="true"
      COMMIT_CHANGES="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$IMAGE_REPO" ]]; then
  IMAGE_REPO="$(default_image_for_env "$ENVIRONMENT")"
fi

if [[ -z "$IMAGE_REPO" ]]; then
  echo "Error: unsupported --env '${ENVIRONMENT}'." >&2
  exit 1
fi

if [[ -z "$TAG" ]]; then
  GIT_SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)"
  TAG="v$(date +%Y%m%d%H%M%S)-${GIT_SHA}"
fi

IMAGE_REF="${IMAGE_REPO}:${TAG}"
REGISTRY="$(registry_from_image_repo "$IMAGE_REPO")"
PATCH_FILE="${PROJECT_DIR}/overlays/${ENVIRONMENT}/deployment-patch.yaml"
EXPECTED_ARGO_PATH="analysis-catalog/overlays/${ENVIRONMENT}"

if [[ ! -f "$PATCH_FILE" ]]; then
  echo "Error: deployment patch not found: ${PATCH_FILE}" >&2
  echo "Hint: add overlays/${ENVIRONMENT}/deployment-patch.yaml first." >&2
  exit 1
fi

echo "==> Release plan"
echo "    env:          ${ENVIRONMENT}"
echo "    image:        ${IMAGE_REF}"
echo "    patch file:   ${PATCH_FILE}"
echo "    argocd app:   ${ARGOCD_APP}"

if [[ "$SKIP_BUILD" != "true" ]]; then
  require_cmd podman
  echo "==> Building image"
  podman build -t "$IMAGE_REF" "$PROJECT_DIR"
fi

if [[ "$SKIP_PUSH" != "true" ]]; then
  require_cmd podman
  check_registry_login "$REGISTRY"
  echo "==> Pushing image"
  if ! podman push "$IMAGE_REF"; then
    echo "Push failed for ${IMAGE_REF}" >&2
    echo "Common reasons:" >&2
    echo "  1) registry login expired -> podman login ${REGISTRY}" >&2
    echo "  2) account lacks push permission to repository ${IMAGE_REPO}" >&2
    echo "  3) wrong image repo for this environment (override with --image)" >&2
    exit 125
  fi
fi

echo "==> Updating overlay image"
python3 - "$PATCH_FILE" "$IMAGE_REF" <<'PY'
from pathlib import Path
import re
import sys

patch_file = Path(sys.argv[1])
image_ref = sys.argv[2]
text = patch_file.read_text(encoding="utf-8")
new_text, count = re.subn(r"^(\s*image:\s*).*$", rf"\1{image_ref}", text, count=1, flags=re.MULTILINE)
if count == 0:
    raise SystemExit(f"No image: line found in {patch_file}")
patch_file.write_text(new_text, encoding="utf-8")
print(f"Updated {patch_file} -> {image_ref}")
PY

if [[ "$COMMIT_CHANGES" == "true" ]]; then
  echo "==> Committing overlay update"
  git -C "$REPO_ROOT" add "$PATCH_FILE"
  if ! git -C "$REPO_ROOT" diff --cached --quiet; then
    git -C "$REPO_ROOT" commit -m "chore(release): bump ${ENVIRONMENT} image to ${TAG}"
  else
    echo "No staged changes to commit."
  fi

  if [[ "$PUSH_GIT" == "true" ]]; then
    echo "==> Pushing git commit"
    git -C "$REPO_ROOT" push
  fi
fi

if [[ "$SKIP_SYNC" != "true" ]] && [[ "$COMMIT_CHANGES" != "true" ]]; then
  echo "Error: sync requested but overlay change is not committed to git." >&2
  echo "Argo CD pulls from remote git, so local patch updates are invisible." >&2
  echo "Use one of:" >&2
  echo "  1) add --commit --push-git" >&2
  echo "  2) add --skip-sync and sync after manual commit/push" >&2
  exit 21
fi

if [[ "$SKIP_SYNC" != "true" ]]; then
  echo "==> Triggering Argo CD sync"
  check_argocd_source_path "$EXPECTED_ARGO_PATH"
  check_argocd_repo_state
  if command -v argocd >/dev/null 2>&1; then
    if ! run_argocd_sync; then
      echo "Warning: argocd sync failed." >&2
      if command -v kubectl >/dev/null 2>&1; then
        kubectl -n argocd annotate application "$ARGOCD_APP" \
          "euclid-mcp/sync-ts=$(date +%s)" --overwrite
        echo "Fallback: applied annotation to trigger Argo CD refresh."
      else
        exit 20
      fi
    fi
  elif command -v kubectl >/dev/null 2>&1; then
    kubectl -n argocd annotate application "$ARGOCD_APP" \
      "euclid-mcp/sync-ts=$(date +%s)" --overwrite
    echo "argocd CLI not found. Applied annotation to trigger refresh."
  else
    echo "Warning: neither argocd nor kubectl is available; sync skipped." >&2
  fi
fi

echo "==> Done"
echo "    image: ${IMAGE_REF}"
echo "    overlay: overlays/${ENVIRONMENT}/deployment-patch.yaml"
