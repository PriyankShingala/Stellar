"""
Deterministic Interaction Reasoner Engine.
Designed for PRAYOG-AI / Stellar HAR system for Bharatiya Antariksh Station (BAS) Experiments.

Target experiment: "Bottle and Glass Water Transfer".
Combines:
- 12 major body joints from PoseEstimator (using left/right wrists strictly as hand proxies)
- 'bottle' and 'glass' bounding boxes + confidence from ObjectDetector
- Temporal persistence to tolerate intermittent single-frame YOLO dropouts
- Explainable geometric rules for proximity, grasping, and pouring interaction detection.
"""

import math
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("InteractionReasoner")

# Geometric and Temporal Thresholds
DEFAULT_GRASP_THRESHOLD_PX = 65.0      # Maximum Euclidean distance (px) from wrist to bbox to count as grasp
MAX_MISSING_DETECTION_GRACE = 15       # Consecutive missing YOLO frames tolerated while object is held (approx 0.5-0.6s)
MIN_HELD_FRAMES_FOR_PICKUP = 2         # Consecutive proximity frames required to trigger pickup
MIN_SEPARATED_FRAMES_FOR_PUTDOWN = 3   # Consecutive separated frames required to trigger put down

# Pouring Geometry Thresholds
POUR_MAX_HORIZONTAL_DIST_PX = 120.0    # Stricter horizontal alignment tolerance (was 180.0)
POUR_TILT_MAX_ASPECT_RATIO = 1.10      # Stricter aspect ratio (h/w) <= 1.10 for true horizontal tilt (was 1.45)
MIN_POURING_FRAMES = 12                # Consecutive frames satisfying pouring geometry to emit event (approx 0.4s, was 2)


def point_to_bbox_distance(px: float, py: float, bbox: List[int]) -> float:
    """
    Calculate Euclidean distance from a 2D point (px, py) to the perimeter of an axis-aligned bbox.
    If the point is inside the bounding box, the distance is 0.0.

    Args:
        px: X coordinate of point.
        py: Y coordinate of point.
        bbox: [x1, y1, x2, y2] integer pixel coordinates.

    Returns:
        Euclidean distance in pixels.
    """
    x1, y1, x2, y2 = bbox
    dx = max(x1 - px, 0.0, px - x2)
    dy = max(y1 - py, 0.0, py - y2)
    return math.hypot(dx, dy)


def bbox_center(bbox: List[int]) -> Tuple[float, float]:
    """Return the center (cx, cy) of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def bbox_aspect_ratio(bbox: List[int]) -> float:
    """Return height / width aspect ratio of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    width = max(1.0, float(x2 - x1))
    height = max(1.0, float(y2 - y1))
    return height / width


class InteractionReasoner:
    """
    Deterministic rule-based reasoner detecting Hand-Object Interactions (HOI)
    and experiment event transitions for the 'Bottle and Glass Water Transfer' protocol.
    """

    def __init__(
        self,
        grasp_threshold_px: float = DEFAULT_GRASP_THRESHOLD_PX,
        missing_grace_frames: int = MAX_MISSING_DETECTION_GRACE,
        min_pouring_frames: int = MIN_POURING_FRAMES
    ):
        self.grasp_threshold_px = grasp_threshold_px
        self.missing_grace_frames = missing_grace_frames
        self.min_pouring_frames = min_pouring_frames

        # Internal state tracking per object
        self._objects: Dict[str, Dict[str, Any]] = {
            "bottle": self._init_object_state(),
            "glass": self._init_object_state()
        }

        # Pouring interaction tracker
        self._is_pouring = False
        self._consecutive_pouring_frames = 0
        
        # Sequence milestones for context-aware put-down
        self._milestones = {
            "poured": False,
            "glass_put_down": False
        }

    def _init_object_state(self) -> Dict[str, Any]:
        """Initialize tracking state dictionary for an object."""
        return {
            "state": "IDLE",            # "IDLE" | "HELD"
            "held_by": None,            # "left" | "right" | None
            "last_bbox": None,          # [x1, y1, x2, y2]
            "last_confidence": 0.0,
            "consecutive_close_frames": 0,
            "consecutive_separated_frames": 0,
            "missing_frames": 0,
            "wrist_distance": float("inf")
        }

    def reset(self):
        """Reset all internal state machines and history."""
        self._objects = {
            "bottle": self._init_object_state(),
            "glass": self._init_object_state()
        }
        self._is_pouring = False
        self._consecutive_pouring_frames = 0
        self._milestones = {
            "poured": False,
            "glass_put_down": False
        }
        logger.info("InteractionReasoner state reset successfully.")

    def update(self, pose_results: dict, object_detections: list) -> dict:
        """
        Process single-frame perception outputs and infer active states and transition events.

        Args:
            pose_results: Output dictionary from PoseEstimator.estimate_pose().
            object_detections: Output list of dicts from ObjectDetector.detect().

        Returns:
            Dictionary containing instantaneous events, persistent active states,
            detailed object interaction info, and spatial relations.
        """
        events: List[str] = []
        active_states: List[str] = []

        # 1. Extract Hand Positions (Wrists as proxies only)
        wrists = self._extract_wrists(pose_results)

        # 2. Map incoming YOLO detections by label (selecting most interaction-relevant candidate)
        detected_objects = self._filter_detections(object_detections, wrists)

        # 3. Update interaction state for 'bottle' and 'glass'
        for label in ["bottle", "glass"]:
            obj_det = detected_objects.get(label)
            obj_events, is_held = self._update_object_interaction(label, obj_det, wrists)
            events.extend(obj_events)
            if is_held:
                active_states.append(f"{label}_held")

        # 4. Check Pouring Condition
        pouring_event, pouring_active, spatial_info = self._evaluate_pouring()
        if pouring_event:
            events.append(pouring_event)
        if pouring_active:
            active_states.append("pouring")

        # 5. Build structured output payload
        return {
            "events": events,
            "active_states": active_states,
            "interactions": {
                "bottle": {
                    "state": self._objects["bottle"]["state"],
                    "held_by": self._objects["bottle"]["held_by"],
                    "wrist_distance": round(self._objects["bottle"]["wrist_distance"], 2),
                    "bbox": self._objects["bottle"]["last_bbox"],
                    "confidence": self._objects["bottle"]["last_confidence"]
                },
                "glass": {
                    "state": self._objects["glass"]["state"],
                    "held_by": self._objects["glass"]["held_by"],
                    "wrist_distance": round(self._objects["glass"]["wrist_distance"], 2),
                    "bbox": self._objects["glass"]["last_bbox"],
                    "confidence": self._objects["glass"]["last_confidence"]
                }
            },
            "spatial_relations": spatial_info,
            "diagnostics": {
                "bottle_close_frames": self._objects["bottle"]["consecutive_close_frames"],
                "glass_close_frames": self._objects["glass"]["consecutive_close_frames"],
                "pouring_consecutive_frames": self._consecutive_pouring_frames,
                "missing_yolo_frames": {
                    "bottle": self._objects["bottle"]["missing_frames"],
                    "glass": self._objects["glass"]["missing_frames"]
                }
            }
        }

    def _extract_wrists(self, pose_results: dict) -> Dict[str, Optional[Tuple[float, float]]]:
        """Extract left and right wrist pixel positions strictly as hand proxies."""
        wrists = {"left": None, "right": None}
        if not pose_results:
            return wrists

        body_kps = pose_results.get("body_keypoints", {})
        if "left_wrist" in body_kps:
            kp = body_kps["left_wrist"]
            wrists["left"] = (float(kp["px"]), float(kp["py"]))

        if "right_wrist" in body_kps:
            kp = body_kps["right_wrist"]
            wrists["right"] = (float(kp["px"]), float(kp["py"]))

        # Fallback to hand_positions if body_keypoints format is abbreviated
        if wrists["left"] is None or wrists["right"] is None:
            hand_pos = pose_results.get("hand_positions", {})
            if wrists["left"] is None and hand_pos.get("left"):
                wrists["left"] = (float(hand_pos["left"][0]), float(hand_pos["left"][1]))
            if wrists["right"] is None and hand_pos.get("right"):
                wrists["right"] = (float(hand_pos["right"][0]), float(hand_pos["right"][1]))

        return wrists

    def _filter_detections(
        self,
        detections: list,
        wrists: Optional[Dict[str, Optional[Tuple[float, float]]]] = None
    ) -> Dict[str, dict]:
        """
        Select the most interaction-relevant detection per label ('bottle', 'glass').
        Prioritizes:
        1. Closest to holding hand if currently HELD.
        2. Closest to previous tracked position if previously tracked (spatial continuity).
        3. Highest confidence score.
        """
        if not detections:
            return {}

        wrists = wrists or {}
        by_label: Dict[str, List[dict]] = {"bottle": [], "glass": []}
        for det in detections:
            lbl = det.get("label")
            if lbl in by_label:
                by_label[lbl].append(det)

        filtered = {}
        for label, candidates in by_label.items():
            if not candidates:
                continue

            if len(candidates) == 1:
                filtered[label] = candidates[0]
                continue

            obj = self._objects[label]
            # 1. If currently HELD, select candidate closest to holding hand
            if obj["state"] == "HELD" and obj["held_by"] and wrists.get(obj["held_by"]):
                w_pos = wrists[obj["held_by"]]
                best = min(
                    candidates,
                    key=lambda c: point_to_bbox_distance(w_pos[0], w_pos[1], c["bbox"])
                )
                filtered[label] = best
            # 2. If previously tracked, select candidate closest to last known position
            elif obj["last_bbox"] is not None:
                prev_cx, prev_cy = bbox_center(obj["last_bbox"])
                best = min(
                    candidates,
                    key=lambda c: math.hypot(
                        bbox_center(c["bbox"])[0] - prev_cx,
                        bbox_center(c["bbox"])[1] - prev_cy
                    )
                )
                filtered[label] = best
            # 3. Fallback: select highest confidence
            else:
                best = max(candidates, key=lambda c: c.get("confidence", 0.0))
                filtered[label] = best

        return filtered

    def _update_object_interaction(
        self,
        label: str,
        detection: Optional[dict],
        wrists: Dict[str, Optional[Tuple[float, float]]]
    ) -> Tuple[List[str], bool]:
        """Update finite state machine for a single object based on wrist distances and persistence."""
        events: List[str] = []
        obj = self._objects[label]

        # Determine closest wrist
        closest_hand = None
        min_dist = float("inf")

        active_bbox = detection["bbox"] if detection else obj["last_bbox"]

        if active_bbox is not None:
            for hand in ["left", "right"]:
                w_pos = wrists.get(hand)
                if w_pos is not None:
                    d = point_to_bbox_distance(w_pos[0], w_pos[1], active_bbox)
                    if d < min_dist:
                        min_dist = d
                        closest_hand = hand

        obj["wrist_distance"] = min_dist

        # Case A: Object was actively detected by YOLO in current frame
        if detection is not None:
            obj["last_bbox"] = detection["bbox"]
            obj["last_confidence"] = detection.get("confidence", 0.0)
            obj["missing_frames"] = 0

            if min_dist <= self.grasp_threshold_px:
                obj["consecutive_close_frames"] += 1
                obj["consecutive_separated_frames"] = 0

                if obj["state"] == "IDLE" and obj["consecutive_close_frames"] >= MIN_HELD_FRAMES_FOR_PICKUP:
                    obj["state"] = "HELD"
                    obj["held_by"] = closest_hand
                    events.append(f"{label}_pickup")
                    logger.info(f"Event triggered: {label}_pickup by {closest_hand} hand (dist={min_dist:.1f}px)")
                elif obj["state"] == "HELD":
                    if closest_hand is not None:
                        obj["held_by"] = closest_hand
            else:
                obj["consecutive_separated_frames"] += 1
                obj["consecutive_close_frames"] = 0

                if obj["state"] == "HELD" and obj["consecutive_separated_frames"] >= MIN_SEPARATED_FRAMES_FOR_PUTDOWN:
                    obj["state"] = "IDLE"
                    obj["held_by"] = None
                    events.append(f"{label}_put_down")
                    if label == "glass":
                        self._milestones["glass_put_down"] = True
                    logger.info(f"Event triggered: {label}_put_down (wrist moved away: dist={min_dist:.1f}px)")

        # Case B: Object was NOT detected by YOLO in current frame (dropout / occlusion)
        else:
            if obj["state"] == "HELD":
                obj["missing_frames"] += 1
                # If within grace period, keep held status (temporal carry-forward)
                if obj["missing_frames"] <= self.missing_grace_frames:
                    obj["consecutive_close_frames"] += 1
                else:
                    # Grace period expired without recovery:
                    obj["state"] = "IDLE"
                    obj["held_by"] = None
                    
                    if label == "glass" and self._milestones.get("poured"):
                        events.append("glass_put_down")
                        self._milestones["glass_put_down"] = True
                        logger.info(f"Event triggered: glass_put_down (stable disappearance after pouring)")
                    elif label == "bottle" and self._milestones.get("glass_put_down"):
                        events.append("bottle_put_down")
                        logger.info(f"Event triggered: bottle_put_down (stable disappearance after glass_put_down)")
                    else:
                        logger.info(
                            f"Object tracking lost: {label} (YOLO detection missing for {obj['missing_frames']} frames; NO put_down emitted)"
                        )
            else:
                obj["consecutive_close_frames"] = 0
                obj["missing_frames"] += 1

        is_held = (obj["state"] == "HELD")
        return events, is_held

    def _evaluate_pouring(self) -> Tuple[Optional[str], bool, dict]:
        """
        Evaluate geometric and spatial conditions for water pouring interaction.
        Requires:
        1. Bottle is held by a hand.
        2. Glass is present in workspace (fresh or cached).
        3. Bottle center is strictly above glass center (b_cy < g_cy).
        4. Bottle top is strictly above glass top (b_bbox[1] < g_bbox[1]).
        5. Horizontal proximity between bottle and glass is within pouring range (<= 120px).
        6. Bottle bounding box exhibits true horizontal tilt aspect ratio (h/w <= 1.10).
        7. Conditions sustained for min_pouring_frames (approx 12 frames).
        """
        bottle = self._objects["bottle"]
        glass = self._objects["glass"]

        spatial_info = {
            "bottle_glass_distance": None,
            "bottle_above_glass": False,
            "bottle_aspect_ratio": None,
            "is_tilted": False,
            "is_pouring_geometry": False
        }

        # 1. Bottle must be held
        if bottle["state"] != "HELD" or bottle["last_bbox"] is None:
            self._consecutive_pouring_frames = 0
            self._is_pouring = False
            return None, False, spatial_info

        # 2. Glass must be present (fresh or cached within 6 frames of dropout)
        if glass["last_bbox"] is None or glass["missing_frames"] > 6:
            self._consecutive_pouring_frames = 0
            self._is_pouring = False
            return None, False, spatial_info

        b_bbox = bottle["last_bbox"]
        g_bbox = glass["last_bbox"]

        b_cx, b_cy = bbox_center(b_bbox)
        g_cx, g_cy = bbox_center(g_bbox)

        # Horizontal distance between bottle and glass centers
        horiz_dist = abs(b_cx - g_cx)
        spatial_info["bottle_glass_distance"] = round(math.hypot(b_cx - g_cx, b_cy - g_cy), 2)

        # Vertical check:
        # Bottle center must be strictly above glass center (b_cy < g_cy)
        # AND bottle top strictly above glass top (b_bbox[1] < g_bbox[1])
        bottle_above = (b_cy < g_cy) and (b_bbox[1] < g_bbox[1])
        spatial_info["bottle_above_glass"] = bottle_above

        # Tilt check: Aspect ratio (h/w) drops when bottle tilts horizontally (h/w <= 1.10)
        ar = bbox_aspect_ratio(b_bbox)
        spatial_info["bottle_aspect_ratio"] = round(ar, 3)
        is_tilted = (ar <= POUR_TILT_MAX_ASPECT_RATIO)
        spatial_info["is_tilted"] = is_tilted

        # Combined Pouring Geometry Check
        is_pouring_geom = (
            bottle_above and
            (horiz_dist <= POUR_MAX_HORIZONTAL_DIST_PX) and
            is_tilted
        )
        spatial_info["is_pouring_geometry"] = is_pouring_geom

        event = None
        if is_pouring_geom:
            self._consecutive_pouring_frames += 1
            if self._consecutive_pouring_frames >= self.min_pouring_frames:
                if not self._is_pouring:
                    self._is_pouring = True
                    event = "pouring"
                    self._milestones["poured"] = True
                    logger.info(
                        f"Event triggered: pouring (bottle tilted over glass for {self._consecutive_pouring_frames} frames)"
                    )
        else:
            self._consecutive_pouring_frames = 0
            self._is_pouring = False

        return event, self._is_pouring, spatial_info

