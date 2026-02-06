"""MCP server for Euclid catalog FITS file parsing - using FastMCP."""

import json
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Handle both relative and absolute imports
try:
    from .fits_parser import FITSCatalogParser
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from fits_parser import FITSCatalogParser

# Create FastMCP server
mcp = FastMCP("euclid-catalog-mcp")


@mcp.tool()
def parse_fits_catalog(catalog_path: str) -> str:
    """Parse a FITS catalog file and return basic information including HDU structure, number of objects, fields, and coordinate ranges.

    Args:
        catalog_path: Path to the FITS catalog file

    Returns:
        JSON string with catalog information
    """
    try:
        with FITSCatalogParser(catalog_path) as parser:
            info = parser.get_basic_info()
        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_fields(catalog_path: str) -> str:
    """Get detailed information about all fields/columns in the catalog including data types, units, and statistics.

    Args:
        catalog_path: Path to the FITS catalog file

    Returns:
        JSON string with field information
    """
    try:
        with FITSCatalogParser(catalog_path) as parser:
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
    """Retrieve object/source data from the catalog with optional pagination and column filtering.

    Args:
        catalog_path: Path to the FITS catalog file
        start: Starting row index (default: 0)
        limit: Maximum number of objects to return (default: 100)
        columns: List of column names to include (omit for all columns)

    Returns:
        JSON string with object data
    """
    try:
        with FITSCatalogParser(catalog_path) as parser:
            objects = parser.get_objects(start=start, limit=limit, columns=columns)
        return json.dumps(objects, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_statistics(catalog_path: str) -> str:
    """Get statistical summary of the catalog including total objects, fields, and field types.

    Args:
        catalog_path: Path to the FITS catalog file

    Returns:
        JSON string with statistics
    """
    try:
        with FITSCatalogParser(catalog_path) as parser:
            stats = parser.get_statistics()
        return json.dumps(stats, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

 
if __name__ == "__main__":
    # Run SSE server on 0.0.0.0 for devcontainer access
    mcp.run(transport="sse", host="0.0.0.0", port=8004)
