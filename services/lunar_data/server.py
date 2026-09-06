"""NEXUS-LUNAR Layer 1: Lunar Data Explorer Microservice Server
Provides RESTful APIs for catalog indexing, spatial queries, solar illumination telemetry,
and candidate overlapping pair discovery for Chandrayaan-2, LRO NAC, and SELENE observations.
"""

from __future__ import annotations
import os
import sys
import json
import math
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_PATH = WORKSPACE_ROOT / "data" / "catalog.json"
RAW_DATA_DIR = WORKSPACE_ROOT / "data" / "raw"
WEB_DIR = WORKSPACE_ROOT / "apps" / "web"

sys.path.insert(0, str(WORKSPACE_ROOT))


class LunarDataService:
    """Core in-memory catalog manager & query processor for Layer 1."""

    def __init__(self, catalog_file: Path = CATALOG_PATH):
        self.catalog_file = catalog_file
        self.observations: dict[str, dict] = {}
        self.load_catalog()

    def _resolve_local_image_path(self, raw_path: str | None) -> Path | None:
        """Resolves absolute or relative image paths to the current machine's workspace."""
        if not raw_path:
            return None
        
        # Check direct path
        p = Path(raw_path)
        if p.exists() and p.is_file():
            return p
        
        # Look for matching path under data/raw
        parts = p.parts
        if "data" in parts:
            try:
                idx = parts.index("data")
                relative_sub = Path(*parts[idx:])
                candidate = WORKSPACE_ROOT / relative_sub
                if candidate.exists() and candidate.is_file():
                    return candidate
            except Exception:
                pass

        # Look specifically in data/raw for the filename
        filename = p.name
        for match in RAW_DATA_DIR.rglob(filename):
            if match.is_file():
                return match

        return None

    def load_catalog(self):
        """Loads and normalizes the catalog observations."""
        if not self.catalog_file.exists():
            self.observations = {}
            return

        try:
            with open(self.catalog_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            normalized = {}
            for pid, obs in raw_data.items():
                item = dict(obs)
                
                # Check and fix local paths
                preview = self._resolve_local_image_path(item.get("preview_image_path"))
                primary = self._resolve_local_image_path(item.get("primary_image_path"))
                
                if preview:
                    item["preview_local_rel"] = str(preview.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    item["preview_exists"] = True
                else:
                    item["preview_local_rel"] = None
                    item["preview_exists"] = False

                if primary:
                    item["primary_local_rel"] = str(primary.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    item["primary_exists"] = True
                else:
                    item["primary_local_rel"] = None
                    item["primary_exists"] = False

                # Ensure bbox coords are floats
                bbox = item.get("bbox", {})
                item["bbox"] = {
                    "min_lat": float(bbox.get("min_lat", 0)),
                    "max_lat": float(bbox.get("max_lat", 0)),
                    "min_lon": float(bbox.get("min_lon", 0)),
                    "max_lon": float(bbox.get("max_lon", 0)),
                }

                # Ensure geometry dict exists with numbers
                geom = item.get("geometry", {})
                item["geometry"] = {
                    "solar_zenith_deg": geom.get("solar_zenith_deg"),
                    "solar_azimuth_deg": geom.get("solar_azimuth_deg"),
                    "incidence_angle_deg": geom.get("incidence_angle_deg"),
                    "emission_angle_deg": geom.get("emission_angle_deg"),
                    "phase_angle_deg": geom.get("phase_angle_deg"),
                    "spacecraft_altitude_km": geom.get("spacecraft_altitude_km"),
                }

                normalized[pid] = item

            self.observations = normalized
            print(f"[Layer 1 Data Explorer] Loaded {len(self.observations)} lunar observations.")
        except Exception as e:
            print(f"[Layer 1 Data Explorer] Error loading catalog: {e}")
            self.observations = {}

    def get_stats(self) -> dict:
        """Computes high-level catalog statistics for UI telemetry display."""
        sensors: dict[str, int] = {}
        missions: dict[str, int] = {}
        resolutions = []
        min_lat, max_lat = 90.0, -90.0
        min_lon, max_lon = 180.0, -180.0

        for obs in self.observations.values():
            s = obs.get("sensor", "UNKNOWN")
            m = obs.get("mission", "UNKNOWN")
            sensors[s] = sensors.get(s, 0) + 1
            missions[m] = missions.get(m, 0) + 1
            
            res = obs.get("spatial_resolution_m")
            if res is not None:
                resolutions.append(res)

            bb = obs.get("bbox", {})
            if bb:
                min_lat = min(min_lat, bb.get("min_lat", min_lat))
                max_lat = max(max_lat, bb.get("max_lat", max_lat))
                min_lon = min(min_lon, bb.get("min_lon", min_lon))
                max_lon = max(max_lon, bb.get("max_lon", max_lon))

        return {
            "total_observations": len(self.observations),
            "sensors": sensors,
            "missions": missions,
            "resolution_range": {
                "min_m": min(resolutions) if resolutions else 0.25,
                "max_m": max(resolutions) if resolutions else 80.0,
            },
            "bounding_coverage": {
                "min_lat": min_lat if min_lat <= 90 else -90.0,
                "max_lat": max_lat if max_lat >= -90 else 90.0,
                "min_lon": min_lon if min_lon <= 180 else -180.0,
                "max_lon": max_lon if max_lon >= -180 else 180.0,
            },
            "layer": "Layer 1 — Lunar Data Explorer",
            "system": "NEXUS-LUNAR SIH Platform",
        }

    def query(
        self,
        sensors: list[str] | None = None,
        mission: str | None = None,
        min_lat: float | None = None,
        max_lat: float | None = None,
        min_lon: float | None = None,
        max_lon: float | None = None,
        min_res: float | None = None,
        max_res: float | None = None,
        search_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Queries observations matching spatial, sensor, and resolution constraints."""
        matched = []

        for obs in self.observations.values():
            # Sensor filter
            if sensors and obs.get("sensor") not in sensors:
                continue

            # Mission filter
            if mission and obs.get("mission") != mission:
                continue

            # Resolution filter
            res = obs.get("spatial_resolution_m")
            if min_res is not None and (res is None or res < min_res):
                continue
            if max_res is not None and (res is None or res > max_res):
                continue

            # Bounding box intersection check
            bb = obs.get("bbox", {})
            if min_lat is not None and bb.get("max_lat", -999) < min_lat:
                continue
            if max_lat is not None and bb.get("min_lat", 999) > max_lat:
                continue
            if min_lon is not None and bb.get("max_lon", -999) < min_lon:
                continue
            if max_lon is not None and bb.get("min_lon", 999) > max_lon:
                continue

            # Search text query
            if search_query:
                sq = search_query.lower()
                pid = obs.get("product_id", "").lower()
                sensor = obs.get("sensor", "").lower()
                if sq not in pid and sq not in sensor:
                    continue

            matched.append(obs)

        total = len(matched)
        paginated = matched[offset : offset + limit]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": paginated,
        }

    def find_overlapping_pairs(
        self,
        source_sensor: str = "OHRC",
        reference_sensor: str = "LRO_NAC",
        min_overlap_pct: float = 1.0,
    ) -> list[dict]:
        """Calculates geographic overlap between source observations and reference observations.
        Forms the bridge between Layer 1 data explorer and Layer 2/3 registration.
        """
        sources = [o for o in self.observations.values() if o.get("sensor") == source_sensor]
        references = [o for o in self.observations.values() if o.get("sensor") == reference_sensor]

        pairs = []

        for src in sources:
            sbb = src.get("bbox", {})
            s_min_x, s_max_x = sbb.get("min_lon", 0), sbb.get("max_lon", 0)
            s_min_y, s_max_y = sbb.get("min_lat", 0), sbb.get("max_lat", 0)
            s_width = max(0.0, s_max_x - s_min_x)
            s_height = max(0.0, s_max_y - s_min_y)
            s_area = s_width * s_height

            if s_area <= 0:
                continue

            for ref in references:
                rbb = ref.get("bbox", {})
                r_min_x, r_max_x = rbb.get("min_lon", 0), rbb.get("max_lon", 0)
                r_min_y, r_max_y = rbb.get("min_lat", 0), rbb.get("max_lat", 0)
                r_width = max(0.0, r_max_x - r_min_x)
                r_height = max(0.0, r_max_y - r_min_y)
                r_area = r_width * r_height

                if r_area <= 0:
                    continue

                # Intersection bounds
                i_min_x = max(s_min_x, r_min_x)
                i_max_x = min(s_max_x, r_max_x)
                i_min_y = max(s_min_y, r_min_y)
                i_max_y = min(s_max_y, r_max_y)

                if i_max_x > i_min_x and i_max_y > i_min_y:
                    i_area = (i_max_x - i_min_x) * (i_max_y - i_min_y)
                    src_overlap_pct = (i_area / s_area) * 100.0
                    ref_overlap_pct = (i_area / r_area) * 100.0

                    if src_overlap_pct >= min_overlap_pct or ref_overlap_pct >= min_overlap_pct:
                        src_inc = (src.get("geometry") or {}).get("incidence_angle_deg") or 0.0
                        ref_inc = (ref.get("geometry") or {}).get("incidence_angle_deg") or 0.0
                        inc_diff = abs(src_inc - ref_inc)

                        # Compute Layer 3 Registration Suitability Score (0-100)
                        # High overlap + low incidence diff = optimal registration candidate
                        overlap_factor = min(100.0, max(src_overlap_pct, ref_overlap_pct))
                        incidence_penalty = min(50.0, inc_diff * 1.5)
                        suitability_score = round(max(10.0, overlap_factor * 0.7 + (50.0 - incidence_penalty) * 0.6), 1)

                        pairs.append({
                            "source_product_id": src.get("product_id"),
                            "source_sensor": src.get("sensor"),
                            "source_resolution_m": src.get("spatial_resolution_m"),
                            "source_preview": src.get("preview_local_rel"),
                            "reference_product_id": ref.get("product_id"),
                            "reference_sensor": ref.get("sensor"),
                            "reference_resolution_m": ref.get("spatial_resolution_m"),
                            "reference_preview": ref.get("preview_local_rel"),
                            "overlap_percent_of_source": round(src_overlap_pct, 2),
                            "overlap_percent_of_reference": round(ref_overlap_pct, 2),
                            "intersection_bbox": {
                                "min_lat": round(i_min_y, 4),
                                "max_lat": round(i_max_y, 4),
                                "min_lon": round(i_min_x, 4),
                                "max_lon": round(i_max_x, 4),
                            },
                            "solar_incidence_diff_deg": round(inc_diff, 2),
                            "registration_suitability_score": suitability_score,
                            "ready_for_layer2_overlap": True,
                            "ready_for_layer3_registration": True,
                        })

        pairs.sort(key=lambda p: p["overlap_percent_of_source"], reverse=True)
        return pairs


# Global Service Instance
data_service = LunarDataService()


class LunarDataHTTPHandler(SimpleHTTPRequestHandler):
    """Handles REST API calls and serves web application static files."""

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
        qs = parse_qs(parsed.query)

        # 1. API: Health Check
        if path == "/api/v1/health":
            self._send_json(200, {
                "status": "online",
                "service": "nexus-lunar-data",
                "layer": "Layer 1 — Lunar Data Explorer",
                "version": "1.0.0-poc1",
                "active_observations": len(data_service.observations),
                "timestamp": datetime.utcnow().isoformat(),
            })
            return

        # 2. API: Catalog Stats
        if path == "/api/v1/catalog/stats":
            self._send_json(200, data_service.get_stats())
            return

        # 3. API: Search & Query Observations
        if path == "/api/v1/observations":
            sensors_param = qs.get("sensor") or qs.get("sensors")
            sensors_list = None
            if sensors_param:
                s_set = set()
                for sp in sensors_param:
                    s_set.update([x.strip().upper() for x in sp.split(",") if x.strip()])
                sensors_list = list(s_set)

            def _safe_float(val: str | None) -> float | None:
                if val is None:
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            mission = qs.get("mission", [None])[0]
            min_lat = _safe_float(qs.get("min_lat", [None])[0])
            max_lat = _safe_float(qs.get("max_lat", [None])[0])
            min_lon = _safe_float(qs.get("min_lon", [None])[0])
            max_lon = _safe_float(qs.get("max_lon", [None])[0])
            min_res = _safe_float(qs.get("min_res", [None])[0])
            max_res = _safe_float(qs.get("max_res", [None])[0])
            q = qs.get("q", [None])[0]
            try:
                limit = int(qs.get("limit", [50])[0])
                offset = int(qs.get("offset", [0])[0])
            except (ValueError, TypeError):
                limit, offset = 50, 0

            result = data_service.query(
                sensors=sensors_list,
                mission=mission,
                min_lat=min_lat,
                max_lat=max_lat,
                min_lon=min_lon,
                max_lon=max_lon,
                min_res=min_res,
                max_res=max_res,
                search_query=q,
                limit=limit,
                offset=offset,
            )
            self._send_json(200, result)
            return

        # 4. API: Overlapping Pairs Discovery
        if path == "/api/v1/pairs/overlapping":
            src = qs.get("source", ["OHRC"])[0]
            ref = qs.get("reference", ["LRO_NAC"])[0]
            min_overlap = float(qs.get("min_overlap", [1.0])[0])
            pairs = data_service.find_overlapping_pairs(
                source_sensor=src,
                reference_sensor=ref,
                min_overlap_pct=min_overlap,
            )
            self._send_json(200, {
                "source_sensor": src,
                "reference_sensor": ref,
                "total_overlapping_pairs": len(pairs),
                "pairs": pairs,
            })
            return

        # 5. API: Single Observation Detail
        if path.startswith("/api/v1/observations/"):
            rest = path[len("/api/v1/observations/") :]
            if "/preview" in rest:
                product_id = rest.split("/preview")[0]
                obs = data_service.observations.get(product_id)
                if not obs:
                    self._send_json(404, {"error": f"Observation {product_id} not found"})
                    return
                
                # Check for preview image file
                rel = obs.get("preview_local_rel")
                if rel:
                    full_p = WORKSPACE_ROOT / rel
                    if full_p.exists():
                        self.path = f"/{rel}"
                        return super().do_GET()
                
                # Fallback to primary image if preview missing
                prim = obs.get("primary_local_rel")
                if prim:
                    full_p = WORKSPACE_ROOT / prim
                    if full_p.exists():
                        self.path = f"/{prim}"
                        return super().do_GET()

                self._send_json(404, {"error": "Preview image file not found on disk"})
                return
            else:
                product_id = rest
                obs = data_service.observations.get(product_id)
                if obs:
                    self._send_json(200, obs)
                else:
                    self._send_json(404, {"error": f"Observation {product_id} not found"})
                return

        # 6. POC 3: Classical Registration API
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

        if path.startswith("/api/v1/registration/"):
            from services.registration.server import registration_service, JOBS_DIR
            parts = path.strip("/").split("/")
            if len(parts) == 5:
                _, _, _, job_id, artifact = parts
                job_dir = JOBS_DIR / job_id
                target_img = job_dir / f"{artifact}.png"
                if target_img.exists():
                    self.path = str(target_img.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
                    return super().do_GET()
                else:
                    self._send_json(404, {"error": f"Artifact '{artifact}' for job {job_id} not found"})
                    return
            elif len(parts) == 4:
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

        # 7. Web App UI Serving
        if path == "/" or path == "/index.html":
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                with open(index_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if path in ["/styles.css", "/app.js"]:
            static_file = WEB_DIR / path.lstrip("/")
            if static_file.exists():
                mime, _ = mimetypes.guess_type(str(static_file))
                with open(static_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", f"{mime}; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Fallback to standard directory server for images in data/raw/...
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/v1/register":
            from services.registration.server import registration_service
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body) if body else {}
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            source_id = data.get("source_product_id") or data.get("source_image") or data.get("source_id") or "ch2_ohr_ncp_20230915t041230_boguslawsky_d18"
            reference_id = data.get("reference_product_id") or data.get("reference_image") or data.get("reference_id") or "M1345982701LR_BOGUSLAWSKY_REF"
            method = data.get("method", "SIFT")
            transform_type = data.get("transform_type", "Homography")
            try:
                ratio_thresh = float(data.get("ratio_test_thresh") or data.get("ratio_thresh") or 0.75)
                ransac_thresh = float(data.get("ransac_thresh_px") or data.get("ransac_thresh") or 3.0)
            except (ValueError, TypeError):
                ratio_thresh = 0.75
                ransac_thresh = 3.0

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


def run_server(port: int = 8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, LunarDataHTTPHandler)
    print(f"================================================================")
    print(f" [NEXUS-LUNAR] Layer 1 Microservice: Lunar Data Explorer Online")
    print(f" Web UI:       http://localhost:{port}/")
    print(f" Health API:   http://localhost:{port}/api/v1/health")
    print(f" Catalog API:  http://localhost:{port}/api/v1/observations")
    print(f" Pairs API:    http://localhost:{port}/api/v1/pairs/overlapping")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Layer 1 service...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run_server(port)
