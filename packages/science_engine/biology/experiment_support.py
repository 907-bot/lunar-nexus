"""Biological Experiment Support."""

from typing import Dict, List, Optional
from packages.science_engine.models import ScienceStatus

def evaluate_experiment_suitability(
    habitability_data: dict,
    requirements: dict
) -> dict:
    """
    Evaluate whether the region's available evidence satisfies specified experimental requirements.
    """
    if habitability_data.get("status") == ScienceStatus.INSUFFICIENT_DATA:
        return {
            "status": "INSUFFICIENT_DATA",
            "evidence": [],
            "missing_data": ["habitability_data"],
            "confidence": 0.0
        }

    met_reqs = []
    missing_data = []
    
    req_water = requirements.get("water_requirement")
    if req_water:
        if habitability_data.get("water_ice_evidence") in [req_water, "CONFIRMED_BY_SOURCE"]:
            met_reqs.append("water_requirement_met")
        elif habitability_data.get("water_ice_evidence") == "INSUFFICIENT_DATA":
            missing_data.append("water_ice_evidence")

    req_terrain = requirements.get("terrain_accessibility")
    if req_terrain:
        if habitability_data.get("terrain_accessibility") == req_terrain:
            met_reqs.append("terrain_accessibility_met")
        elif habitability_data.get("terrain_accessibility") == "UNKNOWN":
            missing_data.append("terrain_accessibility")
            
    # Naive overall status
    if len(missing_data) > 0 and len(met_reqs) > 0:
        status = "PARTIALLY_SUPPORTED"
    elif len(met_reqs) > 0:
        status = "SUPPORTED"
    elif len(missing_data) > 0:
        status = "INSUFFICIENT_DATA"
    else:
        status = "NOT_SUPPORTED"

    return {
        "status": status,
        "evidence": met_reqs,
        "missing_data": missing_data,
        "confidence": 0.5 if status == "PARTIALLY_SUPPORTED" else (0.9 if status == "SUPPORTED" else 0.0)
    }
