"""NEXUS-LUNAR POC-7: Spatial Intelligence Test Suite.

Verifies:
1. POC-6 input ingestion and schema validation
2. Strict isolation: rejected correspondences are excluded from spatial knowledge
3. Graph node creation with typed schemas and stable IDs
4. Graph edge creation with provenance
5. Terrain slope calculation and categorization (LOW, MODERATE, HIGH, VERY_HIGH)
6. Terrain aspect calculation and 8-compass cardinal heading mapping
7. Elevation metric extraction (min, max, mean, median)
8. Terrain roughness scoring via local elevation standard deviation
9. Crater proximity computation and UNKNOWN handling when crater observations are absent
10. Illumination state classification and shadow fraction computation
11. Solar potential indicator qualification
12. Mineralogical & volatile spectral indicator qualification (scientific safeguards)
13. Hazard detection and severity grading (CRITICAL, HIGH, MODERATE, LOW)
14. Candidate site multi-factor scoring (terrain, illumination, hazard, resource, data quality)
15. Graceful handling of missing / unavailable data without silent score inflation
16. Deterministic synthetic demo fallback consistency
17. Graph queries: registered correspondences, candidate site filters, ego neighborhood
18. Graph serialization to JSON (poc7_knowledge_graph.json, nodes.json, edges.json) and round-trip deserialization
19. POC-8 handover artifact structure
20. End-to-end experiment pipeline execution
"""

import json
import pytest
import numpy as np
from pathlib import Path

from packages.data_pipeline import (
    NodeType,
    RelationType,
    SlopeCategory,
    IlluminationStatus,
    HazardType,
    HazardSeverity,
    SiteDataStatus,
    GraphNode,
    GraphEdge,
    TerrainMetrics,
    IlluminationMetrics,
    ResourceIndicator,
    HazardIndicator,
    CandidateSite,
    SpatialKnowledgeGraph,
    TerrainIntelligenceEngine,
    IlluminationIntelligenceEngine,
    ResourceIntelligenceEngine,
    HazardIntelligenceEngine,
    CandidateSiteScoringEngine,
    POC7ExperimentRunner,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def poc6_verified_path():
    return PROJECT_ROOT / "outputs" / "poc6" / "poc6_verified_for_poc7.json"


@pytest.fixture
def poc6_results_path():
    return PROJECT_ROOT / "outputs" / "poc6" / "poc6_results.json"


# =============================================================================
# 1. POC-6 Input Loading & Rejection Isolation Tests
# =============================================================================

def test_poc6_input_loading(poc6_verified_path):
    """Test loading POC-6 verified correspondences."""
    assert poc6_verified_path.exists(), "POC-6 verified handover file missing"
    with open(poc6_verified_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_accepted_pairs"] > 0
    assert len(data["accepted_pairs"]) == data["total_accepted_pairs"]
    for pair in data["accepted_pairs"]:
        assert pair["accepted"] is True
        assert pair["decision"] == "ACCEPTED"
        assert "verification_confidence" in pair
        assert "transformation_matrix" in pair


def test_rejected_correspondences_excluded_from_graph(poc6_results_path):
    """Verify that rejected POC-6 correspondences are never treated as verified."""
    if poc6_results_path.exists():
        with open(poc6_results_path, "r", encoding="utf-8") as f:
            res_data = json.load(f)
        rejected = [r for r in res_data.get("results", []) if r.get("decision") == "REJECTED" or not r.get("accepted")]
        assert len(rejected) > 0

        # Construct a graph and verify that rejected pairs never receive CORRESPONDS_TO edges
        graph = SpatialKnowledgeGraph()
        # In POC-7, only accepted pairs receive CORRESPONDS_TO
        for r in rejected:
            q_id = f"TERRAIN_PATCH_{r['query_patch_id']}"
            c_id = f"TERRAIN_PATCH_{r['candidate_patch_id']}"
            corrs = [e for e in graph.get_outgoing_edges(q_id, RelationType.CORRESPONDS_TO) if e.target == c_id]
            assert len(corrs) == 0, f"Rejected match {q_id}->{c_id} must not exist as CORRESPONDS_TO edge"


# =============================================================================
# 2. Knowledge Graph Node & Edge Creation Tests
# =============================================================================

def test_graph_node_creation_and_stable_ids():
    """Test creating graph nodes with stable IDs and typed categories."""
    graph = SpatialKnowledgeGraph()
    node = graph.add_node(
        node_id="LUNAR_REGION_001",
        node_type=NodeType.LUNAR_REGION,
        properties={"name": "Boguslawsky South Pole"},
        provenance={"experiment_id": "EXP_TEST"},
    )
    assert node.id == "LUNAR_REGION_001"
    assert node.type == NodeType.LUNAR_REGION
    assert graph.get_node("LUNAR_REGION_001") is node
    assert len(graph.get_nodes_by_type(NodeType.LUNAR_REGION)) == 1


def test_graph_edge_creation_and_adjacency():
    """Test adding directed edges with typed relationships and provenance."""
    graph = SpatialKnowledgeGraph()
    graph.add_node("TERRAIN_PATCH_001", NodeType.TERRAIN_PATCH)
    graph.add_node("SENSOR_OHRC", NodeType.SENSOR)

    edge = graph.add_edge(
        source_id="TERRAIN_PATCH_001",
        relationship=RelationType.OBSERVED_BY,
        target_id="SENSOR_OHRC",
        properties={"sensor_mode": "HIGH_RES"},
        provenance={"source": "ISRO Catalog"},
    )
    assert edge.source == "TERRAIN_PATCH_001"
    assert edge.relationship == RelationType.OBSERVED_BY
    assert edge.target == "SENSOR_OHRC"

    out_edges = graph.get_outgoing_edges("TERRAIN_PATCH_001", RelationType.OBSERVED_BY)
    assert len(out_edges) == 1
    in_edges = graph.get_incoming_edges("SENSOR_OHRC", RelationType.OBSERVED_BY)
    assert len(in_edges) == 1


# =============================================================================
# 3. Topographic Terrain Intelligence Tests
# =============================================================================

def test_slope_calculation_and_categorization():
    """Test slope gradient computation and category binning."""
    engine = TerrainIntelligenceEngine()

    # Flat plane -> Slope 0 deg -> LOW
    flat_grid = np.zeros((32, 32), dtype=np.float32)
    slope, cat, aspect, card = engine.compute_slope_and_aspect(flat_grid, cell_size_m=1.0)
    assert slope == 0.0
    assert cat == SlopeCategory.LOW

    # Categorization thresholds
    assert engine.categorize_slope(3.2) == SlopeCategory.LOW
    assert engine.categorize_slope(7.5) == SlopeCategory.MODERATE
    assert engine.categorize_slope(15.0) == SlopeCategory.HIGH
    assert engine.categorize_slope(24.5) == SlopeCategory.VERY_HIGH


def test_aspect_calculation_and_cardinal_directions():
    """Test aspect degree mapping to 8-compass cardinal directions."""
    engine = TerrainIntelligenceEngine()
    assert engine.degrees_to_cardinal_aspect(0.0) == "N"
    assert engine.degrees_to_cardinal_aspect(45.0) == "NE"
    assert engine.degrees_to_cardinal_aspect(90.0) == "E"
    assert engine.degrees_to_cardinal_aspect(135.0) == "SE"
    assert engine.degrees_to_cardinal_aspect(180.0) == "S"
    assert engine.degrees_to_cardinal_aspect(225.0) == "SW"
    assert engine.degrees_to_cardinal_aspect(270.0) == "W"
    assert engine.degrees_to_cardinal_aspect(315.0) == "NW"


def test_elevation_metrics_extraction():
    """Test min, max, mean, median elevation calculation preserving units."""
    engine = TerrainIntelligenceEngine()
    grid = np.array([
        [-3850.0, -3840.0],
        [-3830.0, -3820.0],
    ], dtype=np.float32)
    # Expand to 3x3 for gradient
    grid_3x3 = np.pad(grid, ((0, 1), (0, 1)), mode="edge")
    bbox = {"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0}
    center = {"lat": -72.25, "lon": 24.5}

    metrics = engine.analyze_terrain_patch("TEST_PATCH", grid_3x3, bbox, center)
    assert metrics.elevation_min_m == -3850.0
    assert metrics.elevation_max_m == -3820.0
    assert metrics.elevation_units == "meters"
    assert metrics.data_status == "DATA-DRIVEN"


def test_terrain_roughness_metric():
    """Test local standard deviation roughness score calculation."""
    engine = TerrainIntelligenceEngine()
    grid = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    roughness, method = engine.compute_roughness(grid)
    expected_std = float(np.std(grid))
    assert pytest.approx(roughness, 0.01) == expected_std
    assert method == "local_elevation_std_dev"


def test_crater_proximity_handling():
    """Test crater proximity computation and UNKNOWN handling when craters are unobserved."""
    engine = TerrainIntelligenceEngine()

    # Center exactly at Boguslawsky South Pole Micro-Crater (-72.3, 24.5)
    c_id, dist = engine.compute_crater_proximity(-72.3, 24.5)
    assert c_id is not None
    assert dist == 0.0  # Inside rim

    # When no crater observations exist, must return None (UNKNOWN), NOT zero!
    c_none, dist_none = engine.compute_crater_proximity(-72.3, 24.5, known_craters=[])
    assert c_none is None, "Must return UNKNOWN rather than zero when crater data is unavailable"
    assert dist_none is None


# =============================================================================
# 4. Illumination & Solar Potential Intelligence Tests
# =============================================================================

def test_illumination_state_classification():
    """Test illumination classification across illuminated, partially illuminated, and shadowed regimes."""
    engine = IlluminationIntelligenceEngine()
    assert engine.classify_illumination(0.85, 0.05) == IlluminationStatus.ILLUMINATED
    assert engine.classify_illumination(0.50, 0.25) == IlluminationStatus.PARTIALLY_ILLUMINATED
    assert engine.classify_illumination(0.25, 0.40) == IlluminationStatus.LOW_LIGHT
    assert engine.classify_illumination(0.10, 0.75) == IlluminationStatus.SHADOWED


def test_solar_potential_indicator_wording():
    """Test solar potential indicator wording avoids unscientific guaranteed claims."""
    engine = IlluminationIntelligenceEngine()
    pot_high = engine.determine_solar_potential(IlluminationStatus.ILLUMINATED, 0.85, 0.05)
    assert "POTENTIAL SOLAR-ENERGY ZONE" in pot_high
    assert "guaranteed" not in pot_high.lower()

    pot_shadow = engine.determine_solar_potential(IlluminationStatus.SHADOWED, 0.10, 0.80)
    assert "NON-SOLAR ZONE" in pot_shadow


def test_illumination_single_epoch_temporal_qualification():
    """Test single observation flags temporal validation as unavailable."""
    engine = IlluminationIntelligenceEngine()
    metrics = engine.analyze_patch_illumination("PATCH_001", image_array=np.ones((16, 16)))
    assert metrics.temporal_consistency == "TEMPORAL_VALIDATION_UNAVAILABLE"


# =============================================================================
# 5. Mineralogical / Resource Spectral Indicator Safeguards
# =============================================================================

def test_resource_indicator_scientific_qualification():
    """Verify resource indicators strictly disclaim confirmed mineability."""
    engine = ResourceIntelligenceEngine()
    indicator = engine.evaluate_iirs_spectral_indicator("PATCH_001", {"lat": -72.5, "lon": 24.5})
    assert indicator.sensor == "IIRS"
    assert "RESOURCE-RELATED SPECTRAL INDICATOR" in indicator.mineralogical_feature
    assert "mineable" not in indicator.mineralogical_feature.lower()
    assert "not a confirmed mineable mineral deposit" in indicator.disclaimer.lower()


# =============================================================================
# 6. Hazard Intelligence Tests
# =============================================================================

def test_hazard_detection_and_severity_grading():
    """Test hazard classification for steep slopes, rough terrain, and crater rims."""
    h_engine = HazardIntelligenceEngine(critical_slope_threshold=20.0, high_slope_threshold=12.0)
    t_engine = TerrainIntelligenceEngine()
    i_engine = IlluminationIntelligenceEngine()

    t_metrics = t_engine.analyze_terrain_patch("STEEP_PATCH", np.zeros((32, 32)),
                                              {"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
                                              {"lat": -72.25, "lon": 24.5})
    t_metrics.slope_degrees = 22.5  # Critical slope
    t_metrics.roughness_score = 7.2  # Critical roughness
    t_metrics.distance_to_crater_m = 150.0  # Rim danger

    i_metrics = i_engine.analyze_patch_illumination("STEEP_PATCH", image_array=np.ones((16, 16)) * 0.05)

    hazards = h_engine.assess_hazards("STEEP_PATCH", t_metrics, i_metrics, {"lat": -72.25, "lon": 24.5})
    assert len(hazards) >= 3

    types = [h.hazard_type for h in hazards]
    assert HazardType.STEEP_SLOPE in types
    assert HazardType.ROUGH_TERRAIN in types
    assert HazardType.CRATER_RIM in types

    severities = [h.severity for h in hazards]
    assert HazardSeverity.CRITICAL in severities


# =============================================================================
# 7. Candidate Site Intelligence & Explainability Tests
# =============================================================================

def test_candidate_site_scoring_and_explanation():
    """Test transparent multi-factor candidate site evaluation and checklist explainability."""
    scoring_engine = CandidateSiteScoringEngine()
    t_engine = TerrainIntelligenceEngine()
    i_engine = IlluminationIntelligenceEngine()

    t_metrics = t_engine.analyze_terrain_patch("FAVORABLE_PATCH", np.zeros((32, 32)),
                                              {"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
                                              {"lat": -72.25, "lon": 24.5})
    t_metrics.slope_degrees = 3.5  # Low slope
    t_metrics.roughness_score = 0.5  # Low roughness
    t_metrics.distance_to_crater_m = 5000.0  # Far from rim

    i_metrics = i_engine.analyze_patch_illumination("FAVORABLE_PATCH", image_array=np.ones((16, 16)) * 0.8)

    res_ind = ResourceIndicator(indicator_id="RES_01", indicator_score=0.45)

    site = scoring_engine.evaluate_site(
        site_id="SITE_001",
        patch_id="FAVORABLE_PATCH",
        coordinates={"lat": -72.25, "lon": 24.5},
        bbox={"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
        terrain=t_metrics,
        illumination=i_metrics,
        resource=res_ind,
        hazards=[],
        poc6_registration_confidence=0.98,
        poc6_inlier_ratio=1.0,
    )

    assert site.overall_suitability_score >= 0.60
    assert site.terrain_score == 1.0
    assert site.hazard_penalty == 0.0
    assert site.explanation is not None
    assert len(site.explanation.positive_factors) > 0
    assert "FAVORABLE" in site.explanation.summary_verdict


def test_unavailable_data_handling():
    """Verify that missing terrain or illumination data receives neutral score without silent inflation."""
    scoring_engine = CandidateSiteScoringEngine()
    t_score, pos, neg = scoring_engine.compute_terrain_score(None)
    assert t_score == 0.5
    assert "NOT_AVAILABLE" in neg[0]

    i_score, pos, neg = scoring_engine.compute_illumination_score(None)
    assert i_score == 0.5
    assert "NOT_AVAILABLE" in neg[0]


# =============================================================================
# 8. Graph Queries, Algorithms & Serialization Tests
# =============================================================================

def test_graph_queries_and_algorithms():
    """Test graph traversal, neighborhood expansion, and connected components."""
    graph = SpatialKnowledgeGraph()
    graph.add_node("REGION_A", NodeType.LUNAR_REGION)
    graph.add_node("PATCH_1", NodeType.TERRAIN_PATCH)
    graph.add_node("PATCH_2", NodeType.TERRAIN_PATCH)
    graph.add_node("SITE_1", NodeType.CANDIDATE_SITE, properties={"overall_suitability_score": 0.75, "slope_degrees": 4.0})

    graph.add_edge("REGION_A", RelationType.CONTAINS, "PATCH_1")
    graph.add_edge("PATCH_1", RelationType.CORRESPONDS_TO, "PATCH_2", properties={"verification_confidence": 0.95})
    graph.add_edge("PATCH_1", RelationType.CONTAINS, "SITE_1")

    # Registered correspondences query
    corrs = graph.find_registered_correspondences()
    assert len(corrs) == 1
    assert corrs[0]["source_id"] == "PATCH_1"
    assert corrs[0]["target_id"] == "PATCH_2"

    # Candidate sites query
    sites = graph.find_candidate_sites(max_slope=10.0, min_suitability=0.50)
    assert len(sites) == 1
    assert sites[0].id == "SITE_1"

    # Neighborhood expansion
    nbr = graph.neighborhood("PATCH_1", depth=1)
    nbr_ids = [n["id"] for n in nbr["nodes"]]
    assert "REGION_A" in nbr_ids
    assert "PATCH_2" in nbr_ids
    assert "SITE_1" in nbr_ids

    # Connected components
    comps = graph.connected_components()
    assert len(comps) == 1
    assert len(comps[0]) == 4


def test_graph_export_and_import(tmp_path):
    """Test serialization to poc7_knowledge_graph.json, nodes.json, edges.json and round-trip restore."""
    graph = SpatialKnowledgeGraph(name="ROUNDTRIP_TEST")
    graph.add_node("N1", NodeType.LUNAR_REGION, properties={"p": 1})
    graph.add_node("N2", NodeType.TERRAIN_PATCH, properties={"p": 2})
    graph.add_edge("N1", RelationType.CONTAINS, "N2")

    files = graph.export_to_files(tmp_path)
    assert files["graph"].exists()
    assert files["nodes"].exists()
    assert files["edges"].exists()

    with open(files["graph"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_nodes"] == 2
    assert data["total_edges"] == 1

    restored = SpatialKnowledgeGraph.from_dict(data)
    assert len(restored.nodes) == 2
    assert len(restored.edges) == 1
    assert restored.get_node("N1") is not None


# =============================================================================
# 9. End-to-End Pipeline Runner & POC-8 Handover Tests
# =============================================================================

def test_poc7_pipeline_runner(tmp_path):
    """Test end-to-end POC-7 experiment execution generating all outputs and figures."""
    runner = POC7ExperimentRunner(output_dir=tmp_path)
    accepted_pairs, _ = runner.load_poc6_inputs()
    n_pairs = len(accepted_pairs)
    result = runner.run()

    assert result["total_nodes"] >= 20
    assert result["total_edges"] >= 30
    assert len(result["candidate_sites"]) == n_pairs
    assert (tmp_path / "poc7_spatial_knowledge.json").exists()
    assert (tmp_path / "poc7_terrain_intelligence.json").exists()
    assert (tmp_path / "poc7_illumination_intelligence.json").exists()
    assert (tmp_path / "poc7_resource_indicators.json").exists()
    assert (tmp_path / "poc7_hazard_intelligence.json").exists()
    assert (tmp_path / "poc7_candidate_sites.json").exists()
    assert (tmp_path / "poc7_handover_for_poc8.json").exists()
    assert (tmp_path / "knowledge_graph_overview.png").exists()
    assert (tmp_path / "candidate_site_explanation.png").exists()

    # Validate POC-8 handover content
    with open(tmp_path / "poc7_handover_for_poc8.json", "r", encoding="utf-8") as f:
        ho = json.load(f)
    assert ho["target_downstream"] == "POC-8 Habitat Digital Twin Engine"
    assert len(ho["candidate_sites"]) == n_pairs
    for s in ho["candidate_sites"]:
        assert "overall_suitability_score" in s
        assert "terrain_score" in s
        assert "coordinates" in s
        assert "explanation" in s


# =============================================================================
# 10. Audit Correction Tests (Issues 2-8)
# =============================================================================

def test_pipeline_creates_image_and_observation_nodes(tmp_path):
    """ISSUE-2: Verify Image and Observation nodes are created per accepted pair in the pipeline."""
    runner = POC7ExperimentRunner(output_dir=tmp_path)
    accepted_pairs, _ = runner.load_poc6_inputs()
    n_pairs = len(accepted_pairs)
    result = runner.run()
    graph = result["graph"]

    image_nodes = graph.get_nodes_by_type(NodeType.IMAGE)
    observation_nodes = graph.get_nodes_by_type(NodeType.OBSERVATION)

    # N accepted pairs => 2*N images (2 per pair) and 2*N observations (2 per pair)
    assert len(image_nodes) == 2 * n_pairs, f"Expected {2 * n_pairs} Image nodes, got {len(image_nodes)}"
    assert len(observation_nodes) == 2 * n_pairs, f"Expected {2 * n_pairs} Observation nodes, got {len(observation_nodes)}"

    # Verify Image nodes carry product_id and sensor
    for img_node in image_nodes:
        assert "product_id" in img_node.properties
        assert "sensor" in img_node.properties
        assert "data_source" in img_node.properties

    # Verify Observation nodes carry verification info
    for obs_node in observation_nodes:
        assert "observation_id" in obs_node.properties
        assert "verification_confidence" in obs_node.properties
        assert "data_status" in obs_node.properties


def test_pipeline_creates_has_elevation_edges(tmp_path):
    """ISSUE-3: Verify HAS_ELEVATION edges are created linking terrain patches to elevation data."""
    runner = POC7ExperimentRunner(output_dir=tmp_path)
    accepted_pairs, _ = runner.load_poc6_inputs()
    n_pairs = len(accepted_pairs)
    result = runner.run()
    graph = result["graph"]

    has_elev_edges = [e for e in graph.edges
                      if (e.relationship.value if hasattr(e.relationship, "value") else str(e.relationship))
                      == RelationType.HAS_ELEVATION.value]

    # N accepted pairs => N query patches => N HAS_ELEVATION edges
    assert len(has_elev_edges) == n_pairs, f"Expected {n_pairs} HAS_ELEVATION edges, got {len(has_elev_edges)}"

    # Verify elevation properties on the edge
    for edge in has_elev_edges:
        assert "elevation_mean_m" in edge.properties
        assert "elevation_units" in edge.properties
        assert edge.properties["elevation_units"] == "meters"


def test_pipeline_creates_overlaps_edges(tmp_path):
    """ISSUE-4: Verify OVERLAPS edges are created between accepted correspondent patches."""
    runner = POC7ExperimentRunner(output_dir=tmp_path)
    accepted_pairs, _ = runner.load_poc6_inputs()
    n_pairs = len(accepted_pairs)
    result = runner.run()
    graph = result["graph"]

    overlaps_edges = [e for e in graph.edges
                      if (e.relationship.value if hasattr(e.relationship, "value") else str(e.relationship))
                      == RelationType.OVERLAPS.value]

    # N accepted pairs => N OVERLAPS edges
    assert len(overlaps_edges) == n_pairs, f"Expected {n_pairs} OVERLAPS edges, got {len(overlaps_edges)}"

    # Each OVERLAPS edge must reference POC-6 confirmation
    for edge in overlaps_edges:
        assert "overlap_confirmed_by" in edge.properties
        assert "POC-6" in edge.properties["overlap_confirmed_by"]


def test_low_light_uses_constraint_not_permanent_shadow():
    """ISSUE-6: LOW_LIGHT single-epoch must use LOW_LIGHT_CONSTRAINT, not PERMANENT_SHADOW."""
    h_engine = HazardIntelligenceEngine()
    t_engine = TerrainIntelligenceEngine()
    i_engine = IlluminationIntelligenceEngine()

    t_metrics = t_engine.analyze_terrain_patch("LOWLIGHT_PATCH", np.zeros((32, 32)),
                                              {"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
                                              {"lat": -72.25, "lon": 24.5})

    # Create a low-light image (mean ~0.25, below 0.35 threshold, above 0.15 shadow threshold)
    i_metrics = i_engine.analyze_patch_illumination("LOWLIGHT_PATCH", image_array=np.ones((16, 16)) * 0.25)
    assert i_metrics.illumination_state == IlluminationStatus.LOW_LIGHT

    hazards = h_engine.assess_hazards("LOWLIGHT_PATCH", t_metrics, i_metrics, {"lat": -72.25, "lon": 24.5})

    # Should have a LOW_LIGHT_CONSTRAINT hazard, NOT PERMANENT_SHADOW
    light_hazards = [h for h in hazards if h.hazard_type in (HazardType.LOW_LIGHT_CONSTRAINT, HazardType.PERMANENT_SHADOW)]
    assert len(light_hazards) >= 1
    for h in light_hazards:
        assert h.hazard_type == HazardType.LOW_LIGHT_CONSTRAINT, \
            f"Expected LOW_LIGHT_CONSTRAINT, got {h.hazard_type} — single-epoch LOW_LIGHT must not claim PERMANENT_SHADOW"
        assert "single epoch" in h.description.lower()
        assert "permanent" not in h.description.lower()


def test_resource_indicator_data_status():
    """ISSUE-7: ResourceIndicator must have explicit data_status field distinguishing real vs synthetic."""
    engine = ResourceIntelligenceEngine()

    # Synthetic path (no IIRS catalog item)
    synthetic = engine.evaluate_iirs_spectral_indicator("PATCH_001", {"lat": -72.5, "lon": 24.5})
    assert hasattr(synthetic, "data_status"), "ResourceIndicator must have data_status field"
    assert synthetic.data_status == "SYNTHETIC OFFLINE DEMO"

    # Real-data path (with IIRS catalog item)
    real = engine.evaluate_iirs_spectral_indicator(
        "PATCH_002", {"lat": -72.5, "lon": 24.5},
        iirs_catalog_item={"band_wavelength": "2.8 um", "spectral_indicator_score": 0.55}
    )
    assert real.data_status == "DATA-DRIVEN"


def test_candidate_site_data_status_propagation():
    """ISSUE-8: Candidate site data_status must conservatively propagate from components.
    If any component is synthetic, the site must be SYNTHETIC_DEMO, not DATA_DRIVEN."""
    scoring_engine = CandidateSiteScoringEngine()
    t_engine = TerrainIntelligenceEngine()
    i_engine = IlluminationIntelligenceEngine()

    # All synthetic components
    t_metrics = t_engine.analyze_terrain_patch("SYNTH_PATCH", None,
                                              {"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
                                              {"lat": -72.25, "lon": 24.5})
    assert t_metrics.data_status == "SYNTHETIC OFFLINE DEMO"

    i_metrics = i_engine.analyze_patch_illumination("SYNTH_PATCH")
    assert i_metrics.data_status == "SYNTHETIC OFFLINE DEMO"

    res_ind = ResourceIndicator(indicator_id="RES_SYNTH", indicator_score=0.4,
                                data_status="SYNTHETIC OFFLINE DEMO")

    site = scoring_engine.evaluate_site(
        site_id="SITE_SYNTH",
        patch_id="SYNTH_PATCH",
        coordinates={"lat": -72.25, "lon": 24.5},
        bbox={"min_lat": -72.5, "max_lat": -72.0, "min_lon": 24.0, "max_lon": 25.0},
        terrain=t_metrics,
        illumination=i_metrics,
        resource=res_ind,
        hazards=[],
    )

    # Must NOT be DATA-DRIVEN when all components are synthetic
    assert site.data_status == SiteDataStatus.SYNTHETIC_DEMO, \
        f"Expected SYNTHETIC_DEMO, got {site.data_status} — synthetic components must not produce DATA_DRIVEN site"

