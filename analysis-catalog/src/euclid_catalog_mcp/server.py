"""MCP server for Euclid catalog FITS file parsing - using FastMCP."""

import json
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Handle both relative and absolute imports
try:
    from .fits_parser import FITSCatalogParser
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from fits_parser import FITSCatalogParser

# Get catalog base path from environment variable
CATALOG_BASE_PATH = os.getenv("CATALOG_DATA_PATH", "/data/catalogs")

# Create FastMCP server
mcp = FastMCP("euclid-catalog-mcp")


def resolve_catalog_path(catalog_path: str) -> str:
    """Resolve catalog path, supporting both absolute and relative paths.

    If the path is relative, it will be resolved relative to CATALOG_BASE_PATH.

    Args:
        catalog_path: Absolute or relative path to catalog file

    Returns:
        Absolute path to catalog file
    """
    path = Path(catalog_path)
    if path.is_absolute():
        return str(path)
    return str(Path(CATALOG_BASE_PATH) / catalog_path)


@mcp.tool()
def list_catalogs() -> str:
    """List all available FITS catalog files in the catalog directory.

    Returns:
        JSON string with list of available catalog files
    """
    try:
        catalog_dir = Path(CATALOG_BASE_PATH)
        if not catalog_dir.exists():
            return json.dumps(
                {
                    "error": f"Catalog directory does not exist: {CATALOG_BASE_PATH}",
                    "catalogs": [],
                }
            )

        # Find all .fits files
        fits_files = []
        for fits_file in catalog_dir.rglob("*.fits"):
            relative_path = fits_file.relative_to(catalog_dir)
            fits_files.append(
                {
                    "name": fits_file.name,
                    "path": str(relative_path),
                    "size_mb": round(fits_file.stat().st_size / (1024 * 1024), 2),
                }
            )

        return json.dumps(
            {
                "catalog_base_path": CATALOG_BASE_PATH,
                "total_catalogs": len(fits_files),
                "catalogs": sorted(fits_files, key=lambda x: x["name"]),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def parse_fits_catalog(catalog_path: str) -> str:
    """Parse a FITS catalog file and return basic information.

    Returns HDU structure, number of objects, fields, and coordinate ranges.

    Args:
        catalog_path: Path to FITS file (absolute or relative to catalog base)

    Returns:
        JSON string with catalog information
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        with FITSCatalogParser(resolved_path) as parser:
            info = parser.get_basic_info()
        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_fields(catalog_path: str) -> str:
    """Get detailed field information from catalog.

    Returns data types, units, and statistics for all columns.

    Args:
        catalog_path: Path to FITS file (absolute or relative to catalog base)

    Returns:
        JSON string with field information
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        with FITSCatalogParser(resolved_path) as parser:
            fields = parser.get_fields()
        return json.dumps(fields, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_objects(
    catalog_path: str,
    start: int = 0,
    limit: int = 100,
    columns: list[str] | None = None,
) -> str:
    """Retrieve object data from catalog with pagination.

    Args:
        catalog_path: Path to FITS file (absolute or relative to catalog base)
        start: Starting row index (default: 0)
        limit: Maximum objects to return (default: 100)
        columns: Column names to include (omit for all)

    Returns:
        JSON string with object data
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        with FITSCatalogParser(resolved_path) as parser:
            objects = parser.get_objects(start=start, limit=limit, columns=columns)
        return json.dumps(objects, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_statistics(catalog_path: str) -> str:
    """Get statistical summary of catalog.

    Returns total objects, fields, and field types.

    Args:
        catalog_path: Path to FITS file (absolute or relative to catalog base)

    Returns:
        JSON string with statistics
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        with FITSCatalogParser(resolved_path) as parser:
            stats = parser.get_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        # Run in stdio mode (for MCP Inspector with stdio transport)
        mcp.run(transport="stdio")
    else:
        # Run SSE server on 0.0.0.0 for devcontainer access (default)
        # This allows N8N and other HTTP clients to connect
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
