"""
Unit tests for Experiment Object Detector (YOLOv8n).
"""

import unittest
import numpy as np
import cv2
from ai.inference.object_detector import ObjectDetector, COCO_TO_STELLAR_MAPPING


class TestObjectDetector(unittest.TestCase):

    def setUp(self):
        self.detector = ObjectDetector(conf_threshold=0.5)
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_coco_mapping_table(self):
        """Verify COCO class ID mapping to unified Stellar labels."""
        self.assertEqual(COCO_TO_STELLAR_MAPPING.get(39), "bottle")
        self.assertEqual(COCO_TO_STELLAR_MAPPING.get(40), "glass")
        self.assertEqual(COCO_TO_STELLAR_MAPPING.get(41), "glass")
        # Ensure only bottle and glass are mapped
        stellar_labels = set(COCO_TO_STELLAR_MAPPING.values())
        self.assertEqual(stellar_labels, {"bottle", "glass"})

    def test_object_detector_initialization(self):
        """Verify ObjectDetector initializes with configured confidence threshold."""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.conf_threshold, 0.5)

    def test_detect_schema(self):
        """Verify detect() returns a list of dictionaries with correct keys."""
        detections = self.detector.detect(self.dummy_frame)
        self.assertIsInstance(detections, list)
        for det in detections:
            self.assertIn("label", det)
            self.assertIn("bbox", det)
            self.assertIn("confidence", det)
            self.assertIn(det["label"], {"bottle", "glass"})
            self.assertEqual(len(det["bbox"]), 4)

    def test_draw_detections(self):
        """Verify draw_detections renders bounding boxes without errors."""
        sample_detections = [
            {"label": "bottle", "bbox": [100, 100, 200, 300], "confidence": 0.88},
            {"label": "glass", "bbox": [250, 150, 350, 280], "confidence": 0.79}
        ]
        annotated = self.detector.draw_detections(self.dummy_frame, sample_detections)
        self.assertEqual(annotated.shape, self.dummy_frame.shape)
        # Verify drawing modified image pixels
        self.assertGreater(np.sum(annotated), 0)


if __name__ == "__main__":
    unittest.main()
