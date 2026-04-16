# analysis-catalog UPDATE / Developer Guide

本文件面向开发者，记录实现细节、调试方式和近期变更。

## 当前运行模式

- 默认传输：`streamable-http`
- 默认端点：`http://0.0.0.0:8000/mcp`
- `stdio` 仅作为本地调试 fallback

代码入口：`src/euclid_catalog_mcp/server.py`

## 一条命令调试（开发）

推荐：

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make inspect-http
```

说明：

- 会先清理常见旧进程
- 启动 MCP server（streamable-http）
- 启动 MCP Inspector
- 输出 UI 需要填写的 Transport / URL / Proxy Address

脚本位置：`ops/inspect-http.sh`

备用（stdio）：

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make inspect-stdio
```

## 近期关键修改

1. **默认传输改为 streamable-http**

- 之前默认 SSE；现在默认 streamable-http，避免多端口与兼容问题。

2. **STDIO 协议流清理**

- 修复 `Unexpected token ... is not valid JSON`。
- 所有运行日志改写到 `stderr`，避免污染 stdio JSON-RPC 消息。
- 相关文件：
  - `src/euclid_catalog_mcp/server.py`
  - `src/euclid_catalog_mcp/storage/s3.py`

3. **`resolve_tile_id` 入参增强**

- `ra`/`dec` 改为可选。
- 支持仅传 `catalog_path`。
- 回退逻辑：filename -> header ->（可用时）坐标推断 -> mock。

4. **mock tile 格式修正**

- mock tile 从字符串前缀格式改为 9 位纯数字字符串。
- 相关文件：
  - `src/euclid_catalog_mcp/tile_index.py`
  - `tests/test_tile_index.py`

## 开发者常见问题

### 0) `get_catalog_objects` 如何返回指定字段

- 该工具已支持 `columns` 参数（`list[str]`）。
- 不传 `columns`（或传 `null`）时，返回全部字段。
- 传入 `columns` 时，仅返回指定字段。
- 示例：`columns=["OBJECT_ID", "RIGHT_ASCENSION", "DECLINATION"]`

### 1) Inspector 报 proxy token 错误

- 现象：`Connection Error - Did you add the proxy session token...`
- 处理：
  - 使用 `DANGEROUSLY_OMIT_AUTH=true`（本地调试）
  - 或设置固定 `MCP_PROXY_TOKEN`，并在 UI 填 `MCP_PROXY_AUTH_TOKEN`

### 2) Inspector 报 JSON parse 错误

- 现象：`Unexpected token 'S'...` / `Unexpected end of JSON input`
- 原因：server 把普通日志输出到了 STDOUT
- 处理：确认使用当前版本代码（日志已定向到 STDERR）

### 3) 端口冲突

- 优先使用 `make inspect-http CLIENT_PORT=... SERVER_PORT=... MCP_HTTP_PORT=...`
- 或先手动清理：

```bash
pkill -f "modelcontextprotocol/inspector|mcp-inspector|euclid_catalog_mcp.server" || true
```

## 发布与部署

发布命令和 Argo CD 说明请看：`docs/release-ops.md`

常用命令：

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make help
make release-zjlab
```
