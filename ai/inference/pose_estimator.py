"""
Human Pose Keypoint Estimator (MediaPipe Pose Engine).
Designed for PRAYOG-AI / Stellar HAR system for Bharatiya Antariksh Station (BAS) Experiments.

Exposes strictly 12 major body joints for real-time edge activity recognition,
with rack-relative coordinate normalization and temporal missing-data carry-forward.
"""

import logging
import numpy as np
import cv2

logger = logging.getLogger("PoseEstimator")

# Publicly exposed 12 major body joints (mapped from MediaPipe Pose landmark indices)
MAJOR_BODY_JOINTS = {
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle"
}

# Skeletal connections between the 12 major body joints for rendering
POSE_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"), ("right_knee", "right_ankle")
]


class PoseEstimator:
    """
    Tracks human major body pose keypoints for Stellar MVP activity recognition & HOI.
    
    Features:
    - Pretrained MediaPipe 2D Pose model filtered strictly to 12 major body joints.
    - Left/right wrist keypoint proxies for downstream hand position tracking.
    - Rack-relative coordinate normalization (mapping coordinates to payload rack ROI).
    - Temporal carry-forward for occluded/missing frames (Part 13 of SIH spec).
    - Skeleton landmark rendering for live GUI monitoring.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        max_carry_forward_frames: int = 5,
        rack_bounds: list = None
    ):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.max_carry_forward_frames = max_carry_forward_frames
        self.rack_bounds = rack_bounds  # [rx1, ry1, rx2, ry2] in pixels or normalized

        self._mp_pose = None
        self._pose_solution = None

        # Temporal smoothing / carry-forward state
        self._last_valid_result = None
        self._missing_frames_count = 0

        self._init_mediapipe()

    def _init_mediapipe(self):
        """Initialize MediaPipe Pose solution with explicit dependency check."""
        try:
            import mediapipe as mp
            self._mp_pose = mp.solutions.pose
            self._pose_solution = self._mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            logger.info("MediaPipe Pose solution initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Pose solution: {e}")
            raise RuntimeError(
                f"MediaPipe Pose initialization failed. Ensure 'mediapipe' is installed. Error: {e}"
            )

    def estimate_pose(self, frame: np.ndarray, rack_bounds: list = None) -> dict:
        """
        Run pose estimation on a single frame and return filtered 12-joint keypoints.

        Args:
            frame: OpenCV BGR image array (H, W, C).
            rack_bounds: Optional payload rack reference bounding box [x1, y1, x2, y2].

        Returns:
            Dict containing:
            - "detected": bool
            - "body_keypoints": dict containing ONLY the 12 major body joints
            - "hand_positions": quick lookup dict for left/right wrist proxies
            - "rack_relative_keypoints": keypoints normalized relative to payload rack
            - "body_bounds": [x1, y1, x2, y2] bounding box
            - "carried_forward": bool indicating if frame data was carried forward
            - "carry_count": int missing frame count
        """
        if frame is None or frame.size == 0:
            return self._handle_missing_detection()

        height, width = frame.shape[:2]
        effective_rack_bounds = rack_bounds or self.rack_bounds

        if self._pose_solution is not None:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_results = self._pose_solution.process(frame_rgb)

                if pose_results and pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark

                    # Expose ONLY the 12 major body joints
                    body_keypoints = {}
                    x_coords, y_coords = [], []

                    for idx, name in MAJOR_BODY_JOINTS.items():
                        if idx < len(landmarks):
                            lm = landmarks[idx]
                            px = int(lm.x * width)
                            py = int(lm.y * height)
                            body_keypoints[name] = {
                                "x": float(lm.x),
                                "y": float(lm.y),
                                "z": float(lm.z),
                                "visibility": float(lm.visibility),
                                "px": px,
                                "py": py
                            }
                            x_coords.append(px)
                            y_coords.append(py)

                    # Compute body bounding box from the 12 major joints
                    if x_coords and y_coords:
                        body_bounds = [
                            max(0, min(x_coords)),
                            max(0, min(y_coords)),
                            min(width, max(x_coords)),
                            min(height, max(y_coords))
                        ]
                    else:
                        body_bounds = [0, 0, 0, 0]

                    # Wrist proxy hand positions
                    hand_positions = self._extract_hand_positions(body_keypoints)

                    # Rack-relative coordinate normalization
                    rack_relative_kps = self._compute_rack_relative_keypoints(
                        body_keypoints, effective_rack_bounds, width, height
                    )

                    result = {
                        "detected": True,
                        "body_keypoints": body_keypoints,
                        "hand_positions": hand_positions,
                        "rack_relative_keypoints": rack_relative_kps,
                        "body_bounds": body_bounds,
                        "carried_forward": False,
                        "carry_count": 0
                    }

                    # Cache state for temporal carry-forward
                    self._last_valid_result = result
                    self._missing_frames_count = 0
                    return result

            except Exception as e:
                logger.error(f"Error during pose estimation: {e}")

        return self._handle_missing_detection()

    def _extract_hand_positions(self, body_kps: dict) -> dict:
        """Extract wrist keypoints from the 12 major body joints as hand proxies."""
        positions = {}
        for side in ["left", "right"]:
            wrist_name = f"{side}_wrist"
            if wrist_name in body_kps:
                wrist_pt = (body_kps[wrist_name]["px"], body_kps[wrist_name]["py"])
                positions[side] = {
                    "wrist": wrist_pt,
                    "contact_point": wrist_pt
                }
            else:
                positions[side] = None
        return positions

    def _compute_rack_relative_keypoints(self, body_kps: dict, rack_bounds: list, frame_w: int, frame_h: int) -> dict:
        """
        Normalize keypoint coordinates relative to payload rack bounding box.
        
        Maps keypoints relative to specified payload rack ROI [rx1, ry1, rx2, ry2].
        """
        if not rack_bounds or len(rack_bounds) < 4:
            rx1, ry1, rx2, ry2 = int(frame_w * 0.2), int(frame_h * 0.2), int(frame_w * 0.8), int(frame_h * 0.8)
        else:
            rx1, ry1, rx2, ry2 = rack_bounds

        rack_w = max(1, rx2 - rx1)
        rack_h = max(1, ry2 - ry1)

        rack_relative = {}
        for kp_name, kp in body_kps.items():
            rx_norm = (kp["px"] - rx1) / float(rack_w)
            ry_norm = (kp["py"] - ry1) / float(rack_h)
            rack_relative[kp_name] = {
                "rx": round(rx_norm, 4),
                "ry": round(ry_norm, 4),
                "in_rack": (0.0 <= rx_norm <= 1.0 and 0.0 <= ry_norm <= 1.0)
            }
        return rack_relative

    def _handle_missing_detection(self) -> dict:
        """Carry forward last confident pose estimates when frames are temporarily occluded."""
        self._missing_frames_count += 1
        if self._last_valid_result is not None and self._missing_frames_count <= self.max_carry_forward_frames:
            carried = dict(self._last_valid_result)
            carried["carried_forward"] = True
            carried["carry_count"] = self._missing_frames_count
            return carried

        return {
            "detected": False,
            "body_keypoints": {},
            "hand_positions": {"left": None, "right": None},
            "rack_relative_keypoints": {},
            "body_bounds": [0, 0, 0, 0],
            "carried_forward": False,
            "carry_count": self._missing_frames_count
        }

    def draw_landmarks(self, frame: np.ndarray, pose_results: dict, draw_rack_bounds: bool = True) -> np.ndarray:
        """
        Render the 12-joint body skeleton and rack reference frame on image.

        Args:
            frame: OpenCV BGR image array.
            pose_results: Dict returned by estimate_pose.
            draw_rack_bounds: Whether to draw payload rack reference frame.

        Returns:
            Annotated OpenCV BGR image array.
        """
        if frame is None or frame.size == 0 or not pose_results:
            return frame

        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Draw Payload Rack Reference Frame
        if draw_rack_bounds:
            rack_b = self.rack_bounds or [int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8)]
            rx1, ry1, rx2, ry2 = rack_b
            cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
            cv2.putText(
                annotated, "PAYLOAD RACK REF FRAME", (rx1 + 10, ry1 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1, cv2.LINE_AA
            )

        if not pose_results.get("detected", False) and not pose_results.get("carried_forward", False):
            return annotated

        body_kps = pose_results.get("body_keypoints", {})

        # Draw Skeletal Connections between the 12 major joints
        for joint_a, joint_b in POSE_CONNECTIONS:
            if joint_a in body_kps and joint_b in body_kps:
                pt_a = (body_kps[joint_a]["px"], body_kps[joint_a]["py"])
                pt_b = (body_kps[joint_b]["px"], body_kps[joint_b]["py"])

                line_color = (0, 255, 255) if pose_results.get("carried_forward") else (0, 255, 0)
                cv2.line(annotated, pt_a, pt_b, line_color, 2, cv2.LINE_AA)

        # Draw the 12 Joint Circles
        for kp_name, kp in body_kps.items():
            pt = (kp["px"], kp["py"])
            cv2.circle(annotated, pt, 5, (0, 0, 255), -1, cv2.LINE_AA)

        # Status text overlay
        status_txt = "POSE: TRACKING (12 JOINTS)"
        if pose_results.get("carried_forward"):
            status_txt = f"POSE: SMOOTHED (FRAME +{pose_results.get('carry_count')})"
        cv2.putText(
            annotated, status_txt, (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA
        )

        return annotated

    def close(self):
        """Release MediaPipe resources."""
        if self._pose_solution is not None:
            self._pose_solution.close()

