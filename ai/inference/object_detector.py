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

# Explicit mapping from COCO dataset class IDs to unified Stellar MVP object labels
# COCO Class 39: bottle      -> Stellar "bottle"
# COCO Class 40: wine glass -> Stellar "glass"
# COCO Class 41: cup        -> Stellar "glass"
COCO_TO_STELLAR_MAPPING = {
    39: "bottle",
    40: "glass",
    41: "glass"
}


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
        conf_threshold: float = 0.5
    ):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self._init_model()

    def _init_model(self):
        """Initialize YOLOv8 object detector with fallback handling for weight locations."""
        try:
            from ultralytics import YOLO

            # Check primary model path, fallback to default 'yolov8n.pt'
            target_weights = self.model_path
            if not os.path.exists(target_weights):
                alt_weights = "yolov8n.pt"
                logger.info(f"Primary model path '{target_weights}' not found locally. Trying '{alt_weights}'...")
                target_weights = alt_weights

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
            results = self.model(
                frame,
                verbose=False,
                conf=self.conf_threshold,
                classes=list(COCO_TO_STELLAR_MAPPING.keys())
            )

            if results and len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    stellar_label = COCO_TO_STELLAR_MAPPING.get(cls_id)

                    if stellar_label:
                        xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                        conf = float(box.conf[0].item())
                        detections.append({
                            "label": stellar_label,
                            "bbox": xyxy,  # [x1, y1, x2, y2]
                            "confidence": round(conf, 4)
                        })

        except Exception as e:
            logger.error(f"Error during object detection inference: {e}")

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

