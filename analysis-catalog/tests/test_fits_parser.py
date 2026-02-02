"""Tests for FITS parser."""

import pytest
from pathlib import Path
from euclid_catalog_mcp.fits_parser import FITSCatalogParser


def test_parser_file_not_found():
    """Test that parser raises error for non-existent file."""
    with pytest.raises(FileNotFoundError):
        FITSCatalogParser("nonexistent.fits")


# Additional tests would require sample FITS files
# These can be added when test data is available
