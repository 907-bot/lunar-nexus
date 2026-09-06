"""Unit and integration tests for POC 1: Lunar Data & Geo Explorer.
Verifies metadata parsing, coordinate normalization, spatial queries,
overlapping pair candidate discovery, and REST API microservice endpoints.
"""

import sys
import json
import unittest
import threading
import time
from http.server import HTTPServer
from pathlib import Path
import urllib.request
import urllib.error

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from packages.data_pipeline.models import (
    SensorType,
    MissionType,
    BoundingBox,
    ObservationGeometry,
    LunarObservation,
    CatalogQuery,
)
from packages.data_pipeline.catalog import LunarDataCatalog
from packages.data_pipeline.metadata_parser import MetadataParser
from packages.data_pipeline.issdc_client import ISSDCClient
from services.lunar_data.server import LunarDataService, LunarDataHTTPHandler


class TestLunarDataExplorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = LunarDataCatalog(WORKSPACE_ROOT / "data" / "catalog.json")
        cls.data_service = LunarDataService(WORKSPACE_ROOT / "data" / "catalog.json")

    def test_01_catalog_loaded_items(self):
        """Validates that catalog indexes the Chandrayaan-2 and LRO products."""
        observations = self.catalog.list_observations()
        self.assertGreaterEqual(len(observations), 10, "Catalog should contain at least 10 indexed products")
        
        # Check presence of key sensors
        sensors = {obs.sensor for obs in observations}
        self.assertIn(SensorType.OHRC, sensors, "Catalog must include Chandrayaan-2 OHRC")
        self.assertIn(SensorType.TMC2, sensors, "Catalog must include Chandrayaan-2 TMC-2")
        self.assertIn(SensorType.LRO_NAC, sensors, "Catalog must include LRO NAC")

    def test_02_observation_model_and_coordinate_normalization(self):
        """Validates coordinate bounding box properties and center calculation."""
        bbox = BoundingBox(min_lat=-74.5, max_lat=-72.0, min_lon=24.0, max_lon=28.0)
        center_lat, center_lon = bbox.center
        self.assertAlmostEqual(center_lat, -73.25)
        self.assertAlmostEqual(center_lon, 26.0)
        
        coords = bbox.polygon_coords
        self.assertEqual(len(coords), 5, "Polygon coordinates should be a closed ring with 5 points")
        self.assertEqual(coords[0], coords[-1], "First and last point must match for closed polygon")

    def test_03_metadata_parser_pds3(self):
        """Tests PDS3 label parsing and coordinate normalization from 0..360 to -180..180."""
        sample_pds3_label = """
        PDS_VERSION_ID = PDS3
        RECORD_TYPE = FIXED_LENGTH
        PRODUCT_ID = "M1345982701LR"
        INSTRUMENT_HOST_NAME = "LUNAR RECONNAISSANCE ORBITER"
        INSTRUMENT_ID = "LROC"
        START_TIME = 2020-09-15T04:12:30.123
        MAP_RESOLUTION = 0.5 <METER/PIXEL>
        MINIMUM_LATITUDE = -74.5 <DEGREE>
        MAXIMUM_LATITUDE = -72.0 <DEGREE>
        WESTERNMOST_LONGITUDE = 24.0 <DEGREE>
        EASTERNMOST_LONGITUDE = 28.0 <DEGREE>
        INCIDENCE_ANGLE = 67.0 <DEGREE>
        EMISSION_ANGLE = 1.2 <DEGREE>
        PHASE_ANGLE = 66.8 <DEGREE>
        SOLAR_AZIMUTH_ANGLE = 112.5 <DEGREE>
        """
        obs = MetadataParser.observation_from_pds3(sample_pds3_label)
        self.assertEqual(obs.product_id, "M1345982701LR")
        self.assertEqual(obs.sensor, SensorType.LRO_NAC)
        self.assertEqual(obs.mission, MissionType.LRO)
        self.assertAlmostEqual(obs.spatial_resolution_m, 0.5)
        self.assertAlmostEqual(obs.bbox.min_lat, -74.5)
        self.assertAlmostEqual(obs.bbox.max_lat, -72.0)
        self.assertAlmostEqual(obs.bbox.min_lon, 24.0)
        self.assertAlmostEqual(obs.bbox.max_lon, 28.0)
        self.assertIsNotNone(obs.geometry.incidence_angle_deg)
        self.assertAlmostEqual(obs.geometry.incidence_angle_deg, 67.0)

    def test_04_issdc_pds4_xml_parsing(self):
        """Tests parsing of real Chandrayaan-2 PDS4 XML label on disk."""
        xml_path = WORKSPACE_ROOT / "data" / "raw" / "ohrc" / "ch2_ohr_ncp_20230915t041230_boguslawsky_d18" / "ch2_ohr_ncp_20230915t041230_boguslawsky_d18.xml"
        if not xml_path.exists():
            self.skipTest(f"PDS4 XML file not found at {xml_path}")

        client = ISSDCClient(raw_dir=WORKSPACE_ROOT / "data" / "raw")
        obs = client.parse_pds4_xml(xml_path)
        self.assertEqual(obs.product_id, "ch2_ohr_ncp_20230915t041230_boguslawsky_d18")
        self.assertEqual(obs.sensor, SensorType.OHRC)
        self.assertEqual(obs.mission, MissionType.CHANDRAYAAN2)
        self.assertAlmostEqual(obs.spatial_resolution_m, 0.25)
        self.assertAlmostEqual(obs.bbox.min_lat, -74.5)
        self.assertAlmostEqual(obs.bbox.max_lat, -72.0)
        self.assertAlmostEqual(obs.bbox.min_lon, 24.0)
        self.assertAlmostEqual(obs.bbox.max_lon, 28.0)
        self.assertIsNotNone(obs.geometry.solar_zenith_deg)

    def test_05_spatial_and_sensor_query(self):
        """Tests filtering observations by sensor and spatial bounding box."""
        # Query only OHRC
        query_ohrc = CatalogQuery(sensors=[SensorType.OHRC])
        res_ohrc = self.catalog.query(query_ohrc)
        self.assertGreater(len(res_ohrc), 0)
        for r in res_ohrc:
            self.assertEqual(r.sensor, SensorType.OHRC)

        # Query with spatial bounding box
        query_box = CatalogQuery(
            bbox=BoundingBox(min_lat=-75.0, max_lat=-70.0, min_lon=20.0, max_lon=30.0)
        )
        res_box = self.catalog.query(query_box)
        self.assertGreater(len(res_box), 0, "Should match Boguslawsky crater observations")

    def test_06_overlapping_pairs_discovery(self):
        """Tests geographic overlap candidate discovery between OHRC and LRO NAC."""
        pairs = self.catalog.find_overlapping_pairs(
            source_sensor=SensorType.OHRC,
            reference_sensor=SensorType.LRO_NAC,
            min_overlap_pct=5.0,
        )
        self.assertGreaterEqual(len(pairs), 1, "Must find at least 1 overlapping pair (e.g. Boguslawsky / Shackleton)")
        top_pair = pairs[0]
        self.assertEqual(top_pair["source_sensor"], "OHRC")
        self.assertEqual(top_pair["reference_sensor"], "LRO_NAC")
        self.assertGreater(top_pair["overlap_percent_of_source"], 0.0)
        self.assertIn("intersection_bbox", top_pair)
        self.assertIn("solar_incidence_diff_deg", top_pair)

    def test_07_service_catalog_stats(self):
        """Tests data service aggregation of catalog statistics."""
        stats = self.data_service.get_stats()
        self.assertIn("total_observations", stats)
        self.assertIn("sensors", stats)
        self.assertIn("missions", stats)
        self.assertGreaterEqual(stats["total_observations"], 10)
        self.assertIn("OHRC", stats["sensors"])
        self.assertIn("LRO_NAC", stats["sensors"])

    def test_08_live_http_server_endpoints(self):
        """Spins up a temporary live instance of LunarDataHTTPHandler to verify all REST endpoints."""
        test_port = 8899
        server = HTTPServer(("127.0.0.1", test_port), LunarDataHTTPHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        time.sleep(0.3)

        base_url = f"http://127.0.0.1:{test_port}"
        try:
            # 1. Health endpoint
            with urllib.request.urlopen(f"{base_url}/api/v1/health") as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(data["status"], "online")
                self.assertIn("Layer 1", data["layer"])

            # 2. Stats endpoint
            with urllib.request.urlopen(f"{base_url}/api/v1/catalog/stats") as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertGreater(data["total_observations"], 0)

            # 3. Observations search endpoint
            with urllib.request.urlopen(f"{base_url}/api/v1/observations?sensor=OHRC") as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("items", data)
                self.assertGreater(len(data["items"]), 0)
                for item in data["items"]:
                    self.assertEqual(item["sensor"], "OHRC")

            # 4. Overlapping pairs endpoint
            with urllib.request.urlopen(f"{base_url}/api/v1/pairs/overlapping?source=OHRC&reference=LRO_NAC") as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("pairs", data)
                self.assertGreater(data["total_overlapping_pairs"], 0)

            # 5. Registration methods endpoint
            with urllib.request.urlopen(f"{base_url}/api/v1/registration/methods") as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("algorithms", data)
                algo_ids = [a["id"] for a in data["algorithms"]]
                self.assertIn("SIFT", algo_ids)
                self.assertIn("RootSIFT", algo_ids)
                self.assertIn("ORB", algo_ids)
                self.assertIn("AKAZE", algo_ids)
                self.assertIn("PhaseCorrelation", algo_ids)

            # 6. Web UI root
            with urllib.request.urlopen(f"{base_url}/") as resp:
                self.assertEqual(resp.status, 200)
                content = resp.read().decode("utf-8")
                self.assertIn("NEXUS-LUNAR", content)
                self.assertIn("POC 3 REGISTRATION", content)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
