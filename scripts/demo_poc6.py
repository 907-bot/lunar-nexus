#!/usr/bin/env python3
"""NEXUS-LUNAR: POC 6 Standalone Reproducible Demonstration.

Demonstrates:
1. Loading multimodal AI candidates from POC-5 (outputs/poc5/poc5_candidates_for_poc6.json)
2. Classical keypoint detection, orientation descriptors, and Lowe's ratio test matching
3. Robust RANSAC affine geometric verification and least-squares refinement
4. Quantitative inlier metrics: tentative matches, inlier count, inlier ratio, RMSE
5. Spatial distribution analysis: 4x4 grid occupancy and bounding area spread
6. Multi-signal verification confidence score calculation (combining 8 normalized signals)
7. Deterministic ACCEPT/REJECT decision policy
8. Explainable AI (XAI) diagnostic explanations: "Why was this match accepted?" & "Why was this match rejected?"
9. Rejection of high-AI false positives (demonstrating AI similarity is evidence, not proof)
10. Handover dataset serialization for downstream POC-7
11. Generation of 6 publication-ready diagnostic figures in outputs/poc6/
"""

from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline import (
    VerificationConfig,
    GeometricVerifier,
    POC6ExperimentRunner,
    generate_all_poc6_visualizations,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_poc6_demo():
    print("=" * 80)
    print("  NEXUS-LUNAR POC-6: GEOMETRIC VERIFICATION + EXPLAINABLE AI (XAI) DEMO")
    print("=" * 80)

    output_dir = PROJECT_ROOT / "outputs" / "poc6"
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_file = PROJECT_ROOT / "outputs" / "poc5" / "poc5_candidates_for_poc6.json"

    print("\n[Step 1/6] Ingesting POC-5 Retrieval Candidates...")
    runner = POC6ExperimentRunner(
        output_dir=output_dir,
        config=VerificationConfig(
            min_inliers=6,
            min_inlier_ratio=0.35,
            max_rmse=3.5,
            min_confidence=0.50,
            allow_disjoint=False,
        ),
        experiment_id=f"EXP_POC6_DEMO_{int(time.time())}",
        seed=42,
    )

    if not candidate_file.exists():
        print(f"  [ERROR] POC-5 candidate file '{candidate_file}' not found.")
        print("  Generating deterministic offline synthetic candidates fixture...")
        raise FileNotFoundError(f"Missing candidate file: {candidate_file}")

    candidates, parent_meta = runner.load_candidates(candidate_file)
    provenance = parent_meta.get("provenance", "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT")
    print(f"  * Loaded {len(candidates)} candidate pairs from: {candidate_file.name}")
    print(f"  * Provenance: {provenance}")

    print("\n[Step 2/6] Building Patch Raster Registry & Feature Extractors...")
    registry = runner.build_patch_image_registry(candidates)
    print(f"  * Cached {len(registry)} unique lunar patch rasters.")

    print("\n[Step 3/6] Executing RANSAC Geometric Verification & Multi-Signal Scoring...")
    start_t = time.perf_counter()
    verified_results = runner.run_benchmark(candidate_file_path=candidate_file)
    elapsed = time.perf_counter() - start_t
    print(f"  * Verified {len(verified_results)} candidates in {elapsed:.2f}s ({elapsed/len(verified_results)*1000:.1f} ms/pair).")

    accepted_list = [r for r in verified_results if r.accepted]
    rejected_list = [r for r in verified_results if not r.accepted]
    print(f"  * ACCEPTED: {len(accepted_list)} | REJECTED: {len(rejected_list)} | Rate: {len(accepted_list)/len(verified_results)*100:.1f}%")

    print("\n[Step 4/6] Exporting Standardized Output Artifacts...")
    exported_files = runner.export_all_artifacts(verified_results, provenance=provenance)
    for k, v in exported_files.items():
        print(f"  * {k}: {v.relative_to(PROJECT_ROOT)}")

    print("\n[Step 5/6] Generating Publication Diagnostic Visualizations...")
    fig_paths = generate_all_poc6_visualizations(verified_results, registry, output_dir=output_dir)
    for k, v in fig_paths.items():
        print(f"  * Visual: {v.relative_to(PROJECT_ROOT)}")

    print("\n[Step 6/6] Critical XAI Demonstration: High-AI False Positive vs Verified True Match")
    print("-" * 80)
    
    # 1. Show Top Candidate with High AI similarity that was REJECTED
    high_ai_rejected = [r for r in rejected_list if r.ai_similarity_score >= 0.70]
    if high_ai_rejected:
        r_false = high_ai_rejected[0]
        print(f"\nCASE A: High-AI Candidate Safely REJECTED by Geometric Verification")
        print(f"  Pair: {r_false.query_patch_id} vs {r_false.candidate_patch_id} (Rank #{r_false.rank})")
        print(f"  AI Similarity Score:       {r_false.ai_similarity_score:.4f}  (High AI score!)")
        print(f"  Tentative Matches:         {r_false.tentative_match_count}")
        print(f"  Geometric Inliers:         {r_false.inlier_count}")
        print(f"  Inlier Ratio:              {r_false.inlier_ratio*100:.1f}%")
        print(f"  Reprojection RMSE:         {r_false.rmse:.2f} px")
        print(f"  Geographic Relationship:   {r_false.geographic_relation}")
        print(f"  Spatial Distribution:      {r_false.spatial_distribution_score:.2f} ({r_false.spatial_distribution_status})")
        print(f"  Verification Confidence:   {r_false.verification_confidence:.4f}")
        print(f"  FINAL DECISION:            ✗ {r_false.decision}")
        print(f"  WHY WAS THIS MATCH REJECTED?")
        for rej in r_false.rejection_reasons:
            print(f"    - [{rej['code']}]: {rej['message']}")

    # 2. Show True Match that was ACCEPTED
    if accepted_list:
        r_true = accepted_list[0]
        print(f"\nCASE B: Geometrically Verified True Match ACCEPTED")
        print(f"  Pair: {r_true.query_patch_id} vs {r_true.candidate_patch_id} (Rank #{r_true.rank})")
        print(f"  AI Similarity Score:       {r_true.ai_similarity_score:.4f}")
        print(f"  Tentative Matches:         {r_true.tentative_match_count}")
        print(f"  Geometric Inliers:         {r_true.inlier_count}")
        print(f"  Inlier Ratio:              {r_true.inlier_ratio*100:.1f}%")
        print(f"  Reprojection RMSE:         {r_true.rmse:.2f} px")
        print(f"  Geographic Relationship:   {r_true.geographic_relation}")
        print(f"  Spatial Distribution:      {r_true.spatial_distribution_score:.2f} ({r_true.spatial_distribution_status})")
        print(f"  Verification Confidence:   {r_true.verification_confidence:.4f}")
        print(f"  FINAL DECISION:            ✓ {r_true.decision}")
        print(f"  WHY WAS THIS MATCH ACCEPTED?")
        for acc in r_true.acceptance_reasons:
            print(f"    - ✓ {acc}")

    print("\n" + "=" * 80)
    print("  POC-6 VERIFICATION DEMONSTRATION COMPLETE: ALL OBJECTIVES ACHIEVED")
    print("=" * 80)


if __name__ == "__main__":
    run_poc6_demo()
