"""Unit and integration tests for POC 3 Classical Registration Engine.
Verifies detector descriptors (SIFT, RootSIFT, ORB, AKAZE), RANSAC geometric estimation,
reprojection RMSE, transformation matrix decomposition, and REST API endpoints.
"""

import sys
import json
import unittest
from pathlib import Path
import numpy as np
import cv2

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from packages.registration.algorithms import (
    extract_features,
    FeatureMethod,
    apply_rootsift_normalization,
)
from packages.registration.matchers import (
    match_descriptors,
)
from packages.registration.geometric import (
    estimate_transformation,
    TransformType,
    phase_correlation_shift,
)
from packages.registration.metrics import (
    compute_registration_metrics,
    decompose_transform_matrix,
)
from packages.registration.visualizer import (
    draw_matches_visualization,
    create_checkerboard_overlay,
    warp_image,
)
from services.registration.server import ClassicalRegistrationService


class TestClassicalRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create synthetic lunar terrain images for deterministic mathematical validation
        cls.img_size = (400, 400)
        np.random.seed(42)
        base = np.zeros(cls.img_size, dtype=np.uint8)
        # Draw synthetic craters
        craters = [
            (100, 100, 30),
            (250, 150, 45),
            (180, 280, 25),
            (320, 310, 35),
            (80, 300, 20),
            (220, 80, 15),
        ]
        for cx, cy, r in craters:
            cv2.circle(base, (cx, cy), r, 180, -1)
            cv2.circle(base, (cx, cy), r, 60, 3)
            cv2.circle(base, (cx + 5, cy - 5), r // 2, 230, -1)

        # Add regolith noise texture
        noise = np.random.normal(0, 15, cls.img_size).astype(np.int16)
        cls.src_img = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Generate reference image via known affine transform:
        # Rotation 4.0 deg, translation dx=+12.0, dy=-8.0, scale=1.02
        center = (cls.img_size[0] / 2, cls.img_size[1] / 2)
        cls.known_angle = 4.0
        cls.known_scale = 1.02
        cls.known_dx = 12.0
        cls.known_dy = -8.0
        M = cv2.getRotationMatrix2D(center, cls.known_angle, cls.known_scale)
        M[0, 2] += cls.known_dx
        M[1, 2] += cls.known_dy
        cls.known_matrix = M
        cls.ref_img = cv2.warpAffine(cls.src_img, M, cls.img_size, borderMode=cv2.BORDER_REFLECT)

    def test_01_feature_extraction_sift(self):
        kps, descs = extract_features(self.src_img, FeatureMethod.SIFT, max_features=500)
        self.assertGreater(len(kps), 20, "SIFT should detect significant keypoints on crater texture")
        self.assertEqual(descs.shape[1], 128, "SIFT descriptor dimensionality must be 128")

    def test_02_feature_extraction_rootsift(self):
        kps, descs = extract_features(self.src_img, FeatureMethod.ROOT_SIFT, max_features=500)
        self.assertGreater(len(kps), 20, "RootSIFT should detect keypoints")
        self.assertEqual(descs.shape[1], 128, "RootSIFT descriptor dimensionality must be 128")
        # Verify L1 normalization property: sum of squared sqrt descriptors ≈ 1.0
        norms = np.linalg.norm(descs, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-3, err_msg="RootSIFT vectors must have unit L2 norm")

    def test_03_feature_extraction_orb(self):
        kps, descs = extract_features(self.src_img, FeatureMethod.ORB, max_features=500)
        self.assertGreater(len(kps), 20, "ORB should detect keypoints")
        self.assertEqual(descs.shape[1], 32, "ORB binary descriptor must be 32 bytes (256 bits)")

    def test_04_feature_matching_flann(self):
        kps_src, descs_src = extract_features(self.src_img, FeatureMethod.SIFT, max_features=500)
        kps_ref, descs_ref = extract_features(self.ref_img, FeatureMethod.SIFT, max_features=500)
        matches = match_descriptors(descs_src, descs_ref, FeatureMethod.SIFT, ratio_thresh=0.75)
        self.assertGreater(len(matches), 10, "FLANN matcher with Lowe's ratio test should find matches")

    def test_05_geometric_estimation_and_recovery(self):
        kps_src, descs_src = extract_features(self.src_img, FeatureMethod.SIFT, max_features=800)
        kps_ref, descs_ref = extract_features(self.ref_img, FeatureMethod.SIFT, max_features=800)
        matches = match_descriptors(descs_src, descs_ref, FeatureMethod.SIFT, ratio_thresh=0.75)

        M, inliers, pts_src, pts_ref = estimate_transformation(
            kps_src, kps_ref, matches, TransformType.AFFINE, ransac_thresh_px=3.0
        )
        self.assertIsNotNone(M, "RANSAC should successfully estimate affine transformation")
        self.assertGreater(len(inliers), 5, "Should have sufficient inliers")

        # Decompose estimated transformation and check agreement with known ground truth
        decomp = decompose_transform_matrix(M)
        self.assertAlmostEqual(abs(decomp["rotation_deg"]), self.known_angle, delta=1.5,
                               msg="Recovered rotation angle magnitude should match ground truth within 1.5 deg")
        self.assertAlmostEqual(decomp["scale_x"], self.known_scale, delta=0.08,
                               msg="Recovered scale should match ground truth")

    def test_06_metrics_computation(self):
        kps_src, descs_src = extract_features(self.src_img, FeatureMethod.SIFT, max_features=800)
        kps_ref, descs_ref = extract_features(self.ref_img, FeatureMethod.SIFT, max_features=800)
        matches = match_descriptors(descs_src, descs_ref, FeatureMethod.SIFT, ratio_thresh=0.75)
        M, inliers, pts_src, pts_ref = estimate_transformation(
            kps_src, kps_ref, matches, TransformType.HOMOGRAPHY, ransac_thresh_px=3.0
        )
        metrics = compute_registration_metrics(
            total_matches=len(matches),
            inliers_mask=inliers,
            inlier_src_pts=pts_src,
            inlier_ref_pts=pts_ref,
            transformation_matrix=M,
            runtime_ms=35.5,
        )
        self.assertIn("reprojection_rmse_px", metrics)
        self.assertIn("inlier_ratio_pct", metrics)
        self.assertLess(metrics["reprojection_rmse_px"], 2.0, "Sub-pixel or low reprojection RMSE expected")
        self.assertGreater(metrics["inlier_ratio_pct"], 40.0, "Inlier ratio should be reasonably high")

    def test_07_phase_correlation_shift(self):
        shift_x, shift_y = 15.0, -10.0
        M_shift = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        shifted = cv2.warpAffine(self.src_img, M_shift, self.img_size)
        M_shift_recovered, response = phase_correlation_shift(self.src_img, shifted)
        dx = M_shift_recovered[0, 2]
        dy = M_shift_recovered[1, 2]
        self.assertAlmostEqual(dx, shift_x, delta=1.0, msg="Phase correlation should recover dx within 1 px")
        self.assertAlmostEqual(dy, shift_y, delta=1.0, msg="Phase correlation should recover dy within 1 px")

    def test_08_visualizer_generation(self):
        kps_src, descs_src = extract_features(self.src_img, FeatureMethod.SIFT, max_features=200)
        kps_ref, descs_ref = extract_features(self.ref_img, FeatureMethod.SIFT, max_features=200)
        matches = match_descriptors(descs_src, descs_ref, FeatureMethod.SIFT, ratio_thresh=0.75)
        M, inliers, pts_src, pts_ref = estimate_transformation(
            kps_src, kps_ref, matches, TransformType.AFFINE, ransac_thresh_px=3.0
        )
        # Visualizer matches
        vis = draw_matches_visualization(self.src_img, kps_src, self.ref_img, kps_ref, matches, inliers)
        self.assertEqual(len(vis.shape), 3, "Visualization output must be a 3-channel RGB image")
        # Visualizer checkerboard
        warped = warp_image(self.ref_img, M, (self.img_size[1], self.img_size[0]))
        cb = create_checkerboard_overlay(self.src_img, warped, grid_size=8)
        self.assertEqual(cb.shape[:2], self.img_size, "Checkerboard dimensions must match input")

    def test_09_registration_service_live_images(self):
        service = ClassicalRegistrationService()
        result = service.execute_registration(
            source_id="ch2_ohr_ncp_20230915t041230_boguslawsky_d18",
            reference_id="M1345982701LR_BOGUSLAWSKY_REF",
            method_str="SIFT",
            transform_type_str="Homography",
            ratio_thresh=0.75,
            ransac_thresh_px=3.0,
        )
        self.assertIn("job_id", result)
        self.assertIn("metrics", result)
        self.assertIn("transformation_matrix", result)
        self.assertIn("artifacts", result)
        self.assertGreater(result["metrics"]["match_count"], 5)
        self.assertGreater(result["metrics"]["inlier_count"], 3)

    def test_multiple_source_images_registration(self):
        """Validates that newly populated source images (Shackleton, Apollo 17) register correctly."""
        service = ClassicalRegistrationService()
        # Shackleton Crater Rim pair
        res_shackleton = service.execute_registration(
            source_id="ch2_ohr_ncp_20230823t123015_shackleton_rim",
            reference_id="M1123456789_SHACKLETON_REF",
            method_str="SIFT",
            transform_type_str="Homography",
        )
        self.assertEqual(res_shackleton["status"], "COMPLETED")
        self.assertGreater(res_shackleton["metrics"]["inlier_count"], 10)

        # Apollo 17 Valley pair
        res_apollo = service.execute_registration(
            source_id="ch2_ohr_ncp_20230712t081545_apollo17_site",
            reference_id="M1198765432_APOLLO17_REF",
            method_str="ORB",
            transform_type_str="Affine",
        )
        self.assertEqual(res_apollo["status"], "COMPLETED")
        self.assertGreater(res_apollo["metrics"]["inlier_count"], 10)


if __name__ == "__main__":
    unittest.main()

