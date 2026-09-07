#!/usr/bin/env python3
"""NEXUS-LUNAR: Run POC-6 Geometric Verification Experiment CLI."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline import (
    VerificationConfig,
    POC6ExperimentRunner,
    generate_all_poc6_visualizations,
)


def main():
    parser = argparse.ArgumentParser(description="NEXUS-LUNAR POC-6 Geometric Verification Runner")
    parser.add_argument(
        "--candidates",
        type=str,
        default="outputs/poc5/poc5_candidates_for_poc6.json",
        help="Path to POC-5 candidates JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/poc6",
        help="Output directory for results, metrics, and figures",
    )
    parser.add_argument(
        "--min-inliers",
        type=int,
        default=6,
        help="Minimum RANSAC inlier count for acceptance",
    )
    parser.add_argument(
        "--min-inlier-ratio",
        type=float,
        default=0.35,
        help="Minimum inlier ratio for acceptance",
    )
    parser.add_argument(
        "--max-rmse",
        type=float,
        default=3.5,
        help="Maximum allowable reprojection RMSE (px)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.50,
        help="Minimum composite verification confidence for acceptance",
    )
    parser.add_argument(
        "--allow-disjoint",
        action="store_true",
        help="Allow geographically disjoint candidates to be accepted",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic reproducibility",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Maximum candidate pairs to evaluate (default: all)",
    )

    args = parser.parse_args()

    config = VerificationConfig(
        min_inliers=args.min_inliers,
        min_inlier_ratio=args.min_inlier_ratio,
        max_rmse=args.max_rmse,
        min_confidence=args.min_confidence,
        allow_disjoint=args.allow_disjoint,
    )

    runner = POC6ExperimentRunner(
        output_dir=args.output_dir,
        config=config,
        seed=args.seed,
    )

    print(f"Executing POC-6 verification on '{args.candidates}'...")
    results = runner.run_benchmark(args.candidates, max_candidates=args.max_candidates)
    artifacts = runner.export_all_artifacts(results)
    
    # Visualizations
    candidates, _ = runner.load_candidates(args.candidates)
    registry = runner.build_patch_image_registry(candidates)
    figs = generate_all_poc6_visualizations(results, registry, output_dir=args.output_dir)

    accepted = sum(1 for r in results if r.accepted)
    print(f"Done! Verified {len(results)} pairs ({accepted} ACCEPTED, {len(results)-accepted} REJECTED).")
    print(f"Artifacts exported to: {args.output_dir}")


if __name__ == "__main__":
    main()
