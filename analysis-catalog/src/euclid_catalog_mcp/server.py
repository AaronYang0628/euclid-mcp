"""MCP server for Euclid catalog FITS file parsing - using FastMCP."""

import json
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env file from project root (analysis-catalog directory)
    # __file__ is: /workspaces/euclid-mcp/analysis-catalog/src/euclid_catalog_mcp/server.py
    # We need to go up 3 levels to reach /workspaces/euclid-mcp/analysis-catalog
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from: {env_path}")
    else:
        print(f"No .env file found at: {env_path}")
except ImportError:
    print("python-dotenv not installed, skipping .env file loading")

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
    """List all available FITS catalog files in a directory.

    Use this tool when you need to:
    - Browse available catalog files in a directory
    - Get file sizes before opening
    - List catalogs in S3 bucket or local directory

    Args:
        path: Directory path (local or s3://bucket/prefix/).
              For S3: s3://bucket-name/path/to/catalogs/
              For local: leave empty to use default, or provide absolute path
              Defaults to CATALOG_BASE_PATH (/data/catalogs).

    Returns:
        JSON string with list of available catalog files including names, paths, and sizes
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
def get_catalog_info_with_stats(catalog_path: str) -> str:
    """Parse FITS catalog with data statistics - downloads and analyzes actual data.

    ⚠️ DOWNLOADS DATA: This tool reads actual table data to compute statistics.
    For large S3 files, use parse_fits_header_only instead unless you need statistics.

    Use this tool when you need:
    - Coordinate ranges (RA/DEC min/max)
    - Data statistics computed from actual values
    - Full catalog analysis including data content

    This tool provides everything from parse_fits_header_only PLUS:
    - Coordinate ranges (if RA/DEC columns exist)
    - Data-derived statistics

    For S3 files: Uses streaming to minimize download, but still reads data portions.
    For large files: Consider using parse_fits_header_only first to check structure.

    Args:
        catalog_path: Path to FITS file
                     S3: s3://bucket-name/path/to/file.fits
                     Local: absolute path or relative to CATALOG_BASE_PATH

    Returns:
        JSON with HDU structure, row/column counts, and coordinate ranges
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
def parse_fits_header_only(catalog_path: str) -> str:
    """Parse FITS file header WITHOUT downloading data - RECOMMENDED for S3 files.

    ⚡ FAST & EFFICIENT: Only downloads ~5-10MB of header data, even for multi-GB files.

    Use this tool when you need to:
    - Get catalog structure and metadata quickly
    - View column definitions (names, types, units)
    - Check number of rows and columns
    - Inspect HDU structure
    - Work with large S3 files (saves time and bandwidth)

    This tool reads ONLY the FITS header portion which contains:
    - HDU structure and types
    - Column names, data types, and units
    - Number of rows (from NAXIS2 header keyword)
    - All metadata without touching actual data

    Perfect for: Initial exploration, schema inspection, large files on S3

    Args:
        catalog_path: Path to FITS file
                     S3: s3://bucket-name/path/to/file.fits
                     Local: absolute path or relative to CATALOG_BASE_PATH

    Returns:
        JSON with HDU structure, column definitions, row counts, and metadata
    """
    try:
        import io
        from astropy.io import fits

        resolved_path = resolve_catalog_path(catalog_path)
        storage, _ = get_storage_backend(resolved_path)

        # For S3, use header-only reading
        if resolved_path.startswith("s3://"):
            header_data = storage.read_fits_header_only(resolved_path)
            hdul = fits.open(io.BytesIO(header_data))
        else:
            # For local files, open normally
            file_obj = storage.open(resolved_path)
            hdul = fits.open(file_obj)

        info = {
            "filename": resolved_path,
            "num_hdus": len(hdul),
            "hdus": []
        }

        for i, hdu in enumerate(hdul):
            hdu_info = {
                "index": i,
                "name": hdu.name,
                "type": type(hdu).__name__,
                "header_cards": len(hdu.header)
            }

            # Get column information from table HDUs
            if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                hdu_info["num_columns"] = len(hdu.columns) if hdu.columns else 0
                hdu_info["columns"] = []

                if hdu.columns:
                    for col in hdu.columns:
                        col_info = {
                            "name": col.name,
                            "format": col.format,
                        }
                        if col.unit:
                            col_info["unit"] = col.unit
                        if col.disp:
                            col_info["display_format"] = col.disp
                        hdu_info["columns"].append(col_info)

                # Get row count from header (NAXIS2)
                if "NAXIS2" in hdu.header:
                    hdu_info["num_rows"] = hdu.header["NAXIS2"]

            info["hdus"].append(hdu_info)

        hdul.close()
        return json.dumps(info, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_catalog_fields(catalog_path: str) -> str:
    """Get detailed field information with statistics - downloads data for analysis.

    ⚠️ DOWNLOADS DATA: Reads actual column data to compute min/max/mean/median.
    For metadata only, use parse_fits_header_only instead.

    Use this tool when you need:
    - Detailed statistics for each numeric column (min, max, mean, median)
    - Data type and shape information
    - Unit and description metadata
    - Value ranges for filtering or analysis

    This tool analyzes actual data values to provide comprehensive field statistics.

    Args:
        catalog_path: Path to FITS file
                     S3: s3://bucket-name/path/to/file.fits
                     Local: absolute path or relative to CATALOG_BASE_PATH

    Returns:
        JSON with detailed field information including statistics for numeric columns
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
    """Retrieve actual object/row data from catalog with pagination.

    ⚠️ DOWNLOADS DATA: Reads actual table rows. Uses streaming for efficiency.

    Use this tool when you need:
    - Actual data values from catalog rows
    - Sample data for inspection
    - Specific objects by row index
    - Subset of columns to reduce data transfer

    Pagination helps manage large catalogs efficiently. For S3 files, uses
    streaming to download only the requested rows when possible.

    Args:
        catalog_path: Path to FITS file
                     S3: s3://bucket-name/path/to/file.fits
                     Local: absolute path or relative to CATALOG_BASE_PATH
        start: Starting row index (0-based, default: 0)
        limit: Maximum number of rows to return (default: 100, max recommended: 1000)
        columns: List of column names to include (default: all columns)
                Example: ["RIGHT_ASCENSION", "DECLINATION", "MAGNITUDE"]

    Returns:
        JSON with object data including start/end indices, total count, and row values
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
    """Get statistical summary of catalog structure - minimal data download.

    ✅ LIGHTWEIGHT: Only reads metadata, minimal data access.

    Use this tool when you need:
    - Total object/row count
    - Total field/column count
    - List of all field names
    - Count of numeric vs non-numeric fields
    - Quick overview without detailed statistics

    This provides a high-level summary without computing per-field statistics.
    For detailed field statistics, use get_catalog_fields instead.

    Args:
        catalog_path: Path to FITS file
                     S3: s3://bucket-name/path/to/file.fits
                     Local: absolute path or relative to CATALOG_BASE_PATH

    Returns:
        JSON with catalog statistics: total objects, fields, field names, and type counts
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
    # Print environment configuration on startup
    print("=" * 60)
    print("Euclid Catalog MCP Server - Environment Configuration")
    print("=" * 60)
    print(f"CATALOG_DATA_PATH: {CATALOG_BASE_PATH}")

    # S3 Configuration
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_endpoint = os.getenv("AWS_ENDPOINT_URL")
    aws_region = os.getenv("AWS_REGION", "not set")

    print("\nS3 Configuration:")
    print(f"  AWS_ACCESS_KEY_ID: {'***set***' if aws_access_key else 'NOT SET'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'***set***' if aws_secret_key else 'NOT SET'}")
    print(
        f"  AWS_ENDPOINT_URL: {aws_endpoint if aws_endpoint else 'NOT SET (using default)'}"
    )
    print(f"  AWS_REGION: {aws_region}")
    print("=" * 60)
    print()

    if "--stdio" in sys.argv:
        # Run in stdio mode (for MCP Inspector with stdio transport)
        print("Starting server in STDIO mode...")
        mcp.run(transport="stdio")
    else:
        # Run SSE server on 0.0.0.0 for devcontainer access (default)
        # This allows N8N and other HTTP clients to connect
        print("Starting server in SSE mode on 0.0.0.0:8000...")
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
