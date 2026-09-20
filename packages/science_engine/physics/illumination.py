"""Illumination calculations."""

from typing import Tuple, Optional
import math
from packages.data_pipeline.models import ObservationGeometry
from packages.science_engine.models import ScienceStatus

def calculate_illumination(
    latitude: float,
    longitude: float,
    geometry: ObservationGeometry,
    timestamp: Optional[str] = None
) -> dict:
    """
    Estimate local solar geometry and illumination conditions.
    """
    if geometry.solar_zenith_deg is None and geometry.incidence_angle_deg is None:
        return {
            "status": ScienceStatus.INSUFFICIENT_DATA,
            "solar_elevation_deg": None,
            "illumination_condition": "UNKNOWN"
        }
    
    incidence = geometry.incidence_angle_deg if geometry.incidence_angle_deg is not None else geometry.solar_zenith_deg
    elevation = 90.0 - incidence
    
    condition = "UNKNOWN"
    if elevation > 10:
        condition = "WELL_ILLUMINATED"
    elif elevation > 0:
        condition = "LOW_SUN"
    else:
        condition = "SHADOWED_OR_NIGHT"

    return {
        "status": ScienceStatus.COMPLETE,
        "solar_elevation_deg": round(elevation, 2),
        "illumination_condition": condition,
        "solar_azimuth_deg": geometry.solar_azimuth_deg
    }
