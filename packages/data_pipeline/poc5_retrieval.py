"""NEXUS-LUNAR POC-5: Cross-Modal Retrieval Engine & POC-6 Candidate Schema.

Computes similarity matrices, performs Top-K candidate ranking, evaluates spatial
geographic overlap relationships, and produces standardized candidate objects
consumable by the downstream POC-6 geometric verification engine.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from .poc5_models import MultimodalPatchEmbedding, BaseMultimodalEncoder


@dataclass
class MultimodalCandidateMatch:
    """Standardized cross-modal candidate correspondence for POC-5 output and POC-6 consumption.

    POC-6 Geometric Verification Engine will receive these candidates as input:
    Query Patch -> Top-K Candidate Matches -> Keypoint Detection -> Homography / RANSAC Verification.
    """
    query_patch_id: str
    candidate_patch_id: str
    query_sensor: str
    candidate_sensor: str
    query_coordinates: Dict[str, float]  # {"lat": float, "lon": float}
    candidate_coordinates: Dict[str, float]  # {"lat": float, "lon": float}
    query_bbox: Dict[str, float]  # min_lat, max_lat, min_lon, max_lon
    candidate_bbox: Dict[str, float]
    query_gsd: float
    candidate_gsd: float
    similarity_score: float  # Cosine similarity in [-1.0, 1.0], typically [0.0, 1.0]
    rank: int  # 1-indexed (1 = top match)
    embedding_model: str
    embedding_dim: int
    experiment_id: str
    ground_truth_status: str  # "AVAILABLE", "UNAVAILABLE", "SYNTHETIC_GROUND_TRUTH"
    is_ground_truth: bool  # True if this candidate is the verified true corresponding geographic patch
    geographic_relation: str  # "OVERLAPPING", "NEARBY", "DISJOINT", "UNKNOWN"
    provenance: str = "REAL-GEOGRAPHY / SYNTHETIC-MODALITY EXPERIMENT"
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query_patch_id": self.query_patch_id,
            "candidate_patch_id": self.candidate_patch_id,
            "query_sensor": self.query_sensor,
            "candidate_sensor": self.candidate_sensor,
            "query_coordinates": self.query_coordinates,
            "candidate_coordinates": self.candidate_coordinates,
            "query_bbox": self.query_bbox,
            "candidate_bbox": self.candidate_bbox,
            "query_gsd": self.query_gsd,
            "candidate_gsd": self.candidate_gsd,
            "similarity_score": round(float(self.similarity_score), 4),
            "rank": self.rank,
            "embedding_model": self.embedding_model,
            "embedding_dim": self.embedding_dim,
            "experiment_id": self.experiment_id,
            "ground_truth_status": self.ground_truth_status,
            "is_ground_truth": self.is_ground_truth,
            "geographic_relation": self.geographic_relation,
            "provenance": self.provenance,
            "extra_metadata": self.extra_metadata,
        }


def compute_geographic_relation(
    bbox1: Dict[str, float],
    bbox2: Dict[str, float],
    nearby_deg_threshold: float = 0.15
) -> str:
    """Determine spatial relationship between two patch bounding boxes."""
    if not bbox1 or not bbox2:
        return "UNKNOWN"

    min_lat1, max_lat1 = bbox1.get("min_lat", 0), bbox1.get("max_lat", 0)
    min_lon1, max_lon1 = bbox1.get("min_lon", 0), bbox1.get("max_lon", 0)
    min_lat2, max_lat2 = bbox2.get("min_lat", 0), bbox2.get("max_lat", 0)
    min_lon2, max_lon2 = bbox2.get("min_lon", 0), bbox2.get("max_lon", 0)

    # Check for direct bounding box intersection
    lat_overlap = max(0.0, min(max_lat1, max_lat2) - max(min_lat1, min_lat2))
    lon_overlap = max(0.0, min(max_lon1, max_lon2) - max(min_lon1, min_lon2))

    if lat_overlap > 0 and lon_overlap > 0:
        return "OVERLAPPING"

    # Compute minimal edge distance between bounding boxes
    d_lat = max(0.0, max(min_lat1, min_lat2) - min(max_lat1, max_lat2))
    d_lon = max(0.0, max(min_lon1, min_lon2) - min(max_lon1, max_lon2))
    edge_dist = math.sqrt(d_lat**2 + d_lon**2)

    if edge_dist <= nearby_deg_threshold:
        return "NEARBY"
    return "DISJOINT"


class CrossModalRetrievalEngine:
    """Engine for indexing reference embeddings and executing Top-K nearest neighbor queries."""

    def __init__(self, metric: str = "cosine"):
        self.metric = metric

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute similarity vector between a 1D query and a 2D matrix of candidate embeddings.

        Args:
            query_embedding: Shape (D,)
            candidate_embeddings: Shape (N, D)

        Returns:
            Similarities: Shape (N,)
        """
        if candidate_embeddings.size == 0:
            return np.array([], dtype=np.float32)

        q = query_embedding.astype(np.float32)
        c = candidate_embeddings.astype(np.float32)

        if q.ndim == 1:
            q = q.reshape(1, -1)

        # Ensure unit L2 normalization
        q_norm = np.linalg.norm(q, axis=1, keepdims=True) + 1e-8
        c_norm = np.linalg.norm(c, axis=1, keepdims=True) + 1e-8
        q_unit = q / q_norm
        c_unit = c / c_norm

        if self.metric == "cosine":
            # Dot product of unit vectors
            sims = np.dot(c_unit, q_unit.T).squeeze(-1)  # Shape (N,)
            return np.clip(sims, -1.0, 1.0)
        elif self.metric == "l2_distance":
            dists = np.linalg.norm(c_unit - q_unit, axis=1)
            # Convert Euclidean distance to similarity score in [0, 1]
            return np.exp(-dists)
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def retrieve_candidates(
        self,
        query: MultimodalPatchEmbedding,
        candidates: List[MultimodalPatchEmbedding],
        top_k: int = 5,
        ground_truth_patch_id: Optional[str] = None,
        min_similarity_threshold: Optional[float] = None,
    ) -> List[MultimodalCandidateMatch]:
        """Rank and retrieve the Top-K candidate matches for a single query patch."""
        if not candidates:
            return []

        # Stack candidate vectors
        matrix = np.stack([c.embedding for c in candidates], axis=0)  # (N, D)
        scores = self.compute_similarity(query.embedding, matrix)

        # Sort indices by descending similarity
        ranked_indices = np.argsort(-scores)

        results: List[MultimodalCandidateMatch] = []
        k_limit = min(top_k, len(candidates))

        for rank_idx in range(k_limit):
            c_idx = int(ranked_indices[rank_idx])
            cand = candidates[c_idx]
            sim_score = float(scores[c_idx])

            if min_similarity_threshold is not None and sim_score < min_similarity_threshold:
                continue

            # Ground truth determination
            gt_status = "UNAVAILABLE"
            is_gt = False
            if ground_truth_patch_id is not None:
                gt_status = "AVAILABLE"
                is_gt = (cand.patch_id == ground_truth_patch_id)
            elif query.patch_id == cand.patch_id:
                # Same patch index across sensors
                gt_status = "AVAILABLE"
                is_gt = True

            geo_rel = compute_geographic_relation(query.ground_bbox, cand.ground_bbox)

            match = MultimodalCandidateMatch(
                query_patch_id=query.patch_id,
                candidate_patch_id=cand.patch_id,
                query_sensor=query.sensor,
                candidate_sensor=cand.sensor,
                query_coordinates={"lat": query.center_coordinates[0], "lon": query.center_coordinates[1]},
                candidate_coordinates={"lat": cand.center_coordinates[0], "lon": cand.center_coordinates[1]},
                query_bbox=query.ground_bbox,
                candidate_bbox=cand.ground_bbox,
                query_gsd=query.gsd_m,
                candidate_gsd=cand.gsd_m,
                similarity_score=sim_score,
                rank=rank_idx + 1,
                embedding_model=query.encoder_name,
                embedding_dim=query.embedding_dim,
                experiment_id=query.experiment_id,
                ground_truth_status=gt_status,
                is_ground_truth=is_gt,
                geographic_relation=geo_rel,
                provenance=query.provenance,
                extra_metadata={
                    "query_modality": query.modality,
                    "candidate_modality": cand.modality,
                }
            )
            results.append(match)

        return results

    def batch_retrieve(
        self,
        queries: List[MultimodalPatchEmbedding],
        candidates: List[MultimodalPatchEmbedding],
        top_k: int = 5,
        ground_truth_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, List[MultimodalCandidateMatch]]:
        """Perform cross-modal retrieval across a collection of query patches."""
        out = {}
        for q in queries:
            gt_target = ground_truth_mapping.get(q.patch_id) if ground_truth_mapping else None
            matches = self.retrieve_candidates(
                query=q,
                candidates=candidates,
                top_k=top_k,
                ground_truth_patch_id=gt_target
            )
            out[q.patch_id] = matches
        return out
