# release-euclid-mcp

## Purpose

Standardized release workflow for `analysis-catalog` (euclid-catalog MCP) using one script.

## When to use

- After code changes are ready for deployment.
- When you need to bump image tag in kustomize overlay and sync Argo CD.

## Commands

From `analysis-catalog` (recommended):

```bash
cd analysis-catalog
make release-zjlab
```

Or from repo root (`euclid-mcp`):

```bash
analysis-catalog/ops/release.sh --env env-zjlab --commit --push-git
```

With commit and push:

```bash
analysis-catalog/ops/release.sh --env env-zjlab --commit --push-git
```

Target another environment:

```bash
analysis-catalog/ops/release.sh --env env-72602 --commit
```

## Safety checks

1. Confirm target overlay (`env-zjlab` or `env-72602`).
2. Verify image repository is expected for that environment.
3. Ensure Argo CD app name is `euclid-catalog-mcp` (or override with `--argocd-app`).

## Expected outputs

- Updated image tag in `analysis-catalog/overlays/<env>/deployment-patch.yaml`
- Optional git commit/push
- Argo CD sync (or refresh annotation fallback)

## References

- Script: `analysis-catalog/ops/release.sh`
- Ops doc: `analysis-catalog/docs/release-ops.md`
