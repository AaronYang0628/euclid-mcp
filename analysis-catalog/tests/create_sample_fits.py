"""Create a sample FITS catalog file for testing."""

import numpy as np
from astropy.io import fits
from astropy.table import Table

# Create sample catalog data
n_objects = 100

# Generate sample data
data = {
    "OBJECT_ID": np.arange(1, n_objects + 1),
    "RA": np.random.uniform(0, 360, n_objects),
    "DEC": np.random.uniform(-90, 90, n_objects),
    "MAG_AUTO": np.random.uniform(18, 25, n_objects),
    "FLUX_AUTO": np.random.uniform(100, 10000, n_objects),
    "CLASS_STAR": np.random.uniform(0, 1, n_objects),
    "REDSHIFT": np.random.uniform(0, 3, n_objects),
}

# Create table
table = Table(data)

# Add units and descriptions
table["RA"].unit = "deg"
table["RA"].description = "Right Ascension (J2000)"
table["DEC"].unit = "deg"
table["DEC"].description = "Declination (J2000)"
table["MAG_AUTO"].unit = "mag"
table["MAG_AUTO"].description = "Automatic aperture magnitude"
table["FLUX_AUTO"].unit = "count"
table["FLUX_AUTO"].description = "Automatic aperture flux"
table["CLASS_STAR"].description = "Star/Galaxy classifier (0=galaxy, 1=star)"
table["REDSHIFT"].description = "Photometric redshift"

# Create FITS file
primary_hdu = fits.PrimaryHDU()
table_hdu = fits.BinTableHDU(table)
table_hdu.name = "CATALOG"

hdul = fits.HDUList([primary_hdu, table_hdu])

# Save to file
output_file = "sample_euclid_catalog.fits"
hdul.writeto(output_file, overwrite=True)

print(f"Created sample FITS catalog: {output_file}")
print(f"Number of objects: {n_objects}")
print(f"Fields: {', '.join(table.colnames)}")
