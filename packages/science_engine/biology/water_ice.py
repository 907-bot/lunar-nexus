"""Water / Ice Analysis."""

from typing import Optional
from packages.science_engine.models import EvidenceStatus

def analyze_water_ice(
    authoritative_source_available: bool,
    spectral_evidence: bool = False
) -> EvidenceStatus:
    """
    Evaluate water/ice evidence from available datasets.
    """
    if authoritative_source_available:
        return EvidenceStatus.CONFIRMED_BY_SOURCE
    if spectral_evidence:
        return EvidenceStatus.POSSIBLE
    return EvidenceStatus.INSUFFICIENT_DATA
