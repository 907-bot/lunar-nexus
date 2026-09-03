"""Data models and schemas for lunar observations, metadata, and queries."""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


class SensorType(str, Enum):
    OHRC = "OHRC"          # Chandrayaan-2 Orbiter High Resolution Camera (~0.25m)
    TMC2 = "TMC2"          # Chandrayaan-2 Terrain Mapping Camera-2 (~5m)
    IIRS = "IIRS"          # Chandrayaan-2 Imaging Infrared Spectrometer (~80m, 256 bands)
    LRO_NAC = "LRO_NAC"    # LRO Narrow Angle Camera (~0.5 - 2m)
    SELENE_TC = "SELENE_TC"# SELENE (Kaguya) Terrain Camera (~10m)
    SELENE_MI = "SELENE_MI"# SELENE Multiband Imager (~20m)


class MissionType(str, Enum):
    CHANDRAYAAN2 = "CHANDRAYAAN-2"
    LRO = "LRO"
    SELENE = "SELENE"


class BoundingBox(BaseModel):
    min_lat: float = Field(..., description="Minimum latitude in degrees (-90 to 90)")
    max_lat: float = Field(..., description="Maximum latitude in degrees (-90 to 90)")
    min_lon: float = Field(..., description="Minimum longitude in degrees (-180 to 180 or 0 to 360)")
    max_lon: float = Field(..., description="Maximum longitude in degrees (-180 to 180 or 0 to 360)")

    @property
    def center(self) -> Tuple[float, float]:
        """Returns (center_lat, center_lon)."""
        return ((self.min_lat + self.max_lat) / 2.0, (self.min_lon + self.max_lon) / 2.0)

    @property
    def polygon_coords(self) -> List[Tuple[float, float]]:
        """Returns list of (lon, lat) closed coordinates for polygon construction."""
        return [
            (self.min_lon, self.min_lat),
            (self.max_lon, self.min_lat),
            (self.max_lon, self.max_lat),
            (self.min_lon, self.max_lat),
            (self.min_lon, self.min_lat),
        ]


class ObservationGeometry(BaseModel):
    solar_zenith_deg: Optional[float] = None
    solar_azimuth_deg: Optional[float] = None
    incidence_angle_deg: Optional[float] = None
    emission_angle_deg: Optional[float] = None
    phase_angle_deg: Optional[float] = None
    sub_solar_lat: Optional[float] = None
    sub_solar_lon: Optional[float] = None
    spacecraft_altitude_km: Optional[float] = None


class LunarObservation(BaseModel):
    product_id: str = Field(..., description="Unique product identifier (e.g. ch2_ohr_ncp_..., M1144485705LR)")
    mission: MissionType
    sensor: SensorType
    acquisition_time: Optional[datetime] = None
    spatial_resolution_m: Optional[float] = None
    crs: str = "Moon 2000 (IAU2000:30100)"
    bbox: BoundingBox
    footprint_polygon: Optional[List[Tuple[float, float]]] = Field(
        default=None, description="Detailed (lon, lat) polygon boundary coordinates"
    )
    geometry: ObservationGeometry = Field(default_factory=ObservationGeometry)
    
    # File locations
    primary_image_path: Optional[str] = None
    label_path: Optional[str] = None
    preview_image_path: Optional[str] = None
    auxiliary_files: List[str] = Field(default_factory=list)
    
    # Remote source references
    source_url: Optional[str] = None
    download_urls: Dict[str, str] = Field(default_factory=dict)
    
    # Additional raw metadata
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "mission": self.mission.value,
            "sensor": self.sensor.value,
            "acquisition_time": self.acquisition_time.isoformat() if self.acquisition_time else None,
            "resolution_m": self.spatial_resolution_m,
            "bbox": self.bbox.dict(),
            "center": self.bbox.center,
            "primary_image": self.primary_image_path,
            "preview_image": self.preview_image_path,
            "incidence_angle": self.geometry.incidence_angle_deg,
            "solar_azimuth": self.geometry.solar_azimuth_deg,
        }


class CatalogQuery(BaseModel):
    sensors: Optional[List[SensorType]] = None
    bbox: Optional[BoundingBox] = None
    min_resolution_m: Optional[float] = None
    max_resolution_m: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 50
