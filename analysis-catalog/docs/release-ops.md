# Release & Ops Automation

This document standardizes image release and Argo CD deployment for `analysis-catalog`.

## Why

Current flow is mostly manual:

1. Build image with podman
2. Push image
3. Edit deployment image tag
4. Trigger Argo CD sync

To reduce mistakes, use `ops/release.sh` for one-command release.

## Script

- Path: `analysis-catalog/ops/release.sh`
- Purpose: build/push image, update overlay image tag, optional git commit/push, optional Argo CD sync.

## Prerequisites

- `podman` for image build/push
- `git`
- `argocd` CLI (preferred) or `kubectl`

## Quick Start

From repo root:

```bash
analysis-catalog/ops/release.sh --env env-zjlab
```

This does:

- build image
- push image
- update `analysis-catalog/overlays/env-zjlab/deployment-patch.yaml`
- sync Argo CD app `euclid-catalog-mcp`

Important: Argo CD sync sees only remote git state. If you update overlay locally,
you must commit/push before sync.

Or use make target:

```bash
cd analysis-catalog
make release-zjlab
```

## Common Commands

Release to `env-zjlab` and create commit:

```bash
analysis-catalog/ops/release.sh --env env-zjlab --commit
```

Release and push git before sync (recommended):

```bash
analysis-catalog/ops/release.sh --env env-zjlab --commit --push-git
```

Release to `env-72602` with explicit tag and push git:

```bash
analysis-catalog/ops/release.sh --env env-72602 --tag v2026041301 --commit --push-git
```

Only update overlay tag (no build/push/sync):

```bash
analysis-catalog/ops/release.sh --env env-zjlab --tag v2026041301 --skip-build --skip-push --skip-sync
```

Show options:

```bash
analysis-catalog/ops/release.sh --help
```

## Makefile Shortcuts

From `analysis-catalog/`:

```bash
make help
make release-zjlab
make release-72602 TAG=v2026041301
make tag-only ENV=env-zjlab TAG=v2026041301
make sync
make status
```

## Environment Defaults

- `env-zjlab` -> `harbor.zhejianglab.com/ay-dev/euclid-catalog-mcp`
- `env-72602` -> `crpi-wixjy6gci86ms14e.cn-hongkong.personal.cr.aliyuncs.com/ay-dev/euclid-catalog-mcp`

You can override with `--image`.

## Overlay Notes

- `env-72602` already has `deployment-patch.yaml`.
- `env-zjlab` now also has `deployment-patch.yaml` so release automation can update tags consistently.

## Recommended Team Workflow

1. Merge code to target branch.
2. Run release script with `--commit`.
3. If CI/GitOps requires, push git (`--push-git`) before/after sync according to your policy.
4. Verify Argo CD app health and pod readiness.

## Troubleshooting

- `permission denied` when running script:
  - run `chmod +x analysis-catalog/ops/release.sh`
- no `argocd` CLI:
  - script falls back to `kubectl annotate` refresh trigger.
- wrong environment image repo:
  - pass `--image <repo/image>` explicitly.

- `unauthorized to access repository ... action: push`:
  1. Re-login registry:
     ```bash
     podman login harbor.zhejianglab.com
     ```
  2. Verify you have push permission to target repo (for example `ay-dev/euclid-catalog-mcp`).
  3. If this env should use a different image repo, override explicitly:
     ```bash
     analysis-catalog/ops/release.sh --env env-zjlab --image <your-repo>/euclid-catalog-mcp
     ```

- Argo CD error `invalid session` / `token is expired`:
  - The release script now tries auto-login when sync returns auth errors.
  - Auto-login source:
    1. `--argocd-server`, `--argocd-username`, `--argocd-password` if provided
    2. otherwise auto-detects server/password from cluster via `kubectl`
  - Manual equivalent:
    ```bash
    ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    MASTER_IP=$(kubectl get nodes --selector=node-role.kubernetes.io/control-plane -o jsonpath='{$.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    argocd login --insecure --username admin "$MASTER_IP:30443" --password "$ARGOCD_PASS"
    ```

- Sync succeeded but pod image did not change:
  1. Check Argo CD app source path:
     ```bash
     kubectl -n argocd get application euclid-catalog-mcp -o jsonpath='{.spec.source.path}{"\n"}'
     ```
  2. Expected path for env-zjlab is `analysis-catalog/overlays/env-zjlab`.
  3. If app still points to old `analysis-catalog/manifests`, update it:
     ```bash
     kubectl -n argocd patch application euclid-catalog-mcp --type merge -p '{"spec":{"source":{"path":"analysis-catalog/overlays/env-zjlab"}}}'
     ```
  4. Ensure overlay change is pushed to remote git before sync.
  5. Confirm Argo CD repoURL matches the remote you pushed to (for example `origin` vs `github`).
