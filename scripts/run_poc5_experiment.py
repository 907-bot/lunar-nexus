#!/usr/bin/env python3
"""NEXUS-LUNAR: CLI Experiment Runner for POC-5 Multimodal AI Correspondence.

Usage:
    python scripts/run_poc5_experiment.py [--num-pairs 12] [--top-k 5] [--output-dir outputs/poc5]
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline import (
    POC5ExperimentRunner,
    generate_all_poc5_figures,
    load_or_create_poc5_test_collection,
)


def main():
    parser = argparse.ArgumentParser(description="NEXUS-LUNAR POC-5 Experiment Runner")
    parser.add_argument("--num-pairs", type=int, default=12, help="Number of cross-modal patch pairs (default: 12)")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K candidates to retrieve (default: 5)")
    parser.add_argument("--output-dir", type=str, default="outputs/poc5", help="Output directory path")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--no-figures", action="store_true", help="Skip figure generation")
    args = parser.parse_args()

    out_dir = PROJECT_ROOT / args.output_dir
    runner = POC5ExperimentRunner(output_dir=out_dir, seed=args.seed)

    print(f"Running POC-5 benchmark with {args.num_pairs} pairs, Top-{args.top_k} retrieval...")
    results = runner.run_full_benchmark(
        num_pairs=args.num_pairs,
        top_k=args.top_k,
        data_dir=PROJECT_ROOT / "data"
    )

    if not args.no_figures:
        pairs, _ = load_or_create_poc5_test_collection(
            data_dir=PROJECT_ROOT / "data",
            num_pairs=args.num_pairs,
            seed=args.seed
        )
        figures = generate_all_poc5_figures(results, pairs, output_dir=out_dir)
        print(f"Generated {len(figures)} figures in {out_dir}.")

    sm = results["summary_metrics"]
    print("\n--- POC-5 Benchmark Results ---")
    print(f"Recall@1:  {sm['recall_at_1']}")
    print(f"Recall@3:  {sm['recall_at_3']}")
    print(f"Recall@5:  {sm['recall_at_5']}")
    print(f"Recall@10: {sm['recall_at_10']}")
    print(f"MRR:       {sm['mean_reciprocal_rank']}")
    print(f"Mean Sim:  {sm['mean_similarity_score']}")
    print(f"Candidates exported for POC-6: {out_dir / 'poc5_candidates_for_poc6.json'}")


if __name__ == "__main__":
    main()
