"""Chandrayaan-2 (OHRC, TMC-2, IIRS) Data Ingestion and Processor for ISSDC PRADAN datasets."""

from __future__ import annotations
import os
import re
import zipfile
import tarfile
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
import xmltodict
import numpy as np
from PIL import Image

from .models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
)

logger = logging.getLogger("nexus.data.issdc")


class ISSDCClient:
    """Processor and Ingestion Engine for Chandrayaan-2 (ISRO ISSDC PRADAN) Products."""

    def __init__(self, raw_dir: Union[str, Path] = "data/raw", processed_dir: Union[str, Path] = "data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def detect_sensor_from_product_id(product_id: str) -> SensorType:
        """Determines sensor type from standard ISRO Chandrayaan-2 product nomenclature."""
        pid = product_id.upper()
        if "OHR" in pid or "OHRC" in pid:
            return SensorType.OHRC
        elif "TMC" in pid or "TMC2" in pid:
            return SensorType.TMC2
        elif "IIR" in pid or "IIRS" in pid:
            return SensorType.IIRS
        elif "NAC" in pid or "LROC" in pid or pid.startswith("M1"):
            return SensorType.LRO_NAC
        elif "TC" in pid:
            return SensorType.SELENE_TC
        elif "MI" in pid:
            return SensorType.SELENE_MI
        return SensorType.OHRC

    def parse_pds4_xml(self, xml_path: Union[str, Path]) -> LunarObservation:
        """Parses a Chandrayaan-2 PDS4 XML label file into a standardized LunarObservation."""
        xml_path = Path(xml_path)
        with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
            doc = xmltodict.parse(f.read())

        root = doc.get("Product_Observational") or doc.get("Product_Browse") or list(doc.values())[0]
        
        # 1. Product Identification
        ident = root.get("Identification_Area", {})
        logical_ident = ident.get("logical_identifier", "")
        # Extract product id from logical identifier: urn:isro:isda:ch2_ohr:data_calibrated:ch2_ohr_ncp_...
        product_id = logical_ident.split(":")[-1] if ":" in logical_ident else xml_path.stem
        if not product_id:
            product_id = xml_path.stem

        sensor = self.detect_sensor_from_product_id(product_id)

        # 2. Observation & Time
        obs_area = root.get("Observation_Area", {})
        time_coords = obs_area.get("Time_Coordinates", {})
        start_time_str = time_coords.get("start_date_time") or time_coords.get("stop_date_time")
        acq_time = None
        if start_time_str:
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    acq_time = datetime.strptime(start_time_str.rstrip("Z") + ("Z" if "Z" in fmt else ""), fmt)
                    break
                except ValueError:
                    continue

        # 3. Geometry & Coordinates
        disc_area = obs_area.get("Discipline_Area", {})
        geom_area = disc_area.get("geom:Geometry", {}) or disc_area.get("Geometry", {})
        cart_area = disc_area.get("cart:Cartography", {}) or disc_area.get("Cartography", {})

        # Default fallback bounding values
        min_lat, max_lat, min_lon, max_lon = -90.0, 90.0, -180.0, 180.0
        footprint_poly: Optional[List[Tuple[float, float]]] = None

        # Try to find bounding coordinates in cartography or geometry tags
        bounding_coords = (
            cart_area.get("cart:Spatial_Domain", {}).get("cart:Bounding_Coordinates", {})
            or cart_area.get("Spatial_Domain", {}).get("Bounding_Coordinates", {})
            or geom_area.get("geom:Bounding_Coordinates", {})
        )

        if bounding_coords:
            try:
                min_lat = float(bounding_coords.get("cart:south_bounding_coordinate") or bounding_coords.get("south_bounding_coordinate", -90))
                max_lat = float(bounding_coords.get("cart:north_bounding_coordinate") or bounding_coords.get("north_bounding_coordinate", 90))
                min_lon = float(bounding_coords.get("cart:west_bounding_coordinate") or bounding_coords.get("west_bounding_coordinate", -180))
                max_lon = float(bounding_coords.get("cart:east_bounding_coordinate") or bounding_coords.get("east_bounding_coordinate", 180))
            except Exception as e:
                logger.warning(f"Error parsing bounding coordinates: {e}")

        # Try to extract footprint corner points (lon, lat)
        surface_geom = geom_area.get("geom:Surface_Geometry", {}) or geom_area.get("Surface_Geometry", {})
        corners = surface_geom.get("geom:Corner_Points", {}).get("geom:Corner_Point", [])
        if isinstance(corners, list) and len(corners) >= 3:
            poly = []
            for cp in corners:
                try:
                    clat = float(cp.get("geom:latitude", cp.get("latitude")))
                    clon = float(cp.get("geom:longitude", cp.get("longitude")))
                    poly.append((clon, clat))
                except Exception:
                    pass
            if len(poly) >= 3:
                if poly[0] != poly[-1]:
                    poly.append(poly[0])
                footprint_poly = poly
                lats = [p[1] for p in poly]
                lons = [p[0] for p in poly]
                min_lat, max_lat = min(lats), max(lats)
                min_lon, max_lon = min(lons), max(lons)

        # 4. Illumination angles
        illum = geom_area.get("geom:Illumination_Geometry", {}) or geom_area.get("Illumination_Geometry", {})
        geometry = ObservationGeometry(
            solar_zenith_deg=float(illum.get("geom:solar_zenith_angle", illum.get("solar_zenith_angle", 0))) or None,
            solar_azimuth_deg=float(illum.get("geom:solar_azimuth_angle", illum.get("solar_azimuth_angle", 0))) or None,
            incidence_angle_deg=float(illum.get("geom:incidence_angle", illum.get("incidence_angle", 0))) or None,
            emission_angle_deg=float(illum.get("geom:emission_angle", illum.get("emission_angle", 0))) or None,
            phase_angle_deg=float(illum.get("geom:phase_angle", illum.get("phase_angle", 0))) or None,
        )

        # 5. File references in PDS4
        primary_img = None
        aux_files = []
        file_area = root.get("File_Area_Observational", {}) or root.get("File_Area_Browse", {})
        file_obj = file_area.get("File", {})
        if isinstance(file_obj, list):
            file_names = [f.get("file_name") for f in file_obj if f.get("file_name")]
        elif isinstance(file_obj, dict) and file_obj.get("file_name"):
            file_names = [file_obj.get("file_name")]
        else:
            file_names = []

        # Recognized raster image extensions for lunar observation products
        raster_exts = (".img", ".raw", ".tif", ".tiff", ".cub", ".jp2", ".png", ".jpg", ".jpeg")

        # Find actual data file on disk near xml_path
        data_candidates = list(xml_path.parent.glob(f"{xml_path.stem}.*")) + [xml_path.parent / fn for fn in file_names]
        unique_cands = [c for c in set(data_candidates) if c.is_file() and c.resolve() != xml_path.resolve()]

        # Sort candidates prioritizing primary raster data over preview files
        for cand in sorted(unique_cands, key=lambda c: ("preview" in c.name.lower(), c.suffix.lower() not in (".img", ".raw", ".tif", ".tiff"))):
            ext = cand.suffix.lower()
            if ext in raster_exts and not primary_img:
                primary_img = str(cand.resolve())
            else:
                aux_files.append(str(cand.resolve()))

        # Typical spatial resolutions
        res_map = {
            SensorType.OHRC: 0.25,
            SensorType.TMC2: 5.0,
            SensorType.IIRS: 80.0,
            SensorType.LRO_NAC: 0.5,
            SensorType.SELENE_TC: 10.0,
            SensorType.SELENE_MI: 20.0,
        }

        preview_path = primary_img if (primary_img and Path(primary_img).suffix.lower() in (".png", ".jpg", ".jpeg")) else None

        return LunarObservation(
            product_id=product_id,
            mission=MissionType.CHANDRAYAAN2,
            sensor=sensor,
            acquisition_time=acq_time,
            spatial_resolution_m=res_map.get(sensor, 1.0),
            bbox=BoundingBox(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon),
            footprint_polygon=footprint_poly,
            geometry=geometry,
            label_path=str(xml_path.resolve()),
            primary_image_path=primary_img,
            preview_image_path=preview_path,
            auxiliary_files=aux_files,
            extra_metadata={"pds4_source": str(xml_path.name)},
        )

    def ingest_archive(self, archive_path: Union[str, Path]) -> List[LunarObservation]:
        """Extracts a ZIP or TAR archive from ISSDC PRADAN and ingests all contained PDS4 products."""
        archive_path = Path(archive_path)
        extract_dir = self.raw_dir / "issdc_extracted" / archive_path.stem
        extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting ISSDC archive {archive_path.name} -> {extract_dir}")
        if archive_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)
        elif archive_path.suffix.lower() in (".tar", ".gz", ".tgz"):
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(extract_dir)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

        return self.ingest_directory(extract_dir)

    def ingest_directory(self, directory_path: Union[str, Path]) -> List[LunarObservation]:
        """Recursively scans a directory for Chandrayaan-2 XML/PDS4 labels and ingests them."""
        directory_path = Path(directory_path)
        xml_files = list(directory_path.rglob("*.xml"))
        observations: List[LunarObservation] = []

        logger.info(f"Scanning directory {directory_path}: found {len(xml_files)} XML files.")
        for xml_file in xml_files:
            try:
                obs = self.parse_pds4_xml(xml_file)
                # Organize into standard destination
                target_dir = self.raw_dir / obs.sensor.value.lower() / obs.product_id
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy or link files into structured storage
                dest_xml = target_dir / xml_file.name
                if not dest_xml.exists() and xml_file.resolve() != dest_xml.resolve():
                    dest_xml.write_bytes(xml_file.read_bytes())
                obs.label_path = str(dest_xml.resolve())

                # If primary image exists, copy/link into target directory
                if obs.primary_image_path and Path(obs.primary_image_path).exists():
                    src_img = Path(obs.primary_image_path)
                    dest_img = target_dir / src_img.name
                    if not dest_img.exists() and src_img.resolve() != dest_img.resolve():
                        dest_img.write_bytes(src_img.read_bytes())
                    obs.primary_image_path = str(dest_img.resolve())

                    # Generate normalized preview image
                    preview_file = target_dir / f"{obs.product_id}_preview.png"
                    if src_img.suffix.lower() in (".png", ".jpg", ".jpeg") and not preview_file.exists():
                        self._generate_preview_from_raster(obs.primary_image_path, preview_file)
                    elif not preview_file.exists():
                        self._generate_preview_from_raster(obs.primary_image_path, preview_file)

                    obs.preview_image_path = str(preview_file.resolve()) if preview_file.exists() else obs.primary_image_path

                observations.append(obs)
                logger.info(f"Ingested observation: {obs.product_id} ({obs.sensor.value})")
            except Exception as e:
                logger.warning(f"Could not parse XML {xml_file}: {e}")

        return observations

    def _generate_preview_from_raster(self, raster_path: Union[str, Path], output_png: Path):
        """Creates a normalized 8-bit PNG preview from raster/PDS image data."""
        try:
            # Try standard PIL image open (works for GeoTIFF / PNG / JPEG)
            Image.MAX_IMAGE_PIXELS = None
            with Image.open(raster_path) as img:
                img.thumbnail((1024, 1024))
                img.convert("L").save(output_png, "PNG")
                return
        except Exception:
            pass

        try:
            # Read raw binary array as 16-bit or 8-bit grayscale
            raw_bytes = Path(raster_path).read_bytes()
            num_pixels = len(raw_bytes) // 2  # Assume 16-bit integers
            dim = int(np.sqrt(num_pixels))
            if dim > 64:
                arr = np.frombuffer(raw_bytes[: dim * dim * 2], dtype=np.uint16).reshape((dim, dim))
                # Robust percentile contrast stretch (2% to 98%)
                p2, p98 = np.percentile(arr, (2, 98))
                spread = max(float(p98 - p2), 1e-5)
                scaled = np.clip((arr.astype(np.float32) - p2) / spread * 255.0, 0, 255).astype(np.uint8)
                preview = Image.fromarray(scaled)
                preview.thumbnail((1024, 1024))
                preview.save(output_png, "PNG")
        except Exception as ex:
            logger.debug(f"Preview generation skipped for {raster_path}: {ex}")

