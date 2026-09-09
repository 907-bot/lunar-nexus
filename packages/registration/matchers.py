"""Descriptor Matching with Lowe's Ratio Test (FLANN and Brute-Force)."""

from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np
import cv2
from .algorithms import FeatureMethod


def match_descriptors(
    desc_source: np.ndarray,
    desc_reference: np.ndarray,
    method: FeatureMethod = FeatureMethod.SIFT,
    ratio_thresh: float = 0.75,
) -> List[cv2.DMatch]:
    """Matches descriptors between Source and Reference using Lowe's ratio test.
    
    Returns:
        List of filtered cv2.DMatch objects passing Lowe's ratio test.
    """
    if desc_source is None or desc_reference is None:
        return []
    if len(desc_source) < 2 or len(desc_reference) < 2:
        return []

    # Choose matcher based on descriptor type (floating point vs binary)
    is_binary = method in (FeatureMethod.ORB, FeatureMethod.AKAZE)

    if is_binary:
        # Brute-Force with Hamming distance for binary descriptors
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        knn_matches = bf.knnMatch(desc_source, desc_reference, k=2)
    else:
        # FLANN matcher for floating-point descriptors (SIFT / RootSIFT)
        # FLANN parameters: 5 randomized kd-trees, 50 checks
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        # Ensure float32 for FLANN
        src_f = desc_source.astype(np.float32)
        ref_f = desc_reference.astype(np.float32)
        knn_matches = flann.knnMatch(src_f, ref_f, k=2)

    # Lowe's ratio test: discard ambiguous matches where second best is almost as close as best
    good_matches: List[cv2.DMatch] = []
    for match_pair in knn_matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < ratio_thresh * n.distance:
                good_matches.append(m)

    # Sort matches by distance (best match first)
    good_matches.sort(key=lambda x: x.distance)
    return good_matches
