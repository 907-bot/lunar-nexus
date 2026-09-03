"""Client for querying and downloading Lunar data via NASA PDS Orbital Data Explorer (ODE) REST API and ASU LROC archive."""

from __future__ import annotations
import os
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import requests
from tqdm import tqdm

from .models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
)

logger = logging.getLogger("nexus.data.pds")
logging.basicConfig(level=logging.INFO)


class PDSODEClient:
    """NASA PDS Orbital Data Explorer (ODE) REST API Client for Lunar Data."""

    ODE_BASE_URL = "https://oderest.rsl.wustl.edu/live2/"
    
    # Mapping sensor types to ODE search parameters (IHID, IID, PT)
    SENSOR_CONFIG = {
        SensorType.LRO_NAC: {
            "mission": MissionType.LRO,
            "target": "Moon",
            "ihid": "LRO",
            "iid": "LROC",
            "pt": "EDRNAC4", # EDRNAC4 (Experiment Data Record NAC) or CDRNAC4
            "default_res": 0.5,
        },
        SensorType.SELENE_TC: {
            "mission": MissionType.SELENE,
            "target": "Moon",
            "ihid": "SLN",
            "iid": "TC",
            "pt": "TCSL2B", # TCSL2B (Level 2B0) or TCORT
            "default_res": 10.0,
        },
        SensorType.SELENE_MI: {
            "mission": MissionType.SELENE,
            "target": "Moon",
            "ihid": "SLN",
            "iid": "MI",
            "pt": "MISMAP",
            "default_res": 20.0,
        },
    }

    def __init__(self, output_dir: Union[str, Path] = "data/raw"):
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "NEXUS-LUNAR/1.0 (SIH AI Lunar Correspondence Research; contact@nexus-lunar.local)"
        })

    def query_products(
        self,
        sensor: SensorType = SensorType.LRO_NAC,
        bbox: Optional[BoundingBox] = None,
        product_id: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query Lunar products from NASA ODE REST API.
        
        Args:
            sensor: Target lunar sensor (LRO_NAC, SELENE_TC, etc.)
            bbox: Bounding box in lat/lon
            product_id: Optional specific product ID to match
            product_type: EDR, CDR, RDR, etc.
            limit: Maximum number of products to return
            offset: Result offset for pagination
        """
        cfg = self.SENSOR_CONFIG.get(sensor, self.SENSOR_CONFIG[SensorType.LRO_NAC])
        
        params: Dict[str, Any] = {
            "target": cfg.get("target", "Moon"),
            "query": "product",
            "results": "fpm",  # files + product metadata + spatial geometry
            "output": "JSON",
            "limit": str(limit),
            "offset": str(offset),
        }

        if "ihid" in cfg:
            params["ihid"] = cfg["ihid"]
        if "iid" in cfg:
            params["iid"] = cfg["iid"]
        if product_type:
            params["pt"] = product_type
        elif "pt" in cfg:
            params["pt"] = cfg["pt"]

        if product_id:
            params["prodid"] = product_id

        if bbox:
            params["minlat"] = f"{bbox.min_lat:.4f}"
            params["maxlat"] = f"{bbox.max_lat:.4f}"
            # ODE uses 0-360 longitude internally for western/eastern lon
            w_lon = (bbox.min_lon + 360.0) % 360.0
            e_lon = (bbox.max_lon + 360.0) % 360.0
            params["westernlon"] = f"{w_lon:.4f}"
            params["easternlon"] = f"{e_lon:.4f}"

        logger.info(f"Querying NASA ODE API for {sensor.value} with params: {params}")
        
        try:
            resp = self.session.get(self.ODE_BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Failed to query ODE API: {e}")
            return []

        ode_obj = data.get("ODEResults", {})
        status = ode_obj.get("Status")
        if status not in ("Success", "Warning"):
            logger.warning(f"ODE query returned status: {status}, message: {ode_obj.get('Description')}")
            return []

        products = ode_obj.get("Products", {}).get("Product", [])
        if isinstance(products, dict):
            products = [products]

        logger.info(f"Retrieved {len(products)} products from ODE.")
        return products

    def convert_ode_product_to_observation(
        self, product: Dict[str, Any], sensor: SensorType
    ) -> LunarObservation:
        """Parses ODE product dictionary into standardized LunarObservation schema."""
        prod_id = product.get("pdsid") or product.get("PdsId") or product.get("ProductId") or "UNKNOWN_PROD"
        cfg = self.SENSOR_CONFIG.get(sensor, self.SENSOR_CONFIG[SensorType.LRO_NAC])

        def _to_float(v: Any, default: Optional[float] = None) -> Optional[float]:
            if v is None or v == "":
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default

        # 1. Extract bounding coordinates (ODE uses Minimum_latitude / Westernmost_longitude)
        min_lat = _to_float(product.get("Minimum_latitude") or product.get("Min_lat") or product.get("Minlat"), -90.0)
        max_lat = _to_float(product.get("Maximum_latitude") or product.get("Max_lat") or product.get("Maxlat"), 90.0)
        raw_w_lon = _to_float(product.get("Westernmost_longitude") or product.get("Western_lon") or product.get("Westernlon"), -180.0)
        raw_e_lon = _to_float(product.get("Easternmost_longitude") or product.get("Eastern_lon") or product.get("Easternlon"), 180.0)

        def norm_lon(lon: float) -> float:
            if lon > 180.0:
                return lon - 360.0
            return lon

        min_lon = norm_lon(raw_w_lon)
        max_lon = norm_lon(raw_e_lon)
        if min_lon > max_lon and not (raw_w_lon > 180.0 and raw_e_lon <= 180.0):
            min_lon, max_lon = max_lon, min_lon

        bbox = BoundingBox(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon)

        # 2. Extract Footprint Polygon from WKT if available
        footprint_poly: Optional[List[Tuple[float, float]]] = None
        wkt_str = product.get("Footprint_geometry") or product.get("Footprint_C0_geometry")
        if wkt_str and "POLYGON" in wkt_str.upper():
            try:
                from shapely import wkt
                poly_geom = wkt.loads(wkt_str)
                coords = list(poly_geom.exterior.coords)
                footprint_poly = [(norm_lon(c[0]), c[1]) for c in coords]
            except Exception as e:
                logger.debug(f"Could not parse WKT footprint: {e}")

        # 3. Extract acquisition date
        acq_str = product.get("UTC_start_time") or product.get("Observation_time") or product.get("Acquisition_date")
        acq_time = None
        if acq_str:
            for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    acq_time = datetime.strptime(acq_str.rstrip("Z") + ("Z" if "Z" in fmt else ""), fmt)
                    break
                except ValueError:
                    continue

        # 4. Extract geometry angles
        geom = ObservationGeometry(
            emission_angle_deg=_to_float(product.get("Emission_angle")),
            incidence_angle_deg=_to_float(product.get("Incidence_angle")),
            phase_angle_deg=_to_float(product.get("Phase_angle")),
            solar_azimuth_deg=_to_float(product.get("Solar_azimuth") or product.get("Sub_solar_azimuth")),
            solar_zenith_deg=_to_float(product.get("Incidence_angle")), # Solar zenith equals solar incidence on flat sphere
        )

        # 5. Extract download file URLs disambiguated by role and extension
        download_urls: Dict[str, str] = {}
        product_files = product.get("Product_files", {}).get("Product_file", [])
        if isinstance(product_files, dict):
            product_files = [product_files]
        
        browse_raster_url: Optional[str] = None
        primary_raster_url: Optional[str] = None

        for f in product_files:
            url = f.get("URL") or f.get("Url")
            fname = f.get("FileName") or ""
            ftype = (f.get("Type") or f.get("type") or "file").lower()
            ext = Path(fname).suffix.lower()

            if url:
                file_key = f"{ftype}_{ext.lstrip('.')}" if ext else ftype
                download_urls[file_key] = url

                # Identify browse raster image (prioritizing image formats over XML labels)
                if ftype == "browse" and ext in (".tif", ".tiff", ".png", ".jpg", ".jpeg"):
                    browse_raster_url = url
                elif ftype == "product" and ext in (".img", ".raw", ".tif", ".tiff", ".cub", ".jp2"):
                    primary_raster_url = url

        # Direct browse image if provided
        browse_url = browse_raster_url or product.get("Product_browse_url")

        res_val = _to_float(product.get("Map_resolution") or product.get("Map_scale"), cfg.get("default_res", 1.0))

        return LunarObservation(
            product_id=prod_id,
            mission=cfg["mission"],
            sensor=sensor,
            acquisition_time=acq_time,
            spatial_resolution_m=res_val,
            bbox=bbox,
            footprint_polygon=footprint_poly,
            geometry=geom,
            source_url=product.get("Product_url") or product.get("ProductURL"),
            download_urls=download_urls,
            preview_image_path=browse_url,
            extra_metadata=product,
        )

    def download_file(
        self, url: str, dest_path: Union[str, Path], overwrite: bool = False
    ) -> Path:
        """Download remote URL to local destination with progress bar."""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and not overwrite and dest.stat().st_size > 0:
            logger.info(f"File already exists: {dest}")
            return dest

        logger.info(f"Downloading {url} -> {dest}")
        resp = self.session.get(url, stream=True, timeout=(10, 60))
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0))
        block_size = 1024 * 64

        with open(dest, "wb") as f, tqdm(
            desc=dest.name,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        ) as bar:
            for chunk in resp.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        return dest

    def download_observation(
        self,
        obs: LunarObservation,
        download_preview_only: bool = False,
        overwrite: bool = False,
    ) -> LunarObservation:
        """Downloads files for a given LunarObservation and updates its local file paths."""
        sensor_dir = self.output_dir / obs.sensor.value.lower() / obs.product_id
        sensor_dir.mkdir(parents=True, exist_ok=True)

        # Download preview / browse image
        if obs.preview_image_path and obs.preview_image_path.startswith("http"):
            raw_ext = os.path.splitext(obs.preview_image_path.split("?")[0])[-1] or ".png"
            dest_preview = sensor_dir / f"{obs.product_id}_browse{raw_ext}"
            try:
                self.download_file(obs.preview_image_path, dest_preview, overwrite=overwrite)
                
                # If downloaded browse is a TIFF / PYR.TIF, convert to normalized PNG preview for UI display
                if raw_ext.lower() in (".tif", ".tiff"):
                    try:
                        from PIL import Image
                        Image.MAX_IMAGE_PIXELS = None
                        png_preview = sensor_dir / f"{obs.product_id}_preview.png"
                        if not png_preview.exists() or overwrite:
                            with Image.open(dest_preview) as im:
                                im.thumbnail((1024, 1024))
                                im.convert("L").save(png_preview, "PNG")
                        obs.preview_image_path = str(png_preview.resolve())
                    except Exception as ex:
                        logger.debug(f"TIFF preview conversion note: {ex}")
                        obs.preview_image_path = str(dest_preview.resolve())
                else:
                    obs.preview_image_path = str(dest_preview.resolve())
            except Exception as e:
                logger.warning(f"Failed to download preview image: {e}")

        if download_preview_only:
            return obs

        # Download primary data and label files
        for ftype, url in obs.download_urls.items():
            ext = os.path.splitext(url.split("?")[0])[-1]
            dest = sensor_dir / f"{obs.product_id}_{ftype}{ext}"
            try:
                saved = self.download_file(url, dest, overwrite=overwrite)
                if ext.lower() in (".img", ".tif", ".tiff", ".cub", ".raw", ".jp2") and not obs.primary_image_path:
                    obs.primary_image_path = str(saved.resolve())
                elif ext.lower() in (".xml", ".lbl"):
                    obs.label_path = str(saved.resolve())
                else:
                    obs.auxiliary_files.append(str(saved.resolve()))
            except Exception as e:
                logger.warning(f"Failed to download file {ftype} ({url}): {e}")

        return obs

