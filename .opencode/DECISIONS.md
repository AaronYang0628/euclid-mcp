# Decisions

## 2026-04-13 — 引入 release 脚本统一发版

- 决策：使用 `analysis-catalog/ops/release.sh` 统一处理 build/push/overlay 更新/sync。
- 原因：减少手工步骤导致的镜像标签或 ArgoCD 路径错误。

## 2026-04-13 — env-zjlab 使用 overlay patch

- 决策：为 `env-zjlab` 增加 `deployment-patch.yaml`，与 `env-72602` 对齐。
- 原因：便于自动化只修改 overlay 镜像标签，不改 base。

## 2026-04-13 — resolve_tile_id 先走 mock

- 决策：新增 `resolve_tile_id(ra,dec)` 工具，当前返回稳定 mock tile id。
- 原因：先保证下游流程可跑，再替换为真实 tile 边界映射。

## 2026-04-13 — ArgoCD 同步前置校验

- 决策：release 脚本在 sync 前校验 app source.path 与 remote 分支状态。
- 原因：避免“本地改了但 ArgoCD 拉不到”导致的假成功。
