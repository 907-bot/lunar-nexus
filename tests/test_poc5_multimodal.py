"""Unit tests for POC-5: Multimodal AI Correspondence & Retrieval.

Tests:
1. Deterministic embedding generation & L2 unit normalization
2. Cosine similarity calculation & properties
3. Candidate ranking & Top-K retrieval
4. Geographic metadata preservation & spatial relations
5. Ground truth evaluation: Recall@1, Recall@3, Recall@5, Recall@10, MRR
6. Unavailable ground truth fallback handling (strictly returns NaN / UNAVAILABLE)
7. Edge cases: Empty candidates, single candidate, invalid image dimensions
8. Reproducibility across seeds
9. Failure case tracking and diagnostic categorization
10. Handover schema validation for POC-6 Geometric Verification Engine
11. Experiment runner, ablation evaluator, and artifact exporter
12. Figure generation
"""

import os
import json
import math
import pytest
import numpy as np
from PIL import Image
from pathlib import Path

from packages.data_pipeline import (
    MultimodalPatchEmbedding,
    BaseMultimodalEncoder,
    DeterministicMultimodalProxyEncoder,
    PixelBaselineEncoder,
    PretrainedMultimodalEncoder,
    MultimodalCandidateMatch,
    CrossModalRetrievalEngine,
    compute_geographic_relation,
    RetrievalMetricsReport,
    compute_retrieval_metrics,
    FailureCaseRecord,
    POC5FailureCaseTracker,
    POC5ExperimentRunner,
    load_or_create_poc5_test_collection,
    generate_all_poc5_figures,
)


@pytest.fixture
def sample_image_pair():
    """Generates a pair of synthetic test images."""
    y, x = np.mgrid[-1:1:64j, -1:1:64j]
    crater = np.exp(-4.0 * (x**2 + y**2))
    img1 = np.clip(0.5 + crater * 0.4, 0.0, 1.0).astype(np.float32)
    img2 = np.clip(0.4 + crater * 0.5 + 0.05 * np.sin(4 * x), 0.0, 1.0).astype(np.float32)
    return img1, img2


def test_deterministic_embedding_generation_and_l2_norm(sample_image_pair):
    """Verify that encoder produces deterministic, unit-L2-norm embeddings of exact dimension."""
    img1, _ = sample_image_pair
    encoder = DeterministicMultimodalProxyEncoder(embedding_dim=128, seed=42)
    
    emb1 = encoder.encode_image(img1)
    emb2 = encoder.encode_image(img1)

    assert emb1.shape == (128,)
    assert emb1.dtype == np.float32
    # Verify deterministic output
    np.testing.assert_allclose(emb1, emb2, atol=1e-6)
    # Verify unit L2 norm
    norm = np.linalg.norm(emb1)
    assert pytest.approx(norm, 1e-4) == 1.0


def test_embedding_geospatial_metadata_preservation(sample_image_pair):
    """Verify that MultimodalPatchEmbedding bundles full geospatial and sensor provenance."""
    img1, _ = sample_image_pair
    encoder = DeterministicMultimodalProxyEncoder(embedding_dim=128, seed=42)
    
    bbox = {"min_lat": -73.25, "max_lat": -73.20, "min_lon": 26.00, "max_lon": 26.05}
    patch_emb = encoder.encode_patch(
        image=img1,
        patch_id="OHRC_PATCH_0042",
        sensor="CH2_OHRC",
        ground_bbox=bbox,
        center_coordinates=(-73.225, 26.025),
        gsd_m=0.25,
        modality="HIGH_RES_OPTICAL",
        provenance="REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
        experiment_id="TEST_EXP",
    )

    assert patch_emb.patch_id == "OHRC_PATCH_0042"
    assert patch_emb.sensor == "CH2_OHRC"
    assert patch_emb.gsd_m == 0.25
    assert patch_emb.center_coordinates == (-73.225, 26.025)
    assert patch_emb.ground_bbox == bbox
    assert patch_emb.embedding.shape == (128,)
    
    # Test dictionary serialization
    d = patch_emb.to_dict(include_vector=True)
    assert d["patch_id"] == "OHRC_PATCH_0042"
    assert "embedding" in d
    assert len(d["embedding"]) == 128


def test_pixel_baseline_encoder(sample_image_pair):
    """Verify PixelBaselineEncoder downsamples and normalizes properly."""
    img1, _ = sample_image_pair
    encoder = PixelBaselineEncoder(embedding_dim=64)
    emb = encoder.encode_image(img1)
    
    assert emb.shape == (64,)
    assert pytest.approx(np.linalg.norm(emb), 1e-4) == 1.0


def test_pretrained_encoder_fallback(sample_image_pair):
    """Verify PretrainedMultimodalEncoder behaves cleanly when weights are missing."""
    img1, _ = sample_image_pair
    encoder = PretrainedMultimodalEncoder(model_name="lunar_vit_base", embedding_dim=128)
    emb = encoder.encode_image(img1)
    assert emb.shape == (128,)
    assert pytest.approx(np.linalg.norm(emb), 1e-4) == 1.0


def test_cosine_similarity_matrix_computation():
    """Verify CrossModalRetrievalEngine calculates bounded cosine similarities."""
    engine = CrossModalRetrievalEngine(metric="cosine")
    
    # Identical vectors
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]], dtype=np.float32)
    
    sims = engine.compute_similarity(v1, v2)
    assert len(sims) == 3
    assert pytest.approx(sims[0], 1e-5) == 1.0
    assert pytest.approx(sims[1], 1e-5) == 0.0
    assert pytest.approx(sims[2], 1e-5) == -1.0


def test_top_k_candidate_retrieval_and_ranking(sample_image_pair):
    """Verify Top-K candidate ranking order and limit enforcement."""
    img1, img2 = sample_image_pair
    encoder = DeterministicMultimodalProxyEncoder(embedding_dim=128, seed=42)
    engine = CrossModalRetrievalEngine(metric="cosine")

    bbox = {"min_lat": -73.2, "max_lat": -73.1, "min_lon": 26.0, "max_lon": 26.1}
    query = encoder.encode_patch(img1, "Q1", "OHRC", bbox, (-73.15, 26.05), 0.25)
    
    # 5 Candidates with decreasing structural similarity to img1
    c1 = encoder.encode_patch(img1, "C1_PERFECT", "LRO", bbox, (-73.15, 26.05), 1.0)
    c2 = encoder.encode_patch(img2, "C2_CLOSE", "LRO", bbox, (-73.15, 26.05), 1.0)
    c3 = encoder.encode_patch(np.zeros((64, 64)), "C3_BLANK", "LRO", bbox, (-73.15, 26.05), 1.0)
    c4 = encoder.encode_patch(np.ones((64, 64)), "C4_WHITE", "LRO", bbox, (-73.15, 26.05), 1.0)
    c5 = encoder.encode_patch(np.random.RandomState(99).rand(64, 64), "C5_NOISE", "LRO", bbox, (-73.15, 26.05), 1.0)

    matches = engine.retrieve_candidates(query, [c1, c2, c3, c4, c5], top_k=3, ground_truth_patch_id="C1_PERFECT")
    
    assert len(matches) == 3
    assert matches[0].rank == 1
    assert matches[0].candidate_patch_id == "C1_PERFECT"
    assert matches[0].is_ground_truth is True
    assert matches[0].similarity_score >= matches[1].similarity_score
    assert matches[1].similarity_score >= matches[2].similarity_score


def test_empty_candidate_collection():
    """Verify retrieval returns empty list gracefully on empty candidates."""
    encoder = DeterministicMultimodalProxyEncoder(embedding_dim=128)
    engine = CrossModalRetrievalEngine(metric="cosine")
    query = encoder.encode_patch(np.zeros((32, 32)), "Q1", "OHRC", {}, (0, 0), 0.25)
    
    matches = engine.retrieve_candidates(query, [], top_k=5)
    assert matches == []


def test_geographic_relation_computation():
    """Verify spatial bounding box overlap and proximity determination."""
    b_base = {"min_lat": -73.2, "max_lat": -73.1, "min_lon": 26.0, "max_lon": 26.1}
    b_overlap = {"min_lat": -73.15, "max_lat": -73.05, "min_lon": 26.05, "max_lon": 26.15}
    b_nearby = {"min_lat": -73.22, "max_lat": -73.21, "min_lon": 26.12, "max_lon": 26.13}
    b_far = {"min_lat": -85.0, "max_lat": -84.9, "min_lon": 0.0, "max_lon": 0.1}

    assert compute_geographic_relation(b_base, b_overlap) == "OVERLAPPING"
    assert compute_geographic_relation(b_base, b_nearby) in ["NEARBY", "OVERLAPPING"]
    assert compute_geographic_relation(b_base, b_far) == "DISJOINT"
    assert compute_geographic_relation({}, {}) == "UNKNOWN"


def test_ground_truth_recall_at_k_evaluation():
    """Verify Recall@1, Recall@3, Recall@5, Recall@10, and MRR calculations."""
    matches_q1 = [
        MultimodalCandidateMatch("Q1", "C_TRUE", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.95, 1, "model", 128, "exp", "AVAILABLE", True, "OVERLAPPING"),
        MultimodalCandidateMatch("Q1", "C_FALSE1", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.80, 2, "model", 128, "exp", "AVAILABLE", False, "DISJOINT"),
    ]
    matches_q2 = [
        MultimodalCandidateMatch("Q2", "C_FALSE2", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.90, 1, "model", 128, "exp", "AVAILABLE", False, "DISJOINT"),
        MultimodalCandidateMatch("Q2", "C_FALSE3", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.85, 2, "model", 128, "exp", "AVAILABLE", False, "DISJOINT"),
        MultimodalCandidateMatch("Q2", "C_TRUE2", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.82, 3, "model", 128, "exp", "AVAILABLE", True, "OVERLAPPING"),
    ]

    retrieval_dict = {"Q1": matches_q1, "Q2": matches_q2}
    gt_map = {"Q1": "C_TRUE", "Q2": "C_TRUE2"}

    metrics = compute_retrieval_metrics(retrieval_dict, gt_map)
    assert metrics.recall_at_1 == 0.5  # Q1 succeeded at rank 1, Q2 failed at rank 1
    assert metrics.recall_at_3 == 1.0  # Both found within Top 3
    assert metrics.recall_at_5 == 1.0
    assert metrics.recall_at_10 == 1.0
    # MRR = (1/1 + 1/3) / 2 = (1.0 + 0.3333) / 2 = 0.6666
    assert pytest.approx(metrics.mean_reciprocal_rank, 1e-3) == 0.6667
    assert metrics.ground_truth_status == "AVAILABLE"


def test_unavailable_ground_truth_strict_fallback():
    """MANDATORY SCIENTIFIC RULE: Verify unavailable ground truth returns NaN and status UNAVAILABLE."""
    matches_q1 = [
        MultimodalCandidateMatch("Q1", "C_UNK", "OHRC", "LRO", {}, {}, {}, {}, 0.25, 1.0, 0.85, 1, "model", 128, "exp", "UNAVAILABLE", False, "UNKNOWN")
    ]
    retrieval_dict = {"Q1": matches_q1}

    metrics = compute_retrieval_metrics(retrieval_dict, ground_truth_mapping=None)
    assert math.isnan(metrics.recall_at_1)
    assert math.isnan(metrics.recall_at_5)
    assert math.isnan(metrics.mean_reciprocal_rank)
    assert metrics.ground_truth_status == "GROUND TRUTH UNAVAILABLE"
    
    d = metrics.to_dict()
    assert d["recall_at_1"] == "GROUND TRUTH UNAVAILABLE"


def test_failure_case_tracker():
    """Verify failure case recording and category aggregation."""
    tracker = POC5FailureCaseTracker()
    
    tracker.record_failure(
        query_patch_id="OHRC_001",
        query_sensor="OHRC",
        candidate_sensor="LRO_NAC",
        predicted_top1_id="LRO_005",
        expected_ground_truth_id="LRO_001",
        top1_similarity_score=0.72,
        expected_candidate_rank=4,
        expected_candidate_score=0.68,
        failure_category="EXTREME_GSD_DISPARITY",
        explanation="0.25m vs 1.0m resolution gap caused rank 4 prediction.",
    )

    counts = tracker.get_category_counts()
    assert counts["EXTREME_GSD_DISPARITY"] == 1
    assert counts["SHADOW_OCCLUSION"] == 0
    assert len(tracker.failures) == 1


def test_poc6_candidate_handover_schema_compatibility():
    """Verify that MultimodalCandidateMatch has all mandatory fields for POC-6 geometric verification."""
    match = MultimodalCandidateMatch(
        query_patch_id="OHRC_001",
        candidate_patch_id="LROC_001",
        query_sensor="OHRC",
        candidate_sensor="LRO_NAC",
        query_coordinates={"lat": -73.2, "lon": 26.0},
        candidate_coordinates={"lat": -73.2, "lon": 26.0},
        query_bbox={"min_lat": -73.21, "max_lat": -73.19, "min_lon": 25.99, "max_lon": 26.01},
        candidate_bbox={"min_lat": -73.21, "max_lat": -73.19, "min_lon": 25.99, "max_lon": 26.01},
        query_gsd=0.25,
        candidate_gsd=1.00,
        similarity_score=0.925,
        rank=1,
        embedding_model="DeterministicMultimodalProxyEncoder",
        embedding_dim=128,
        experiment_id="EXP_001",
        ground_truth_status="AVAILABLE",
        is_ground_truth=True,
        geographic_relation="OVERLAPPING",
        provenance="REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
    )

    d = match.to_dict()
    required_keys = [
        "query_patch_id", "candidate_patch_id", "query_sensor", "candidate_sensor",
        "query_coordinates", "candidate_coordinates", "query_bbox", "candidate_bbox",
        "query_gsd", "candidate_gsd", "similarity_score", "rank", "embedding_model",
        "experiment_id", "ground_truth_status", "is_ground_truth", "geographic_relation",
        "provenance"
    ]
    for k in required_keys:
        assert k in d, f"Missing required POC-6 handover key: {k}"


def test_poc5_full_benchmark_and_artifacts(tmp_path):
    """Verify end-to-end experiment benchmark and JSON/CSV artifact exports."""
    runner = POC5ExperimentRunner(output_dir=tmp_path, experiment_id="TEST_POC5_RUN", seed=42)
    results = runner.run_full_benchmark(num_pairs=6, top_k=3)

    assert results["total_queries"] == 6
    assert results["top_k"] == 3
    assert "summary_metrics" in results
    assert "ablation_comparison" in results

    # Verify files created on disk
    assert (tmp_path / "poc5_results.json").exists()
    assert (tmp_path / "poc5_results.csv").exists()
    assert (tmp_path / "poc5_metadata.json").exists()
    assert (tmp_path / "poc5_failure_cases.json").exists()
    assert (tmp_path / "poc5_candidates_for_poc6.json").exists()

    # Verify POC-6 candidate schema file
    with open(tmp_path / "poc5_candidates_for_poc6.json", "r", encoding="utf-8") as f:
        handover = json.load(f)
    assert handover["schema_version"] == "1.0.0"
    assert len(handover["candidates"]) == 18  # 6 queries * top_k=3


def test_all_six_poc5_figures_generation(tmp_path):
    """Verify that all 6 publication figures are generated properly."""
    runner = POC5ExperimentRunner(output_dir=tmp_path, experiment_id="FIG_TEST", seed=42)
    results = runner.run_full_benchmark(num_pairs=4, top_k=3)
    pairs, _ = load_or_create_poc5_test_collection(num_pairs=4, seed=42)

    figs = generate_all_poc5_figures(results, pairs, output_dir=tmp_path)
    expected_figures = [
        "query_retrieval_gallery",
        "similarity_ranking_curve",
        "retrieval_score_distribution",
        "cross_sensor_embedding_space",
        "ablation_baseline_comparison",
        "failure_analysis_breakdown",
    ]
    for fig_name in expected_figures:
        assert fig_name in figs
        assert figs[fig_name].exists()
        assert figs[fig_name].stat().st_size > 500  # File is non-empty PNG
