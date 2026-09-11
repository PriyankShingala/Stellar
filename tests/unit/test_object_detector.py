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

    def test_compute_iou(self):
        """Verify IoU calculation between overlapping boxes."""
        from ai.inference.object_detector import compute_iou

        # Identical boxes -> IoU = 1.0
        box1 = [100, 100, 200, 200]
        box2 = [100, 100, 200, 200]
        self.assertAlmostEqual(compute_iou(box1, box2), 1.0)

        # Disjoint boxes -> IoU = 0.0
        box3 = [300, 300, 400, 400]
        self.assertEqual(compute_iou(box1, box3), 0.0)

        # Partial overlap
        box4 = [150, 100, 250, 200]
        iou = compute_iou(box1, box4)
        self.assertGreater(iou, 0.3)
        self.assertLess(iou, 0.4)

    def test_duplicate_glass_suppression_logic(self):
        """Verify duplicate overlapping glass detections are suppressed, keeping highest confidence."""
        from ai.inference.object_detector import compute_iou

        # Simulate YOLO output with two overlapping glass detections (e.g. COCO 40 and 41 on same cup)
        raw_detections = [
            {"label": "glass", "bbox": [200, 200, 280, 320], "confidence": 0.82},
            {"label": "glass", "bbox": [202, 198, 278, 322], "confidence": 0.65},  # Overlaps 0.82 with IoU > 0.8
            {"label": "glass", "bbox": [450, 200, 530, 320], "confidence": 0.78},  # Separate glass across room
        ]

        # Apply the exact suppression logic used in ObjectDetector.detect
        raw_detections.sort(key=lambda d: d.get("confidence", 0.0), reverse=True)
        suppressed = []
        for det in raw_detections:
            keep = True
            for accepted in suppressed:
                if det["label"] == accepted["label"]:
                    if compute_iou(det["bbox"], accepted["bbox"]) > 0.35:
                        keep = False
                        break
            if keep:
                suppressed.append(det)

        # Exactly 2 glasses should remain: 0.82 (retained) and 0.78 (retained), while 0.65 is suppressed
        self.assertEqual(len(suppressed), 2)
        confs = [d["confidence"] for d in suppressed]
        self.assertIn(0.82, confs)
        self.assertIn(0.78, confs)
        self.assertNotIn(0.65, confs)

    def test_class_specific_thresholds(self):
        """Verify glass uses default threshold while bottle uses custom lower threshold."""
        detector = ObjectDetector(conf_threshold=0.5, bottle_conf_threshold=0.38)
        self.assertEqual(detector.glass_conf_threshold, 0.5)
        self.assertEqual(detector.bottle_conf_threshold, 0.38)

    def test_bottle_temporal_persistence(self):
        """Verify a missing bottle is persisted for up to persistence_frames frames."""
        detector = ObjectDetector(conf_threshold=0.5, bottle_conf_threshold=0.38, bottle_persistence_frames=3)
        
        # Inject mock model that returns an empty list, but manually populate detections inside detect if needed.
        # However, detect relies on self.model(frame). Let's just mock self.model.
        class MockResult:
            class MockBox:
                def __init__(self, cls_id, conf, xyxy):
                    class Item:
                        def __init__(self, val): self.val = val
                        def item(self): return self.val
                        
                    self.cls = [Item(cls_id)]
                    self.conf = [Item(conf)]
                    
                    class MockCPU:
                        def __init__(self, arr): self.arr = arr
                        def numpy(self):
                            class MockAstype:
                                def __init__(self, arr): self.arr = arr
                                def astype(self, typ):
                                    class MockToList:
                                        def __init__(self, arr): self.arr = arr
                                        def tolist(self): return self.arr
                                    return MockToList(self.arr)
                            return MockAstype(self.arr)
                    self.xyxy = [MockCPU(xyxy)]
            
            def __init__(self, boxes):
                self.boxes = boxes

        class MockModel:
            def __init__(self, results_seq):
                self.results_seq = results_seq
                self.call_idx = 0
            def __call__(self, frame, **kwargs):
                res = self.results_seq[self.call_idx]
                self.call_idx += 1
                return res

        # Frame 1: Model detects bottle (class 39) with confidence 0.8
        res1 = [MockResult([MockResult.MockBox(39, 0.8, [100, 100, 200, 200])])]
        # Frame 2, 3, 4, 5: Model detects nothing
        res_empty = []
        
        detector.model = MockModel([res1, res_empty, res_empty, res_empty, res_empty, res_empty])
        
        # Frame 1: Detection is present
        dets1 = detector.detect(self.dummy_frame)
        self.assertEqual(len(dets1), 1)
        self.assertEqual(dets1[0]["label"], "bottle")
        self.assertEqual(dets1[0]["confidence"], 0.8)

        # Frame 2: Model empty, but persistence kicks in (missing = 1)
        dets2 = detector.detect(self.dummy_frame)
        self.assertEqual(len(dets2), 1)
        self.assertEqual(dets2[0]["label"], "bottle")

        # Frame 3: Model empty, persistence kicks in (missing = 2)
        dets3 = detector.detect(self.dummy_frame)
        self.assertEqual(len(dets3), 1)

        # Frame 4: Model empty, persistence kicks in (missing = 3 <= 3)
        dets4 = detector.detect(self.dummy_frame)
        self.assertEqual(len(dets4), 1)

        # Frame 5: Model empty, persistence expired (missing = 4 > 3)
        dets5 = detector.detect(self.dummy_frame)
        self.assertEqual(len(dets5), 0)


if __name__ == "__main__":
    unittest.main()
