"""Tests for tile index resolver."""

import pytest

from euclid_catalog_mcp.tile_index import resolve_tile_id_mock


def test_resolve_tile_id_mock_is_deterministic():
    a = resolve_tile_id_mock(ra=51.12015772112324, dec=-26.971838908444358)
    b = resolve_tile_id_mock(ra=51.12015772112324, dec=-26.971838908444358)
    assert a.tile_id == b.tile_id
    assert a.method == "mock_sha1_radec"


def test_resolve_tile_id_mock_validates_ra():
    with pytest.raises(ValueError):
        resolve_tile_id_mock(ra=360.0, dec=0.0)


def test_resolve_tile_id_mock_validates_dec():
    with pytest.raises(ValueError):
        resolve_tile_id_mock(ra=10.0, dec=91.0)
