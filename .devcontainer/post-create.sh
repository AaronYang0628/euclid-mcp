#!/usr/bin/env bash
set -euo pipefail

echo "[post-create] checking CLI tools..."

if command -v opencode >/dev/null 2>&1; then
  echo "[post-create] opencode: $(opencode --version)"
else
  echo "[post-create] opencode not found" >&2
fi

if command -v claude >/dev/null 2>&1; then
  echo "[post-create] claude: installed"
fi

if command -v node >/dev/null 2>&1; then
  echo "[post-create] node: $(node --version)"
fi

if command -v kubectl >/dev/null 2>&1; then
  echo "[post-create] kubectl: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
else
  echo "[post-create] kubectl not found" >&2
fi

echo "[post-create] done"
