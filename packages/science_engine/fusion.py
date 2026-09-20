"""Multi-Science Fusion Engine."""

from typing import List
from packages.science_engine.models import (
    ScienceIntelligenceResult, 
    ScienceStatus, 
    PhysicsResult, 
    ChemistryResult, 
    BiologyResult, 
    ConfidenceScore, 
    Provenance
)

def fuse_evidence(
    region_id: str,
    physics: PhysicsResult,
    chemistry: ChemistryResult,
    biology: BiologyResult,
    provenance_list: List[Provenance]
) -> ScienceIntelligenceResult:
    """
    Combine Physics + Chemistry + Biology into a unified scientific interpretation.
    Preserves individual evidence instead of hiding it.
    """
    
    # Simple logic to determine overall status
    statuses = [physics.status, chemistry.status, biology.status]
    
    if all(s == ScienceStatus.COMPLETE for s in statuses):
        overall_status = ScienceStatus.COMPLETE
    elif all(s == ScienceStatus.INSUFFICIENT_DATA for s in statuses):
        overall_status = ScienceStatus.INSUFFICIENT_DATA
    else:
        overall_status = ScienceStatus.PARTIAL

    # Determine confidence for each separately. 
    # Example mock logic based on statuses:
    phys_conf = 0.9 if physics.status == ScienceStatus.COMPLETE else 0.0
    chem_conf = 0.8 if chemistry.status == ScienceStatus.COMPLETE else 0.0
    bio_conf = 0.7 if biology.status == ScienceStatus.COMPLETE else 0.0
    
    confidence = ConfidenceScore(
        physics=phys_conf,
        chemistry=chem_conf,
        biology=bio_conf
    )

    missing_data = []
    if physics.status == ScienceStatus.INSUFFICIENT_DATA:
        missing_data.append("physics_data")
    if chemistry.status == ScienceStatus.INSUFFICIENT_DATA:
        missing_data.append("chemistry_spectral_data")
    if biology.status == ScienceStatus.INSUFFICIENT_DATA:
        missing_data.append("habitability_environmental_data")

    limitations = [
        "All results are candidate estimates and require ground truth validation.",
        "Biology results indicate habitability, NOT presence of life."
    ]

    return ScienceIntelligenceResult(
        region_id=region_id,
        status=overall_status,
        physics=physics,
        chemistry=chemistry,
        habitability=biology,
        confidence=confidence,
        provenance=provenance_list,
        missing_data=missing_data,
        limitations=limitations
    )
