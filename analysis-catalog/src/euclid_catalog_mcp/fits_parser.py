"""FITS catalog file parser for Euclid mission data."""

from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
from astropy.io import fits
from astropy.table import Table


class FITSCatalogParser:
    """Parser for Euclid FITS catalog files."""

    def __init__(self, fits_path: str):
        """Initialize parser with FITS file path.

        Args:
            fits_path: Path to the FITS file
        """
        self.fits_path = Path(fits_path)
        if not self.fits_path.exists():
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
            Dictionary with basic catalog information
        """
        if not self.hdul:
            raise RuntimeError("FITS file not opened")

        info = {
            "filename": self.fits_path.name,
            "num_hdus": len(self.hdul),
            "hdus": []
        }

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
                valid_data = col[~np.isnan(col)] if np.issubdtype(col.dtype, np.floating) else col
                if len(valid_data) > 0:
                    field_info["statistics"] = {
                        "min": float(np.min(valid_data)),
                        "max": float(np.max(valid_data)),
                        "mean": float(np.mean(valid_data)),
                        "median": float(np.median(valid_data)),
                    }

            fields.append(field_info)

        return fields

    def get_objects(self, start: int = 0, limit: int = 100,
                   columns: Optional[List[str]] = None) -> Dict[str, Any]:
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
                    obj[colname] = float(value) if np.issubdtype(type(value), np.floating) else int(value)
                elif isinstance(value, np.ndarray):
                    obj[colname] = value.tolist()
                elif isinstance(value, bytes):
                    obj[colname] = value.decode('utf-8', errors='ignore')
                else:
                    obj[colname] = str(value)
            objects.append(obj)

        return {
            "start": start,
            "end": end,
            "total": len(self.table),
            "count": len(objects),
            "objects": objects
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
