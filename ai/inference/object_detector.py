"""
Lab Equipment & Tool Object Detector (YOLO/ONNX).
"""

import logging

logger = logging.getLogger("ObjectDetector")

class ObjectDetector:
    """Detects lab tools, consumables, vials, and equipment in video frames."""
    def __init__(self, model_path: str = "ai/models/object_detection/lab_tools.pt", conf_threshold: float = 0.5):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        logger.info(f"Object Detector initialized with model: {model_path}")

    def detect(self, frame):
        """
        Run inference on frame.
        Returns list of detected bounding boxes: [{'label': 'vial', 'bbox': [x1, y1, x2, y2], 'confidence': 0.92}]
        """
        return []
