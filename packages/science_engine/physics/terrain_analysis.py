"""Terrain Analysis."""

from typing import Optional
from packages.science_engine.models import ScienceStatus

def analyze_terrain(
    dem_available: bool,
    slope_deg: Optional[float] = None,
    aspect_deg: Optional[float] = None,
    elevation_m: Optional[float] = None,
    roughness: Optional[float] = None
) -> dict:
    """
    Calculate terrain properties where DEM data is available.
    """
    if not dem_available:
        return {
            "status": ScienceStatus.INSUFFICIENT_DATA,
            "slope_deg": None,
            "aspect_deg": None,
            "elevation_m": None,
            "roughness": None
        }

    return {
        "status": ScienceStatus.COMPLETE,
        "slope_deg": slope_deg,
        "aspect_deg": aspect_deg,
        "elevation_m": elevation_m,
        "roughness": roughness,
        "units": {
            "elevation": "meters",
            "slope": "degrees",
            "aspect": "degrees"
        }
    }
