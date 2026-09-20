"""Science Engine models."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ScienceStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    MODEL_DERIVED = "MODEL_DERIVED"
    ASSUMED = "ASSUMED"
    SYNTHETIC = "SYNTHETIC"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    POSSIBLE = "POSSIBLE"
    CONFIRMED_BY_SOURCE = "CONFIRMED_BY_SOURCE"

class Provenance(BaseModel):
    source: str
    dataset_id: Optional[str] = None
    observation_id: Optional[str] = None
    processing_method: str
    timestamp: Optional[str] = None
    derived: bool = True
    assumptions: List[str] = Field(default_factory=list)

class ConfidenceScore(BaseModel):
    physics: Optional[float] = None
    chemistry: Optional[float] = None
    biology: Optional[float] = None

class PhysicsResult(BaseModel):
    illumination_condition: Optional[str] = None
    solar_elevation_deg: Optional[float] = None
    shadow_detected: Optional[bool] = None
    estimated_shadow_length_m: Optional[float] = None
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    thermal_estimate: Optional[str] = None
    status: ScienceStatus = ScienceStatus.INSUFFICIENT_DATA

class ChemistryResult(BaseModel):
    spectral_coverage: bool = False
    candidate_materials: List[Dict[str, Any]] = Field(default_factory=list)
    status: ScienceStatus = ScienceStatus.INSUFFICIENT_DATA

class BiologyResult(BaseModel):
    water_ice_evidence: str = EvidenceStatus.INSUFFICIENT_DATA
    thermal_suitability: Optional[str] = None
    radiation_availability: str = EvidenceStatus.INSUFFICIENT_DATA
    terrain_accessibility: Optional[str] = None
    experiment_suitability: Optional[str] = None
    status: ScienceStatus = ScienceStatus.INSUFFICIENT_DATA

class ScienceIntelligenceResult(BaseModel):
    region_id: str
    status: ScienceStatus
    physics: PhysicsResult
    chemistry: ChemistryResult
    habitability: BiologyResult
    confidence: ConfidenceScore
    provenance: List[Provenance]
    missing_data: List[str]
    limitations: List[str]
