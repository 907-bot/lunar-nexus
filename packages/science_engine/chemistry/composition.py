"""Composition synthesis."""

from typing import List, Dict
from packages.science_engine.models import ScienceStatus

def synthesize_composition(candidate_materials: List[Dict]) -> dict:
    """
    Summarize overall composition estimate from multiple material candidates.
    """
    if not candidate_materials:
        return {
            "status": ScienceStatus.INSUFFICIENT_DATA,
            "interpretation": "No spectral evidence available."
        }
    
    return {
        "status": ScienceStatus.COMPLETE,
        "interpretation": "Spectra is consistent with a mixture of reported candidate materials.",
        "candidates": candidate_materials
    }
