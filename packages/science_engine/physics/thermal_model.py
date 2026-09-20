"""Thermal Estimation Model."""

from typing import Optional
from packages.science_engine.models import ScienceStatus

def estimate_thermal_condition(
    solar_elevation_deg: Optional[float],
    albedo: Optional[float] = None,
    latitude: Optional[float] = None
) -> dict:
    """
    Implement a scientifically cautious thermal estimation module.
    """
    if solar_elevation_deg is None:
        return {
            "status": ScienceStatus.INSUFFICIENT_DATA,
            "thermal_estimate": None
        }

    estimate = "UNKNOWN"
    if solar_elevation_deg <= 0:
        estimate = "MODEL_DERIVED_THERMAL_ESTIMATE: EXTREME_COLD"
    elif solar_elevation_deg > 45:
        if latitude is not None and abs(latitude) > 75:
            estimate = "MODEL_DERIVED_THERMAL_ESTIMATE: MODERATE"
        else:
            estimate = "MODEL_DERIVED_THERMAL_ESTIMATE: HOT"
    else:
        estimate = "MODEL_DERIVED_THERMAL_ESTIMATE: MODERATE"

    return {
        "status": ScienceStatus.COMPLETE,
        "thermal_estimate": estimate,
        "assumptions": [
            "Thermal estimate is derived from solar elevation and latitude.",
            "This is NOT a measured temperature."
        ]
    }
