"""FITS catalog file parser for Euclid mission data."""

from pathlib import Path
from typing import Any, Dict, List, Optional, BinaryIO, Union

import numpy as np
from astropy.io import fits
from astropy.table import Table

try:
    from .storage.base import StorageBackend
except ImportError:
    from storage.base import StorageBackend


class FITSCatalogParser:
    """Parser for Euclid FITS catalog files."""

    def __init__(self, fits_path: Union[str, BinaryIO], storage: Optional[StorageBackend] = None):
        """Initialize parser with FITS file path or file-like object.

        Args:
            fits_path: Path to FITS file or file-like object
            storage: Storage backend (for path-based access)
        """
        self.fits_path = fits_path if isinstance(fits_path, str) else None
        self.file_obj = fits_path if not isinstance(fits_path, str) else None
        self.storage = storage

        # Validate file exists if using path with storage
        if self.fits_path and self.storage:
            if not self.storage.exists(self.fits_path):
                raise FileNotFoundError(f"FITS file not found: {fits_path}")
        elif self.fits_path and not self.storage:
            # Legacy: direct path without storage backend
            path = Path(fits_path)
            if not path.exists():
                raise FileNotFoundError(f"FITS file not found: {fits_path}")

        self.hdul = None
        self.table = None

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def open(self):
        """Open the FITS file."""
        # Use file object if provided, otherwise open via storage or path
        if self.file_obj:
            self.hdul = fits.open(self.file_obj)
        elif self.storage and self.fits_path:
            file_obj = self.storage.open(self.fits_path)
            self.hdul = fits.open(file_obj)
        else:
            # Legacy: direct path access
            self.hdul = fits.open(self.fits_path)

        # Find the first table HDU (usually extension 1)
        for hdu in self.hdul:
            if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                self.table = Table(hdu.data)
                break

    def close(self):
        """Close the FITS file."""
        if self.hdul:
            self.hdul.close()

    def get_basic_info(self) -> Dict[str, Any]:
        """Get basic information about the FITS catalog.

        Returns:
            Dictionary with basic catalog information including coordinate ranges
        """
        if not self.hdul:
            raise RuntimeError("FITS file not opened")

        filename = self.fits_path if isinstance(self.fits_path, str) else "stream"
        info = {"filename": filename, "num_hdus": len(self.hdul), "hdus": []}

        for i, hdu in enumerate(self.hdul):
            hdu_info = {
                "index": i,
                "name": hdu.name,
                "type": type(hdu).__name__,
            }

            if isinstance(hdu, (fits.BinTableHDU, fits.TableHDU)):
                hdu_info["num_rows"] = hdu.data.shape[0] if hdu.data is not None else 0
                hdu_info["num_columns"] = len(hdu.columns) if hdu.columns else 0

            info["hdus"].append(hdu_info)

        if self.table:
            info["num_objects"] = len(self.table)
            info["num_fields"] = len(self.table.colnames)

            # Add coordinate ranges if available
            if (
                "RIGHT_ASCENSION" in self.table.colnames
                and "DECLINATION" in self.table.colnames
            ):
                ra = self.table["RIGHT_ASCENSION"]
                dec = self.table["DECLINATION"]
                info["coordinate_ranges"] = {
                    "ra_min": float(np.min(ra)),
                    "ra_max": float(np.max(ra)),
                    "dec_min": float(np.min(dec)),
                    "dec_max": float(np.max(dec)),
                }

        return info

    def get_fields(self) -> List[Dict[str, Any]]:
        """Get detailed field/column information.

        Returns:
            List of field information dictionaries
        """
        if not self.table:
            raise RuntimeError("No table data found in FITS file")

        fields = []
        for colname in self.table.colnames:
            col = self.table[colname]
            field_info = {
                "name": colname,
                "dtype": str(col.dtype),
                "shape": col.shape,
            }

            # Add unit if available
            if col.unit:
                field_info["unit"] = str(col.unit)

            # Add description if available
            if col.description:
                field_info["description"] = col.description

            # Add basic statistics for numeric columns
            if np.issubdtype(col.dtype, np.number):
                valid_data = (
                    col[~np.isnan(col)]
                    if np.issubdtype(col.dtype, np.floating)
                    else col
                )
                if len(valid_data) > 0:
                    field_info["statistics"] = {
                        "min": float(np.min(valid_data)),
                        "max": float(np.max(valid_data)),
                        "mean": float(np.mean(valid_data)),
                        "median": float(np.median(valid_data)),
                    }

            fields.append(field_info)

        return fields

    def get_objects(
        self, start: int = 0, limit: int = 100, columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get object data from the catalog.

        Args:
            start: Starting row index
            limit: Maximum number of rows to return
            columns: List of column names to include (None = all)

        Returns:
            Dictionary with object data
        """
        if not self.table:
            raise RuntimeError("No table data found in FITS file")

        end = min(start + limit, len(self.table))
        subset = self.table[start:end]

        if columns:
            # Filter to requested columns
            subset = subset[columns]

        # Convert to list of dictionaries
        objects = []
        for row in subset:
            obj = {}
            for colname in subset.colnames:
                value = row[colname]
                # Convert numpy types to Python types
                if isinstance(value, (np.integer, np.floating)):
                    obj[colname] = (
                        float(value)
                        if np.issubdtype(type(value), np.floating)
                        else int(value)
                    )
                elif isinstance(value, np.ndarray):
                    obj[colname] = value.tolist()
                elif isinstance(value, bytes):
                    obj[colname] = value.decode("utf-8", errors="ignore")
                else:
                    obj[colname] = str(value)
            objects.append(obj)

        return {
            "start": start,
            "end": end,
            "total": len(self.table),
            "count": len(objects),
            "objects": objects,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical summary of the catalog.

        Returns:
            Dictionary with catalog statistics
        """
        if not self.table:
            raise RuntimeError("No table data found in FITS file")

        stats = {
            "total_objects": len(self.table),
            "total_fields": len(self.table.colnames),
            "field_names": self.table.colnames,
        }

        # Count numeric vs non-numeric fields
        numeric_fields = []
        for colname in self.table.colnames:
            if np.issubdtype(self.table[colname].dtype, np.number):
                numeric_fields.append(colname)

        stats["numeric_fields"] = len(numeric_fields)
        stats["non_numeric_fields"] = len(self.table.colnames) - len(numeric_fields)

        return stats
