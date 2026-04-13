# Project Context

## 项目目标

本项目提供 Euclid Catalog MCP 服务，支持本地/S3 FITS 星表解析、字段提取、对象分页读取。

## 当前主流程（analysis-catalog）

1. 通过 `list_catalogs` 浏览可用 FITS 目录
2. 用 `parse_fits_header_only` 快速查看 schema（优先）
3. 按需调用 `get_catalog_fields` / `get_catalog_info_with_stats`
4. 用 `get_catalog_objects` 做分页读取样例
5. 对坐标调用 `resolve_tile_id`（当前为 mock 映射）

## 执行约束

- 优先使用 header-only 路径，避免无必要下载大文件
- 输出必须包含可复现参数：catalog_path/start/limit/columns
- 大文件处理默认走路径，不在会话中粘贴大块数据
- 结果与诊断文件尽量落在 `analysis-catalog/` 子目录内

## 发布与运维约定

- 发布入口：`analysis-catalog/ops/release.sh`
- 常用命令：`cd analysis-catalog && make release-zjlab`
- ArgoCD 跟踪路径应为：`analysis-catalog/overlays/<env>`
- 同步前需确保变更已 commit/push 到 ArgoCD 跟踪 remote

## 当前能力状态

- `resolve_tile_id` 已上线 mock 版本（稳定可复现）
- 后续将替换为真实 RA/DEC -> tile 边界映射
