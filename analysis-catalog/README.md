# Euclid Catalog MCP Server

面向使用者的最简使用说明（开发细节见 `UPDATE.md`）。

## 1) 快速启动（推荐）

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make inspect-http
```

启动后在浏览器打开：`http://127.0.0.1:6275`

Inspector 中填写：

- Transport: `streamable-http`
- URL: `http://127.0.0.1:8000/mcp`
- Proxy Address: `http://127.0.0.1:6278`

## 2) 可选自定义端口

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make inspect-http CLIENT_PORT=6395 SERVER_PORT=6398 MCP_HTTP_PORT=8010
```

## 3) 常用工具

- `list_catalogs`: 列出目录中的 FITS catalog
- `parse_fits_header_only`: 快速查看 FITS 头（推荐先用）
- `get_catalog_info_with_stats`: 读取数据并给出范围统计
- `get_catalog_fields`: 字段统计信息
- `get_catalog_objects`: 按分页读取对象行数据（`columns` 可选；不传返回全部字段，传入则只返回指定字段）
- `resolve_tile_id`: 优先从 catalog 路径/头提取 tile，提取失败时回退到 RA/DEC 数字 mock

## 4) `resolve_tile_id` 示例

只给路径（推荐）：

```json
{
  "catalog_path": "s3://bucket/path/file.fits"
}
```

只给坐标（mock fallback）：

```json
{
  "ra": 10.0,
  "dec": 20.0
}
```

## 5) 连接失败时先检查

- 端口是否转发：`CLIENT_PORT` 和 `SERVER_PORT` 都要转发
- Proxy Address 是否与 `SERVER_PORT` 一致
- 有旧进程占端口时，先重启命令（脚本会自动清理常见旧进程）

## 6) `get_catalog_objects` 字段筛选示例

返回全部字段（不传 `columns`）：

```json
{
  "catalog_path": "s3://bucket/path/file.fits",
  "start": 0,
  "limit": 5
}
```

只返回指定字段（传 `columns`）：

```json
{
  "catalog_path": "s3://bucket/path/file.fits",
  "start": 0,
  "limit": 5,
  "columns": ["OBJECT_ID", "RIGHT_ASCENSION", "DECLINATION"]
}
```

## 7) 作为 MCP Server 接入

```json
{
  "mcpServers": {
    "euclid-catalog": {
      "command": "python3",
      "args": ["-m", "euclid_catalog_mcp.server"]
    }
  }
}
```

## 8) 更多文档

- 开发者文档：`UPDATE.md`
- 发布与部署：`docs/release-ops.md`
