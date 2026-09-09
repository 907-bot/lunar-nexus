"""NEXUS-LUNAR Registration Package (POC 3: Classical Registration Engine)
Provides transparent non-AI feature extraction, descriptor matching,
RANSAC geometric verification, homography/affine warping, and scientific metrics.
"""

from .algorithms import extract_features, FeatureMethod
from .matchers import match_descriptors
from .geometric import estimate_transformation, TransformType, phase_correlation_shift
from .metrics import compute_registration_metrics, decompose_transform_matrix
from .visualizer import draw_matches_visualization, create_checkerboard_overlay, warp_image

__all__ = [
    "extract_features",
    "FeatureMethod",
    "match_descriptors",
    "estimate_transformation",
    "TransformType",
    "phase_correlation_shift",
    "compute_registration_metrics",
    "decompose_transform_matrix",
    "draw_matches_visualization",
    "create_checkerboard_overlay",
    "warp_image",
]
