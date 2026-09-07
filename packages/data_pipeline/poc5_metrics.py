"""NEXUS-LUNAR POC-5: Retrieval Evaluation Metrics & Failure Case Diagnostics.

Calculates Recall@1, Recall@3, Recall@5, Recall@10, Mean Reciprocal Rank (MRR),
similarity distributions, and tracks structured failure cases with explicit ground
truth provenance.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from .poc5_retrieval import MultimodalCandidateMatch


@dataclass
class RetrievalMetricsReport:
    """Scientific evaluation report for cross-modal retrieval benchmarks."""
    recall_at_1: float  # Top-1 accuracy (0.0 to 1.0 or NaN if unavailable)
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    mean_reciprocal_rank: float  # MRR: 1/rank of true match
    mean_similarity_score: float
    median_similarity_score: float
    ground_truth_status: str  # "AVAILABLE", "GROUND TRUTH UNAVAILABLE"
    ground_truth_definition: str
    total_queries: int
    evaluated_queries: int
    provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT"
    disclaimer: str = "Candidate cross-modal retrieval stage; requires downstream POC-6 geometric verification."

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        def clean_float(val: float) -> Union[float, str]:
            if math.isnan(val):
                return "GROUND TRUTH UNAVAILABLE"
            return round(float(val), 4)

        return {
            "recall_at_1": clean_float(self.recall_at_1),
            "recall_at_3": clean_float(self.recall_at_3),
            "recall_at_5": clean_float(self.recall_at_5),
            "recall_at_10": clean_float(self.recall_at_10),
            "mean_reciprocal_rank": clean_float(self.mean_reciprocal_rank),
            "mean_similarity_score": round(float(self.mean_similarity_score), 4),
            "median_similarity_score": round(float(self.median_similarity_score), 4),
            "ground_truth_status": self.ground_truth_status,
            "ground_truth_definition": self.ground_truth_definition,
            "total_queries": self.total_queries,
            "evaluated_queries": self.evaluated_queries,
            "provenance": self.provenance,
            "disclaimer": self.disclaimer,
        }


def compute_retrieval_metrics(
    retrieval_results: Dict[str, List[MultimodalCandidateMatch]],
    ground_truth_mapping: Optional[Dict[str, str]] = None,
    ground_truth_definition: Optional[str] = None,
    provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
) -> RetrievalMetricsReport:
    """Compute Recall@K, MRR, and score statistics across retrieval results.

    Mandatory Scientific Rule:
    If ground_truth_mapping is None or empty, strictly returns NaN with status
    'GROUND TRUTH UNAVAILABLE' instead of fabricating performance metrics.
    """
    all_scores: List[float] = []
    for matches in retrieval_results.values():
        for m in matches:
            all_scores.append(m.similarity_score)

    mean_score = float(np.mean(all_scores)) if all_scores else 0.0
    median_score = float(np.median(all_scores)) if all_scores else 0.0
    total_queries = len(retrieval_results)

    if not ground_truth_mapping:
        return RetrievalMetricsReport(
            recall_at_1=float("nan"),
            recall_at_3=float("nan"),
            recall_at_5=float("nan"),
            recall_at_10=float("nan"),
            mean_reciprocal_rank=float("nan"),
            mean_similarity_score=mean_score,
            median_similarity_score=median_score,
            ground_truth_status="GROUND TRUTH UNAVAILABLE",
            ground_truth_definition="Ground truth unavailable — cross-modal retrieval metrics not computed.",
            total_queries=total_queries,
            evaluated_queries=0,
            provenance=provenance,
        )

    r1_hits = 0
    r3_hits = 0
    r5_hits = 0
    r10_hits = 0
    reciprocal_ranks: List[float] = []
    evaluated = 0

    for q_id, matches in retrieval_results.items():
        if q_id not in ground_truth_mapping:
            continue
        expected_cand_id = ground_truth_mapping[q_id]
        evaluated += 1

        found_rank = None
        for m in matches:
            if m.candidate_patch_id == expected_cand_id or m.is_ground_truth:
                found_rank = m.rank
                break

        if found_rank is not None:
            reciprocal_ranks.append(1.0 / found_rank)
            if found_rank <= 1:
                r1_hits += 1
            if found_rank <= 3:
                r3_hits += 1
            if found_rank <= 5:
                r5_hits += 1
            if found_rank <= 10:
                r10_hits += 1
        else:
            reciprocal_ranks.append(0.0)

    num_eval = max(1, evaluated)
    gt_def = ground_truth_definition or "Verified geographic co-registration patch pair generated via POC-2 footprint engine."

    return RetrievalMetricsReport(
        recall_at_1=r1_hits / num_eval,
        recall_at_3=r3_hits / num_eval,
        recall_at_5=r5_hits / num_eval,
        recall_at_10=r10_hits / num_eval,
        mean_reciprocal_rank=float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0,
        mean_similarity_score=mean_score,
        median_similarity_score=median_score,
        ground_truth_status="AVAILABLE",
        ground_truth_definition=gt_def,
        total_queries=total_queries,
        evaluated_queries=evaluated,
        provenance=provenance,
    )


@dataclass
class FailureCaseRecord:
    """Diagnostic record for a failed or sub-optimal cross-modal retrieval query."""
    query_patch_id: str
    query_sensor: str
    candidate_sensor: str
    predicted_top1_id: Optional[str]
    expected_ground_truth_id: Optional[str]
    top1_similarity_score: float
    expected_candidate_rank: Optional[int]
    expected_candidate_score: Optional[float]
    failure_category: str
    explanation: str
    provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class POC5FailureCaseTracker:
    """Tracks and taxonomizes cross-modal correspondence retrieval failures."""

    CATEGORIES = {
        "LOW_TEXTURE": "Patch has minimal topographic relief, crater rims, or structural gradient energy.",
        "ILLUMINATION_DISPARITY": "Severe solar elevation angle discrepancy causing inverted shadows.",
        "SHADOW_OCCLUSION": "Deep polar micro-cold trap or crater floor shadow obscuring structural terrain.",
        "EXTREME_GSD_DISPARITY": "Cross-sensor spatial resolution ratio exceeds 4.0x (e.g. 0.25m OHRC vs 5.0m TMC-2).",
        "CROSS_MODAL_SPECTRUM_SHIFT": "Spectral band reflectance shift between narrow optical and broadband context.",
        "REPETITIVE_TERRAIN": "Homogeneous regolith field with multiple ambiguous candidates.",
        "WEAK_EMBEDDING_DISCRIMINATION": "Low cosine separation between positive and negative candidates in embedding space.",
    }

    def __init__(self):
        self.failures: List[FailureCaseRecord] = []

    def record_failure(
        self,
        query_patch_id: str,
        query_sensor: str,
        candidate_sensor: str,
        predicted_top1_id: Optional[str],
        expected_ground_truth_id: Optional[str],
        top1_similarity_score: float,
        expected_candidate_rank: Optional[int],
        expected_candidate_score: Optional[float],
        failure_category: str,
        explanation: str,
        provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
    ) -> FailureCaseRecord:
        """Register a retrieval failure case."""
        record = FailureCaseRecord(
            query_patch_id=query_patch_id,
            query_sensor=query_sensor,
            candidate_sensor=candidate_sensor,
            predicted_top1_id=predicted_top1_id,
            expected_ground_truth_id=expected_ground_truth_id,
            top1_similarity_score=round(top1_similarity_score, 4),
            expected_candidate_rank=expected_candidate_rank,
            expected_candidate_score=round(expected_candidate_score, 4) if expected_candidate_score is not None else None,
            failure_category=failure_category,
            explanation=explanation,
            provenance=provenance,
        )
        self.failures.append(record)
        return record

    def analyze_results(
        self,
        retrieval_results: Dict[str, List[MultimodalCandidateMatch]],
        ground_truth_mapping: Dict[str, str],
        provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT",
    ) -> List[FailureCaseRecord]:
        """Automatically identify and categorize failures where Rank 1 != Expected Ground Truth."""
        for q_id, matches in retrieval_results.items():
            if q_id not in ground_truth_mapping:
                continue
            expected_id = ground_truth_mapping[q_id]

            top1 = matches[0] if matches else None
            top1_id = top1.candidate_patch_id if top1 else None
            top1_score = top1.similarity_score if top1 else 0.0

            # Find expected match rank
            exp_rank = None
            exp_score = None
            for m in matches:
                if m.candidate_patch_id == expected_id or m.is_ground_truth:
                    exp_rank = m.rank
                    exp_score = m.similarity_score
                    break

            if top1_id != expected_id:
                # Classify root cause
                category = "WEAK_EMBEDDING_DISCRIMINATION"
                reason = f"Top-1 predicted candidate '{top1_id}' (score {top1_score:.3f}) ranked higher than expected geographic patch '{expected_id}'."
                
                if top1 and top1.query_gsd and top1.candidate_gsd:
                    gsd_ratio = max(top1.query_gsd, top1.candidate_gsd) / max(0.01, min(top1.query_gsd, top1.candidate_gsd))
                    if gsd_ratio >= 4.0:
                        category = "EXTREME_GSD_DISPARITY"
                        reason = f"High resolution disparity ({gsd_ratio:.1f}x GSD) attenuated fine structural correlation."
                
                if exp_score is not None and (top1_score - exp_score) < 0.05:
                    category = "REPETITIVE_TERRAIN"
                    reason = f"Ambiguous regolith score margin between Top-1 ({top1_score:.3f}) and Expected ({exp_score:.3f}) was < 0.05."

                self.record_failure(
                    query_patch_id=q_id,
                    query_sensor=top1.query_sensor if top1 else "OHRC",
                    candidate_sensor=top1.candidate_sensor if top1 else "LRO_NAC",
                    predicted_top1_id=top1_id,
                    expected_ground_truth_id=expected_id,
                    top1_similarity_score=top1_score,
                    expected_candidate_rank=exp_rank,
                    expected_candidate_score=exp_score,
                    failure_category=category,
                    explanation=reason,
                    provenance=provenance,
                )

        return self.failures

    def get_category_counts(self) -> Dict[str, int]:
        """Aggregate total failures by category."""
        counts = {cat: 0 for cat in self.CATEGORIES}
        for f in self.failures:
            counts[f.failure_category] = counts.get(f.failure_category, 0) + 1
        return counts

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.failures]
