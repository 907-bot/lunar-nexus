"""Unit and integration tests for NEXUS-LUNAR POC-6: Geometric Verification + Explainable AI (XAI)."""

import json
import pytest
import numpy as np
from pathlib import Path

from packages.data_pipeline import (
    VerificationConfig,
    SpatialDistributionResult,
    TransformationStabilityResult,
    ConfidenceBreakdown,
    VerifiedCandidateMatch,
    evaluate_spatial_distribution,
    evaluate_transformation_stability,
    evaluate_sensor_compatibility,
    compute_geographic_overlap_score,
    calculate_verification_confidence,
    generate_xai_explanations,
    GeometricVerifier,
    POC6ExperimentRunner,
    generate_all_poc6_visualizations,
    KeypointMatch,
)


@pytest.fixture
def sample_patches():
    """Generates synthetic pair of overlapping lunar patches with known features."""
    rng = np.random.RandomState(42)
    y, x = np.mgrid[-1:1:128j, -1:1:128j]
    r = np.sqrt(x**2 + y**2)
    crater = np.exp(-4.0 * (r - 0.4)**2) * 0.6
    micro = np.sin(6 * x) * np.cos(6 * y) * 0.15
    base = np.clip(0.45 + crater + micro + rng.normal(0, 0.02, (128, 128)), 0.0, 1.0).astype(np.float32)
    
    q_img = base.copy()
    c_img = np.clip(base * 0.95 + 0.05, 0.0, 1.0).astype(np.float32)
    return q_img, c_img


def test_poc5_input_schema_validation(tmp_path):
    """Validates that POC-6 correctly parses candidate schema from POC-5."""
    dummy_file = tmp_path / "candidates.json"
    dummy_data = {
        "schema_version": "1.0.0",
        "provenance": "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
        "candidates": [
            {
                "query_patch_id": "Q_01",
                "candidate_patch_id": "C_01",
                "query_sensor": "OHRC",
                "candidate_sensor": "LRO_NAC",
                "query_coordinates": {"lat": -73.0, "lon": 25.0},
                "candidate_coordinates": {"lat": -73.0, "lon": 25.0},
                "query_bbox": {"min_lat": -73.1, "max_lat": -72.9, "min_lon": 24.9, "max_lon": 25.1},
                "candidate_bbox": {"min_lat": -73.1, "max_lat": -72.9, "min_lon": 24.9, "max_lon": 25.1},
                "query_gsd": 0.25,
                "candidate_gsd": 1.0,
                "similarity_score": 0.89,
                "rank": 1,
                "geographic_relation": "OVERLAPPING",
            }
        ],
    }
    with open(dummy_file, "w", encoding="utf-8") as f:
        json.dump(dummy_data, f)

    runner = POC6ExperimentRunner(output_dir=tmp_path)
    candidates, meta = runner.load_candidates(dummy_file)
    assert len(candidates) == 1
    assert candidates[0]["query_patch_id"] == "Q_01"
    assert meta["schema_version"] == "1.0.0"


def test_missing_poc5_file_handling(tmp_path):
    """Ensures clear FileNotFoundError when candidates file is missing."""
    runner = POC6ExperimentRunner(output_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        runner.load_candidates(tmp_path / "non_existent_file.json")


def test_malformed_candidate_handling(tmp_path):
    """Verifies ValueError on malformed candidate JSON schema."""
    bad_file = tmp_path / "bad.json"
    with open(bad_file, "w", encoding="utf-8") as f:
        json.dump({"no_candidates_key": []}, f)

    runner = POC6ExperimentRunner(output_dir=tmp_path)
    with pytest.raises(ValueError):
        runner.load_candidates(bad_file)


def test_spatial_distribution_good_vs_poor():
    """Tests grid occupancy and spatial distribution evaluation on spread vs clustered points."""
    # Well spread inliers
    spread_matches = [
        KeypointMatch(0, 0, 0.1, (10.0, 10.0), (10.0, 10.0)),
        KeypointMatch(1, 1, 0.1, (100.0, 15.0), (100.0, 15.0)),
        KeypointMatch(2, 2, 0.1, (20.0, 110.0), (20.0, 110.0)),
        KeypointMatch(3, 3, 0.1, (110.0, 110.0), (110.0, 110.0)),
        KeypointMatch(4, 4, 0.1, (60.0, 60.0), (60.0, 60.0)),
    ]
    good_res = evaluate_spatial_distribution(spread_matches, patch_shape=(128, 128))
    assert good_res.spatial_distribution_status == "GOOD"
    assert good_res.occupied_cells >= 4
    assert good_res.spatial_distribution_score >= 0.5

    # Clustered inliers in top-left corner
    clustered_matches = [
        KeypointMatch(0, 0, 0.1, (10.0, 10.0), (10.0, 10.0)),
        KeypointMatch(1, 1, 0.1, (12.0, 11.0), (12.0, 11.0)),
        KeypointMatch(2, 2, 0.1, (14.0, 13.0), (14.0, 13.0)),
        KeypointMatch(3, 3, 0.1, (15.0, 15.0), (15.0, 15.0)),
    ]
    poor_res = evaluate_spatial_distribution(clustered_matches, patch_shape=(128, 128))
    assert poor_res.spatial_distribution_status == "POOR"
    assert poor_res.occupied_cells == 1
    assert poor_res.spatial_distribution_score < 0.4


def test_transformation_stability_evaluation():
    """Verifies classification of STABLE vs UNSTABLE transformations."""
    # Stable identity transformation
    affine_stable = np.array([[1.0, 0.0, 5.0], [0.0, 1.0, -3.0]])
    stab = evaluate_transformation_stability(affine_stable, inlier_count=10, rmse=1.2)
    assert stab.status == "STABLE"
    assert stab.stability_score == 1.0
    assert abs(stab.determinant - 1.0) < 1e-4

    # Degenerate transformation (collapsed to line, det = 0)
    affine_degenerate = np.array([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
    unstab = evaluate_transformation_stability(affine_degenerate, inlier_count=10, rmse=1.2)
    assert unstab.status == "UNSTABLE"

    # Mirrored transformation (reflection, det < 0)
    affine_mirrored = np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    unstab_mirror = evaluate_transformation_stability(affine_mirrored, inlier_count=10, rmse=1.2)
    assert unstab_mirror.status == "UNSTABLE"


def test_geographic_overlap_scoring_and_disjoint_penalty():
    """Verifies geographic overlap scoring and severe confidence suppression on DISJOINT pairs."""
    assert compute_geographic_overlap_score("OVERLAPPING") == 1.0
    assert compute_geographic_overlap_score("NEARBY") == 0.5
    assert compute_geographic_overlap_score("UNKNOWN") == 0.3
    assert compute_geographic_overlap_score("DISJOINT") == 0.0

    cfg = VerificationConfig()
    conf_over = calculate_verification_confidence(
        ai_similarity=0.85, inlier_count=12, inlier_ratio=0.8, rmse=1.5,
        geographic_relation="OVERLAPPING", spatial_dist_score=0.8,
        transform_stability_score=1.0, sensor_compat_score=1.0, config=cfg
    )
    assert conf_over.final_verification_confidence > 0.70
    assert not conf_over.disjoint_penalty_applied

    conf_disjoint = calculate_verification_confidence(
        ai_similarity=0.85, inlier_count=12, inlier_ratio=0.8, rmse=1.5,
        geographic_relation="DISJOINT", spatial_dist_score=0.8,
        transform_stability_score=1.0, sensor_compat_score=1.0, config=cfg
    )
    assert conf_disjoint.disjoint_penalty_applied
    assert conf_disjoint.final_verification_confidence <= conf_over.final_verification_confidence * 0.30


def test_sensor_compatibility_evaluation():
    """Verifies sensor GSD ratio compatibility scoring."""
    status, score = evaluate_sensor_compatibility("OHRC", "LRO_NAC", 0.25, 1.0)
    assert status == "GOOD"
    assert score == 1.0

    status_mod, score_mod = evaluate_sensor_compatibility("OHRC", "TMC2", 0.25, 1.5)  # ratio 6.0
    assert status_mod == "MODERATE"
    assert score_mod == 0.7

    status_low, score_low = evaluate_sensor_compatibility("OHRC", "WAC", 0.25, 10.0)  # ratio 40.0
    assert status_low == "LOW"
    assert score_low == 0.3


def test_multi_signal_confidence_formula():
    """Verifies that confidence calculation correctly weights all 8 components."""
    cfg = VerificationConfig(
        ai_match_weight=0.10,
        inlier_weight=0.20,
        inlier_ratio_weight=0.20,
        rmse_weight=0.15,
        overlap_weight=0.15,
        spatial_distribution_weight=0.10,
        transformation_stability_weight=0.05,
        sensor_compatibility_weight=0.05,
    )
    conf = calculate_verification_confidence(
        ai_similarity=1.0,
        inlier_count=15,
        inlier_ratio=1.0,
        rmse=0.0,
        geographic_relation="OVERLAPPING",
        spatial_dist_score=1.0,
        transform_stability_score=1.0,
        sensor_compat_score=1.0,
        config=cfg,
    )
    # With perfect scores on all signals, confidence must equal 1.0
    assert abs(conf.final_verification_confidence - 1.0) < 1e-4


def test_high_ai_similarity_false_positive_rejection(sample_patches):
    """CRITICAL TEST: Verifies that high AI similarity with disjoint geometry is REJECTED."""
    q_img, _ = sample_patches
    # Completely black or inverted candidate with no features
    unrelated_img = np.zeros_like(q_img)

    cand_dict = {
        "query_patch_id": "OHRC_001",
        "candidate_patch_id": "LROC_UNRELATED",
        "query_sensor": "OHRC",
        "candidate_sensor": "LRO_NAC",
        "query_gsd": 0.25,
        "candidate_gsd": 1.0,
        "similarity_score": 0.95,  # Very high AI score!
        "rank": 1,
        "geographic_relation": "DISJOINT",
        "provenance": "SYNTHETIC OFFLINE DEMO",
    }

    verifier = GeometricVerifier(config=VerificationConfig())
    res = verifier.verify_candidate_pair(cand_dict, q_img, unrelated_img)

    assert not res.accepted
    assert res.decision == "REJECTED"
    # Ensure failure reasons capture the discrepancy
    codes = [rej["code"] for rej in res.rejection_reasons]
    assert "GEOGRAPHIC_DISJOINT" in codes
    assert "AI_SIMILARITY_FALSE_POSITIVE" in codes


def test_verified_true_match_acceptance(sample_patches):
    """Verifies that an identical/well-aligned pair with good geometry is ACCEPTED."""
    q_img, c_img = sample_patches

    cand_dict = {
        "query_patch_id": "OHRC_001",
        "candidate_patch_id": "LROC_001",
        "query_sensor": "OHRC",
        "candidate_sensor": "LRO_NAC",
        "query_gsd": 0.5,
        "candidate_gsd": 1.0,
        "similarity_score": 0.88,
        "rank": 1,
        "geographic_relation": "OVERLAPPING",
        "provenance": "SYNTHETIC OFFLINE DEMO",
    }

    verifier = GeometricVerifier(config=VerificationConfig(min_inliers=6, max_rmse=3.5))
    res = verifier.verify_candidate_pair(cand_dict, q_img, c_img)

    assert res.accepted
    assert res.decision == "ACCEPTED"
    assert res.inlier_count >= 6
    assert res.inlier_ratio >= 0.35
    assert res.rmse <= 3.5
    assert len(res.acceptance_reasons) >= 4


def test_poc6_results_and_csv_generation(tmp_path, sample_patches):
    """Tests end-to-end benchmark execution and JSON/CSV artifact exporting."""
    q_img, c_img = sample_patches
    runner = POC6ExperimentRunner(output_dir=tmp_path)

    # Synthetic candidate file
    cand_file = tmp_path / "candidates.json"
    with open(cand_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": "1.0.0",
                "provenance": "SYNTHETIC OFFLINE DEMO",
                "candidates": [
                    {
                        "query_patch_id": "Q1",
                        "candidate_patch_id": "C1",
                        "query_sensor": "OHRC",
                        "candidate_sensor": "LRO_NAC",
                        "query_gsd": 0.5,
                        "candidate_gsd": 1.0,
                        "similarity_score": 0.85,
                        "rank": 1,
                        "geographic_relation": "OVERLAPPING",
                    }
                ],
            },
            f,
        )

    results = runner.run_benchmark(cand_file)
    assert len(results) == 1
    artifacts = runner.export_all_artifacts(results)

    for key in ["results_json", "results_csv", "failure_cases", "metadata", "poc7_handover"]:
        assert artifacts[key].exists()
        assert artifacts[key].stat().st_size > 0


def test_poc6_verified_for_poc7_handover_schema(tmp_path, sample_patches):
    """Validates that POC-7 handoff file contains verified transformation matrix and inliers."""
    q_img, c_img = sample_patches
    cand_dict = {
        "query_patch_id": "Q1",
        "candidate_patch_id": "C1",
        "query_sensor": "OHRC",
        "candidate_sensor": "LRO_NAC",
        "query_gsd": 0.5,
        "candidate_gsd": 1.0,
        "similarity_score": 0.90,
        "rank": 1,
        "geographic_relation": "OVERLAPPING",
        "provenance": "SYNTHETIC OFFLINE DEMO",
    }
    verifier = GeometricVerifier()
    res = verifier.verify_candidate_pair(cand_dict, q_img, c_img)
    handover = res.to_poc7_handover_dict()

    assert "query_patch_id" in handover
    assert "candidate_patch_id" in handover
    assert "transformation_model" in handover
    assert "transformation_matrix" in handover
    assert "inliers" in handover
    assert "rmse" in handover


def test_all_six_poc6_visualizations_generation(tmp_path, sample_patches):
    """Validates generation of all 6 publication diagnostic PNG figures."""
    q_img, c_img = sample_patches
    cand_dict = {
        "query_patch_id": "Q1",
        "candidate_patch_id": "C1",
        "query_sensor": "OHRC",
        "candidate_sensor": "LRO_NAC",
        "query_gsd": 0.5,
        "candidate_gsd": 1.0,
        "similarity_score": 0.85,
        "rank": 1,
        "geographic_relation": "OVERLAPPING",
        "provenance": "SYNTHETIC OFFLINE DEMO",
    }
    verifier = GeometricVerifier()
    res = verifier.verify_candidate_pair(cand_dict, q_img, c_img)
    
    registry = {"Q1": q_img, "C1": c_img}
    figs = generate_all_poc6_visualizations([res], registry, output_dir=tmp_path)

    assert len(figs) == 6
    for name, p in figs.items():
        assert p.exists()
        assert p.stat().st_size > 1000
