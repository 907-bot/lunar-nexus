"""Shadow Analysis."""

from typing import Optional
import math
from packages.science_engine.models import ScienceStatus

def analyze_shadow(
    solar_elevation_deg: Optional[float],
    solar_azimuth_deg: Optional[float],
    local_relief_m: Optional[float] = None
) -> dict:
    """
    Estimate shadow length and direction based on local relief.
    """
    if solar_elevation_deg is None or solar_elevation_deg <= 0:
        return {
            "status": ScienceStatus.INSUFFICIENT_DATA if solar_elevation_deg is None else ScienceStatus.COMPLETE,
            "shadow_detected": True if solar_elevation_deg and solar_elevation_deg <= 0 else None,
            "estimated_shadow_length_m": None,
            "shadow_direction_deg": None
        }

    shadow_detected = False
    estimated_length = None
    shadow_direction = None

    if local_relief_m is not None and local_relief_m > 0:
        shadow_detected = True
        # L = h / tan(elevation)
        tan_elev = math.tan(math.radians(solar_elevation_deg))
        if tan_elev > 0:
            estimated_length = round(local_relief_m / tan_elev, 2)
        
        if solar_azimuth_deg is not None:
            shadow_direction = round((solar_azimuth_deg + 180) % 360, 2)

    return {
        "status": ScienceStatus.COMPLETE if local_relief_m is not None else ScienceStatus.PARTIAL,
        "shadow_detected": shadow_detected,
        "estimated_shadow_length_m": estimated_length,
        "shadow_direction_deg": shadow_direction,
        "method": "geometric_shadow_model"
    }
