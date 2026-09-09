"""Scientific Metrics Computation for Registration Validation."""

from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import cv2


def compute_reprojection_rmse(
    src_pts: np.ndarray,
    ref_pts: np.ndarray,
    M: np.ndarray,
) -> float:
    """Computes the Root Mean Square Error (RMSE) of reprojected inlier points in pixels."""
    if len(src_pts) == 0 or M is None:
        return 0.0

    src_reshaped = np.float32(src_pts).reshape(-1, 1, 2)
    ref_reshaped = np.float32(ref_pts).reshape(-1, 1, 2)

    if M.shape == (3, 3):
        # Homography perspective projection
        projected = cv2.perspectiveTransform(src_reshaped, M)
    elif M.shape == (2, 3):
        # Affine transform projection
        projected = cv2.transform(src_reshaped, M)
    else:
        return 0.0

    # Euclidean distance squared per point
    errors = np.linalg.norm(projected - ref_reshaped, axis=2) ** 2
    rmse = math.sqrt(float(np.mean(errors)))
    return round(rmse, 4)


def decompose_transform_matrix(M: Optional[np.ndarray]) -> Dict[str, Any]:
    """Decomposes affine or homography matrix into rotation (deg), scale (sx, sy), and translation (dx, dy)."""
    if M is None:
        return {
            "rotation_deg": 0.0,
            "scale_x": 1.0,
            "scale_y": 1.0,
            "translation_x_px": 0.0,
            "translation_y_px": 0.0,
        }

    # Extract translation
    dx = float(M[0, 2])
    dy = float(M[1, 2])

    # Extract 2x2 linear portion
    a, b = float(M[0, 0]), float(M[0, 1])
    c, d = float(M[1, 0]), float(M[1, 1])

    # Compute scale factors
    sx = math.sqrt(a * a + c * c)
    sy = math.sqrt(b * b + d * d)

    # Compute rotation angle
    rot_rad = math.atan2(c, a)
    rot_deg = math.degrees(rot_rad)

    return {
        "rotation_deg": round(rot_deg, 3),
        "scale_x": round(sx, 4),
        "scale_y": round(sy, 4),
        "translation_x_px": round(dx, 2),
        "translation_y_px": round(dy, 2),
    }


def compute_registration_metrics(
    total_matches: int,
    inliers_mask: Optional[np.ndarray],
    inlier_src_pts: List[Tuple[float, float]],
    inlier_ref_pts: List[Tuple[float, float]],
    transformation_matrix: Optional[np.ndarray],
    runtime_ms: float,
) -> Dict[str, Any]:
    """Assembles comprehensive scientific metrics as required by SIH POC 3 blueprint.
    
    Metrics:
    - match count
    - inlier count
    - inlier ratio (%)
    - RMSE (pixels)
    - runtime (ms)
    - decomposition (rotation, scale, shift)
    """
    inlier_count = int(np.sum(inliers_mask)) if inliers_mask is not None else len(inlier_src_pts)
    inlier_ratio = (inlier_count / total_matches * 100.0) if total_matches > 0 else 0.0

    rmse = compute_reprojection_rmse(
        np.array(inlier_src_pts),
        np.array(inlier_ref_pts),
        transformation_matrix,
    ) if transformation_matrix is not None else 0.0

    geom_decomp = decompose_transform_matrix(transformation_matrix)

    # Compute registration confidence classification
    if inlier_count >= 50 and inlier_ratio >= 60.0 and rmse <= 2.5:
        confidence = "HIGH"
    elif inlier_count >= 15 and inlier_ratio >= 35.0 and rmse <= 4.0:
        confidence = "MODERATE"
    elif inlier_count > 0:
        confidence = "LOW"
    else:
        confidence = "FAILED"

    return {
        "match_count": total_matches,
        "inlier_count": inlier_count,
        "inlier_ratio_pct": round(inlier_ratio, 2),
        "reprojection_rmse_px": rmse,
        "runtime_ms": round(runtime_ms, 2),
        "confidence_level": confidence,
        "estimated_rotation_deg": geom_decomp["rotation_deg"],
        "estimated_scale": {
            "sx": geom_decomp["scale_x"],
            "sy": geom_decomp["scale_y"],
        },
        "estimated_translation_px": {
            "dx": geom_decomp["translation_x_px"],
            "dy": geom_decomp["translation_y_px"],
        },
        "is_registration_successful": inlier_count >= 4 and transformation_matrix is not None,
    }
