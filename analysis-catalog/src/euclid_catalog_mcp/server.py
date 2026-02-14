"""MCP server for Euclid catalog FITS file parsing - using FastMCP."""

import json
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Handle both relative and absolute imports
try:
    from .fits_parser import FITSCatalogParser
    from .storage import LocalStorage, S3Storage
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from fits_parser import FITSCatalogParser
    from storage import LocalStorage, S3Storage

# Get catalog base path from environment variable
CATALOG_BASE_PATH = os.getenv("CATALOG_DATA_PATH", "/data/catalogs")

# Create FastMCP server
mcp = FastMCP("euclid-catalog-mcp")

# Initialize storage backends
local_storage = LocalStorage(CATALOG_BASE_PATH)
s3_storage = None  # Lazy initialization


def get_storage_backend(path: str):
    """Get appropriate storage backend based on path.

    Args:
        path: File path (local or s3://)

    Returns:
        Tuple of (storage_backend, resolved_path)
    """
    global s3_storage

    if path.startswith("s3://"):
        if s3_storage is None:
            s3_storage = S3Storage()
        return s3_storage, path
    else:
        # Local path - use existing resolve logic
        return local_storage, path


def resolve_catalog_path(catalog_path: str) -> str:
    """Resolve catalog path, supporting both absolute and relative paths.

    If the path is relative, it will be resolved relative to CATALOG_BASE_PATH.
    S3 paths (s3://) are returned as-is.

    Args:
        catalog_path: Absolute, relative, or S3 path to catalog file

    Returns:
        Resolved path to catalog file
    """
    if catalog_path.startswith("s3://"):
        return catalog_path

    path = Path(catalog_path)
    if path.is_absolute():
        return str(path)
    return str(Path(CATALOG_BASE_PATH) / catalog_path)


@mcp.tool()
def list_catalogs(path: str = "") -> str:
    """List all available FITS catalog files in the catalog directory.

    Args:
        path: Directory path (local or s3://). Defaults to CATALOG_BASE_PATH.

    Returns:
        JSON string with list of available catalog files
    """
    try:
        # Use default local path if not specified
        if not path:
            path = CATALOG_BASE_PATH

        storage, resolved_path = get_storage_backend(path)
        fits_files = storage.list_files(resolved_path, "*.fits")

        return json.dumps(
            {
                "catalog_path": resolved_path,
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
        catalog_path: Path to FITS file (local, absolute, relative, or s3://)

    Returns:
        JSON string with catalog information
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        storage, _ = get_storage_backend(resolved_path)
        with FITSCatalogParser(resolved_path, storage=storage) as parser:
            info = parser.get_basic_info()
        return json.dumps(info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_fields(catalog_path: str) -> str:
    """Get detailed field information from catalog.

    Returns data types, units, and statistics for all columns.

    Args:
        catalog_path: Path to FITS file (local, absolute, relative, or s3://)

    Returns:
        JSON string with field information
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        storage, _ = get_storage_backend(resolved_path)
        with FITSCatalogParser(resolved_path, storage=storage) as parser:
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
        catalog_path: Path to FITS file (local, absolute, relative, or s3://)
        start: Starting row index (default: 0)
        limit: Maximum objects to return (default: 100)
        columns: Column names to include (omit for all)

    Returns:
        JSON string with object data
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        storage, _ = get_storage_backend(resolved_path)
        with FITSCatalogParser(resolved_path, storage=storage) as parser:
            objects = parser.get_objects(start=start, limit=limit, columns=columns)
        return json.dumps(objects, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_statistics(catalog_path: str) -> str:
    """Get statistical summary of catalog.

    Returns total objects, fields, and field types.

    Args:
        catalog_path: Path to FITS file (local, absolute, relative, or s3://)

    Returns:
        JSON string with statistics
    """
    try:
        resolved_path = resolve_catalog_path(catalog_path)
        storage, _ = get_storage_backend(resolved_path)
        with FITSCatalogParser(resolved_path, storage=storage) as parser:
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
