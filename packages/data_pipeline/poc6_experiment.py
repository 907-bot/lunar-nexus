"""NEXUS-LUNAR POC-6: Experiment Benchmark Runner & Artifact Exporter.

Loads candidates from outputs/poc5/poc5_candidates_for_poc6.json, executes
RANSAC geometric verification and Explainable AI diagnostics on every candidate,
and serializes standardized JSON, CSV, failure case, and POC-7 handoff artifacts.
"""

from __future__ import annotations
import os
import sys
import csv
import json
import time
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from .poc6_verification import (
    VerificationConfig,
    VerifiedCandidateMatch,
    GeometricVerifier,
)
from .poc5_experiment import load_or_create_poc5_test_collection


class POC6ExperimentRunner:
    """Executes geometric verification benchmarks on POC-5 candidate retrievals."""

    def __init__(
        self,
        output_dir: Union[str, Path] = "outputs/poc6",
        config: Optional[VerificationConfig] = None,
        experiment_id: Optional[str] = None,
        seed: int = 42,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or VerificationConfig()
        self.experiment_id = experiment_id or f"EXP_POC6_{int(time.time())}"
        self.seed = seed
        self.verifier = GeometricVerifier(config=self.config, seed=self.seed)

    def load_candidates(
        self, candidate_file_path: Union[str, Path] = "outputs/poc5/poc5_candidates_for_poc6.json"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Validates and loads POC-5 candidate retrieval handover file.

        Raises:
            FileNotFoundError: If the specified POC-5 candidate file is missing.
            ValueError: If schema or essential keys are invalid.
        """
        path = Path(candidate_file_path)
        if not path.exists():
            raise FileNotFoundError(
                f"POC-5 candidate file not found at '{path}'. "
                f"Ensure POC-5 experiment has executed and produced 'poc5_candidates_for_poc6.json'."
            )

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "candidates" not in data or not isinstance(data["candidates"], list):
            raise ValueError(f"Invalid POC-5 candidate schema in '{path}': missing 'candidates' array.")

        candidates = data["candidates"]
        return candidates, data

    def build_patch_image_registry(
        self, candidates: List[Dict[str, Any]]
    ) -> Dict[str, np.ndarray]:
        """Loads or deterministically constructs image rasters for all candidate patches."""
        registry: Dict[str, np.ndarray] = {}

        # 1. First populate from standard POC-5 collection loader
        pairs, _ = load_or_create_poc5_test_collection(seed=self.seed)
        for p in pairs:
            registry[p["source_id"]] = p["source_image"]
            registry[p["reference_id"]] = p["reference_image"]

        # 2. For any candidate patch ID not in pairs, construct deterministic synthetic lunar raster
        rng = np.random.RandomState(self.seed)
        for c in candidates:
            for patch_key in ["query_patch_id", "candidate_patch_id"]:
                pid = c.get(patch_key)
                if pid and pid not in registry:
                    # Deterministic terrain based on hash of patch_id
                    hash_val = sum(ord(ch) for ch in pid)
                    y, x = np.mgrid[-1:1:128j, -1:1:128j]
                    r = np.sqrt(x**2 + y**2)
                    crater = np.exp(-4.0 * (r - 0.35)**2) * 0.5
                    micro = np.sin(4 * x + hash_val % 7) * np.cos(4 * y) * 0.12
                    noise = rng.normal(0.0, 0.03, (128, 128))
                    img = np.clip(0.45 + crater + micro + noise, 0.0, 1.0).astype(np.float32)
                    registry[pid] = img

        return registry

    def run_benchmark(
        self,
        candidate_file_path: Union[str, Path] = "outputs/poc5/poc5_candidates_for_poc6.json",
        max_candidates: Optional[int] = None,
    ) -> List[VerifiedCandidateMatch]:
        """Runs geometric verification on all or a subset of POC-5 candidates."""
        candidates, parent_meta = self.load_candidates(candidate_file_path)
        if max_candidates is not None:
            candidates = candidates[:max_candidates]

        image_registry = self.build_patch_image_registry(candidates)
        provenance = parent_meta.get("provenance", "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT")

        verified_results: List[VerifiedCandidateMatch] = []
        for cand in candidates:
            # Propagate parent experiment info
            cand_copy = dict(cand)
            cand_copy["experiment_id"] = self.experiment_id
            cand_copy["provenance"] = provenance

            q_id = cand.get("query_patch_id")
            c_id = cand.get("candidate_patch_id")

            q_img = image_registry.get(q_id, np.zeros((128, 128), dtype=np.float32))
            c_img = image_registry.get(c_id, np.zeros((128, 128), dtype=np.float32))

            res = self.verifier.verify_candidate_pair(cand_copy, q_img, c_img)
            verified_results.append(res)

        return verified_results

    def export_all_artifacts(
        self,
        results: List[VerifiedCandidateMatch],
        provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
    ) -> Dict[str, Path]:
        """Serializes all required POC-6 outputs into self.output_dir."""
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in results:
            if not r.timestamp:
                r.timestamp = now_iso

        # 1. outputs/poc6/poc6_results.json
        results_json_path = self.output_dir / "poc6_results.json"
        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": "1.0.0",
                    "experiment_id": self.experiment_id,
                    "provenance": provenance,
                    "timestamp": now_iso,
                    "total_candidates_verified": len(results),
                    "accepted_count": sum(1 for r in results if r.accepted),
                    "rejected_count": sum(1 for r in results if not r.accepted),
                    "results": [r.to_dict() for r in results],
                },
                f,
                indent=2,
            )

        # 2. outputs/poc6/poc6_results.csv
        results_csv_path = self.output_dir / "poc6_results.csv"
        csv_headers = [
            "experiment_id",
            "query_patch_id",
            "candidate_patch_id",
            "query_sensor",
            "candidate_sensor",
            "query_gsd",
            "candidate_gsd",
            "ai_similarity_score",
            "rank",
            "tentative_match_count",
            "inlier_count",
            "inlier_ratio",
            "rmse",
            "transformation_model",
            "transformation_stability",
            "geographic_relation",
            "geographic_overlap_score",
            "spatial_distribution_score",
            "spatial_distribution_status",
            "sensor_compatibility",
            "verification_confidence",
            "accepted",
            "decision",
            "primary_diagnostic_code",
            "provenance",
        ]
        with open(results_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_headers)
            for r in results:
                primary_code = r.rejection_reasons[0]["code"] if r.rejection_reasons else "NONE"
                writer.writerow([
                    r.experiment_id,
                    r.query_patch_id,
                    r.candidate_patch_id,
                    r.query_sensor,
                    r.candidate_sensor,
                    r.query_gsd,
                    r.candidate_gsd,
                    round(float(r.ai_similarity_score), 4),
                    r.rank,
                    r.tentative_match_count,
                    r.inlier_count,
                    round(float(r.inlier_ratio), 4),
                    round(float(r.rmse), 4) if np.isfinite(r.rmse) else 999.0,
                    r.transformation_model,
                    r.transformation_stability,
                    r.geographic_relation,
                    round(float(r.geographic_overlap_score), 4),
                    round(float(r.spatial_distribution_score), 4),
                    r.spatial_distribution_status,
                    r.sensor_compatibility,
                    round(float(r.verification_confidence), 4),
                    r.accepted,
                    r.decision,
                    primary_code,
                    r.provenance,
                ])

        # 3. outputs/poc6/poc6_failure_cases.json
        failure_cases_path = self.output_dir / "poc6_failure_cases.json"
        failure_buckets: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            if not r.accepted:
                for rej in r.rejection_reasons:
                    code = rej["code"]
                    if code not in failure_buckets:
                        failure_buckets[code] = []
                    failure_buckets[code].append({
                        "query_patch_id": r.query_patch_id,
                        "candidate_patch_id": r.candidate_patch_id,
                        "ai_similarity_score": round(float(r.ai_similarity_score), 4),
                        "rank": r.rank,
                        "geographic_relation": r.geographic_relation,
                        "inlier_count": r.inlier_count,
                        "inlier_ratio": round(float(r.inlier_ratio), 4),
                        "rmse": round(float(r.rmse), 4) if np.isfinite(r.rmse) else 999.0,
                        "confidence": round(float(r.verification_confidence), 4),
                        "message": rej["message"],
                    })

        with open(failure_cases_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": "1.0.0",
                    "experiment_id": self.experiment_id,
                    "timestamp": now_iso,
                    "total_rejected_candidates": sum(1 for r in results if not r.accepted),
                    "failure_code_counts": {k: len(v) for k, v in failure_buckets.items()},
                    "failure_cases_by_code": failure_buckets,
                },
                f,
                indent=2,
            )

        # 4. outputs/poc6/poc6_metadata.json
        metadata_path = self.output_dir / "poc6_metadata.json"
        git_commit = "unknown"
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                git_commit = res.stdout.strip()
        except Exception:
            pass

        meta = {
            "experiment_id": self.experiment_id,
            "timestamp": now_iso,
            "git_commit": git_commit,
            "python_version": sys.version,
            "operating_system": f"{platform.system()} {platform.release()}",
            "random_seed": self.seed,
            "provenance": provenance,
            "candidate_source_file": "outputs/poc5/poc5_candidates_for_poc6.json",
            "total_candidates_verified": len(results),
            "accepted_count": sum(1 for r in results if r.accepted),
            "rejected_count": sum(1 for r in results if not r.accepted),
            "acceptance_rate": round(sum(1 for r in results if r.accepted) / max(1, len(results)), 4),
            "algorithm_parameters": {
                "matcher": "Lowe_ratio_test_cross_check",
                "ratio_thresh": self.config.ratio_thresh,
                "descriptor_dim": 128,
                "ransac_model": "affine",
                "max_reproj_error_px": self.config.max_reproj_error,
                "ransac_iterations": self.config.ransac_iterations,
                "ransac_confidence": self.config.ransac_confidence,
                "min_inliers": self.config.min_inliers,
                "min_inlier_ratio": self.config.min_inlier_ratio,
                "max_rmse": self.config.max_rmse,
                "min_confidence": self.config.min_confidence,
            },
            "confidence_weights": {
                "ai_match_weight": self.config.ai_match_weight,
                "inlier_weight": self.config.inlier_weight,
                "inlier_ratio_weight": self.config.inlier_ratio_weight,
                "rmse_weight": self.config.rmse_weight,
                "overlap_weight": self.config.overlap_weight,
                "spatial_distribution_weight": self.config.spatial_distribution_weight,
                "transformation_stability_weight": self.config.transformation_stability_weight,
                "sensor_compatibility_weight": self.config.sensor_compatibility_weight,
            },
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # 5. outputs/poc6/poc6_verified_for_poc7.json (POC-7 handover dataset)
        poc7_path = self.output_dir / "poc6_verified_for_poc7.json"
        accepted_handover = [r.to_poc7_handover_dict() for r in results if r.accepted]
        with open(poc7_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "schema_version": "1.0.0",
                    "handover_target": "POC-7 Relative Pose & Surface Reconstruction",
                    "experiment_id": self.experiment_id,
                    "provenance": provenance,
                    "timestamp": now_iso,
                    "total_accepted_pairs": len(accepted_handover),
                    "accepted_pairs": accepted_handover,
                },
                f,
                indent=2,
            )

        return {
            "results_json": results_json_path,
            "results_csv": results_csv_path,
            "failure_cases": failure_cases_path,
            "metadata": metadata_path,
            "poc7_handover": poc7_path,
        }
