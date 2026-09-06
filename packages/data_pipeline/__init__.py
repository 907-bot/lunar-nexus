"""NEXUS-LUNAR Data Acquisition and Ingestion Pipeline.

Provides automated downloaders, parsers, and catalog indexing for:
- Chandrayaan-2 (OHRC, TMC-2, IIRS)
- LRO NAC (Lunar Reconnaissance Orbiter Narrow Angle Camera)
- SELENE / Kaguya (TC / MI)
"""

from .models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
    CatalogQuery,
    ResolutionStrategy,
    PixelBox,
    PatchExtractionConfig,
    ExtractedPatchPair,
    PatchManifest,
)
from .pds_ode_client import PDSODEClient
from .issdc_client import ISSDCClient
from .metadata_parser import MetadataParser
from .catalog import LunarDataCatalog
from .patch_extractor import (
    GeoPixelTransformer,
    ResolutionHarmonizer,
    OverlapQualityScorer,
    OverlapPatchExtractor,
)
from .footprint_engine import (
    FootprintEngine,
    FootprintResult,
    LUNAR_GEOGRAPHIC_PROJ4,
    LUNAR_SOUTH_POLE_STEREO_PROJ4,
)
from .overlap_engine import (
    OverlapEngine,
    OverlapAnalysisResult,
    calculate_overlap,
    find_overlapping_reference_tiles,
)
from .visualization import (
    generate_overlap_visualization,
    generate_patch_comparison_visualization,
)

__all__ = [
    "SensorType",
    "MissionType",
    "BoundingBox",
    "ObservationGeometry",
    "LunarObservation",
    "CatalogQuery",
    "ResolutionStrategy",
    "PixelBox",
    "PatchExtractionConfig",
    "ExtractedPatchPair",
    "PatchManifest",
    "PDSODEClient",
    "ISSDCClient",
    "MetadataParser",
    "LunarDataCatalog",
    "GeoPixelTransformer",
    "ResolutionHarmonizer",
    "OverlapQualityScorer",
    "OverlapPatchExtractor",
    "FootprintEngine",
    "FootprintResult",
    "LUNAR_GEOGRAPHIC_PROJ4",
    "LUNAR_SOUTH_POLE_STEREO_PROJ4",
    "OverlapEngine",
    "OverlapAnalysisResult",
    "calculate_overlap",
    "find_overlapping_reference_tiles",
    "generate_overlap_visualization",
    "generate_patch_comparison_visualization",
]
