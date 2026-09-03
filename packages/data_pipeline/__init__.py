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
)
from .pds_ode_client import PDSODEClient
from .issdc_client import ISSDCClient
from .metadata_parser import MetadataParser
from .catalog import LunarDataCatalog

__all__ = [
    "SensorType",
    "MissionType",
    "BoundingBox",
    "ObservationGeometry",
    "LunarObservation",
    "CatalogQuery",
    "PDSODEClient",
    "ISSDCClient",
    "MetadataParser",
    "LunarDataCatalog",
]
