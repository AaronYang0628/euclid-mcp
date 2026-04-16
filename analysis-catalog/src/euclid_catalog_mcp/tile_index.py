"""Tile index resolver utilities.

Resolution priority (when catalog path is available):
1) filename pattern extraction
2) FITS header keyword extraction
3) deterministic RA/DEC mock mapping (fallback)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Mapping, Optional


@dataclass(frozen=True)
class TileResolveResult:
    """Resolved tile identity for a coordinate."""

    tile_id: str
    method: str
    confidence: float
    detail: str | None = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "tile_id": self.tile_id,
            "method": self.method,
            "confidence": self.confidence,
            "detail": self.detail,
        }


_TILE_TOKEN_RE = re.compile(r"TILE(?P<tile>\d{6,})(?:-[A-Za-z0-9]+)?", re.IGNORECASE)
_CATALOG_TOKEN_RE = re.compile(r"MER_FINAL_CATALOG_(?P<tile>\d{6,})", re.IGNORECASE)


def _extract_numeric_tile_token(value: object) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Most reliable: TILE123456789 style token
    m = _TILE_TOKEN_RE.search(text)
    if m:
        return m.group("tile")

    # If value is a bare numeric tile id
    if text.isdigit() and len(text) >= 6:
        return text

    # Sometimes header values include surrounding text
    num = re.search(r"(\d{6,})", text)
    if num:
        return num.group(1)

    return None


def resolve_tile_id_from_filename(path_like: str) -> Optional[TileResolveResult]:
    """Extract tile id from Euclid catalog filename.

    Supports patterns like:
    - EUC_MER_BGSUB-MOSAIC-..._TILE102018211-CC66F6_...fits
    - ...MER_FINAL_CATALOG_102018211_...
    """

    filename = path_like.rsplit("/", 1)[-1]

    m = _TILE_TOKEN_RE.search(filename)
    if m:
        return TileResolveResult(
            tile_id=m.group("tile"),
            method="filename_tile_token",
            confidence=1.0,
            detail=filename,
        )

    m = _CATALOG_TOKEN_RE.search(filename)
    if m:
        return TileResolveResult(
            tile_id=m.group("tile"),
            method="filename_catalog_token",
            confidence=0.9,
            detail=filename,
        )

    # Conservative fallback: whole basename is numeric tile id
    basename = filename.rsplit(".", 1)[0]
    if basename.isdigit() and len(basename) >= 6:
        return TileResolveResult(
            tile_id=basename,
            method="filename_numeric_basename",
            confidence=0.6,
            detail=filename,
        )

    return None


def resolve_tile_id_from_header(
    header: Mapping[str, object],
) -> Optional[TileResolveResult]:
    """Extract tile id from FITS header mapping."""

    key_candidates = [
        "TILEID",
        "TILE_ID",
        "TILEINDEX",
        "TILE_INDEX",
        "TILE",
        "TILENAME",
        "TILE_NAME",
    ]

    # Prefer canonical keywords
    for key in key_candidates:
        if key in header:
            tile = _extract_numeric_tile_token(header.get(key))
            if tile:
                return TileResolveResult(
                    tile_id=tile,
                    method=f"fits_header_keyword:{key}",
                    confidence=0.95,
                    detail=str(header.get(key)),
                )

    # Fallback: scan all header values for TILE token
    for _, value in header.items():
        tile = _extract_numeric_tile_token(value)
        if tile:
            return TileResolveResult(
                tile_id=tile,
                method="fits_header_scan",
                confidence=0.7,
                detail=str(value),
            )

    return None


def _validate_coord(ra: float, dec: float) -> None:
    if ra < 0 or ra >= 360:
        raise ValueError(f"RA must be in [0, 360). got={ra}")
    if dec < -90 or dec > 90:
        raise ValueError(f"DEC must be in [-90, 90]. got={dec}")


def resolve_tile_id_mock(ra: float, dec: float) -> TileResolveResult:
    """Resolve a deterministic numeric mock tile id from RA/DEC.

    The output is stable for identical coordinates and shaped like Euclid tile
    IDs (9-digit numeric string), so downstream systems can treat it uniformly
    with extracted tile ids.
    """

    _validate_coord(float(ra), float(dec))

    payload = f"{ra:.8f},{dec:.8f}".encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()

    # Map hash deterministically into a 9-digit numeric tile id range.
    tile_num = 100000000 + (int(digest[:12], 16) % 900000000)
    tile_id = str(tile_num)

    return TileResolveResult(
        tile_id=tile_id,
        method="mock_numeric_sha1_radec",
        confidence=0.0,
    )
