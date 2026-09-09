"""Geometric Transformation Estimation via RANSAC and Phase Correlation."""

from __future__ import annotations
from enum import Enum
from typing import Tuple, Optional, List, Dict, Any
import numpy as np
import cv2


class TransformType(str, Enum):
    HOMOGRAPHY = "Homography"
    AFFINE = "Affine"
    PHASE_CORRELATION = "PhaseCorrelation"


def phase_correlation_shift(
    image_source: np.ndarray,
    image_reference: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """Estimates sub-pixel translation (dx, dy) using 2D FFT Phase Correlation with Hanning window.
    
    Returns:
        (2x3 affine translation matrix, response confidence)
    """
    if len(image_source.shape) == 3:
        gray_src = cv2.cvtColor(image_source, cv2.COLOR_BGR2GRAY)
    else:
        gray_src = image_source
        
    if len(image_reference.shape) == 3:
        gray_ref = cv2.cvtColor(image_reference, cv2.COLOR_BGR2GRAY)
    else:
        gray_ref = image_reference

    # Resize to common dimensions if needed
    h = min(gray_src.shape[0], gray_ref.shape[0])
    w = min(gray_src.shape[1], gray_ref.shape[1])
    s1 = gray_src[:h, :w].astype(np.float32)
    s2 = gray_ref[:h, :w].astype(np.float32)

    # Compute phase correlation with Hanning window
    hanning = cv2.createHanningWindow((w, h), cv2.CV_32F)
    (dx, dy), response = cv2.phaseCorrelate(s1, s2, hanning)

    # Form 2x3 affine translation matrix
    M_affine = np.array([
        [1.0, 0.0, dx],
        [0.0, 1.0, dy],
    ], dtype=np.float64)

    return M_affine, float(response)


def estimate_transformation(
    keypoints_source: List[cv2.KeyPoint],
    keypoints_reference: List[cv2.KeyPoint],
    matches: List[cv2.DMatch],
    transform_type: TransformType = TransformType.HOMOGRAPHY,
    ransac_thresh_px: float = 3.0,
    max_iters: int = 2000,
    confidence: float = 0.99,
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Estimates geometric transformation between matched keypoints using RANSAC.
    
    Args:
        keypoints_source: Keypoints in source image.
        keypoints_reference: Keypoints in reference image.
        matches: List of cv2.DMatch correspondences.
        transform_type: Homography (3x3) or Affine (2x3).
        ransac_thresh_px: Maximum reprojection error in pixels to consider an inlier.
        max_iters: Maximum RANSAC iterations.
        confidence: Desired RANSAC confidence level.
        
    Returns:
        (transformation_matrix, inliers_mask, inlier_src_pts, inlier_ref_pts)
    """
    min_points_required = 4 if transform_type == TransformType.HOMOGRAPHY else 3
    if len(matches) < min_points_required:
        return None, None, [], []

    # Extract coordinate arrays
    src_pts = np.float32([keypoints_source[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    ref_pts = np.float32([keypoints_reference[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    if transform_type == TransformType.HOMOGRAPHY:
        # Compute 3x3 Projective Homography
        M, mask = cv2.findHomography(
            src_pts,
            ref_pts,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_thresh_px,
            maxIters=max_iters,
            confidence=confidence,
        )
    else:
        # Compute 2x3 Affine Transformation
        M, mask = cv2.estimateAffine2D(
            src_pts,
            ref_pts,
            method=cv2.RANSAC,
            ransacReprojThreshold=ransac_thresh_px,
            maxIters=max_iters,
            confidence=confidence,
        )

    if M is None or mask is None:
        return None, None, [], []

    inliers_mask = mask.ravel().astype(bool)
    inlier_src_pts = [(float(pt[0][0]), float(pt[0][1])) for pt, is_in in zip(src_pts, inliers_mask) if is_in]
    inlier_ref_pts = [(float(pt[0][0]), float(pt[0][1])) for pt, is_in in zip(ref_pts, inliers_mask) if is_in]

    return M, inliers_mask, inlier_src_pts, inlier_ref_pts
