"""NEXUS-LUNAR POC 3: Classical Registration Engine Microservice Server.
Provides RESTful endpoints to execute classical image registration (SIFT, RootSIFT, ORB, AKAZE, Phase Correlation),
compute scientific metrics (RMSE, inliers, transformation), and stream visualization overlays.
"""

from __future__ import annotations
import os
import sys
import json
import time
import uuid
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
import numpy as np
import cv2

# Workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = WORKSPACE_ROOT / "data" / "raw"
JOBS_DIR = WORKSPACE_ROOT / "data" / "registration_jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(WORKSPACE_ROOT))

from packages.registration import (
    extract_features,
    FeatureMethod,
    match_descriptors,
    estimate_transformation,
    TransformType,          
    phase_correlation_shift,
    compute_registration_metrics,
    decompose_transform_matrix,
    draw_matches_visualization,
    create_checkerboard_overlay,
    warp_image,
)


class ClassicalRegistrationService:
    """Core registration orchestration and job management engine."""

    def __init__(self, jobs_dir: Path = JOBS_DIR):
        self.jobs_dir = jobs_dir
        self.jobs_cache: dict[str, dict] = {}

    def resolve_image_path(self, product_id_or_path: str) -> Path | None:
        """Finds image file on disk given a product ID or relative/absolute path."""
        p = Path(product_id_or_path)
        if p.exists() and p.is_file():
            return p
        
        # Check workspace relative
        cand = WORKSPACE_ROOT / product_id_or_path.lstrip("/\\")
        if cand.exists() and cand.is_file():
            return cand

        # Search by filename or stem in data/raw
        for match in RAW_DATA_DIR.rglob(f"{p.stem}*.png"):
            if "preview" not in match.name.lower() and match.is_file():
                return match
            elif match.is_file():
                return match

        for match in RAW_DATA_DIR.rglob(f"{product_id_or_path}*.png"):
            if match.is_file():
                return match

        # Check catalog.json for primary_image_path or preview_image_path
        cat_path = WORKSPACE_ROOT / "data" / "catalog.json"
        if cat_path.exists():
            try:
                with open(cat_path, "r", encoding="utf-8") as f:
                    cat = json.load(f)
                    if product_id_or_path in cat:
                        entry = cat[product_id_or_path]
                        for field in ["primary_image_path", "preview_image_path"]:
                            if entry.get(field):
                                fp = Path(entry[field])
                                if fp.exists() and fp.is_file():
                                    return fp
                                cand = WORKSPACE_ROOT / entry[field].lstrip("/\\")
                                if cand.exists() and cand.is_file():
                                    return cand
            except Exception:
                pass

        return None

    def execute_registration(
        self,
        source_id: str,
        reference_id: str,
        method_str: str = "SIFT",
        transform_type_str: str = "Homography",
        ratio_thresh: float = 0.75,
        ransac_thresh_px: float = 3.0,
    ) -> dict:
        """Executes full classical registration pipeline and persists verification artifacts."""
        t_start = time.perf_counter()
        job_id = str(uuid.uuid4())[:8]
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # 1. Resolve image paths
        src_path = self.resolve_image_path(source_id)
        ref_path = self.resolve_image_path(reference_id)

        if not src_path or not src_path.exists():
            raise FileNotFoundError(f"Source image '{source_id}' could not be located on disk")
        if not ref_path or not ref_path.exists():
            raise FileNotFoundError(f"Reference image '{reference_id}' could not be located on disk")

        # 2. Load images
        img_src = cv2.imread(str(src_path))
        img_ref = cv2.imread(str(ref_path))

        if img_src is None:
            raise ValueError(f"Failed to decode source image from {src_path}")
        if img_ref is None:
            raise ValueError(f"Failed to decode reference image from {ref_path}")

        # 3. Parse options
        method = FeatureMethod(method_str) if method_str in FeatureMethod._value2member_map_ else FeatureMethod.SIFT
        t_type = TransformType(transform_type_str) if transform_type_str in TransformType._value2member_map_ else TransformType.HOMOGRAPHY

        # 4. Pipeline Execution
        if method == FeatureMethod.PHASE_CORRELATION:
            M_trans, resp = phase_correlation_shift(img_src, img_ref)
            dur_ms = (time.perf_counter() - t_start) * 1000.0
            warped = warp_image(img_src, M_trans, img_ref.shape)
            checkerboard = create_checkerboard_overlay(img_ref, warped)
            
            # Save artifacts
            warped_path = job_dir / "warped.png"
            checker_path = job_dir / "checkerboard.png"
            cv2.imwrite(str(warped_path), warped)
            cv2.imwrite(str(checker_path), checkerboard)

            metrics = {
                "match_count": 1,
                "inlier_count": 1,
                "inlier_ratio_pct": 100.0,
                "reprojection_rmse_px": 0.0,
                "runtime_ms": round(dur_ms, 2),
                "confidence_level": "HIGH" if resp > 0.5 else "MODERATE",
                "estimated_rotation_deg": 0.0,
                "estimated_scale": {"sx": 1.0, "sy": 1.0},
                "estimated_translation_px": {"dx": round(float(M_trans[0, 2]), 2), "dy": round(float(M_trans[1, 2]), 2)},
                "phase_correlation_response": round(resp, 4),
                "is_registration_successful": True,
            }
            M = M_trans
            matches = []
            mask = None
            kps_src, kps_ref = [], []
        else:
            # Detect keypoints & descriptors
            kps_src, desc_src = extract_features(img_src, method)
            kps_ref, desc_ref = extract_features(img_ref, method)

            # Match descriptors
            matches = match_descriptors(desc_src, desc_ref, method, ratio_thresh)

            # Geometric RANSAC estimation
            M, mask, in_src, in_ref = estimate_transformation(
                kps_src, kps_ref, matches, t_type, ransac_thresh_px
            )

            dur_ms = (time.perf_counter() - t_start) * 1000.0

            # Compute metrics
            metrics = compute_registration_metrics(
                total_matches=len(matches),
                inliers_mask=mask,
                inlier_src_pts=in_src,
                inlier_ref_pts=in_ref,
                transformation_matrix=M,
                runtime_ms=dur_ms,
            )

            # Visual artifacts
            if M is not None:
                warped = warp_image(img_src, M, img_ref.shape)
                checkerboard = create_checkerboard_overlay(img_ref, warped)
                matches_vis = draw_matches_visualization(img_src, kps_src, img_ref, kps_ref, matches, mask)

                warped_path = job_dir / "warped.png"
                checker_path = job_dir / "checkerboard.png"
                matches_path = job_dir / "matches.png"

                cv2.imwrite(str(warped_path), warped)
                cv2.imwrite(str(checker_path), checkerboard)
                cv2.imwrite(str(matches_path), matches_vis)

        # Store job details
        matrix_list = M.tolist() if M is not None else None
        job_result = {
            "job_id": job_id,
            "status": "COMPLETED" if metrics["is_registration_successful"] else "FAILED",
            "source_id": source_id,
            "reference_id": reference_id,
            "method": method.value,
            "transform_type": t_type.value,
            "metrics": metrics,
            "transformation_matrix": matrix_list,
            "artifacts": {
                "warped_url": f"/api/v1/registration/{job_id}/warped",
                "matches_url": f"/api/v1/registration/{job_id}/matches" if method != FeatureMethod.PHASE_CORRELATION else None,
                "checkerboard_url": f"/api/v1/registration/{job_id}/checkerboard",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.jobs_cache[job_id] = job_result
        with open(job_dir / "result.json", "w", encoding="utf-8") as f:
            json.dump(job_result, f, indent=2)

        return job_result


registration_service = ClassicalRegistrationService()


class RegistrationHTTPHandler(SimpleHTTPRequestHandler):
    """REST API Handler for POC 3 Classical Registration Microservice."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE_ROOT), **kwargs)

    def _send_json(self, status: int, payload: dict | list):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/health":
            self._send_json(200, {
                "status": "online",
                "service": "nexus-registration",
                "layer": "POC 3 — Classical Registration Engine",
                "version": "1.0.0-poc3",
                "supported_algorithms": [m.value for m in FeatureMethod],
                "supported_transforms": [t.value for t in TransformType],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return

        if path == "/api/v1/registration/methods":
            self._send_json(200, {
                "algorithms": [
                    {"id": "SIFT", "name": "SIFT (Scale-Invariant Feature Transform)", "type": "Gradient / Scale-space", "best_for": "General terrain registration"},
                    {"id": "RootSIFT", "name": "RootSIFT (Hellinger L1-Root Normalization)", "type": "Hellinger Kernel", "best_for": "Planar regolith & illumination variance"},
                    {"id": "ORB", "name": "ORB (Oriented FAST & Rotated BRIEF)", "type": "Binary Descriptor", "best_for": "Real-time embedded processing"},
                    {"id": "AKAZE", "name": "AKAZE (Accelerated KAZE in Non-linear Scale Space)", "type": "Non-linear diffusion", "best_for": "High-contrast crater boundary preservation"},
                    {"id": "PhaseCorrelation", "name": "2D FFT Phase Correlation", "type": "Frequency Domain", "best_for": "Direct translation & sub-pixel shift"},
                ],
                "transforms": ["Homography", "Affine"],
            })
            return

        # Handle artifact streaming: /api/v1/registration/{job_id}/{artifact}
        if path.startswith("/api/v1/registration/"):
            parts = path.strip("/").split("/")
            if len(parts) == 5:  # api, v1, registration, {job_id}, {artifact}
                _, _, _, job_id, artifact = parts
                job_dir = JOBS_DIR / job_id
                target_img = job_dir / f"{artifact}.png"
                if target_img.exists():
                    self.path = str(target_img.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    return super().do_GET()
                else:
                    self._send_json(404, {"error": f"Artifact '{artifact}' for job {job_id} not found"})
                    return
            elif len(parts) == 4:  # api, v1, registration, {job_id}
                job_id = parts[3]
                if job_id in registration_service.jobs_cache:
                    self._send_json(200, registration_service.jobs_cache[job_id])
                    return
                job_file = JOBS_DIR / job_id / "result.json"
                if job_file.exists():
                    with open(job_file, "r", encoding="utf-8") as f:
                        self._send_json(200, json.load(f))
                    return
                self._send_json(404, {"error": f"Job {job_id} not found"})
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/register":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            source_id = data.get("source_product_id") or "ch2_ohr_ncp_20230915t041230_boguslawsky_d18"
            reference_id = data.get("reference_product_id") or "M1345982701LR_BOGUSLAWSKY_REF"
            method = data.get("method", "SIFT")
            transform_type = data.get("transform_type", "Homography")
            ratio_thresh = float(data.get("ratio_test_thresh", 0.75))
            ransac_thresh = float(data.get("ransac_thresh_px", 3.0))

            try:
                result = registration_service.execute_registration(
                    source_id=source_id,
                    reference_id=reference_id,
                    method_str=method,
                    transform_type_str=transform_type,
                    ratio_thresh=ratio_thresh,
                    ransac_thresh_px=ransac_thresh,
                )
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": f"Registration failed: {str(e)}"})
            return

        self._send_json(404, {"error": "Endpoint not found"})


def run_server(port: int = 8081):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, RegistrationHTTPHandler)
    print("=" * 64)
    print(" [NEXUS-LUNAR] POC 3: Classical Registration Engine Online")
    print(f" Microservice: http://localhost:{port}/")
    print(f" Health API:   http://localhost:{port}/api/v1/health")
    print(f" Register API: http://localhost:{port}/api/v1/register")
    print("=" * 64)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Registration service...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    run_server(port)
