"""Unified Metadata Parser for Lunar Datasets (PDS3 LBL, PDS4 XML, GeoTIFF, and JSON Sidecars)."""

from __future__ import annotations
import re
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from datetime import datetime

from .models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
)


class MetadataParser:
    """Parses heterogeneous Lunar metadata formats into normalized LunarObservation schemas."""

    @staticmethod
    def parse_pds3_label(lbl_text_or_path: Union[str, Path]) -> Dict[str, Any]:
        """Parses a PDS3 ODL/LBL label text or file into a nested Python dictionary."""
        if os.path.exists(str(lbl_text_or_path)):
            with open(lbl_text_or_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        else:
            content = str(lbl_text_or_path)

        metadata: Dict[str, Any] = {}
        # Remove comments
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        
        # Parse KEY = VALUE pairs
        pattern = re.compile(r"^\s*([A-Za-z0-9_:]+)\s*=\s*(.+)$", re.MULTILINE)
        matches = pattern.findall(content)
        
        for key, val in matches:
            key = key.strip().upper()
            val = val.strip().strip('"').strip("'")
            # Strip inline comments
            if "/*" in val:
                val = val.split("/*")[0].strip()
            # Clean units like <DEGREE>, <METER>
            val = re.sub(r"<[^>]+>", "", val).strip()
            
            metadata[key] = val

        return metadata

    @classmethod
    def observation_from_pds3(
        cls, lbl_path: Union[str, Path], image_path: Optional[str] = None
    ) -> LunarObservation:
        """Constructs LunarObservation from PDS3 .LBL file (e.g. LRO NAC or SELENE)."""
        lbl_path = Path(lbl_path)
        meta = cls.parse_pds3_label(lbl_path)

        product_id = meta.get("PRODUCT_ID") or meta.get("DATA_SET_ID") or lbl_path.stem
        inst_id = meta.get("INSTRUMENT_ID", "").upper()
        inst_host = meta.get("INSTRUMENT_HOST_NAME", "").upper()

        sensor = SensorType.LRO_NAC
        mission = MissionType.LRO

        if "NARROW" in inst_id or "NAC" in inst_id or "LROC" in inst_id or product_id.startswith("M1"):
            sensor = SensorType.LRO_NAC
            mission = MissionType.LRO
        elif "TERRAIN CAMERA" in inst_id or "TC" in inst_id or "KAGUYA" in inst_host or "SELENE" in inst_host:
            sensor = SensorType.SELENE_TC
            mission = MissionType.SELENE
        elif "MULTIBAND" in inst_id or "MI" in inst_id:
            sensor = SensorType.SELENE_MI
            mission = MissionType.SELENE

        def _to_float(v: Any, default: Optional[float] = None) -> Optional[float]:
            if v is None or str(v).strip() == "":
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        # Coordinates
        min_lat = _to_float(meta.get("MINIMUM_LATITUDE") or meta.get("SOUTH_BOUNDING_COORDINATE"), -90.0)
        max_lat = _to_float(meta.get("MAXIMUM_LATITUDE") or meta.get("NORTH_BOUNDING_COORDINATE"), 90.0)
        raw_min_lon = _to_float(meta.get("WESTERNMOST_LONGITUDE") or meta.get("WEST_BOUNDING_COORDINATE"), -180.0)
        raw_max_lon = _to_float(meta.get("EASTERNMOST_LONGITUDE") or meta.get("EAST_BOUNDING_COORDINATE"), 180.0)

        # Normalize 0..360 to -180..180
        def norm_lon(lon: float) -> float:
            if lon > 180.0:
                return lon - 360.0
            return lon

        min_lon = norm_lon(raw_min_lon)
        max_lon = norm_lon(raw_max_lon)
        if min_lon > max_lon and not (raw_min_lon > 180.0 and raw_max_lon <= 180.0):
            min_lon, max_lon = max_lon, min_lon

        bbox = BoundingBox(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon)

        # Geometry angles (preserve 0.0 for nadir / equatorial angles)
        geom = ObservationGeometry(
            emission_angle_deg=_to_float(meta.get("EMISSION_ANGLE")),
            incidence_angle_deg=_to_float(meta.get("INCIDENCE_ANGLE")),
            phase_angle_deg=_to_float(meta.get("PHASE_ANGLE")),
            solar_azimuth_deg=_to_float(meta.get("SOLAR_AZIMUTH_ANGLE") or meta.get("SUB_SOLAR_AZIMUTH")),
            sub_solar_lat=_to_float(meta.get("SUB_SOLAR_LATITUDE")),
            sub_solar_lon=_to_float(meta.get("SUB_SOLAR_LONGITUDE")),
            spacecraft_altitude_km=_to_float(meta.get("SPACECRAFT_ALTITUDE")),
        )

        # Acquisition time
        start_time_str = meta.get("START_TIME") or meta.get("IMAGE_TIME")
        acq_time = None
        if start_time_str:
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%jT%H:%M:%S.%f", "%Y-%jT%H:%M:%S"):
                try:
                    acq_time = datetime.strptime(start_time_str.rstrip("Z") + ("Z" if "Z" in fmt else ""), fmt)
                    break
                except ValueError:
                    continue

        resolution = _to_float(meta.get("RESOLUTION") or meta.get("MAP_RESOLUTION"), 0.5)

        return LunarObservation(
            product_id=product_id,
            mission=mission,
            sensor=sensor,
            acquisition_time=acq_time,
            spatial_resolution_m=resolution,
            bbox=bbox,
            geometry=geom,
            label_path=str(lbl_path.resolve()),
            primary_image_path=image_path,
            extra_metadata=meta,
        )

    @staticmethod
    def save_sidecar_json(obs: LunarObservation, output_path: Union[str, Path]):
        """Saves a JSON sidecar representation of the LunarObservation."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(obs.model_dump_json(indent=2))
