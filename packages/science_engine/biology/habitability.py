"""Habitability Analysis."""

from typing import Optional
from packages.science_engine.models import ScienceStatus, EvidenceStatus
from .water_ice import analyze_water_ice

def analyze_habitability(
    water_ice_source_available: bool,
    water_ice_spectral_evidence: bool,
    radiation_data_available: bool,
    thermal_estimate: Optional[str] = None,
    terrain_roughness: Optional[float] = None
) -> dict:
    """
    Environmental Habitability & Biological Experiment Support analysis.
    NOT life detection.
    """
    water_ice_status = analyze_water_ice(water_ice_source_available, water_ice_spectral_evidence)
    
    radiation_status = EvidenceStatus.INSUFFICIENT_DATA
    if radiation_data_available:
        # Mocking actual data reading
        radiation_status = EvidenceStatus.OBSERVED
    
    terrain_accessibility = "UNKNOWN"
    if terrain_roughness is not None:
        if terrain_roughness < 5.0:
            terrain_accessibility = "ACCESSIBLE"
        elif terrain_roughness < 15.0:
            terrain_accessibility = "MODERATE"
        else:
            terrain_accessibility = "DIFFICULT"
            
    return {
        "status": ScienceStatus.COMPLETE,
        "water_ice_evidence": water_ice_status,
        "thermal_suitability": thermal_estimate,
        "radiation_availability": radiation_status,
        "terrain_accessibility": terrain_accessibility,
        "interpretation": "Candidate region for future biological experiments based on environmental limits."
    }
