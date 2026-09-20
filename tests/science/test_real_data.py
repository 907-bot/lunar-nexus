"""Tests for real data endpoints in Science Intelligence API."""

import pytest
import json
import urllib.request
from http.server import HTTPServer
import threading
import time

from scripts.launch_dashboard import NexusDashboardHandler

PORT = 8001

@pytest.fixture(scope="module")
def api_server():
    server = HTTPServer(("localhost", PORT), NexusDashboardHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(1) # wait for server to start
    yield f"http://localhost:{PORT}"
    server.shutdown()
    server.server_close()

def test_catalog_regions(api_server):
    req = urllib.request.urlopen(f"{api_server}/api/catalog/regions")
    assert req.getcode() == 200
    data = json.loads(req.read().decode("utf-8"))
    assert "regions" in data
    assert isinstance(data["regions"], list)

def test_real_region_physics_extraction(api_server):
    req = urllib.request.urlopen(f"{api_server}/api/catalog/regions")
    regions = json.loads(req.read().decode("utf-8"))["regions"]
    if not regions:
        pytest.skip("No real regions in catalog")
    
    real_region_id = regions[0]["id"]
    req = urllib.request.urlopen(f"{api_server}/api/science/region/{real_region_id}")
    assert req.getcode() == 200
    data = json.loads(req.read().decode("utf-8"))
    
    assert data.get("data_mode") == "REAL MISSION DATA"
    assert data["physics"]["thermal_estimate"] is None
    assert "Missing actual terrain models" in data["limitations"]
    
    # Assert missing files logic
    missing_str = " ".join(data["missing_data"])
    assert "Raw DEM / terrain data" in data["missing_data"]
    assert "Raw Radiation dataset" in data["missing_data"]
    
    # Check that confidence scores are passed as None when insufficient data
    assert data["confidence"]["physics"] is None or data["confidence"]["physics"] < 1.0
    assert data["chemistry"]["status"] == "INSUFFICIENT_DATA"

def test_demo_region(api_server):
    req = urllib.request.urlopen(f"{api_server}/api/science/region/DEMO-LUNAR-001")
    assert req.getcode() == 200
    data = json.loads(req.read().decode("utf-8"))
    
    assert data.get("data_mode") == "SYNTHETIC DEMONSTRATION"
    assert data["physics"]["solar_elevation_deg"] == 15.0
