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

        # 3d. API: POC 5 Results JSON
        if path == "/api/poc5/results":
            results_path = PROJECT_ROOT / "outputs" / "poc5" / "poc5_results.json"
            if results_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 5 results not found. Run scripts/demo_poc5.py")
            return

        # 3e. API: POC 5 Demo & Figures
        if path == "/api/poc5/demo":
            results_path = PROJECT_ROOT / "outputs" / "poc5" / "poc5_results.json"
            meta_path = PROJECT_ROOT / "outputs" / "poc5" / "poc5_metadata.json"
            if results_path.exists() and meta_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    res_data = json.load(f)
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                
                resp = {
                    "metadata": meta_data,
                    "summary_metrics": res_data.get("summary_metrics", {}),
                    "baseline_metrics": res_data.get("baseline_metrics", {}),
                    "ablation_comparison": res_data.get("ablation_comparison", []),
                    "total_queries": res_data.get("total_queries", 0),
                    "total_candidates": res_data.get("total_candidates", 0),
                    "retrieval_results": res_data.get("retrieval_results", {}),
                    "failure_summary": res_data.get("failure_summary", {}),
                    "figures": {
                        "query_retrieval_gallery": "/outputs/poc5/query_retrieval_gallery.png",
                        "similarity_ranking_curve": "/outputs/poc5/similarity_ranking_curve.png",
                        "retrieval_score_distribution": "/outputs/poc5/retrieval_score_distribution.png",
                        "cross_sensor_embedding_space": "/outputs/poc5/cross_sensor_embedding_space.png",
                        "ablation_baseline_comparison": "/outputs/poc5/ablation_baseline_comparison.png",
                        "failure_analysis_breakdown": "/outputs/poc5/failure_analysis_breakdown.png",
                    }
                }
                self.send_json_response(resp)
            else:
                self.send_error(404, "POC 5 demo artifacts not generated yet. Run scripts/demo_poc5.py")
            return

        # 3f. API: POC 6 Results JSON
        if path == "/api/poc6/results":
            results_path = PROJECT_ROOT / "outputs" / "poc6" / "poc6_results.json"
            if results_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 6 results not found. Run scripts/demo_poc6.py")
            return

        # 3g. API: POC 6 Demo & Figures
        if path == "/api/poc6/demo":
            results_path = PROJECT_ROOT / "outputs" / "poc6" / "poc6_results.json"
            meta_path = PROJECT_ROOT / "outputs" / "poc6" / "poc6_metadata.json"
            fail_path = PROJECT_ROOT / "outputs" / "poc6" / "poc6_failure_cases.json"
            if results_path.exists() and meta_path.exists():
                with open(results_path, "r", encoding="utf-8") as f:
                    res_data = json.load(f)
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                fail_data = {}
                if fail_path.exists():
                    with open(fail_path, "r", encoding="utf-8") as f:
                        fail_data = json.load(f)

                resp = {
                    "metadata": meta_data,
                    "total_candidates": res_data.get("total_candidates_verified", 0),
                    "accepted_count": res_data.get("accepted_count", 0),
                    "rejected_count": res_data.get("rejected_count", 0),
                    "candidates": res_data.get("results", []),
                    "failure_cases": fail_data,
                    "figures": {
                        "geometric_verification_gallery": "/outputs/poc6/geometric_verification_gallery.png",
                        "inlier_ratio_vs_confidence": "/outputs/poc6/inlier_ratio_vs_confidence.png",
                        "spatial_distribution_inliers": "/outputs/poc6/spatial_distribution_inliers.png",
                        "confidence_score_breakdown": "/outputs/poc6/confidence_score_breakdown.png",
                        "accepted_vs_rejected_scatter": "/outputs/poc6/accepted_vs_rejected_scatter.png",
                        "xai_rejection_reasons_breakdown": "/outputs/poc6/xai_rejection_reasons_breakdown.png",
                    }
                }
                self.send_json_response(resp)
            else:
                self.send_error(404, "POC 6 demo artifacts not generated yet. Run scripts/demo_poc6.py")
            return

        # 3h. API: POC 7 Spatial Knowledge Graph
        if path == "/api/poc7/graph":
            kg_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_knowledge_graph.json"
            if kg_path.exists():
                with open(kg_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Knowledge Graph not found. Run scripts/demo_poc7.py")
            return

        # 3i. API: POC 7 Terrain Intelligence
        if path == "/api/poc7/terrain":
            t_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_terrain_intelligence.json"
            if t_path.exists():
                with open(t_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Terrain Intelligence not found. Run scripts/demo_poc7.py")
            return

        # 3j. API: POC 7 Illumination Intelligence
        if path == "/api/poc7/illumination":
            i_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_illumination_intelligence.json"
            if i_path.exists():
                with open(i_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Illumination Intelligence not found. Run scripts/demo_poc7.py")
            return

        # 3k. API: POC 7 Resource Indicators
        if path == "/api/poc7/resources":
            r_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_resource_indicators.json"
            if r_path.exists():
                with open(r_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Resource Indicators not found. Run scripts/demo_poc7.py")
            return

        # 3l. API: POC 7 Hazards
        if path == "/api/poc7/hazards":
            h_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_hazard_intelligence.json"
            if h_path.exists():
                with open(h_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Hazard Intelligence not found. Run scripts/demo_poc7.py")
            return

        # 3m. API: POC 7 Candidate Sites
        if path == "/api/poc7/sites":
            s_path = PROJECT_ROOT / "outputs" / "poc7" / "poc7_candidate_sites.json"
            if s_path.exists():
                with open(s_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "POC 7 Candidate Sites not found. Run scripts/demo_poc7.py")
            return

        # 3n. API: POC 7 Demo Summary & Figures
        if path == "/api/poc7/demo":
            poc7_dir = PROJECT_ROOT / "outputs" / "poc7"
            kg_path = poc7_dir / "poc7_knowledge_graph.json"
            sites_path = poc7_dir / "poc7_candidate_sites.json"
            meta_path = poc7_dir / "poc7_metadata.json"
            handover_path = poc7_dir / "poc7_handover_for_poc8.json"

            if kg_path.exists() and sites_path.exists():
                with open(kg_path, "r", encoding="utf-8") as f:
                    kg_data = json.load(f)
                with open(sites_path, "r", encoding="utf-8") as f:
                    sites_data = json.load(f)
                meta_data = {}
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                handover_data = {}
                if handover_path.exists():
                    with open(handover_path, "r", encoding="utf-8") as f:
                        handover_data = json.load(f)

                resp = {
                    "metadata": meta_data,
                    "total_nodes": kg_data.get("total_nodes", 0),
                    "total_edges": kg_data.get("total_edges", 0),
                    "node_type_breakdown": kg_data.get("node_type_breakdown", {}),
                    "relationship_type_breakdown": kg_data.get("relationship_type_breakdown", {}),
                    "candidate_sites": sites_data,
                    "top_candidate": sites_data[0] if sites_data else None,
                    "handover": handover_data,
                    "figures": {
                        "knowledge_graph": "/outputs/poc7/knowledge_graph_overview.png",
                        "terrain_intelligence": "/outputs/poc7/terrain_intelligence_map.png",
                        "slope_analysis": "/outputs/poc7/slope_analysis_map.png",
                        "illumination_shadow": "/outputs/poc7/illumination_shadow_map.png",
                        "hazard_intelligence": "/outputs/poc7/hazard_intelligence_map.png",
                        "resource_indicator": "/outputs/poc7/resource_indicator_map.png",
                        "candidate_site_suitability": "/outputs/poc7/candidate_site_suitability_map.png",
                        "candidate_site_explanation": "/outputs/poc7/candidate_site_explanation.png",
                    }
                }
                self.send_error(404, "POC 7 demo artifacts not generated yet. Run scripts/demo_poc7.py")
            return

        # 3h. API: Classical Registration Methods (POC 3)
        if path == "/api/registration/methods" or path == "/api/v1/registration/methods":
            self.send_json_response({
                "algorithms": [
                    {"id": "SIFT", "name": "Scale-Invariant Feature Transform", "type": "Detector & Descriptor"},
                    {"id": "RootSIFT", "name": "L1-Square Root SIFT", "type": "Enhanced SIFT"},
                    {"id": "ORB", "name": "Oriented FAST and Rotated BRIEF", "type": "Binary Detector"},
                    {"id": "AKAZE", "name": "Accelerated-KAZE", "type": "Non-linear Scale Space"},
                    {"id": "PhaseCorrelation", "name": "Frequency-Domain Translation", "type": "Sub-pixel FFT"},
                ],
                "transformations": [
                    {"id": "Homography", "name": "Perspective (8 DOF)"},
                    {"id": "Affine", "name": "Affine (6 DOF)"},
                    {"id": "Rigid", "name": "Euclidean (3 DOF)"},
                    {"id": "Translation", "name": "Shift Only (2 DOF)"},
                ]
            })
            return

        # 3i. API: Classical Registration Jobs (POC 3)
        if path == "/api/registration/jobs" or path == "/api/v1/registration/jobs":
            try:
                from services.registration.server import ClassicalRegistrationService
                service = ClassicalRegistrationService()
                self.send_json_response({"jobs": service.list_jobs()})
            except Exception as e:
                self.send_error(500, f"Failed to list registration jobs: {str(e)}")
            return

        # 3j. API: Specific Classical Registration Job
        if path == "/api/registration/job":
            query = parse_qs(parsed.query)
            job_id = query.get("id", [None])[0]
            if not job_id:
                self.send_error(400, "Missing job id parameter")
                return
            try:
                from services.registration.server import ClassicalRegistrationService
                service = ClassicalRegistrationService()
                job_data = service.get_job(job_id)
                if job_data:
                    self.send_json_response(job_data)
                else:
                    self.send_error(404, f"Job {job_id} not found")
            except Exception as e:
                self.send_error(500, f"Failed to retrieve job: {str(e)}")
            return

        # 3k. API: Blender MCP Server Status (POC 8)
        if path == "/api/nexus/blender/status":
            try:
                from packages.nexus_core.blender_mcp_client import BlenderMCPClient
                client = BlenderMCPClient(project_root=PROJECT_ROOT)
                online = client.is_server_online(timeout=0.3)
                bin_path = client.get_blender_binary()
                rendered_img = PROJECT_ROOT / "outputs" / "nexus_3d" / "nexus_blender_digital_twin.png"
                self.send_json_response({
                    "online": online,
                    "host": client.host,
                    "port": client.port,
                    "blender_bin": bin_path,
                    "blender_available": bin_path is not None,
                    "rendered_image_exists": rendered_img.exists(),
                    "rendered_image_url": "/outputs/nexus_3d/nexus_blender_digital_twin.png",
                })
            except Exception as e:
                self.send_json_response({
                    "online": False,
                    "blender_available": False,
                    "error": str(e),
                })
            return

        # 3l. API: Habitat Layout Plan (POC 8)
        if path == "/api/nexus/habitat/plan":
            plan_path = PROJECT_ROOT / "outputs" / "nexus_3d" / "habitat_layout_plan.json"
            if not plan_path.exists():
                try:
                    from scripts.demo_nexus_poc8 import main as run_poc8_demo
                    run_poc8_demo()
                except Exception as e:
                    logger.warning(f"Auto-generating habitat plan failed: {e}")
            if plan_path.exists():
                with open(plan_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            else:
                self.send_error(404, "Habitat layout plan not available")
            return

        # 3m. API: Unified Mission Summary (All POCs)
        if path == "/api/nexus/summary":
            self.send_json_response({
                "status": "ONLINE",
                "mission": "NEXUS-LUNAR UNIFIED EXPLORATION PLATFORM",
                "target_region": "Boguslawsky Lunar South Pole Crater (-73.25°S, 26.00°E)",
                "pocs": [
                    {"id": "POC-1", "name": "Lunar Data & Geo Explorer", "status": "OPERATIONAL"},
                    {"id": "POC-2", "name": "Geographic Overlap & Patch Engine", "status": "OPERATIONAL"},
                    {"id": "POC-3", "name": "Classical Registration Engine", "status": "OPERATIONAL"},
                    {"id": "POC-4", "name": "Illumination & Scale Robustness", "status": "OPERATIONAL"},
                    {"id": "POC-5", "name": "Multimodal AI Correspondence", "status": "OPERATIONAL"},
                    {"id": "POC-6", "name": "Geometric Verification & XAI", "status": "OPERATIONAL"},
                    {"id": "POC-7", "name": "Spatial Intelligence & SKG", "status": "OPERATIONAL"},
                    {"id": "POC-8", "name": "Habitat Planner & 3D Digital Twin", "status": "OPERATIONAL"},
                ],
                "blender_mcp_port": 9876,
            })
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
        elif path == "/three.min.js":
            self.serve_file(WEB_DIR / "three.min.js", "application/javascript")
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

        if path in ("/api/registration/run", "/api/v1/register", "/api/registration/execute"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body) if body else {}
                from services.registration.server import ClassicalRegistrationService
                service = ClassicalRegistrationService()
                result = service.execute_registration(
                    source_id=payload.get("source_id", "ch2_ohr_ncp_20230915t041230_boguslawsky_d18"),
                    reference_id=payload.get("reference_id", "M1345982701LR_BOGUSLAWSKY_REF"),
                    method_str=payload.get("method", "SIFT"),
                    transform_type_str=payload.get("transform", "Homography"),
                    ratio_thresh=float(payload.get("ratio_thresh", 0.75)),
                    ransac_thresh_px=float(payload.get("ransac_thresh_px", 3.0)),
                )
                self.send_json_response(result)
            except Exception as e:
                logger.error(f"Classical registration error: {e}", exc_info=True)
                self.send_error(500, f"Registration failed: {str(e)}")
            return

        if path == "/api/poc4/run":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body) if body else {}
                result = self.execute_poc4_pipeline(payload)
                self.send_json_response(result)
            except Exception as e:
                logger.error(f"POC-4 execution error: {e}", exc_info=True)
                self.send_error(500, f"POC-4 pipeline failed: {str(e)}")
            return

        if path == "/api/poc5/run":
            try:
                from scripts.demo_poc5 import run_poc5_demo
                logger.info("Triggering POC-5 Multimodal Retrieval Run via Web API...")
                run_poc5_demo()
                results_path = PROJECT_ROOT / "outputs" / "poc5" / "poc5_results.json"
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            except Exception as e:
                logger.error(f"POC-5 execution error: {e}", exc_info=True)
                self.send_error(500, f"POC-5 run failed: {str(e)}")
            return

        if path == "/api/poc6/run":
            try:
                from scripts.demo_poc6 import run_poc6_demo
                logger.info("Triggering POC-6 Geometric Verification Run via Web API...")
                run_poc6_demo()
                results_path = PROJECT_ROOT / "outputs" / "poc6" / "poc6_results.json"
                with open(results_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            except Exception as e:
                logger.error(f"POC-6 execution error: {e}", exc_info=True)
                self.send_error(500, f"POC-6 run failed: {str(e)}")
            return

        if path in ("/api/poc7/run", "/api/poc7/analyze"):
            try:
                from scripts.demo_poc7 import run_poc7_demo
                logger.info("Triggering POC-7 Spatial Intelligence Run via Web API...")
                run_poc7_demo()
                poc7_dir = PROJECT_ROOT / "outputs" / "poc7"
                kg_path = poc7_dir / "poc7_knowledge_graph.json"
                sites_path = poc7_dir / "poc7_candidate_sites.json"
                with open(kg_path, "r", encoding="utf-8") as f:
                    kg_data = json.load(f)
                with open(sites_path, "r", encoding="utf-8") as f:
                    sites_data = json.load(f)
                resp = {
                    "status": "SUCCESS",
                    "total_nodes": kg_data.get("total_nodes", 0),
                    "total_edges": kg_data.get("total_edges", 0),
                    "candidate_sites_count": len(sites_data),
                    "candidate_sites": sites_data,
                }
                self.send_json_response(resp)
            except Exception as e:
                logger.error(f"POC-7 execution error: {e}", exc_info=True)
                self.send_error(500, f"POC-7 run failed: {str(e)}")
            return

        if path in ("/api/nexus/habitat/redesign", "/api/nexus/habitat/run"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body) if body else {}
                from scripts.demo_nexus_poc8 import main as run_poc8_demo
                run_poc8_demo()
                plan_path = PROJECT_ROOT / "outputs" / "nexus_3d" / "habitat_layout_plan.json"
                with open(plan_path, "r", encoding="utf-8") as f:
                    self.send_json_response(json.load(f))
            except Exception as e:
                logger.error(f"Habitat redesign error: {e}", exc_info=True)
                self.send_error(500, f"Habitat redesign failed: {str(e)}")
            return

        if path == "/api/nexus/blender/build":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(body) if body else {}
                force_headless = bool(payload.get("force_headless", True))
                from packages.nexus_core.blender_mcp_client import BlenderMCPClient
                client = BlenderMCPClient(project_root=PROJECT_ROOT)
                logger.info(f"Triggering Blender 3D Infrastructure build (force_headless={force_headless})...")
                res = client.build_infrastructure_pipeline(force_headless=force_headless)
                self.send_json_response(res)
            except Exception as e:
                logger.error(f"Blender build execution error: {e}", exc_info=True)
                self.send_error(500, f"Blender build failed: {str(e)}")
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
            self.send_error(404, "File not found")
            return

        with open(filepath, "rb") as f:
            body = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_json_response(self, data, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def run_server(port: int = 8000, open_browser: bool = True):
    max_retries = 10
    httpd = None
    active_port = port

    for attempt in range(max_retries):
        try:
            server_address = ("", active_port)
            httpd = ReusableThreadingHTTPServer(server_address, NexusDashboardHandler)
            break
        except OSError as e:
            if "Address already in use" in str(e) or e.errno == 48:
                logger.warning(f"Port {active_port} already in use. Retrying on port {active_port + 1}...")
                active_port += 1
            else:
                raise e

    if not httpd:
        raise RuntimeError(f"Could not bind server to any port starting from {port}")

    url = f"http://localhost:{active_port}"
    print(f"\n=======================================================")
    print(f"  NEXUS-LUNAR: Unified Space Intelligence Dashboard")
    print(f"  Local URL:  {url}")
    print(f"  Features:   3D Habitat Digital Twin | Lunar GIS | Patch Engine |")
    print(f"              Classical Registration | Robustness | AI Retrieval |")
    print(f"              Geometric XAI | Spatial Knowledge Graph")
    print(f"=======================================================\n")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="NEXUS-LUNAR Unified Dashboard Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    run_server(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
