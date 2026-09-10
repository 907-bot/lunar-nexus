"""NEXUS-LUNAR POC-7: Spatial Intelligence Data Models & Schemas.

Defines the core typed graph abstractions, terrain intelligence metrics,
illumination metrics, mineralogical/resource indicators, hazard indicators,
and candidate-site suitability evaluations with full geospatial provenance.
"""

from __future__ import annotations
import enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union


class NodeType(str, enum.Enum):
    LUNAR_REGION = "Lunar Region"
    IMAGE = "Image"
    SENSOR = "Sensor"
    OBSERVATION = "Observation"
    TERRAIN_PATCH = "Terrain Patch"
    CRATER = "Crater"
    RIDGE = "Ridge"
    SLOPE_REGION = "Slope Region"
    HAZARD = "Hazard"
    ILLUMINATION_STATE = "Illumination State"
    SPECTRAL_OBSERVATION = "Spectral Observation"
    CANDIDATE_SITE = "Candidate Site"
    HABITAT_COMPONENT = "Habitat Component"
    # First-Principles Scientific Node Types
    PHYSICAL_LAYER = "Physical Layer"
    THERMOCHEMICAL_STATE = "Thermochemical State"
    BIOLOGICAL_ENVELOPE = "Biological Envelope"
    FREQUENCY_SPECTRUM = "Frequency Spectrum"


class RelationType(str, enum.Enum):
    OBSERVED_BY = "OBSERVED_BY"
    CORRESPONDS_TO = "CORRESPONDS_TO"
    OVERLAPS = "OVERLAPS"
    LOCATED_NEAR = "LOCATED_NEAR"
    CONTAINS = "CONTAINS"
    HAS_SLOPE = "HAS_SLOPE"
    HAS_ELEVATION = "HAS_ELEVATION"
    HAS_ILLUMINATION = "HAS_ILLUMINATION"
    HAS_RESOURCE_INDICATOR = "HAS_RESOURCE_INDICATOR"
    SUITABLE_FOR = "SUITABLE_FOR"
    CONSTRAINS = "CONSTRAINS"
    # First-Principles Scientific Relation Types
    HAS_FREQUENCY_PROFILE = "HAS_FREQUENCY_PROFILE"
    HAS_THERMAL_PROFILE = "HAS_THERMAL_PROFILE"
    YIELDS_VOLATILE = "YIELDS_VOLATILE"
    SHIELDS_RADIATION = "SHIELDS_RADIATION"
    SUPPORTS_ECLSS = "SUPPORTS_ECLSS"


class SlopeCategory(str, enum.Enum):
    LOW = "LOW"            # < 5 degrees
    MODERATE = "MODERATE"  # 5 - 12 degrees
    HIGH = "HIGH"          # 12 - 20 degrees
    VERY_HIGH = "VERY_HIGH"# > 20 degrees


class IlluminationStatus(str, enum.Enum):
    ILLUMINATED = "ILLUMINATED"
    PARTIALLY_ILLUMINATED = "PARTIALLY_ILLUMINATED"
    SHADOWED = "SHADOWED"
    LOW_LIGHT = "LOW_LIGHT"
    UNKNOWN = "UNKNOWN"


class HazardType(str, enum.Enum):
    STEEP_SLOPE = "STEEP_SLOPE"
    ROUGH_TERRAIN = "ROUGH_TERRAIN"
    CRATER_RIM = "CRATER_RIM"
    PERMANENT_SHADOW = "PERMANENT_SHADOW"         # Requires multi-epoch temporal confirmation
    LOW_LIGHT_CONSTRAINT = "LOW_LIGHT_CONSTRAINT" # Single-epoch low illumination operational constraint
    UNSTABLE_TERRAIN = "UNSTABLE_TERRAIN"


class HazardSeverity(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SiteDataStatus(str, enum.Enum):
    DATA_DRIVEN = "DATA-DRIVEN"
    PARTIALLY_OBSERVABLE = "PARTIALLY OBSERVABLE"
    SYNTHETIC_DEMO = "SYNTHETIC OFFLINE DEMO"


@dataclass
class ProvenanceRecord:
    """Rigorous scientific data provenance metadata."""
    dataset: str
    sensor: str
    observation_id: str
    patch_id: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None
    crs: str = "Lunar South Pole Stereographic (ESRI:104903)"
    processing_method: str = "NEXUS Spatial Intelligence Engine"
    version: str = "1.0.0"
    experiment_id: str = "EXP_POC7_DEMO"
    timestamp: str = ""
    status: str = "PROTOTYPE"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class GraphNode:
    """Node entity in the Lunar Spatial Knowledge Graph."""
    id: str
    type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, NodeType) else str(self.type),
            "properties": self.properties,
            "provenance": self.provenance,
        }


@dataclass
class GraphEdge:
    """Directed edge entity in the Lunar Spatial Knowledge Graph."""
    source: str
    relationship: RelationType
    target: str
    properties: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "relationship": self.relationship.value if isinstance(self.relationship, RelationType) else str(self.relationship),
            "target": self.target,
            "properties": self.properties,
            "provenance": self.provenance,
        }


@dataclass
class TerrainMetrics:
    """Topographic and geomorphological metrics for a lunar surface region."""
    patch_id: str
    elevation_min_m: float
    elevation_max_m: float
    elevation_mean_m: float
    elevation_median_m: float
    elevation_units: str = "meters"
    slope_degrees: float = 0.0
    slope_category: SlopeCategory = SlopeCategory.LOW
    aspect_degrees: float = 0.0
    aspect_cardinal: str = "N"
    roughness_score: float = 0.0
    roughness_method: str = "local_elevation_std_dev"
    nearest_crater_id: Optional[str] = None
    distance_to_crater_m: Optional[float] = None
    distance_units: str = "meters"
    boundaries: Dict[str, Any] = field(default_factory=dict)  # bbox, lat/lon, crs, area_km2
    data_status: str = "DATA-DRIVEN"
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.slope_category, SlopeCategory):
            d["slope_category"] = self.slope_category.value
        return d


@dataclass
class IlluminationMetrics:
    """Illumination intelligence and solar energy potential indicators."""
    patch_id: str
    illumination_mean: float
    illumination_variance: float
    shadow_fraction: float
    illumination_state: IlluminationStatus = IlluminationStatus.ILLUMINATED
    solar_potential_indicator: str = "POTENTIAL SOLAR-ENERGY ZONE"
    temporal_consistency: str = "TEMPORAL_VALIDATION_UNAVAILABLE"
    data_status: str = "DATA-DRIVEN"
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.illumination_state, IlluminationStatus):
            d["illumination_state"] = self.illumination_state.value
        return d


@dataclass
class ResourceIndicator:
    """Resource-related spectral/mineralogical indicator from sensor observations (e.g. IIRS)."""
    indicator_id: str
    sensor: str = "IIRS"
    wavelength_band_um: Optional[str] = "2.8-3.0 um (OH/H2O absorption band)"
    mineralogical_feature: str = "RESOURCE-RELATED SPECTRAL INDICATOR"
    indicator_score: float = 0.0  # 0.0 - 1.0 indicator intensity
    coordinates: Dict[str, float] = field(default_factory=dict)
    associated_patch_id: str = ""
    # data_status: must be explicitly set to distinguish real IIRS observations from synthetic proxies.
    # Valid values: "DATA-DRIVEN" (real calibrated IIRS product linked),
    #               "SYNTHETIC OFFLINE DEMO" (deterministic offline proxy, no real IIRS file).
    data_status: str = "SYNTHETIC OFFLINE DEMO"
    disclaimer: str = (
        "SCIENTIFIC NOTICE: This represents a spatial spectral indicator only, "
        "not confirmed mineable deposits or extracted resources."
    )
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HazardIndicator:
    """Spatial hazard indicator constraining lunar exploration or infrastructure."""
    hazard_id: str
    hazard_type: HazardType
    severity: HazardSeverity
    description: str
    source_metric: str
    affected_patch_id: str
    coordinates: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.95
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.hazard_type, HazardType):
            d["hazard_type"] = self.hazard_type.value
        if isinstance(self.severity, HazardSeverity):
            d["severity"] = self.severity.value
        return d


@dataclass
class CandidateSiteExplanation:
    """Explainable positive and constraining factors for candidate site ranking."""
    site_id: str
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    summary_verdict: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateSite:
    """Comprehensive multi-factor spatial intelligence candidate site evaluation."""
    site_id: str
    patch_id: str
    coordinates: Dict[str, float]  # lat, lon
    bbox: Dict[str, float]        # min_lat, max_lat, min_lon, max_lon
    terrain_score: float          # 0.0 to 1.0 (favors low slope and low roughness)
    illumination_score: float     # 0.0 to 1.0 (favors high illumination, low shadow)
    hazard_penalty: float         # 0.0 to 1.0 (penalty for detected hazards)
    resource_indicator_score: float # 0.0 to 1.0 (bonus for spectral indicators)
    spatial_data_quality_score: float # 0.0 to 1.0 (from POC-6 registration confidence/inlier ratio)
    overall_suitability_score: float  # Weighted composite score
    scoring_weights: Dict[str, float] = field(default_factory=lambda: {
        "terrain": 0.30,
        "illumination": 0.25,
        "hazard_penalty": 0.20,
        "resource": 0.10,
        "data_quality": 0.15,
    })
    data_status: SiteDataStatus = SiteDataStatus.DATA_DRIVEN
    hazards_affecting: List[str] = field(default_factory=list)
    contributing_observations: List[str] = field(default_factory=list)
    explanation: Optional[CandidateSiteExplanation] = None
    disclaimer: str = (
        "SPATIAL INTELLIGENCE NOTICE: This candidate site ranking is a spatial-suitability "
        "prototype based on preliminary orbital observations. It does not constitute final "
        "lunar landing certification or habitat engineering approval."
    )
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if isinstance(self.data_status, SiteDataStatus):
            d["data_status"] = self.data_status.value
        return d


@dataclass
class POC7Handover:
    """Handover payload for POC-8 Habitat Digital Twin integration."""
    schema_version: str = "1.0.0"
    target_downstream: str = "POC-8 Habitat Digital Twin Engine"
    generated_at: str = ""
    experiment_id: str = "EXP_POC7_HANDOVER"
    candidate_sites: List[Dict[str, Any]] = field(default_factory=list)
    spatial_knowledge_graph_summary: Dict[str, Any] = field(default_factory=dict)
    terrain_constraints_summary: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
