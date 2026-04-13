"""Tile index resolver for RA/DEC -> tile_id mapping.

Current implementation provides a deterministic mock resolver so downstream
workflows can proceed before official tile boundary data is integrated.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TileResolveResult:
    """Resolved tile identity for a coordinate."""

    tile_id: str
    method: str
    confidence: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "tile_id": self.tile_id,
            "method": self.method,
            "confidence": self.confidence,
        }


def _validate_coord(ra: float, dec: float) -> None:
    if ra < 0 or ra >= 360:
        raise ValueError(f"RA must be in [0, 360). got={ra}")
    if dec < -90 or dec > 90:
        raise ValueError(f"DEC must be in [-90, 90]. got={dec}")


def resolve_tile_id_mock(ra: float, dec: float, prefix: str = "EUC_TILE") -> TileResolveResult:
    """Resolve a deterministic mock tile id from RA/DEC.

    The output is stable for identical coordinates and safe to use as a
    placeholder key in downstream pipelines.
    """

    _validate_coord(float(ra), float(dec))

    payload = f"{ra:.8f},{dec:.8f}".encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest().upper()[:10]
    tile_id = f"{prefix}_{digest}"

    return TileResolveResult(
        tile_id=tile_id,
        method="mock_sha1_radec",
        confidence=0.0,
    )
