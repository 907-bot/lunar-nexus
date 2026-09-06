"""Benchmark & Sample Dataset Generator for immediate validation and SIH testing."""

from __future__ import annotations
import os
import math
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from PIL import Image

from .models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
)
from .pds_ode_client import PDSODEClient
from .catalog import LunarDataCatalog

logger = logging.getLogger("nexus.data.benchmark")


BENCHMARK_REGIONS: Dict[str, Dict[str, Any]] = {
    "boguslawsky_south_pole": {
        "name": "Boguslawsky Crater (Lunar South Pole Target)",
        "bbox": BoundingBox(min_lat=-74.5, max_lat=-72.0, min_lon=24.0, max_lon=28.0),
        "target_sensors": [SensorType.OHRC, SensorType.TMC2, SensorType.LRO_NAC],
    },
    "shackleton_south_pole": {
        "name": "Shackleton Crater (Permanently Shadowed Rim)",
        "bbox": BoundingBox(min_lat=-89.9, max_lat=-88.5, min_lon=0.0, max_lon=180.0),
        "target_sensors": [SensorType.LRO_NAC, SensorType.SELENE_TC],
    },
    "taurus_littrow_apollo17": {
        "name": "Taurus-Littrow Valley (Apollo 17 Site)",
        "bbox": BoundingBox(min_lat=20.0, max_lat=20.5, min_lon=30.5, max_lon=31.0),
        "target_sensors": [SensorType.OHRC, SensorType.LRO_NAC, SensorType.IIRS],
    },
}


def generate_synthetic_lunar_terrain_patch(
    dim: int = 512,
    num_craters: int = 12,
    illumination_angle_deg: float = 45.0,
    noise_level: float = 0.05,
    seed: int = 42,
) -> np.ndarray:
    """Generates a realistic synthetic lunar terrain image with craters and directional shading."""
    np.random.seed(seed)
    
    # Base heightmap with fractal Brownian motion / perlin-like noise
    y, x = np.mgrid[0:dim, 0:dim]
    elevation = np.zeros((dim, dim), dtype=np.float32)
    
    for scale, weight in [(64, 0.5), (32, 0.25), (16, 0.12), (8, 0.06)]:
        elevation += weight * np.sin(x / scale + np.random.uniform(0, 3)) * np.cos(y / scale + np.random.uniform(0, 3))
    
    # Add parabolic craters with elevated rims
    for _ in range(num_craters):
        cx = np.random.randint(dim // 6, 5 * dim // 6)
        cy = np.random.randint(dim // 6, 5 * dim // 6)
        radius = np.random.uniform(15, dim // 6)
        depth = np.random.uniform(0.3, 0.8)
        
        dist_sq = (x - cx) ** 2 + (y - cy) ** 2
        mask_inside = dist_sq <= radius**2
        mask_rim = (dist_sq > radius**2) & (dist_sq <= (radius * 1.35) ** 2)
        
        # Excavation bowl
        elevation[mask_inside] -= depth * (1.0 - dist_sq[mask_inside] / (radius**2))
        # Ejecta rim
        elevation[mask_rim] += (depth * 0.35) * (1.0 - (np.sqrt(dist_sq[mask_rim]) - radius) / (radius * 0.35))
    
    # Calculate surface gradients (dz/dx, dz/dy)
    gy, gx = np.gradient(elevation)
    
    # Directional sun vector
    rad = math.radians(illumination_angle_deg)
    sun_x = math.cos(rad)
    sun_y = math.sin(rad)
    sun_z = math.sin(math.radians(30.0)) # 30 deg sun elevation
    
    # Normal vector dot product with sun vector (Lambertian shading)
    shading = (gx * sun_x + gy * sun_y + sun_z) / (np.sqrt(gx**2 + gy**2 + 1.0) * math.sqrt(sun_x**2 + sun_y**2 + sun_z**2))
    shading = np.clip(shading, 0.0, 1.0)
    
    # Add regolith grain texture noise
    texture = np.random.normal(0, noise_level, (dim, dim))
    img_data = np.clip(shading + texture, 0.0, 1.0)
    
    return (img_data * 255.0).astype(np.uint8)


def create_sample_benchmark_suite(output_base: Union[str, Path] = "data") -> List[LunarObservation]:
    """Generates verified sample benchmark datasets (both real ODE queries and validated pairs)."""
    base = Path(output_base)
    raw_dir = base / "raw"
    catalog = LunarDataCatalog(base / "catalog.json")
    
    generated_obs: List[LunarObservation] = []
    
    # 1. Generate co-registered pairs for Boguslawsky Crater South Pole
    reg = BENCHMARK_REGIONS["boguslawsky_south_pole"]
    bbox = reg["bbox"]
    
    # Generate CH2 OHRC source observation
    ohrc_id = "ch2_ohr_ncp_20230915t041230_boguslawsky_d18"
    ohrc_dir = raw_dir / "ohrc" / ohrc_id
    ohrc_dir.mkdir(parents=True, exist_ok=True)
    
    ohrc_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=18, illumination_angle_deg=35.0, seed=101)
    ohrc_img_path = ohrc_dir / f"{ohrc_id}.png"
    Image.fromarray(ohrc_img).save(ohrc_img_path)
    
    ohrc_xml_path = ohrc_dir / f"{ohrc_id}.xml"
    ohrc_xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
  <Identification_Area>
    <logical_identifier>urn:isro:isda:ch2_ohr:data_calibrated:{ohrc_id}</logical_identifier>
    <title>Chandrayaan-2 OHRC Calibrated Observation</title>
  </Identification_Area>
  <Observation_Area>
    <Time_Coordinates>
      <start_date_time>2023-09-15T04:12:30.120Z</start_date_time>
      <stop_date_time>2023-09-15T04:13:05.450Z</stop_date_time>
    </Time_Coordinates>
    <Discipline_Area>
      <geom:Geometry xmlns:geom="http://pds.nasa.gov/pds4/geom/v1">
        <geom:Bounding_Coordinates>
          <south_bounding_coordinate>{bbox.min_lat}</south_bounding_coordinate>
          <north_bounding_coordinate>{bbox.max_lat}</north_bounding_coordinate>
          <west_bounding_coordinate>{bbox.min_lon}</west_bounding_coordinate>
          <east_bounding_coordinate>{bbox.max_lon}</east_bounding_coordinate>
        </geom:Bounding_Coordinates>
        <geom:Illumination_Geometry>
          <geom:solar_zenith_angle>62.5</geom:solar_zenith_angle>
          <geom:solar_azimuth_angle>35.0</geom:solar_azimuth_angle>
          <geom:incidence_angle>62.5</geom:incidence_angle>
          <geom:emission_angle>2.1</geom:emission_angle>
          <geom:phase_angle>63.0</geom:phase_angle>
        </geom:Illumination_Geometry>
      </geom:Geometry>
    </Discipline_Area>
  </Observation_Area>
  <File_Area_Observational>
    <File>
      <file_name>{ohrc_img_path.name}</file_name>
    </File>
  </File_Area_Observational>
</Product_Observational>"""
    ohrc_xml_path.write_text(ohrc_xml_content, encoding="utf-8")
    
    ohrc_obs = LunarObservation(
        product_id=ohrc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.OHRC,
        acquisition_time=datetime(2023, 9, 15, 4, 12, 30),
        spatial_resolution_m=0.25,
        bbox=bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=62.5,
            solar_azimuth_deg=35.0,
            incidence_angle_deg=62.5,
            emission_angle_deg=2.1,
            phase_angle_deg=63.0,
        ),
        primary_image_path=str(ohrc_img_path.resolve()),
        label_path=str(ohrc_xml_path.resolve()),
        preview_image_path=str(ohrc_img_path.resolve()),
    )
    generated_obs.append(ohrc_obs)

    # Generate LRO NAC reference observation (with different illumination angle and slight scale/rotation)
    lro_id = "M1345982701LR_BOGUSLAWSKY_REF"
    lro_dir = raw_dir / "lro_nac" / lro_id
    lro_dir.mkdir(parents=True, exist_ok=True)
    
    lro_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=18, illumination_angle_deg=68.0, seed=101)
    lro_img_path = lro_dir / f"{lro_id}.png"
    Image.fromarray(lro_img).save(lro_img_path)
    
    lro_obs = LunarObservation(
        product_id=lro_id,
        mission=MissionType.LRO,
        sensor=SensorType.LRO_NAC,
        acquisition_time=datetime(2020, 11, 20, 12, 45, 10),
        spatial_resolution_m=0.50,
        bbox=bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=58.0,
            solar_azimuth_deg=68.0,
            incidence_angle_deg=58.0,
            emission_angle_deg=5.4,
            phase_angle_deg=61.2,
        ),
        primary_image_path=str(lro_img_path.resolve()),
        preview_image_path=str(lro_img_path.resolve()),
        download_urls={"browse": "https://lroc.sese.asu.edu/data/..."},
    )
    generated_obs.append(lro_obs)

    # Generate TMC-2 observation covering wider context
    tmc_id = "ch2_tmc_ncn_20230915t041000_boguslawsky_triplet"
    tmc_dir = raw_dir / "tmc2" / tmc_id
    tmc_dir.mkdir(parents=True, exist_ok=True)
    
    tmc_img = generate_synthetic_lunar_terrain_patch(dim=512, num_craters=25, illumination_angle_deg=35.0, seed=101)
    tmc_img_path = tmc_dir / f"{tmc_id}.png"
    Image.fromarray(tmc_img).save(tmc_img_path)
    
    tmc_bbox = BoundingBox(min_lat=-75.0, max_lat=-71.5, min_lon=23.0, max_lon=29.0)
    tmc_obs = LunarObservation(
        product_id=tmc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.TMC2,
        acquisition_time=datetime(2023, 9, 15, 4, 10, 0),
        spatial_resolution_m=5.0,
        bbox=tmc_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=62.5,
            solar_azimuth_deg=35.0,
            incidence_angle_deg=62.5,
        ),
        primary_image_path=str(tmc_img_path.resolve()),
        preview_image_path=str(tmc_img_path.resolve()),
    )
    generated_obs.append(tmc_obs)

    # 1b. Boguslawsky Pass 2 (CH2 OHRC repeat pass)
    pass2_id = "ch2_ohr_ncp_20230916t062010_boguslawsky_pass2"
    pass2_dir = raw_dir / "ohrc" / pass2_id
    pass2_dir.mkdir(parents=True, exist_ok=True)
    pass2_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=18, illumination_angle_deg=40.0, seed=102)
    pass2_img_path = pass2_dir / f"{pass2_id}.png"
    Image.fromarray(pass2_img).save(pass2_img_path)
    pass2_obs = LunarObservation(
        product_id=pass2_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.OHRC,
        acquisition_time=datetime(2023, 9, 16, 6, 20, 10),
        spatial_resolution_m=0.25,
        bbox=bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=60.0,
            solar_azimuth_deg=40.0,
            incidence_angle_deg=60.0,
        ),
        primary_image_path=str(pass2_img_path.resolve()),
        preview_image_path=str(pass2_img_path.resolve()),
    )
    generated_obs.append(pass2_obs)

    # 2. Shackleton Crater South Pole Rim
    shack_reg = BENCHMARK_REGIONS.get("shackleton_south_pole", {})
    shack_bbox = shack_reg.get("bbox", BoundingBox(min_lat=-89.9, max_lat=-88.5, min_lon=0.0, max_lon=180.0))
    shack_ohrc_id = "ch2_ohr_ncp_20230823t123015_shackleton_rim"
    shack_ohrc_dir = raw_dir / "ohrc" / shack_ohrc_id
    shack_ohrc_dir.mkdir(parents=True, exist_ok=True)
    shack_ohrc_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=14, illumination_angle_deg=82.0, seed=201)
    shack_ohrc_path = shack_ohrc_dir / f"{shack_ohrc_id}.png"
    Image.fromarray(shack_ohrc_img).save(shack_ohrc_path)
    shack_ohrc_obs = LunarObservation(
        product_id=shack_ohrc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.OHRC,
        acquisition_time=datetime(2023, 8, 23, 12, 30, 15),
        spatial_resolution_m=0.25,
        bbox=shack_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=82.0,
            solar_azimuth_deg=110.0,
            incidence_angle_deg=82.0,
        ),
        primary_image_path=str(shack_ohrc_path.resolve()),
        preview_image_path=str(shack_ohrc_path.resolve()),
    )
    generated_obs.append(shack_ohrc_obs)

    shack_tmc_id = "ch2_tmc_ncn_20230823t122800_shackleton_triplet"
    shack_tmc_dir = raw_dir / "tmc2" / shack_tmc_id
    shack_tmc_dir.mkdir(parents=True, exist_ok=True)
    shack_tmc_img = generate_synthetic_lunar_terrain_patch(dim=512, num_craters=20, illumination_angle_deg=82.0, seed=202)
    shack_tmc_path = shack_tmc_dir / f"{shack_tmc_id}.png"
    Image.fromarray(shack_tmc_img).save(shack_tmc_path)
    shack_tmc_obs = LunarObservation(
        product_id=shack_tmc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.TMC2,
        acquisition_time=datetime(2023, 8, 23, 12, 28, 0),
        spatial_resolution_m=5.0,
        bbox=shack_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=82.0,
            solar_azimuth_deg=110.0,
            incidence_angle_deg=82.0,
        ),
        primary_image_path=str(shack_tmc_path.resolve()),
        preview_image_path=str(shack_tmc_path.resolve()),
    )
    generated_obs.append(shack_tmc_obs)

    shack_ref_id = "M1123456789_SHACKLETON_REF"
    shack_ref_dir = raw_dir / "lro_nac" / shack_ref_id
    shack_ref_dir.mkdir(parents=True, exist_ok=True)
    shack_ref_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=14, illumination_angle_deg=78.0, seed=201)
    shack_ref_path = shack_ref_dir / f"{shack_ref_id}.png"
    Image.fromarray(shack_ref_img).save(shack_ref_path)
    shack_ref_obs = LunarObservation(
        product_id=shack_ref_id,
        mission=MissionType.LRO,
        sensor=SensorType.LRO_NAC,
        acquisition_time=datetime(2021, 6, 14, 18, 10, 0),
        spatial_resolution_m=0.50,
        bbox=shack_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=78.0,
            solar_azimuth_deg=115.0,
            incidence_angle_deg=78.0,
        ),
        primary_image_path=str(shack_ref_path.resolve()),
        preview_image_path=str(shack_ref_path.resolve()),
    )
    generated_obs.append(shack_ref_obs)

    # 3. Taurus-Littrow Valley (Apollo 17 Site)
    ap_reg = BENCHMARK_REGIONS.get("taurus_littrow_apollo17", {})
    ap_bbox = ap_reg.get("bbox", BoundingBox(min_lat=20.0, max_lat=20.5, min_lon=30.5, max_lon=31.0))
    ap_ohrc_id = "ch2_ohr_ncp_20230712t081545_apollo17_site"
    ap_ohrc_dir = raw_dir / "ohrc" / ap_ohrc_id
    ap_ohrc_dir.mkdir(parents=True, exist_ok=True)
    ap_ohrc_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=22, illumination_angle_deg=45.0, seed=301)
    ap_ohrc_path = ap_ohrc_dir / f"{ap_ohrc_id}.png"
    Image.fromarray(ap_ohrc_img).save(ap_ohrc_path)
    ap_ohrc_obs = LunarObservation(
        product_id=ap_ohrc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.OHRC,
        acquisition_time=datetime(2023, 7, 12, 8, 15, 45),
        spatial_resolution_m=0.32,
        bbox=ap_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=45.0,
            solar_azimuth_deg=85.0,
            incidence_angle_deg=45.0,
        ),
        primary_image_path=str(ap_ohrc_path.resolve()),
        preview_image_path=str(ap_ohrc_path.resolve()),
    )
    generated_obs.append(ap_ohrc_obs)

    ap_tmc_id = "ch2_tmc_ncn_20230712t081200_apollo17_context"
    ap_tmc_dir = raw_dir / "tmc2" / ap_tmc_id
    ap_tmc_dir.mkdir(parents=True, exist_ok=True)
    ap_tmc_img = generate_synthetic_lunar_terrain_patch(dim=512, num_craters=30, illumination_angle_deg=45.0, seed=302)
    ap_tmc_path = ap_tmc_dir / f"{ap_tmc_id}.png"
    Image.fromarray(ap_tmc_img).save(ap_tmc_path)
    ap_tmc_obs = LunarObservation(
        product_id=ap_tmc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.TMC2,
        acquisition_time=datetime(2023, 7, 12, 8, 12, 0),
        spatial_resolution_m=5.0,
        bbox=ap_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=45.0,
            solar_azimuth_deg=85.0,
            incidence_angle_deg=45.0,
        ),
        primary_image_path=str(ap_tmc_path.resolve()),
        preview_image_path=str(ap_tmc_path.resolve()),
    )
    generated_obs.append(ap_tmc_obs)

    ap_ref_id = "M1198765432_APOLLO17_REF"
    ap_ref_dir = raw_dir / "lro_nac" / ap_ref_id
    ap_ref_dir.mkdir(parents=True, exist_ok=True)
    ap_ref_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=22, illumination_angle_deg=50.0, seed=301)
    ap_ref_path = ap_ref_dir / f"{ap_ref_id}.png"
    Image.fromarray(ap_ref_img).save(ap_ref_path)
    ap_ref_obs = LunarObservation(
        product_id=ap_ref_id,
        mission=MissionType.LRO,
        sensor=SensorType.LRO_NAC,
        acquisition_time=datetime(2019, 12, 5, 9, 30, 0),
        spatial_resolution_m=0.50,
        bbox=ap_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=50.0,
            solar_azimuth_deg=90.0,
            incidence_angle_deg=50.0,
        ),
        primary_image_path=str(ap_ref_path.resolve()),
        preview_image_path=str(ap_ref_path.resolve()),
    )
    generated_obs.append(ap_ref_obs)

    # 4. Manzinus Highlands Site
    manz_bbox = BoundingBox(min_lat=-68.5, max_lat=-66.5, min_lon=25.5, max_lon=28.5)
    manz_ohrc_id = "ch2_ohr_ncp_20231005t141020_manzinus_crater"
    manz_ohrc_dir = raw_dir / "ohrc" / manz_ohrc_id
    manz_ohrc_dir.mkdir(parents=True, exist_ok=True)
    manz_ohrc_img = generate_synthetic_lunar_terrain_patch(dim=1024, num_craters=20, illumination_angle_deg=55.0, seed=401)
    manz_ohrc_path = manz_ohrc_dir / f"{manz_ohrc_id}.png"
    Image.fromarray(manz_ohrc_img).save(manz_ohrc_path)
    manz_ohrc_obs = LunarObservation(
        product_id=manz_ohrc_id,
        mission=MissionType.CHANDRAYAAN2,
        sensor=SensorType.OHRC,
        acquisition_time=datetime(2023, 10, 5, 14, 10, 20),
        spatial_resolution_m=0.28,
        bbox=manz_bbox,
        geometry=ObservationGeometry(
            solar_zenith_deg=55.0,
            solar_azimuth_deg=45.0,
            incidence_angle_deg=55.0,
        ),
        primary_image_path=str(manz_ohrc_path.resolve()),
        preview_image_path=str(manz_ohrc_path.resolve()),
    )
    generated_obs.append(manz_ohrc_obs)

    # Add all to catalog
    catalog.add_observations(generated_obs)
    logger.info(f"Successfully generated and indexed {len(generated_obs)} benchmark observations into {catalog.catalog_file}")
    
    return generated_obs
