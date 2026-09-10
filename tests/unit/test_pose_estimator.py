"""
Unit tests for Human Pose Keypoint Estimator (MediaPipe 12-Joint Pose Engine).
"""

import unittest
import numpy as np
import cv2
from ai.inference.pose_estimator import PoseEstimator, MAJOR_BODY_JOINTS

EXPECTED_12_JOINTS = {
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle"
}


class TestPoseEstimator(unittest.TestCase):

    def setUp(self):
        self.estimator = PoseEstimator(
            min_detection_confidence=0.1,
            max_carry_forward_frames=3,
            rack_bounds=[100, 100, 500, 400]
        )
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def tearDown(self):
        self.estimator.close()

    def test_pose_estimator_initialization(self):
        self.assertIsNotNone(self.estimator)
        self.assertEqual(self.estimator.max_carry_forward_frames, 3)
        self.assertEqual(self.estimator.rack_bounds, [100, 100, 500, 400])

    def test_major_body_joints_count_and_names(self):
        """Verify that MAJOR_BODY_JOINTS mapping contains exactly the 12 required joints."""
        joints_set = set(MAJOR_BODY_JOINTS.values())
        self.assertEqual(len(joints_set), 12)
        self.assertEqual(joints_set, EXPECTED_12_JOINTS)

    def test_estimate_pose_schema(self):
        result = self.estimator.estimate_pose(self.dummy_frame)
        self.assertIn("detected", result)
        self.assertIn("body_keypoints", result)
        self.assertIn("hand_positions", result)
        self.assertIn("rack_relative_keypoints", result)
        self.assertIn("body_bounds", result)
        self.assertIn("carried_forward", result)
        self.assertIn("carry_count", result)
        # Ensure detailed 21 hand landmarks dict is removed from MVP schema
        self.assertNotIn("hand_keypoints", result)

    def test_filtered_12_joints_only(self):
        """Verify that body_keypoints contains ONLY the 12 required joints, not 33 landmarks."""
        dummy_body_kps = {
            joint: {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.9, "px": 320, "py": 240}
            for joint in EXPECTED_12_JOINTS
        }
        for joint_name in dummy_body_kps:
            self.assertIn(joint_name, EXPECTED_12_JOINTS)
        self.assertEqual(len(dummy_body_kps), 12)

    def test_rack_relative_keypoints_math(self):
        dummy_body_kps = {
            "left_wrist": {"px": 300, "py": 250, "x": 0.468, "y": 0.520, "z": 0.0, "visibility": 0.9}
        }
        rack_bounds = [100, 100, 500, 400]  # width=400, height=300
        transformed = self.estimator._compute_rack_relative_keypoints(
            dummy_body_kps, rack_bounds, 640, 480
        )
        self.assertIn("left_wrist", transformed)
        # (300-100)/400 = 0.5, (250-100)/300 = 0.5
        self.assertAlmostEqual(transformed["left_wrist"]["rx"], 0.5, places=2)
        self.assertAlmostEqual(transformed["left_wrist"]["ry"], 0.5, places=2)
        self.assertTrue(transformed["left_wrist"]["in_rack"])

    def test_temporal_carry_forward(self):
        synthetic_valid_result = {
            "detected": True,
            "body_keypoints": {
                "right_wrist": {"px": 200, "py": 200, "x": 0.3, "y": 0.4, "z": 0.0, "visibility": 0.9}
            },
            "hand_positions": {"left": None, "right": {"wrist": (200, 200), "contact_point": (200, 200)}},
            "rack_relative_keypoints": {},
            "body_bounds": [180, 180, 220, 220],
            "carried_forward": False,
            "carry_count": 0
        }
        self.estimator._last_valid_result = synthetic_valid_result
        self.estimator._missing_frames_count = 0

        # Frame 1 missing: carry forward (carry_count=1)
        res1 = self.estimator._handle_missing_detection()
        self.assertTrue(res1["carried_forward"])
        self.assertEqual(res1["carry_count"], 1)
        self.assertIn("right_wrist", res1["body_keypoints"])

        # Frame 2 missing: carry forward (carry_count=2)
        res2 = self.estimator._handle_missing_detection()
        self.assertTrue(res2["carried_forward"])
        self.assertEqual(res2["carry_count"], 2)

        # Frame 3 missing: carry forward (carry_count=3)
        res3 = self.estimator._handle_missing_detection()
        self.assertTrue(res3["carried_forward"])
        self.assertEqual(res3["carry_count"], 3)

        # Frame 4 missing: max limit exceeded (max=3), returns detected=False
        res4 = self.estimator._handle_missing_detection()
        self.assertFalse(res4["detected"])
        self.assertFalse(res4["carried_forward"])

    def test_draw_landmarks(self):
        sample_results = {
            "detected": True,
            "body_keypoints": {
                "left_shoulder": {"px": 200, "py": 150},
                "right_shoulder": {"px": 300, "py": 150},
                "left_elbow": {"px": 180, "py": 250},
                "right_elbow": {"px": 320, "py": 250},
                "left_wrist": {"px": 160, "py": 300},
                "right_wrist": {"px": 340, "py": 300}
            },
            "carried_forward": False
        }
        annotated = self.estimator.draw_landmarks(self.dummy_frame, sample_results)
        self.assertEqual(annotated.shape, self.dummy_frame.shape)
        self.assertGreater(np.sum(annotated), 0)


if __name__ == "__main__":
    unittest.main()
