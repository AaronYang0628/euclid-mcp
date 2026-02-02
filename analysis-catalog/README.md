# Euclid Catalog MCP Server

MCP server for parsing and analyzing Euclid mission catalog FITS files.

## Features

- Parse FITS catalog files
- Extract field information (column names, data types, units)
- Retrieve object/source information
- Get statistical summaries of catalog data
- Query specific objects by index or criteria

## Installation

```bash
pip install -e .
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
DANGEROUSLY_OMIT_AUTH=true  npx @modelcontextprotocol/inspector python -m euclid_catalog_mcp.server 
```

### Available Tools

1. **parse_fits_catalog** - Parse a FITS catalog file and return basic information
2. **get_catalog_fields** - Get detailed field/column information
3. **get_catalog_objects** - Retrieve object data with optional filtering
4. **get_catalog_statistics** - Get statistical summary of catalog data

## Requirements

- Python >= 3.10
- astropy >= 6.0.0
- mcp >= 1.0.0
