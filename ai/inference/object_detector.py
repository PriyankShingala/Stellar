"""
Experiment Object Detector (Ultralytics YOLOv8n Engine).
Designed for PRAYOG-AI / Stellar HAR system for Bharatiya Antariksh Station (BAS) Experiments.

Target experiment: "Bottle and Glass Water Transfer".
Detects experiment-relevant objects ("bottle" and "glass") and exposes bounding boxes and confidence scores.
"""

import logging
import os
import numpy as np
import cv2

logger = logging.getLogger("ObjectDetector")

from typing import Optional

# Explicit mapping from COCO dataset class IDs to unified Stellar MVP object labels
# COCO Class 39: bottle      -> Stellar "bottle"
# COCO Class 40: wine glass -> Stellar "glass"
# COCO Class 41: cup        -> Stellar "glass"
# COCO Class 45: bowl       -> Stellar "glass" (fallback for tumblers, wide cups/glasses)
# COCO Class 75: vase       -> Stellar "glass" (fallback for tall glassware / carafes)
COCO_TO_STELLAR_MAPPING = {
    39: "bottle",
    40: "glass",
    41: "glass",
    45: "glass",
    75: "glass"
}


def compute_iou(box1: list, box2: list) -> float:
    """Calculate Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0

    area1 = max(1, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(1, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - intersection

    return intersection / float(union)


class ObjectDetector:
    """
    Lightweight object detector targeting experiment objects ("bottle" and "glass").
    
    Features:
    - Pretrained Ultralytics YOLOv8n model filtered strictly to Stellar experiment labels.
    - Unified label mapping: COCO "bottle" -> "bottle", COCO "cup"/"wine glass" -> "glass".
    - Output schema: [{'label': str, 'bbox': [x1, y1, x2, y2], 'confidence': float}].
    - Bounding box rendering helper for live GUI monitoring and visual validation.
    """

    def __init__(
        self,
        model_path: str = "ai/models/object_detection/yolov8n.pt",
        conf_threshold: float = 0.20,
        glass_conf_threshold: Optional[float] = None,
        bottle_conf_threshold: Optional[float] = None,
        bottle_persistence_frames: int = 15,
        glass_persistence_frames: int = 15,
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.glass_conf_threshold = glass_conf_threshold if glass_conf_threshold is not None else conf_threshold
        self.bottle_conf_threshold = bottle_conf_threshold if bottle_conf_threshold is not None else conf_threshold
        self.bottle_persistence_frames = bottle_persistence_frames
        self.glass_persistence_frames = glass_persistence_frames
        
        self.model = None
        
        # Temporal persistence
        self._last_bottle_det = None
        self._bottle_missing_frames = 0
        self._last_glass_det = None
        self._glass_missing_frames = 0
        
        self._init_model()

    def _init_model(self):
        """Initialize YOLOv8 object detector with fallback handling for weight locations."""
        try:
            from ultralytics import YOLO

            # Check primary model path, fallback to default 'yolov8n.pt'
            target_weights = self.model_path
            if not os.path.exists(target_weights):
                root_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "yolov8n.pt"))
                if os.path.exists(root_weights):
                    target_weights = root_weights
                elif os.path.exists("yolov8n.pt"):
                    target_weights = "yolov8n.pt"
                else:
                    target_weights = "yolov8n.pt"

            self.model = YOLO(target_weights)
            logger.info(f"Object Detector initialized successfully with weights: {target_weights}")

        except Exception as e:
            logger.error(f"Failed to initialize YOLO Object Detector: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> list:
        """
        Run object detection on a single frame and return filtered 'bottle' & 'glass' detections.

        Args:
            frame: OpenCV BGR image array (H, W, C).

        Returns:
            List of dicts:
            [
                {
                    "label": "bottle" | "glass",
                    "bbox": [x1, y1, x2, y2],  # integer pixel coordinates
                    "confidence": float
                }
            ]
        """
        if frame is None or frame.size == 0 or self.model is None:
            return []

        detections = []
        try:
            # Run inference with filtering for COCO classes [39, 40, 41]
            min_conf = min(self.glass_conf_threshold, self.bottle_conf_threshold)
            results = self.model(
                frame,
                verbose=False,
                conf=min_conf,
                classes=list(COCO_TO_STELLAR_MAPPING.keys())
            )

            if results and len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    stellar_label = COCO_TO_STELLAR_MAPPING.get(cls_id)
                    conf = float(box.conf[0].item())

                    if stellar_label == "glass" and conf < self.glass_conf_threshold:
                        continue
                    if stellar_label == "bottle" and conf < self.bottle_conf_threshold:
                        continue

                    if stellar_label:
                        if hasattr(box.xyxy[0], "cpu"):
                            xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        elif hasattr(box.xyxy[0], "numpy"):
                            xyxy = box.xyxy[0].numpy().astype(int).tolist()
                        else:
                            xyxy = np.array(box.xyxy[0]).astype(int).tolist()
                        detections.append({
                            "label": stellar_label,
                            "bbox": xyxy,  # [x1, y1, x2, y2]
                            "confidence": round(conf, 4)
                        })

        except Exception as e:
            logger.error(f"Error during object detection inference: {e}")

        # Handle bottle temporal persistence
        bottle_detected = any(d["label"] == "bottle" for d in detections)
        if bottle_detected:
            best_bottle = max([d for d in detections if d["label"] == "bottle"], key=lambda x: x["confidence"])
            self._last_bottle_det = best_bottle.copy()
            self._bottle_missing_frames = 0
        else:
            if self._last_bottle_det is not None:
                self._bottle_missing_frames += 1
                if self._bottle_missing_frames <= self.bottle_persistence_frames:
                    detections.append(self._last_bottle_det.copy())
                else:
                    self._last_bottle_det = None

        # Handle glass temporal persistence
        glass_detected = any(d["label"] == "glass" for d in detections)
        if glass_detected:
            best_glass = max([d for d in detections if d["label"] == "glass"], key=lambda x: x["confidence"])
            self._last_glass_det = best_glass.copy()
            self._glass_missing_frames = 0
        else:
            if self._last_glass_det is not None:
                self._glass_missing_frames += 1
                if self._glass_missing_frames <= self.glass_persistence_frames:
                    detections.append(self._last_glass_det.copy())
                else:
                    self._last_glass_det = None

        # Intra-class IoU deduplication (suppress duplicate overlapping glass/bottle boxes)
        if len(detections) > 1:
            detections.sort(key=lambda d: d.get("confidence", 0.0), reverse=True)
            suppressed = []
            for det in detections:
                keep = True
                for accepted in suppressed:
                    if det["label"] == accepted["label"]:
                        iou = compute_iou(det["bbox"], accepted["bbox"])
                        if iou > 0.35:
                            keep = False
                            break
                if keep:
                    suppressed.append(det)
            detections = suppressed

        return detections

    def draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """
        Render bounding boxes, object labels, and confidence scores onto an image frame.

        Args:
            frame: OpenCV BGR image array.
            detections: List of detection dicts returned by detect().

        Returns:
            Annotated OpenCV BGR image array.
        """
        if frame is None or frame.size == 0 or not detections:
            return frame

        annotated = frame.copy()
        color_map = {
            "bottle": (0, 255, 255),  # Yellow
            "glass": (255, 165, 0)    # Cyan / Blue-Orange
        }

        for det in detections:
            label = det["label"]
            bbox = det["bbox"]
            conf = det["confidence"]
            color = color_map.get(label, (0, 255, 0))

            x1, y1, x2, y2 = bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            caption = f"{label.upper()}: {conf:.2f}"
            cv2.putText(
                annotated, caption, (x1, max(15, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA
            )

        return annotated

