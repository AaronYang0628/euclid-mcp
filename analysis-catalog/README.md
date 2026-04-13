# Euclid Catalog MCP Server

MCP server for parsing and analyzing Euclid mission catalog FITS files.

## Features

- Parse FITS catalog files from local storage or S3
- Optimized for large S3 files with header-only parsing (no download needed)
- Extract field information (column names, data types, units, statistics)
- Retrieve object/source data with pagination
- Support for streaming access to minimize bandwidth usage

## Installation

```bash
cd /workspaces/euclid-mcp/analysis-catalog && pip install -e .
```

## Usage

### As MCP Server

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "euclid-catalog": {
      "command": "python",
      "args": ["-m", "euclid_catalog_mcp.server"]
    }
  }
}
```


```shell
python -m euclid_catalog_mcp.server
&&
DANGEROUSLY_OMIT_AUTH=true  npx @modelcontextprotocol/inspector python -m euclid_catalog_mcp.server
```

### Available Tools

1. **list_catalogs** - List FITS files in a directory (local or S3)
2. **parse_fits_header_only** - ⚡ Fast header parsing without downloading data (recommended for S3)
3. **get_catalog_info_with_stats** - Get catalog info with coordinate ranges (downloads data)
4. **get_catalog_fields** - Get detailed field statistics (downloads data)
5. **get_catalog_objects** - Retrieve actual row data with pagination
6. **resolve_tile_id** - Resolve tile id by RA/DEC, optionally using catalog path (filename/header first, mock fallback)

### Tool Selection Guide

- **Just browsing?** Use `list_catalogs` → `parse_fits_header_only`
- **Need data statistics?** Use `get_catalog_fields` or `get_catalog_info_with_stats`
- **Need actual data?** Use `get_catalog_objects`

## Requirements

- Python >= 3.10
- astropy >= 6.0.0
- mcp >= 1.0.0

## Building the Docker Image
```bash
cd /workspaces/euclid-mcp/analysis-catalog
podman build -t harbor.zhejianglab.com/ay-dev/euclid-catalog-mcp:latest .
```

## Release Automation

Use release script for build/push/overlay update/Argo CD sync:

```bash
cd /workspaces/euclid-mcp
analysis-catalog/ops/release.sh --env env-zjlab
```

Detailed guide: `analysis-catalog/docs/release-ops.md`

Make targets:

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make help
make release-zjlab
```
