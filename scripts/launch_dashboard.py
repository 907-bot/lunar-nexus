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
