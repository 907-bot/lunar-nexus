"""Visual Verification and Image Warping Utilities for Registration Quality Inspection."""

from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np
import cv2


def warp_image(
    image_source: np.ndarray,
    transformation_matrix: np.ndarray,
    reference_shape: Tuple[int, int],
) -> np.ndarray:
    """Warps source image into reference coordinate frame using estimated Affine or Homography matrix.
    
    Args:
        image_source: Source image (Image A).
        transformation_matrix: 2x3 Affine or 3x3 Homography matrix.
        reference_shape: (height, width) of target reference frame.
        
    Returns:
        Warped image aligned to reference frame.
    """
    h_ref, w_ref = reference_shape[:2]
    
    if transformation_matrix.shape == (3, 3):
        warped = cv2.warpPerspective(
            image_source,
            transformation_matrix,
            (w_ref, h_ref),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
    elif transformation_matrix.shape == (2, 3):
        warped = cv2.warpAffine(
            image_source,
            transformation_matrix,
            (w_ref, h_ref),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
    else:
        raise ValueError(f"Invalid transformation matrix shape: {transformation_matrix.shape}")

    return warped


def draw_matches_visualization(
    img_src: np.ndarray,
    keypoints_src: List[cv2.KeyPoint],
    img_ref: np.ndarray,
    keypoints_ref: List[cv2.KeyPoint],
    matches: List[cv2.DMatch],
    inliers_mask: Optional[np.ndarray] = None,
    max_draw: int = 150,
) -> np.ndarray:
    """Renders visual tie-points between Source and Reference images.
    
    Inliers are drawn in bright neon green, rejected outliers in muted red.
    """
    # Ensure 3-channel RGB for color rendering
    def to_bgr(im):
        if len(im.shape) == 2:
            return cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        elif im.shape[2] == 4:
            return cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)
        return im.copy()

    bgr_src = to_bgr(img_src)
    bgr_ref = to_bgr(img_ref)

    h1, w1 = bgr_src.shape[:2]
    h2, w2 = bgr_ref.shape[:2]
    out_h = max(h1, h2)
    out_w = w1 + w2

    vis = np.zeros((out_h, out_w, 3), dtype=np.uint8)
    vis[:h1, :w1] = bgr_src
    vis[:h2, w1:w1 + w2] = bgr_ref

    if inliers_mask is None:
        inliers_mask = np.ones(len(matches), dtype=bool)

    # Draw subset to avoid visual clutter
    indices = list(range(len(matches)))
    # Prioritize inliers
    inlier_indices = [i for i in indices if inliers_mask[i]]
    outlier_indices = [i for i in indices if not inliers_mask[i]]

    draw_indices = (inlier_indices[:max_draw] + outlier_indices[:max_draw // 3])[:max_draw]

    # Draw outliers first (red)
    for idx in draw_indices:
        if not inliers_mask[idx]:
            m = matches[idx]
            pt1 = (int(keypoints_src[m.queryIdx].pt[0]), int(keypoints_src[m.queryIdx].pt[1]))
            pt2 = (int(keypoints_ref[m.trainIdx].pt[0] + w1), int(keypoints_ref[m.trainIdx].pt[1]))
            cv2.line(vis, pt1, pt2, (40, 40, 200), 1, cv2.LINE_AA)
            cv2.circle(vis, pt1, 2, (40, 40, 220), -1)
            cv2.circle(vis, pt2, 2, (40, 40, 220), -1)

    # Draw inliers on top (bright green)
    for idx in draw_indices:
        if inliers_mask[idx]:
            m = matches[idx]
            pt1 = (int(keypoints_src[m.queryIdx].pt[0]), int(keypoints_src[m.queryIdx].pt[1]))
            pt2 = (int(keypoints_ref[m.trainIdx].pt[0] + w1), int(keypoints_ref[m.trainIdx].pt[1]))
            cv2.line(vis, pt1, pt2, (0, 230, 80), 1, cv2.LINE_AA)
            cv2.circle(vis, pt1, 3, (0, 255, 120), -1)
            cv2.circle(vis, pt2, 3, (0, 255, 120), -1)

    # Add HUD header text
    num_in = int(np.sum(inliers_mask))
    txt = f"Matches: {len(matches)} | Inliers: {num_in} ({num_in/len(matches)*100:.1f}%)"
    cv2.putText(vis, txt, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2, cv2.LINE_AA)

    return vis


def create_checkerboard_overlay(
    img_reference: np.ndarray,
    img_warped_source: np.ndarray,
    grid_size: int = 8,
) -> np.ndarray:
    """Creates an alternating checkerboard pattern to verify pixel alignment along crater edges."""
    h, w = img_reference.shape[:2]
    
    def to_gray(im):
        if len(im.shape) == 3:
            return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return im

    g_ref = to_gray(img_reference)
    g_warp = to_gray(img_warped_source)

    checker = np.zeros((h, w), dtype=np.uint8)
    cell_h = h // grid_size
    cell_w = w // grid_size

    for row in range(grid_size):
        for col in range(grid_size):
            r_start = row * cell_h
            r_end = h if row == grid_size - 1 else (row + 1) * cell_h
            c_start = col * cell_w
            c_end = w if col == grid_size - 1 else (col + 1) * cell_w

            if (row + col) % 2 == 0:
                checker[r_start:r_end, c_start:c_end] = g_ref[r_start:r_end, c_start:c_end]
            else:
                checker[r_start:r_end, c_start:c_end] = g_warp[r_start:r_end, c_start:c_end]

    return cv2.cvtColor(checker, cv2.COLOR_GRAY2BGR)
