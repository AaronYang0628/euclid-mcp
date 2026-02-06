# Euclid Cross-Match MCP Server

MCP server for cross-matching Euclid and DESI astronomical catalogs.

## Features

- `match_euclid_desi`: Cross-match Euclid and DESI catalogs at given RA/DEC coordinates
- Finds Euclid sources near the target position
- Matches them with DESI Legacy Survey sources
- Returns photometry, object types, and image URLs

## Installation

```bash
cd /workspaces/euclid-mcp/cross-matching && pip install -e .
```

## Configuration

Set the following environment variables before running the server:

```bash
export EUCLID_CATALOG_PATH="/path/to/euclid_catalog.fits"
export DESI_CATALOG_PATH="/path/to/desi_sweep_catalog.fits"
export MATCH_RADIUS_ARCSEC="1.0"  # Optional, default is 1.0
```

Or create a `.env` file in the project directory:

```bash
EUCLID_CATALOG_PATH=/path/to/euclid_catalog.fits
DESI_CATALOG_PATH=/path/to/desi_sweep_catalog.fits
MATCH_RADIUS_ARCSEC=1.0
```

## Usage

### As MCP Server (SSE Mode - Default)

Run the server for N8N, HTTP clients, or MCP Inspector with SSE:

```bash
python -m euclid_crossmatch_mcp.server
```

The server will run on `http://0.0.0.0:8002` by default.

### With MCP Inspector

**Option 1: SSE Mode (Recommended)**

Terminal 1 - Start server:
```bash
export EUCLID_CATALOG_PATH="/path/to/euclid_catalog.fits"
export DESI_CATALOG_PATH="/path/to/desi_sweep_catalog.fits"

python -m euclid_crossmatch_mcp.server
```

Terminal 2 - Connect Inspector:
```bash
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector sse http://localhost:8002/sse
```

**Option 2: stdio Mode**

```bash
export EUCLID_CATALOG_PATH="/path/to/euclid_catalog.fits"
export DESI_CATALOG_PATH="/path/to/desi_sweep_catalog.fits"

DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector \
  python -m euclid_crossmatch_mcp.server --stdio
```

### With N8N

1. Start the server:
```bash
python -m euclid_crossmatch_mcp.server
```

2. In N8N, use the HTTP Request node:
   - Method: POST
   - URL: `http://localhost:8002/sse`
   - Body: MCP protocol JSON

## Development

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Tools

### match_euclid_desi

Cross-match Euclid and DESI catalogs at given coordinates.

**Parameters:**
- `ra` (float): Right Ascension in degrees
- `dec` (float): Declination in degrees
- `search_radius` (float, optional): Search radius around the position in arcseconds (default: 10.0)

**Returns:**
JSON string with cross-match results including:
- `status`: "success", "no_euclid_sources", or "error"
- `euclid_sources_found`: Number of Euclid sources within search radius
- `matches_found`: Number of successful cross-matches
- `matches`: Array of matched sources with:
  - Euclid properties (RA, DEC, object ID, photometry)
  - DESI properties (RA, DEC, type, photometry)
  - Match separation in arcseconds
  - DESI image cutout URLs (JPEG, FITS, viewer)

**Example:**

```json
{
  "status": "success",
  "input": {"ra": 150.1234, "dec": 2.5678},
  "search_radius_arcsec": 10.0,
  "match_radius_arcsec": 1.0,
  "euclid_sources_found": 3,
  "matches_found": 2,
  "matches": [
    {
      "euclid": {
        "object_id": 12345,
        "ra": 150.1235,
        "dec": 2.5679,
        "separation_from_target_arcsec": 0.5,
        "flux_vis_psf": 1234.5
      },
      "desi": {
        "ra": 150.1236,
        "dec": 2.5679,
        "type": "PSF",
        "flux_g": 100.2,
        "flux_r": 150.3,
        "flux_z": 200.4,
        "cutout_jpeg_url": "https://...",
        "cutout_fits_url": "https://...",
        "viewer_url": "https://..."
      },
      "match_separation_arcsec": 0.8
    }
  ]
}
```

## Data Requirements

### Euclid Catalog

FITS file with HDU 1 containing a table with columns:
- `RIGHT_ASCENSION`: RA in degrees
- `DECLINATION`: DEC in degrees
- `OBJECT_ID`: Unique object identifier (optional)
- `FLUX_VIS_PSF`: VIS band PSF flux (optional)

### DESI Catalog

FITS file (sweep catalog) with HDU 1 containing a table with columns:
- `RA`: Right Ascension in degrees
- `DEC`: Declination in degrees
- `TYPE`: Object type (PSF, REX, EXP, DEV, etc.)
- `FLUX_G`, `FLUX_R`, `FLUX_Z`: g, r, z band fluxes
- `FLUX_W1`, `FLUX_W2`: WISE W1, W2 fluxes (optional)

Download DESI sweep catalogs from:
https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr10/
