"""Cross-matching logic for Euclid and DESI catalogs."""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, match_coordinates_sky
from astropy.io import fits
from astropy.table import Table


class CrossMatcher:
    """Cross-match Euclid and DESI catalogs at given coordinates."""

    def __init__(
        self,
        euclid_catalog_path: str,
        desi_catalog_path: str,
        match_radius_arcsec: float = 1.0,
        output_dir: str = "/home/node/.n8n-files/output",
        max_inline_results: int = 10,
    ):
        """
        Initialize the cross-matcher.

        Args:
            euclid_catalog_path: Path to Euclid FITS catalog
            desi_catalog_path: Path to DESI FITS catalog
            match_radius_arcsec: Matching radius in arcseconds (default: 1.0)
            output_dir: Directory to save large result files (default: /tmp/crossmatch_results)
            max_inline_results: Maximum number of results to return inline (default: 10)
        """
        self.euclid_path = euclid_catalog_path
        self.desi_path = desi_catalog_path
        self.match_radius = match_radius_arcsec
        self.output_dir = Path(output_dir)
        self.max_inline_results = max_inline_results
        self.euclid_catalog = None
        self.desi_catalog = None
        self.euclid_coords = None
        self.desi_coords = None

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_catalogs(self):
        """Load both Euclid and DESI catalogs."""
        # Load Euclid catalog
        if not Path(self.euclid_path).exists():
            raise FileNotFoundError(f"Euclid catalog not found: {self.euclid_path}")

        with fits.open(self.euclid_path) as hdul:
            self.euclid_catalog = Table(hdul[1].data)

        # Create Euclid coordinate objects
        self.euclid_coords = SkyCoord(
            ra=self.euclid_catalog["RIGHT_ASCENSION"] * u.deg,
            dec=self.euclid_catalog["DECLINATION"] * u.deg,
        )

        # Load DESI catalog
        if not Path(self.desi_path).exists():
            raise FileNotFoundError(f"DESI catalog not found: {self.desi_path}")

        with fits.open(self.desi_path) as hdul:
            self.desi_catalog = Table(hdul[1].data)

        # Create DESI coordinate objects
        self.desi_coords = SkyCoord(
            ra=self.desi_catalog["RA"] * u.deg, dec=self.desi_catalog["DEC"] * u.deg
        )

    def find_matches_at_position(
        self, ra: float, dec: float, search_radius_arcsec: float = 10.0
    ) -> dict:
        """
        Find cross-matches near a given position.

        Args:
            ra: Right Ascension in degrees
            dec: Declination in degrees
            search_radius_arcsec: Search radius around the position (default: 10 arcsec)

        Returns:
            Dictionary with match results
        """
        if self.euclid_catalog is None or self.desi_catalog is None:
            self.load_catalogs()

        # Create target coordinate
        target_coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)

        # Find Euclid sources near the target position
        euclid_seps = target_coord.separation(self.euclid_coords)
        euclid_nearby_mask = euclid_seps < search_radius_arcsec * u.arcsec

        if not np.any(euclid_nearby_mask):
            return {
                "status": "no_euclid_sources",
                "message": f"No Euclid sources found within {search_radius_arcsec} arcsec of RA={ra:.6f}, DEC={dec:.6f}",
                "input": {"ra": ra, "dec": dec},
                "search_radius_arcsec": search_radius_arcsec,
                "euclid_sources_found": 0,
                "matches": [],
            }

        # Get nearby Euclid sources
        euclid_nearby = self.euclid_catalog[euclid_nearby_mask]
        euclid_nearby_coords = self.euclid_coords[euclid_nearby_mask]
        euclid_nearby_seps = euclid_seps[euclid_nearby_mask]

        # For each nearby Euclid source, find DESI matches
        matches = []

        for i, (euclid_row, euclid_coord, euclid_sep) in enumerate(
            zip(euclid_nearby, euclid_nearby_coords, euclid_nearby_seps)
        ):
            # Match this Euclid source with DESI catalog
            # Need to pass as single-element array to get consistent output
            idx, sep2d, _ = match_coordinates_sky(
                SkyCoord([euclid_coord]), self.desi_coords
            )

            # Extract scalar values
            idx = idx[0]
            sep2d = sep2d[0]

            # Check if within matching radius
            if sep2d < self.match_radius * u.arcsec:
                desi_match = self.desi_catalog[idx]

                match_info = {
                    "euclid": {
                        "object_id": (
                            int(euclid_row["OBJECT_ID"])
                            if "OBJECT_ID" in euclid_row.colnames
                            else None
                        ),
                        "ra": float(euclid_row["RIGHT_ASCENSION"]),
                        "dec": float(euclid_row["DECLINATION"]),
                        "separation_from_target_arcsec": float(euclid_sep.arcsec),
                    },
                    "desi": {
                        "ra": float(desi_match["RA"]),
                        "dec": float(desi_match["DEC"]),
                        "type": (
                            desi_match["TYPE"].decode()
                            if isinstance(desi_match["TYPE"], bytes)
                            else str(desi_match["TYPE"])
                        ),
                    },
                    "match_separation_arcsec": float(sep2d.arcsec),
                }

                # Add photometry if available
                if "FLUX_VIS_PSF" in euclid_row.colnames:
                    match_info["euclid"]["flux_vis_psf"] = float(
                        euclid_row["FLUX_VIS_PSF"]
                    )

                # Add DESI fluxes
                for band in ["G", "R", "Z", "W1", "W2"]:
                    col = f"FLUX_{band}"
                    if col in desi_match.colnames:
                        match_info["desi"][f"flux_{band.lower()}"] = float(
                            desi_match[col]
                        )

                # Add image URLs
                desi_ra = float(desi_match["RA"])
                desi_dec = float(desi_match["DEC"])
                match_info["desi"]["cutout_jpeg_url"] = (
                    f"https://www.legacysurvey.org/viewer/cutout.jpg?"
                    f"ra={desi_ra:.6f}&dec={desi_dec:.6f}&layer=ls-dr10&pixscale=0.262&size=256"
                )
                match_info["desi"]["cutout_fits_url"] = (
                    f"https://www.legacysurvey.org/viewer/fits-cutout?"
                    f"ra={desi_ra:.6f}&dec={desi_dec:.6f}&layer=ls-dr10&size=256"
                )
                match_info["desi"]["viewer_url"] = (
                    f"https://www.legacysurvey.org/viewer?"
                    f"ra={desi_ra:.6f}&dec={desi_dec:.6f}&layer=ls-dr10&zoom=14"
                )

                matches.append(match_info)

        # Always save results to file
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crossmatch_results_{timestamp}.json"
        file_path = self.output_dir / filename

        # Prepare result
        result = {
            "status": "success",
            "input": {"ra": ra, "dec": dec},
            "search_radius_arcsec": search_radius_arcsec,
            "match_radius_arcsec": self.match_radius,
            "euclid_sources_found": int(np.sum(euclid_nearby_mask)),
            "matches_found": len(matches),
            "matches": matches,
        }

        # Save full results to file
        with open(file_path, "w") as f:
            json.dump(result, f, indent=2)

        # Return summary with file path
        # Always include preview (first 3 matches) and file path
        return_data = {
            "status": "success",
            "input": {"ra": ra, "dec": dec},
            "search_radius_arcsec": search_radius_arcsec,
            "match_radius_arcsec": self.match_radius,
            "euclid_sources_found": int(np.sum(euclid_nearby_mask)),
            "matches_found": len(matches),
            "output_file": str(file_path),
            "preview": matches[:3] if len(matches) > 0 else [],  # First 3 matches for display
            "message": f"结果已保存到文件，共 {len(matches)} 个匹配天体"
        }

        return return_data
