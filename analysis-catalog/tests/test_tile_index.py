"""Tests for tile index resolver."""

import pytest

from euclid_catalog_mcp.tile_index import (
    resolve_tile_id_from_filename,
    resolve_tile_id_from_header,
    resolve_tile_id_mock,
)


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


def test_resolve_tile_id_from_filename_tile_token():
    path = (
        "s3://test/1772673283_MER_FINAL_CATALOG_102018211_"
        "EUC_MER_FINAL-CAT_TILE102018211-CC66F6_20241018T214045.289017Z_00.00.fits"
    )
    result = resolve_tile_id_from_filename(path)
    assert result is not None
    assert result.tile_id == "102018211"
    assert result.method in {"filename_tile_token", "filename_catalog_token"}


def test_resolve_tile_id_from_header_keyword():
    result = resolve_tile_id_from_header({"TILEID": 103045678})
    assert result is not None
    assert result.tile_id == "103045678"
    assert result.method == "fits_header_keyword:TILEID"


def test_resolve_tile_id_from_header_scan():
    result = resolve_tile_id_from_header({"COMMENT": "something TILE102018211-AB12"})
    assert result is not None
    assert result.tile_id == "102018211"
