"""MCP server for Euclid-DESI cross-matching - using FastMCP."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# Handle both relative and absolute imports
try:
    from .matcher import CrossMatcher
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent))
    from matcher import CrossMatcher

# Create FastMCP server
mcp = FastMCP("euclid-crossmatch-mcp")

# Global matcher instance (lazy loaded)
_matcher: Optional[CrossMatcher] = None


def get_matcher() -> CrossMatcher:
    """Get or create the global matcher instance."""
    global _matcher
    if _matcher is None:
        # Get catalog paths from environment variables or use defaults
        default_euclid = (
            "/workspaces/euclid-mcp/"
            "projects_CSST_shared-data_euclid_aws-mirrors_q1_catalogs_"
            "MER_FINAL_CATALOG_102018211_EUC_MER_FINAL-CAT_"
            "TILE102018211-CC66F6_20241018T214045.289017Z_00.00.fits"
        )
        euclid_path = os.environ.get("EUCLID_CATALOG_PATH", default_euclid)
        desi_path = os.environ.get(
            "DESI_CATALOG_PATH",
            "/workspaces/euclid-mcp/cross-matching/tests/test_desi_matched.fits",
        )

        if not desi_path:
            raise ValueError(
                "DESI_CATALOG_PATH environment variable not set. "
                "Please set it to the path of your DESI catalog file."
            )

        match_radius = float(os.environ.get("MATCH_RADIUS_ARCSEC", "1.0"))
        output_dir = os.environ.get("CROSSMATCH_OUTPUT_DIR", "/home/node/.n8n-files/output")
        max_inline_results = int(os.environ.get("MAX_INLINE_RESULTS", "10"))

        _matcher = CrossMatcher(
            euclid_path, desi_path, match_radius, output_dir, max_inline_results
        )
        _matcher.load_catalogs()

    return _matcher


@mcp.tool()
def match_euclid_desi(ra: float, dec: float, search_radius: float = 10.0) -> str:
    """Cross-match Euclid and DESI catalogs at given coordinates.

    This tool searches for Euclid sources near the given position and
    finds their DESI counterparts within the matching radius.

    Args:
        ra: Right Ascension in degrees
        dec: Declination in degrees
        search_radius: Search radius around the position in arcseconds
            (default: 10.0)

    Returns:
        JSON string with cross-match results including:
        - Number of Euclid sources found near the position
        - Matched sources with their properties
        - DESI image cutout URLs for visualization
        - If results > MAX_INLINE_RESULTS: output_file path and preview
        - If results <= MAX_INLINE_RESULTS: full matches array

    Environment Variables:
        EUCLID_CATALOG_PATH: Path to Euclid FITS catalog
        DESI_CATALOG_PATH: Path to DESI FITS catalog
        MATCH_RADIUS_ARCSEC: Matching radius in arcseconds (default: 1.0)
        CROSSMATCH_OUTPUT_DIR: Directory for saving large results (default: /tmp/crossmatch_results)
        MAX_INLINE_RESULTS: Max results to return inline (default: 10)
    """
    try:
        matcher = get_matcher()
        result = matcher.find_matches_at_position(ra, dec, search_radius)
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
        }
        return json.dumps(error_result)


if __name__ == "__main__":
    # Default to SSE mode for N8N and other HTTP clients
    # Use stdio mode only when explicitly requested
    if "--stdio" in sys.argv:
        # Run in stdio mode (for MCP Inspector with stdio transport)
        mcp.run(transport="stdio")
    else:
        # Run SSE server on 0.0.0.0 for devcontainer access (default)
        # This allows N8N and other HTTP clients to connect
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
