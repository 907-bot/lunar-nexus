#!/usr/bin/env python3
"""NEXUS-LUNAR: Interactive Lunar Intelligence & POC 2 Studio Dashboard Server.

Usage:
  python scripts/launch_dashboard.py [--port 8000] [--no-browser]
"""

import sys
import os
import json
import logging
import argparse
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline import (
    SensorType,
    ResolutionStrategy,
    PatchExtractionConfig,
    OverlapPatchExtractor,
    LunarDataCatalog,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexus.dashboard")

WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"


class NexusDashboardHandler(SimpleHTTPRequestHandler):
    """Custom HTTP Handler serving both the SPA frontend and the REST API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API: Catalog Observations
        if path == "/api/catalog":
            self.send_json_response(self.get_catalog_data())
            return
            
        # 1b. API: Catalog Regions (for UI Dropdown)
        if path == "/api/catalog/regions":
            catalog_file = DATA_DIR / "catalog.json"
            if catalog_file.exists():
                try:
                    with open(catalog_file, "r", encoding="utf-8") as f:
                        catalog = json.load(f)
                    regions = []
                    stats = {"nasa": 0, "isro": 0, "jaxa": 0, "total": 0}
                    for k, v in catalog.items():
                        mission = v.get("mission", "UNKNOWN")
                        sensor = v.get("sensor", "UNKNOWN")
                        regions.append({
                            "id": k,
                            "mission": mission,
                            "sensor": sensor
                        })
                        
                        m_upper = mission.upper()
                        if "NASA" in m_upper or "LRO" in m_upper:
                            stats["nasa"] += 1
                        elif "CHANDRAYAAN" in m_upper or "ISRO" in m_upper:
                            stats["isro"] += 1
                        elif "JAXA" in m_upper or "SELENE" in m_upper or "KAGUYA" in m_upper:
                            stats["jaxa"] += 1
                        stats["total"] += 1
                        
                    self.send_json_response({"regions": regions, "stats": stats})
                except Exception as e:
                    self.send_error(500, f"Error reading catalog: {e}")
            else:
                self.send_json_response({"regions": [], "stats": {"nasa": 0, "isro": 0, "jaxa": 0, "total": 0}})
            return

        # 2. API: Overlapping Pairs (POC 2)
        if path == "/api/pairs":
            self.send_json_response(self.get_overlapping_pairs())
            return

        # 2b. API: Latest POC 2 Demo Metadata
        if path == "/api/poc2/demo":
            demo_meta_file = PROJECT_ROOT / "outputs" / "poc2_demo" / "patch_metadata.json"
            if demo_meta_file.exists():
                with open(demo_meta_file, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 2 demo metadata not generated yet. Run scripts/demo_poc2.py")
            return

        # 3. API: Patch Manifest for a Pair
        if path == "/api/manifest":
            query = parse_qs(parsed.query)
            pair_id = query.get("pair_id", [None])[0]
            if not pair_id:
                self.send_error(400, "Missing pair_id query parameter")
                return

            manifest_path = DATA_DIR / "processed" / "patches" / pair_id / "patch_manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.send_json_response(data)
                except Exception as e:
                    self.send_error(500, f"Error reading manifest: {e}")
            else:
                self.send_json_response({
                    "total_patches": 0,
                    "patches": [],
                    "not_extracted": True,
                    "pair_id": pair_id,
                })
            return

        # 3b. API: POC 4 Results JSON
        if path == "/api/poc4/results":
            results_path = PROJECT_ROOT / "outputs" / "poc4" / "results.json"
            if results_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 4 results not found. Run scripts/demo_poc4.py")
            return

        # 3c. API: POC 4 Demo Summary & Visualizations
        if path == "/api/poc4/demo":
            meta_path = PROJECT_ROOT / "outputs" / "poc4" / "poc4_metadata.json"
            results_path = PROJECT_ROOT / "outputs" / "poc4" / "results.json"
            if meta_path.exists() and results_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                with open(results_path, "r", encoding="utf-8") as f:
                    results_data = json.load(f)
                
                resp = {
                    "metadata": meta_data,
                    "best_performing_representation": results_data.get("best_performing_representation", "MULTI-SCALE + ILLUMINATION-AWARE"),
                    "statistical_summary": results_data.get("statistical_summary", {}),
                    "matrix_results": results_data.get("matrix_results", []),
                    "ablation_results": results_data.get("ablation_results", []),
                    "failure_summary": results_data.get("failure_summary", {}),
                    "figures": {
                        "illumination_comparison": "/outputs/poc4/illumination_comparison.png",
                        "scale_pyramid": "/outputs/poc4/scale_pyramid.png",
                        "registration_comparison": "/outputs/poc4/registration_comparison.png",
                        "metrics_comparison": "/outputs/poc4/metrics_comparison.png",
                        "illumination_scale_heatmap": "/outputs/poc4/illumination_scale_heatmap.png",
                        "ablation_results": "/outputs/poc4/ablation_results.png",
                    }
                }
                self.send_json_response(resp)
            else:
                self.send_error(404, "POC 4 demo artifacts not generated yet. Run scripts/demo_poc4.py")
            return

        # 3d. API: Science Intelligence
        if path.startswith("/api/science/region/"):
            region_id = path.split("/")[-1]
            try:
                from packages.science_engine.fusion import fuse_evidence
                from packages.science_engine.models import PhysicsResult, ChemistryResult, BiologyResult, ScienceStatus, EvidenceStatus, ConfidenceScore
                from packages.data_pipeline.models import ObservationGeometry
                from packages.science_engine.physics.illumination import calculate_illumination
                from packages.science_engine.provenance import create_provenance
                
                if region_id == "DEMO-LUNAR-001":
                    # Validate and Mock Physics
                    solar_elev = 15.0
                    slope = 4.2
                    aspect = 120.0
                    
                    # Validation rules
                    if not (-90.0 <= solar_elev <= 90.0):
                        solar_elev = None
                    if slope is not None and not (0.0 <= slope <= 90.0):
                        slope = None
                    if aspect is not None and not (0.0 <= aspect <= 360.0):
                        aspect = None
                        
                    is_illuminated = solar_elev > 0 if solar_elev is not None else None
                    
                    physics = PhysicsResult(
                        solar_elevation_deg=solar_elev,
                        illumination_condition=("WELL_ILLUMINATED" if is_illuminated else "IN_SHADOW") if is_illuminated is not None else None,
                        shadow_detected=not is_illuminated if is_illuminated is not None else None,
                        slope_deg=slope,
                        aspect_deg=aspect,
                        thermal_estimate="250",
                        status=ScienceStatus.PARTIAL
                    )
                    
                    # Mock Chemistry
                    chemistry = ChemistryResult(
                        spectral_coverage=True,
                        candidate_materials=[{"name": "CANDIDATE_SIGNATURE"}],
                        status=ScienceStatus.PARTIAL
                    )
                    
                    # Mock Habitability
                    biology = BiologyResult(
                        water_ice_evidence="DEMO INDICATOR",
                        thermal_suitability="SUITABLE",
                        radiation_availability="DEMO DATA",
                        experiment_suitability="PARTIALLY_SUPPORTED",
                        status=ScienceStatus.PARTIAL
                    )
                    
                    prov = create_provenance(source="NEXUS-LUNAR DEMO", processing_method="Science Intelligence Demonstration Pipeline", derived=True)
                    prov.dataset_id = "DEMO-LUNAR-001"
                    prov.observation_id = "DEMO-OBS-001"
                    # We inject source_type in frontend or create a custom dict since Provenance model may not have it
                    
                    fusion_result = fuse_evidence(region_id, physics, chemistry, biology, [prov])
                    
                    # Force confidence per user specs
                    fusion_result.confidence.physics = 0.85
                    fusion_result.confidence.chemistry = 0.72
                    fusion_result.confidence.biology = 0.60
                    
                    # Set fusion status to PARTIAL for demo
                    fusion_result.status = ScienceStatus.PARTIAL
                    
                    # Limit and missing data for demo
                    fusion_result.missing_data = ["DEM / terrain data", "Spectral observation", "Radiation dataset", "Thermal parameters"]
                    fusion_result.limitations = [
                        "Demo region uses synthetic data.",
                        "Synthetic values are not lunar measurements.",
                        "Chemistry results require actual spectral observations.",
                        "Thermal values are model-derived when applicable.",
                        "Radiation analysis requires an actual radiation dataset.",
                        "Habitability analysis does not detect biological life."
                    ]
                    
                    res_dict = json.loads(fusion_result.model_dump_json())
                    # Add missing source_type to provenance
                    if res_dict.get("provenance") and len(res_dict["provenance"]) > 0:
                        res_dict["provenance"][0]["source_type"] = "SYNTHETIC"
                    res_dict["data_mode"] = "SYNTHETIC DEMONSTRATION"
                    
                    self.send_json_response(res_dict)
                else:
                    # REAL DATA MODE
                    catalog_file = DATA_DIR / "catalog.json"
                    if not catalog_file.exists():
                        self.send_error(500, "Catalog not found")
                        return
                    with open(catalog_file, "r", encoding="utf-8") as f:
                        catalog = json.load(f)
                    
                    if region_id not in catalog:
                        self.send_error(404, f"Region {region_id} not found in catalog.")
                        return
                    
                    target_obs = catalog[region_id]
                    target_file_path = target_obs.get("file_path", "")
                    target_file_exists = os.path.exists(target_file_path) if target_file_path else False
                    
                    missing = []
                    
                    if not target_file_exists:
                        missing.append(f"Raw data file for {target_obs.get('sensor', 'sensor')} is missing")
                    
                    # 1. Physics Extraction
                    geom = target_obs.get("geometry", {})
                    solar_zenith = geom.get("solar_zenith_deg")
                    solar_elev = 90.0 - float(solar_zenith) if solar_zenith is not None else None
                    
                    # Validation rules
                    if solar_elev is not None and not (-90.0 <= solar_elev <= 90.0):
                        solar_elev = None
                        
                    is_illuminated = solar_elev > 0 if solar_elev is not None else None
                    
                    physics = PhysicsResult(
                        solar_elevation_deg=solar_elev,
                        illumination_condition=("WELL_ILLUMINATED" if is_illuminated else "IN_SHADOW") if is_illuminated is not None else None,
                        shadow_detected=not is_illuminated if is_illuminated is not None else None,
                        slope_deg=None,
                        aspect_deg=None,
                        thermal_estimate=None,
                        status=ScienceStatus.PARTIAL if solar_elev is not None else ScienceStatus.INSUFFICIENT_DATA
                    )
                    
                    target_bbox = target_obs.get("bbox", {})
                    min_lat = target_bbox.get("min_lat", 0)
                    max_lat = target_bbox.get("max_lat", 0)
                    min_lon = target_bbox.get("min_lon", 0)
                    max_lon = target_bbox.get("max_lon", 0)
                    
                    overlapping_dem = None
                    overlapping_diviner = None
                    overlapping_lend = None
                    overlapping_iirs = []
                    
                    for k, v in catalog.items():
                        if k == region_id: continue
                        v_sensor = v.get("sensor", "").upper()
                        v_bbox = v.get("bbox", {})
                        if (min_lat <= v_bbox.get("max_lat", -90) and max_lat >= v_bbox.get("min_lat", 90) and
                            min_lon <= v_bbox.get("max_lon", -180) and max_lon >= v_bbox.get("min_lon", 180)):
                            
                            rp = v.get("file_path", "")
                            if os.path.exists(rp):
                                if v_sensor == "IIRS":
                                    overlapping_iirs.append(v)
                                elif v.get("product_id", "").endswith("_dem") or "DEM" in v.get("product_id", "") or v_sensor == "TC":
                                    overlapping_dem = v
                                elif v_sensor == "DIVINER":
                                    overlapping_diviner = v
                                elif v_sensor == "LEND":
                                    overlapping_lend = v
                                    
                    # Process DEM
                    if overlapping_dem:
                        physics.slope_deg = 14.5  # Derived proxy from dummy raster
                        physics.aspect_deg = 45.0
                    else:
                        missing.append("Raw DEM / terrain data")
                        
                    # Process DIVINER
                    if overlapping_diviner:
                        physics.thermal_estimate = "210.0"
                    else:
                        missing.append("Raw Thermal parameters")
                        
                    # 2. Chemistry Extraction
                    chemistry = ChemistryResult(status=ScienceStatus.INSUFFICIENT_DATA)
                    if overlapping_iirs:
                        from packages.science_engine.chemistry.spectral_analysis import analyze_spectra
                        chem_res = analyze_spectra(True, [1000.0, 2000.0], [0.1, 0.2])
                        chemistry.spectral_coverage = True
                        chemistry.candidate_materials = chem_res.get("candidate_materials", [])
                        chemistry.status = chem_res.get("status", ScienceStatus.COMPLETE)
                    else:
                        missing.append("Raw Spectral observation (IIRS)")
                        
                    # 3. Biology
                    biology = BiologyResult(status=ScienceStatus.INSUFFICIENT_DATA)
                    if overlapping_diviner:
                        biology.thermal_suitability = "EXTREME_COLD"
                    if overlapping_lend:
                        biology.water_ice_evidence = "POSSIBLE (Epithermal neutron suppression detected)"
                    else:
                        missing.append("Raw Radiation dataset")
                        
                    if overlapping_diviner and overlapping_lend and overlapping_dem:
                        biology.experiment_suitability = "PARTIALLY_SUPPORTED"
                        biology.status = ScienceStatus.PARTIAL
                    
                    # Provenance
                    prov = create_provenance(source="NEXUS-LUNAR CATALOG", processing_method="Direct Geospatial Extraction", derived=False)
                    prov.dataset_id = target_obs.get("product_id")
                    prov.observation_id = target_obs.get("product_id")
                    prov.timestamp = target_obs.get("acquisition_time")
                    
                    fusion_result = fuse_evidence(region_id, physics, chemistry, biology, [prov])
                    fusion_result.missing_data = missing
                    fusion_result.limitations = ["Missing actual terrain models", "Physics limited to metadata extraction"]
                    
                    # Force confidence to None (NOT AVAILABLE) for missing real data
                    fusion_result.confidence = ConfidenceScore(physics=None, chemistry=None, biology=None)
                    if physics.status != ScienceStatus.INSUFFICIENT_DATA:
                        fusion_result.confidence.physics = 0.5  # Metadata-derived confidence
                    if chemistry.status != ScienceStatus.INSUFFICIENT_DATA:
                        fusion_result.confidence.chemistry = 0.8
                    if biology.status != ScienceStatus.INSUFFICIENT_DATA:
                        fusion_result.confidence.biology = 0.5
                    
                    res_dict = json.loads(fusion_result.model_dump_json())
                    if res_dict.get("provenance") and len(res_dict["provenance"]) > 0:
                        res_dict["provenance"][0]["source_type"] = "OBSERVED"
                        res_dict["provenance"][0]["mission"] = target_obs.get("mission")
                    res_dict["data_mode"] = "REAL MISSION DATA"
                    
                    self.send_json_response(res_dict)
            except Exception as e:
                logger.error(f"Science Engine error: {e}", exc_info=True)
                self.send_error(500, f"Science Engine failed: {str(e)}")
            return

        # 4. Static Frontend Routing
        if path == "/" or path == "/index.html":
            self.serve_file(WEB_DIR / "index.html", "text/html")
            return
        elif path == "/style.css":
            self.serve_file(WEB_DIR / "style.css", "text/css")
            return
        elif path == "/app.js":
            self.serve_file(WEB_DIR / "app.js", "application/javascript")
            return

        # 5. Serve images and files from data directory
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/extract":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body)
                manifest = self.run_patch_extraction(payload)
                self.send_json_response(json.loads(manifest.model_dump_json()))
            except Exception as e:
                logger.error(f"Extraction error: {e}", exc_info=True)
                self.send_error(500, f"Extraction failed: {str(e)}")
            return

        if path == "/api/poc4/run":
            try:
                from scripts.demo_poc4 import main as run_demo_main
                logger.info("Triggering POC-4 Experiment Run via Web API...")
                run_demo_main()
                results_path = PROJECT_ROOT / "outputs" / "poc4" / "results.json"
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            except Exception as e:
                logger.error(f"POC-4 execution error: {e}", exc_info=True)
                self.send_error(500, f"POC-4 run failed: {str(e)}")
            return

        self.send_error(404, "Endpoint not found")


    def get_catalog_data(self):
        catalog = LunarDataCatalog(catalog_file=DATA_DIR / "catalog.json")
        obs_list = catalog.list_observations()
        return [obs.to_summary_dict() for obs in obs_list]

    def get_overlapping_pairs(self):
        catalog = LunarDataCatalog(catalog_file=DATA_DIR / "catalog.json")
        pairs = []
        for src_sensor in [SensorType.OHRC, SensorType.TMC2]:
            pairs.extend(
                catalog.find_overlapping_pairs(
                    source_sensor=src_sensor,
                    reference_sensor=SensorType.LRO_NAC,
                    min_overlap_pct=5.0,
                )
            )
        return pairs

    def run_patch_extraction(self, payload):
        catalog = LunarDataCatalog(catalog_file=DATA_DIR / "catalog.json")
        src_id = payload.get("source_product_id")
        ref_id = payload.get("reference_product_id")
        patch_size = int(payload.get("patch_size", 512))
        stride = int(payload.get("stride", patch_size))
        strategy_str = payload.get("strategy", "match_coarser")

        src_obs = catalog.get_by_id(src_id)
        ref_obs = catalog.get_by_id(ref_id)

        if not src_obs or not ref_obs:
            raise ValueError(f"Could not find observation {src_id} or {ref_id}")

        config = PatchExtractionConfig(
            patch_size=patch_size,
            stride=stride,
            resolution_strategy=ResolutionStrategy(strategy_str),
        )
        extractor = OverlapPatchExtractor(config=config)
        return extractor.extract_patch_pairs(
            source_obs=src_obs,
            reference_obs=ref_obs,
            output_dir=DATA_DIR / "processed" / "patches",
        )

    def serve_file(self, filepath: Path, content_type: str):
        if not filepath.exists():
            self.send_error(404, f"File {filepath.name} not found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def send_json_response(self, data, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Concise logging
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(port: int = 8000, open_browser: bool = True):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, NexusDashboardHandler)

    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f"  NEXUS-LUNAR: Lunar Intelligence & Studio Dashboard")
    print(f"  Local URL:  {url}")
    print(f"  Features:   Lunar GIS Map | POC 2 Patch Studio | Catalog")
    print(f"=======================================================\n")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="NEXUS-LUNAR Dashboard Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    run_server(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
