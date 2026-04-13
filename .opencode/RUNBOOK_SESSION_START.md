# Session Start Runbook

## 1) 读取上下文

- `.opencode/PROJECT_CONTEXT.md`
- `.opencode/DECISIONS.md`
- `analysis-catalog/docs/release-ops.md`

## 2) 快速环境检查

- `opencode debug config`
- `opencode mcp list`
- `kubectl -n mcp get deploy,svc,ingress`
- `kubectl -n argocd get application euclid-catalog-mcp -o jsonpath='{.spec.source.repoURL}{"\n"}{.spec.source.path}{"\n"}'`

## 3) 本地开发检查（analysis-catalog）

- `cd analysis-catalog`
- `python3 -m py_compile src/euclid_catalog_mcp/server.py`
- `python3 -m py_compile src/euclid_catalog_mcp/tile_index.py`

## 4) 发布建议路径

- `cd analysis-catalog`
- `make release-zjlab`
- 或显式：`./ops/release.sh --env env-zjlab --commit --push-git`

## 5) 验收要点

- Deployment 镜像是否更新：
  - `kubectl -n mcp get deploy euclid-catalog-mcp -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'`
- MCP 健康与工具是否可用（尤其 `resolve_tile_id`）
- ArgoCD 状态是否 `Synced/Healthy`
