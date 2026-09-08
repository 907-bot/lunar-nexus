#!/usr/bin/env python3
"""NEXUS-LUNAR: Run POC-7 Spatial Intelligence Pipeline.

Executes end-to-end spatial knowledge graph creation, terrain intelligence,
illumination analysis, mineralogical indicators, hazard constraints, and
candidate site ranking.

Usage:
  python scripts/run_poc7_experiment.py [--output outputs/poc7]
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from packages.data_pipeline.poc7_experiment import POC7ExperimentRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexus.poc7.cli")


def main():
    parser = argparse.ArgumentParser(description="Run NEXUS POC-7 Spatial Intelligence Pipeline")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "outputs" / "poc7"),
                        help="Directory to save generated JSON artifacts and diagnostic plots")
    parser.add_argument("--poc6-verified", type=str,
                        default=str(PROJECT_ROOT / "outputs" / "poc6" / "poc6_verified_for_poc7.json"),
                        help="Path to verified correspondence JSON from POC-6")
    args = parser.parse_args()

    out_dir = Path(args.output)
    poc6_path = Path(args.poc6_verified)

    runner = POC7ExperimentRunner(
        poc6_verified_path=poc6_path,
        output_dir=out_dir,
    )
    result = runner.run()

    print("\n=======================================================")
    print("   NEXUS POC-7: SPATIAL INTELLIGENCE PIPELINE COMPLETE")
    print("=======================================================")
    print(f"Experiment ID   : {result['experiment_id']}")
    print(f"Execution Time  : {result['elapsed_seconds']}s")
    print(f"Graph Entities  : {result['total_nodes']} Nodes, {result['total_edges']} Edges")
    print(f"Candidate Sites : {len(result['candidate_sites'])} Evaluated")
    if result["candidate_sites"]:
        top = result["candidate_sites"][0]
        print(f"Top Candidate   : {top.site_id} (Patch {top.patch_id}) - Suitability: {top.overall_suitability_score:.3f}")
    print(f"Outputs Saved To: {out_dir}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
