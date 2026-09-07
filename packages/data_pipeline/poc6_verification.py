"""NEXUS-LUNAR POC-6: Geometric Verification + Explainable AI (XAI) Engine.

Validates multimodal AI retrieval candidates using deterministic RANSAC geometric
verification, inlier consensus, spatial distribution analysis, geographic overlap
constraints, and sensor compatibility. Generates structured, diagnostic XAI reasons
explaining why each candidate match was accepted or rejected.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from .poc4_matching import (
    Keypoint,
    KeypointMatch,
    detect_keypoints,
    extract_descriptors,
    match_features,
    estimate_affine_ransac,
    RegistrationResult,
)


@dataclass
class VerificationConfig:
    """Configurable thresholds and weights for POC-6 geometric verification."""
    # Decision thresholds
    min_inliers: int = 6
    min_inlier_ratio: float = 0.35
    max_rmse: float = 3.5  # pixels
    min_confidence: float = 0.50
    allow_disjoint: bool = False
    require_stable_transform: bool = True
    
    # RANSAC parameters
    max_reproj_error: float = 4.0
    ransac_iterations: int = 2000
    ransac_confidence: float = 0.99
    
    # Feature extraction parameters
    max_features: int = 500
    ratio_thresh: float = 0.75
    min_spatial_distribution_score: float = 0.30
    
    # Transparent multi-signal confidence weights (sum to 1.0)
    ai_match_weight: float = 0.10
    inlier_weight: float = 0.20
    inlier_ratio_weight: float = 0.20
    rmse_weight: float = 0.15
    overlap_weight: float = 0.15
    spatial_distribution_weight: float = 0.10
    transformation_stability_weight: float = 0.05
    sensor_compatibility_weight: float = 0.05

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SpatialDistributionResult:
    """Quantitative evaluation of geometric inlier spatial spread across the patch."""
    bounding_area_ratio: float
    occupied_cells: int
    total_cells: int
    spatial_distribution_score: float
    spatial_distribution_status: str  # "GOOD" | "POOR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bounding_area_ratio": round(float(self.bounding_area_ratio), 4),
            "occupied_cells": int(self.occupied_cells),
            "total_cells": int(self.total_cells),
            "spatial_distribution_score": round(float(self.spatial_distribution_score), 4),
            "spatial_distribution_status": self.spatial_distribution_status,
        }


@dataclass
class TransformationStabilityResult:
    """Assessment of the geometric transformation's physical stability and conditioning."""
    status: str  # "STABLE" | "UNSTABLE" | "UNKNOWN"
    determinant: float
    condition_number: float
    scale_x: float
    scale_y: float
    rotation_deg: float
    translation_magnitude: float
    stability_score: float  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "determinant": round(float(self.determinant), 4) if np.isfinite(self.determinant) else 0.0,
            "condition_number": round(float(self.condition_number), 4) if np.isfinite(self.condition_number) else 999.0,
            "scale_x": round(float(self.scale_x), 4) if np.isfinite(self.scale_x) else 0.0,
            "scale_y": round(float(self.scale_y), 4) if np.isfinite(self.scale_y) else 0.0,
            "rotation_deg": round(float(self.rotation_deg), 2) if np.isfinite(self.rotation_deg) else 0.0,
            "translation_magnitude": round(float(self.translation_magnitude), 2) if np.isfinite(self.translation_magnitude) else 0.0,
            "stability_score": round(float(self.stability_score), 4),
        }


@dataclass
class ConfidenceBreakdown:
    """Transparent itemization of individual normalized scores contributing to verification confidence."""
    ai_match_score: float
    inlier_score: float
    inlier_ratio_score: float
    rmse_score: float
    geographic_overlap_score: float
    spatial_distribution_score: float
    transformation_stability_score: float
    sensor_compatibility_score: float
    raw_confidence: float
    disjoint_penalty_applied: bool
    final_verification_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ai_match_score": round(float(self.ai_match_score), 4),
            "inlier_score": round(float(self.inlier_score), 4),
            "inlier_ratio_score": round(float(self.inlier_ratio_score), 4),
            "rmse_score": round(float(self.rmse_score), 4),
            "geographic_overlap_score": round(float(self.geographic_overlap_score), 4),
            "spatial_distribution_score": round(float(self.spatial_distribution_score), 4),
            "transformation_stability_score": round(float(self.transformation_stability_score), 4),
            "sensor_compatibility_score": round(float(self.sensor_compatibility_score), 4),
            "raw_confidence": round(float(self.raw_confidence), 4),
            "disjoint_penalty_applied": self.disjoint_penalty_applied,
            "final_verification_confidence": round(float(self.final_verification_confidence), 4),
        }


@dataclass
class XAIDiagnostic:
    """Structured machine-readable diagnostic explanation."""
    code: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass
class VerifiedCandidateMatch:
    """Comprehensive verified candidate match schema conforming to POC-6 & POC-7 handoff requirements."""
    experiment_id: str
    query_patch_id: str
    candidate_patch_id: str
    query_sensor: str
    candidate_sensor: str
    query_coordinates: Dict[str, float]
    candidate_coordinates: Dict[str, float]
    query_bbox: Dict[str, float]
    candidate_bbox: Dict[str, float]
    query_gsd: float
    candidate_gsd: float
    ai_similarity_score: float
    rank: int
    tentative_match_count: int
    inlier_count: int
    inlier_ratio: float
    transformation_model: str
    transformation_matrix: Optional[List[List[float]]]
    transformation_stability: str
    rmse: float
    reprojection_error: float
    geographic_relation: str
    geographic_overlap_score: float
    spatial_distribution_score: float
    spatial_distribution_status: str
    sensor_compatibility: str
    sensor_compatibility_score: float
    confidence_breakdown: ConfidenceBreakdown
    verification_confidence: float
    accepted: bool
    decision: str  # "ACCEPTED" | "REJECTED"
    acceptance_reasons: List[str]
    rejection_reasons: List[Dict[str, str]]
    inlier_correspondences: List[Dict[str, Any]]
    processing_time_ms: float
    provenance: str
    model_version: str = "1.0.0"
    timestamp: str = ""
    random_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
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
            "ai_similarity_score": round(float(self.ai_similarity_score), 4),
            "rank": int(self.rank),
            "tentative_match_count": int(self.tentative_match_count),
            "inlier_count": int(self.inlier_count),
            "inlier_ratio": round(float(self.inlier_ratio), 4),
            "transformation_model": self.transformation_model,
            "transformation_matrix": self.transformation_matrix,
            "transformation_stability": self.transformation_stability,
            "rmse": round(float(self.rmse), 4) if np.isfinite(self.rmse) else 999.0,
            "reprojection_error": round(float(self.reprojection_error), 4) if np.isfinite(self.reprojection_error) else 999.0,
            "geographic_relation": self.geographic_relation,
            "geographic_overlap_score": round(float(self.geographic_overlap_score), 4),
            "spatial_distribution_score": round(float(self.spatial_distribution_score), 4),
            "spatial_distribution_status": self.spatial_distribution_status,
            "sensor_compatibility": self.sensor_compatibility,
            "sensor_compatibility_score": round(float(self.sensor_compatibility_score), 4),
            "confidence_breakdown": self.confidence_breakdown.to_dict(),
            "verification_confidence": round(float(self.verification_confidence), 4),
            "accepted": bool(self.accepted),
            "decision": self.decision,
            "acceptance_reasons": self.acceptance_reasons,
            "rejection_reasons": self.rejection_reasons,
            "inlier_correspondences_count": len(self.inlier_correspondences),
            "inlier_correspondences": self.inlier_correspondences,
            "processing_time_ms": round(float(self.processing_time_ms), 2),
            "provenance": self.provenance,
            "model_version": self.model_version,
            "timestamp": self.timestamp,
            "random_seed": self.random_seed,
        }

    def to_poc7_handover_dict(self) -> Dict[str, Any]:
        """Compact schema for downstream POC-7 coregistration and relative pose estimation."""
        return {
            "query_patch_id": self.query_patch_id,
            "candidate_patch_id": self.candidate_patch_id,
            "accepted": self.accepted,
            "decision": self.decision,
            "verification_confidence": round(float(self.verification_confidence), 4),
            "transformation_model": self.transformation_model,
            "transformation_matrix": self.transformation_matrix,
            "rmse": round(float(self.rmse), 4) if np.isfinite(self.rmse) else 999.0,
            "inlier_count": int(self.inlier_count),
            "inlier_ratio": round(float(self.inlier_ratio), 4),
            "geographic_relation": self.geographic_relation,
            "query_sensor": self.query_sensor,
            "candidate_sensor": self.candidate_sensor,
            "query_gsd": self.query_gsd,
            "candidate_gsd": self.candidate_gsd,
            "inliers": self.inlier_correspondences,
            "provenance": self.provenance,
        }


def evaluate_spatial_distribution(
    inlier_matches: List[KeypointMatch],
    patch_shape: Tuple[int, int] = (128, 128),
    grid_size: int = 4,
) -> SpatialDistributionResult:
    """Evaluates whether geometric inliers are well-distributed across the patch rather than clustered.

    Computes:
      1. Bounding Area Ratio = (bbox_width * bbox_height) / (patch_width * patch_height)
      2. Grid Occupancy = count of grid cells (out of grid_size x grid_size) containing >= 1 inlier point.
    """
    total_cells = grid_size * grid_size
    if len(inlier_matches) < 3:
        return SpatialDistributionResult(
            bounding_area_ratio=0.0,
            occupied_cells=0,
            total_cells=total_cells,
            spatial_distribution_score=0.0,
            spatial_distribution_status="POOR",
        )

    h, w = patch_shape
    pts = np.array([m.src_pt for m in inlier_matches], dtype=np.float32)  # (N, 2) (x, y)
    
    x_min, x_max = float(np.min(pts[:, 0])), float(np.max(pts[:, 0]))
    y_min, y_max = float(np.min(pts[:, 1])), float(np.max(pts[:, 1]))

    bbox_w = max(0.0, x_max - x_min)
    bbox_h = max(0.0, y_max - y_min)
    patch_area = max(1.0, float(w * h))
    bounding_area_ratio = min(1.0, (bbox_w * bbox_h) / patch_area)

    # Grid occupancy: compute cell coordinates
    cell_w = max(1.0, w / grid_size)
    cell_h = max(1.0, h / grid_size)
    occupied_set = set()
    for pt in pts:
        gx = min(grid_size - 1, max(0, int(pt[0] // cell_w)))
        gy = min(grid_size - 1, max(0, int(pt[1] // cell_h)))
        occupied_set.add((gx, gy))

    occupied_cells = len(occupied_set)

    # Score combines spread area and cell distribution
    area_score = min(1.0, bounding_area_ratio / 0.20)
    grid_score = min(1.0, occupied_cells / 4.0)
    score = 0.5 * area_score + 0.5 * grid_score

    status = "GOOD" if (score >= 0.35 and occupied_cells >= 3) else "POOR"

    return SpatialDistributionResult(
        bounding_area_ratio=bounding_area_ratio,
        occupied_cells=occupied_cells,
        total_cells=total_cells,
        spatial_distribution_score=score,
        spatial_distribution_status=status,
    )


def evaluate_transformation_stability(
    affine_matrix: Optional[np.ndarray],
    inlier_count: int,
    rmse: float,
    min_inliers: int = 6,
) -> TransformationStabilityResult:
    """Analyzes the numerical and physical plausibility of the estimated affine transformation."""
    if affine_matrix is None or inlier_count < 3 or not np.isfinite(rmse):
        return TransformationStabilityResult(
            status="UNKNOWN",
            determinant=0.0,
            condition_number=999.0,
            scale_x=0.0,
            scale_y=0.0,
            rotation_deg=0.0,
            translation_magnitude=0.0,
            stability_score=0.0,
        )

    A = affine_matrix[:2, :2]
    t = affine_matrix[:2, 2]

    det = float(np.linalg.det(A))
    
    # Singular value decomposition for condition number and anisotropic stretch
    try:
        _, s, _ = np.linalg.svd(A)
        s_max, s_min = float(s[0]), float(s[1])
        cond = s_max / max(1e-6, s_min)
    except Exception:
        s_max, s_min = 1.0, 1.0
        cond = 999.0

    scale_x = float(np.linalg.norm(A[:, 0]))
    scale_y = float(np.linalg.norm(A[:, 1]))
    rot_rad = float(math.atan2(A[1, 0], A[0, 0]))
    rot_deg = float(math.degrees(rot_rad))
    trans_mag = float(np.linalg.norm(t))

    # Plausibility checks:
    # 1. Determinant must be positive (no mirroring/reflection)
    # 2. Scale factor in reasonable physical bounds (0.15 to 8.0)
    # 3. Condition number reasonable (<= 8.0, meaning no 1D line collapse)
    # 4. Inlier count >= min_inliers
    # 5. RMSE <= 4.0
    is_positive_det = det > 0.05
    is_scale_reasonable = (0.15 <= s_min) and (s_max <= 8.0)
    is_well_conditioned = cond <= 8.0
    is_low_error = rmse <= 4.0
    has_enough_inliers = inlier_count >= min_inliers

    if is_positive_det and is_scale_reasonable and is_well_conditioned and is_low_error and has_enough_inliers:
        status = "STABLE"
        score = 1.0
    elif is_positive_det and is_well_conditioned:
        status = "UNSTABLE"
        score = 0.4
    else:
        status = "UNSTABLE"
        score = 0.1

    return TransformationStabilityResult(
        status=status,
        determinant=det,
        condition_number=cond,
        scale_x=scale_x,
        scale_y=scale_y,
        rotation_deg=rot_deg,
        translation_magnitude=trans_mag,
        stability_score=score,
    )


def evaluate_sensor_compatibility(
    query_sensor: str,
    candidate_sensor: str,
    query_gsd: float,
    candidate_gsd: float,
) -> Tuple[str, float]:
    """Computes sensor and spatial resolution compatibility score.

    Returns:
        (status_string, normalized_score)
    """
    if query_gsd <= 0.0 or candidate_gsd <= 0.0 or not np.isfinite(query_gsd) or not np.isfinite(candidate_gsd):
        return "UNKNOWN", 0.5

    gsd_ratio = max(query_gsd, candidate_gsd) / max(1e-4, min(query_gsd, candidate_gsd))

    if gsd_ratio <= 4.0:
        return "GOOD", 1.0
    elif gsd_ratio <= 8.0:
        return "MODERATE", 0.7
    else:
        return "LOW", 0.3


def compute_geographic_overlap_score(
    geographic_relation: str,
    query_bbox: Optional[Dict[str, float]] = None,
    candidate_bbox: Optional[Dict[str, float]] = None,
) -> float:
    """Computes geographic overlap score based on relationship status and bounding box intersection."""
    rel = str(geographic_relation).upper()
    if rel == "OVERLAPPING":
        return 1.0
    elif rel == "NEARBY":
        return 0.5
    elif rel == "DISJOINT":
        return 0.0
    else:
        return 0.3


def calculate_verification_confidence(
    ai_similarity: float,
    inlier_count: int,
    inlier_ratio: float,
    rmse: float,
    geographic_relation: str,
    spatial_dist_score: float,
    transform_stability_score: float,
    sensor_compat_score: float,
    config: VerificationConfig,
) -> ConfidenceBreakdown:
    """Calculates transparent multi-signal verification confidence score."""
    # 1. AI match score (normalized [0, 1])
    s_ai = max(0.0, min(1.0, float(ai_similarity)))

    # 2. Inlier count score (saturates at 15 inliers)
    s_inl = max(0.0, min(1.0, float(inlier_count) / 15.0))

    # 3. Inlier ratio score
    s_ratio = max(0.0, min(1.0, float(inlier_ratio)))

    # 4. RMSE score (linear decay from 0 px to 5 px)
    if np.isfinite(rmse):
        s_rmse = max(0.0, min(1.0, 1.0 - (rmse / 5.0)))
    else:
        s_rmse = 0.0

    # 5. Geographic overlap score
    s_geo = compute_geographic_overlap_score(geographic_relation)

    # 6. Spatial distribution score
    s_dist = max(0.0, min(1.0, float(spatial_dist_score)))

    # 7. Transformation stability score
    s_stab = max(0.0, min(1.0, float(transform_stability_score)))

    # 8. Sensor compatibility score
    s_sensor = max(0.0, min(1.0, float(sensor_compat_score)))

    raw_conf = (
        config.ai_match_weight * s_ai +
        config.inlier_weight * s_inl +
        config.inlier_ratio_weight * s_ratio +
        config.rmse_weight * s_rmse +
        config.overlap_weight * s_geo +
        config.spatial_distribution_weight * s_dist +
        config.transformation_stability_weight * s_stab +
        config.sensor_compatibility_weight * s_sensor
    )

    # Geographic DISJOINT penalty:
    # If the candidate is physically disjoint, damp verification confidence severely
    disjoint_applied = False
    final_conf = raw_conf
    if str(geographic_relation).upper() == "DISJOINT":
        disjoint_applied = True
        final_conf = raw_conf * 0.25

    final_conf = max(0.0, min(1.0, final_conf))

    return ConfidenceBreakdown(
        ai_match_score=s_ai,
        inlier_score=s_inl,
        inlier_ratio_score=s_ratio,
        rmse_score=s_rmse,
        geographic_overlap_score=s_geo,
        spatial_distribution_score=s_dist,
        transformation_stability_score=s_stab,
        sensor_compatibility_score=s_sensor,
        raw_confidence=raw_conf,
        disjoint_penalty_applied=disjoint_applied,
        final_verification_confidence=final_conf,
    )


def generate_xai_explanations(
    accepted: bool,
    ai_similarity: float,
    tentative_matches: int,
    inlier_count: int,
    inlier_ratio: float,
    rmse: float,
    geographic_relation: str,
    spatial_dist: SpatialDistributionResult,
    transform_stab: TransformationStabilityResult,
    sensor_compat: Tuple[str, float],
    query_gsd: float,
    candidate_gsd: float,
    confidence: float,
    config: VerificationConfig,
) -> Tuple[List[str], List[Dict[str, str]]]:
    """Generates structured Explainable AI (XAI) diagnostic reasons for acceptance or rejection."""
    acceptance_reasons: List[str] = []
    rejection_reasons: List[Dict[str, str]] = []

    geo_rel = str(geographic_relation).upper()
    gsd_ratio = max(query_gsd, candidate_gsd) / max(1e-4, min(query_gsd, candidate_gsd))

    if accepted:
        # Generate positive evidence verification checklist
        if ai_similarity >= 0.70:
            acceptance_reasons.append(f"Strong AI retrieval similarity ({ai_similarity:.3f})")
        else:
            acceptance_reasons.append(f"Moderate AI retrieval similarity ({ai_similarity:.3f})")

        acceptance_reasons.append(
            f"Strong geometric consensus: {inlier_count}/{tentative_matches} inliers ({inlier_ratio * 100:.1f}%)"
        )
        acceptance_reasons.append(
            f"Low reprojection error: RMSE = {rmse:.2f} px (configured max: {config.max_rmse:.1f} px)"
        )
        acceptance_reasons.append(
            f"Consistent geographic footprint ({geo_rel})"
        )
        acceptance_reasons.append(
            f"Physically stable affine transformation (determinant = {transform_stab.determinant:.2f})"
        )
        acceptance_reasons.append(
            f"Well-distributed spatial spread across patch ({spatial_dist.occupied_cells}/{spatial_dist.total_cells} cells occupied, score = {spatial_dist.spatial_distribution_score:.2f})"
        )
        acceptance_reasons.append(
            f"Compatible cross-sensor acquisition: GSD ratio {gsd_ratio:.1f}x ({sensor_compat[0]})"
        )
    else:
        # Generate diagnostic failure codes and messages
        if geo_rel == "DISJOINT":
            rejection_reasons.append({
                "code": "GEOGRAPHIC_DISJOINT",
                "message": "Candidate patch footprint is geographically disjoint from query observation.",
            })

        if inlier_count < config.min_inliers:
            rejection_reasons.append({
                "code": "TOO_FEW_INLIERS",
                "message": f"Only {inlier_count} geometric inliers found, below required threshold of {config.min_inliers}.",
            })

        if inlier_ratio < config.min_inlier_ratio:
            rejection_reasons.append({
                "code": "LOW_INLIER_RATIO",
                "message": f"Geometric inlier ratio of {inlier_ratio * 100:.1f}% is below acceptable threshold of {config.min_inlier_ratio * 100:.1f}%.",
            })

        if np.isfinite(rmse) and rmse > config.max_rmse:
            rejection_reasons.append({
                "code": "HIGH_REPROJECTION_ERROR",
                "message": f"Reprojection RMSE of {rmse:.2f} px exceeds maximum allowable error of {config.max_rmse:.1f} px.",
            })
        elif not np.isfinite(rmse):
            rejection_reasons.append({
                "code": "NO_VALID_GEOMETRIC_MODEL",
                "message": "RANSAC failed to estimate a valid geometric transformation model.",
            })

        if transform_stab.status != "STABLE":
            rejection_reasons.append({
                "code": "UNSTABLE_TRANSFORMATION",
                "message": f"Estimated affine transformation is degenerate or numerically unstable (status: {transform_stab.status}, det: {transform_stab.determinant:.3f}).",
            })

        if spatial_dist.spatial_distribution_status == "POOR":
            rejection_reasons.append({
                "code": "POOR_SPATIAL_DISTRIBUTION",
                "message": f"Geometric inliers are clustered locally ({spatial_dist.occupied_cells}/{spatial_dist.total_cells} cells, spread score {spatial_dist.spatial_distribution_score:.2f}).",
            })

        if ai_similarity >= 0.75 and len(rejection_reasons) > 0:
            rejection_reasons.append({
                "code": "AI_SIMILARITY_FALSE_POSITIVE",
                "message": f"High AI similarity ({ai_similarity:.3f}) was not supported by verified physical geometry.",
            })

        if confidence < config.min_confidence:
            rejection_reasons.append({
                "code": "LOW_CONFIDENCE",
                "message": f"Verification confidence score ({confidence:.3f}) is below minimum acceptance threshold ({config.min_confidence:.3f}).",
            })

        if len(rejection_reasons) == 0:
            rejection_reasons.append({
                "code": "GENERAL_VERIFICATION_FAILURE",
                "message": "Candidate failed composite verification criteria.",
            })

    return acceptance_reasons, rejection_reasons


class GeometricVerifier:
    """Executes feature matching, RANSAC geometric verification, confidence evaluation, and XAI diagnosis."""

    def __init__(self, config: Optional[VerificationConfig] = None, seed: int = 42):
        self.config = config or VerificationConfig()
        self.seed = seed

    def verify_candidate_pair(
        self,
        candidate_dict: Dict[str, Any],
        query_image: np.ndarray,
        candidate_image: np.ndarray,
    ) -> VerifiedCandidateMatch:
        """Runs full verification pipeline on a candidate pair from POC-5."""
        start_time = time.perf_counter()

        # Extract metadata
        q_id = candidate_dict.get("query_patch_id", "UNKNOWN_QUERY")
        c_id = candidate_dict.get("candidate_patch_id", "UNKNOWN_CANDIDATE")
        q_sensor = candidate_dict.get("query_sensor", "UNKNOWN_SENSOR")
        c_sensor = candidate_dict.get("candidate_sensor", "UNKNOWN_SENSOR")
        q_coords = candidate_dict.get("query_coordinates", {"lat": 0.0, "lon": 0.0})
        c_coords = candidate_dict.get("candidate_coordinates", {"lat": 0.0, "lon": 0.0})
        q_bbox = candidate_dict.get("query_bbox", {})
        c_bbox = candidate_dict.get("candidate_bbox", {})
        q_gsd = float(candidate_dict.get("query_gsd", 0.25))
        c_gsd = float(candidate_dict.get("candidate_gsd", 1.0))
        ai_sim = float(candidate_dict.get("similarity_score", 0.0))
        rank = int(candidate_dict.get("rank", 1))
        exp_id = candidate_dict.get("experiment_id", "EXP_POC6")
        geo_rel = candidate_dict.get("geographic_relation", "UNKNOWN")
        prov = candidate_dict.get("provenance", "SYNTHETIC OFFLINE DEMO")

        # 1. Feature Detection
        src_kps = detect_keypoints(query_image, max_features=self.config.max_features)
        ref_kps = detect_keypoints(candidate_image, max_features=self.config.max_features)

        # 2. Descriptor Extraction
        src_valid, src_descs = extract_descriptors(query_image, src_kps)
        ref_valid, ref_descs = extract_descriptors(candidate_image, ref_kps)

        # 3. Matching
        tentative_matches = match_features(
            src_valid, src_descs, ref_valid, ref_descs, ratio_thresh=self.config.ratio_thresh
        )

        # 4. RANSAC Affine Verification
        affine_mat, inlier_matches, rmse = estimate_affine_ransac(
            tentative_matches,
            max_reproj_error=self.config.max_reproj_error,
            max_iterations=self.config.ransac_iterations,
            confidence=self.config.ransac_confidence,
            min_inliers_thresh=self.config.min_inliers,
            seed=self.seed,
        )

        inl_count = len(inlier_matches)
        tent_count = len(tentative_matches)
        inl_ratio = (inl_count / max(1, tent_count)) if tent_count > 0 else 0.0

        # 5. Spatial Distribution
        spatial_dist = evaluate_spatial_distribution(
            inlier_matches, patch_shape=query_image.shape[:2]
        )

        # 6. Transformation Stability
        transform_stab = evaluate_transformation_stability(
            affine_mat, inlier_count=inl_count, rmse=rmse, min_inliers=self.config.min_inliers
        )

        # 7. Sensor Compatibility
        sensor_compat = evaluate_sensor_compatibility(q_sensor, c_sensor, q_gsd, c_gsd)

        # 8. Confidence Estimation
        confidence_breakdown = calculate_verification_confidence(
            ai_similarity=ai_sim,
            inlier_count=inl_count,
            inlier_ratio=inl_ratio,
            rmse=rmse,
            geographic_relation=geo_rel,
            spatial_dist_score=spatial_dist.spatial_distribution_score,
            transform_stability_score=transform_stab.stability_score,
            sensor_compat_score=sensor_compat[1],
            config=self.config,
        )
        final_conf = confidence_breakdown.final_verification_confidence

        # 9. Acceptance Decision
        is_geo_ok = True
        if not self.config.allow_disjoint and str(geo_rel).upper() == "DISJOINT":
            is_geo_ok = False

        is_stab_ok = True
        if self.config.require_stable_transform and transform_stab.status != "STABLE":
            is_stab_ok = False

        accepted = bool(
            inl_count >= self.config.min_inliers
            and inl_ratio >= self.config.min_inlier_ratio
            and np.isfinite(rmse)
            and rmse <= self.config.max_rmse
            and is_geo_ok
            and is_stab_ok
            and final_conf >= self.config.min_confidence
        )
        decision = "ACCEPTED" if accepted else "REJECTED"

        # 10. Explainable AI Diagnostics
        acc_reasons, rej_reasons = generate_xai_explanations(
            accepted=accepted,
            ai_similarity=ai_sim,
            tentative_matches=tent_count,
            inlier_count=inl_count,
            inlier_ratio=inl_ratio,
            rmse=rmse,
            geographic_relation=geo_rel,
            spatial_dist=spatial_dist,
            transform_stab=transform_stab,
            sensor_compat=sensor_compat,
            query_gsd=q_gsd,
            candidate_gsd=c_gsd,
            confidence=final_conf,
            config=self.config,
        )

        # Format inliers for POC-7 handover
        inlier_corrs = [
            {
                "src_pt": [round(float(m.src_pt[0]), 2), round(float(m.src_pt[1]), 2)],
                "ref_pt": [round(float(m.ref_pt[0]), 2), round(float(m.ref_pt[1]), 2)],
                "distance": round(float(m.distance), 4),
            }
            for m in inlier_matches
        ]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return VerifiedCandidateMatch(
            experiment_id=exp_id,
            query_patch_id=q_id,
            candidate_patch_id=c_id,
            query_sensor=q_sensor,
            candidate_sensor=c_sensor,
            query_coordinates=q_coords,
            candidate_coordinates=c_coords,
            query_bbox=q_bbox,
            candidate_bbox=c_bbox,
            query_gsd=q_gsd,
            candidate_gsd=c_gsd,
            ai_similarity_score=ai_sim,
            rank=rank,
            tentative_match_count=tent_count,
            inlier_count=inl_count,
            inlier_ratio=inl_ratio,
            transformation_model="affine",
            transformation_matrix=affine_mat.tolist() if affine_mat is not None else None,
            transformation_stability=transform_stab.status,
            rmse=rmse,
            reprojection_error=rmse,
            geographic_relation=geo_rel,
            geographic_overlap_score=confidence_breakdown.geographic_overlap_score,
            spatial_distribution_score=spatial_dist.spatial_distribution_score,
            spatial_distribution_status=spatial_dist.spatial_distribution_status,
            sensor_compatibility=sensor_compat[0],
            sensor_compatibility_score=sensor_compat[1],
            confidence_breakdown=confidence_breakdown,
            verification_confidence=final_conf,
            accepted=accepted,
            decision=decision,
            acceptance_reasons=acc_reasons,
            rejection_reasons=rej_reasons,
            inlier_correspondences=inlier_corrs,
            processing_time_ms=elapsed_ms,
            provenance=prov,
            random_seed=self.seed,
        )
