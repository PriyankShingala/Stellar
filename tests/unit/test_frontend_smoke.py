"""
Unit / Smoke tests for Stellar AI PySide6 Frontend.
Verifies widget construction, navigation routing, glassmorphism design integration,
and offscreen layout stability.
"""

import os
import sys
import unittest
import numpy as np

# Force offscreen rendering for headless CI / unit testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from frontend.app import MainWindow
from frontend.styles.theme import GLOBAL_QSS


class TestFrontendSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
        cls.app.setStyleSheet(GLOBAL_QSS)

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        if self.window:
            self.window.close()

    def test_main_window_structure(self):
        """Verify MainWindow initializes with sidebar, top bar, and 6 views."""
        self.assertIn("Stellar AI", self.window.windowTitle())
        self.assertIsNotNone(self.window.sidebar)
        self.assertIsNotNone(self.window.top_bar)
        self.assertIsNotNone(self.window.stacked_widget)
        self.assertEqual(self.window.stacked_widget.count(), 6)

    def test_navigation_routing(self):
        """Verify navigation through all 6 pages."""
        for idx in range(6):
            self.window._navigate_to(idx)
            self.assertEqual(self.window.stacked_widget.currentIndex(), idx)

    def test_live_monitor_widgets(self):
        """Verify LiveMonitorView contains timeline with 5 steps, video viewport, and guidance."""
        live_view = self.window.live_monitor_view
        self.assertEqual(len(live_view.timeline.nodes), 5)
        self.assertIsNotNone(live_view.viewport)
        self.assertIsNotNone(live_view.guidance_card)
        self.assertIsNotNone(live_view.hoi_card)
        self.assertIsNotNone(live_view.compliance_card)

    def test_live_monitor_frame_update_safe(self):
        """Verify frame update does not crash with simulated QImage and telemetry."""
        # Create a blank RGB image
        img_data = np.zeros((480, 640, 3), dtype=np.uint8)
        h, w, ch = img_data.shape
        qimg = QImage(img_data.data, w, h, ch * w, QImage.Format_RGB888).copy()

        telemetry = {
            "pose": {"detected": True, "landmarks": {}},
            "objects": [{"class_id": 39, "class_name": "bottle", "confidence": 0.85, "bbox": [10, 10, 50, 50]}],
            "reasoner": {
                "held_objects": {"left": None, "right": "bottle"},
                "proximity_matrix": {"bottle": [0.05, 0.05]},
                "is_pouring": False
            },
            "validator": {
                "steps": [
                    {"step_number": 1, "step_id": "STEP_BOTTLE_PICKUP", "action_name": "bottle_pickup", "status": "COMPLETED"},
                    {"step_number": 2, "step_id": "STEP_GLASS_PICKUP", "action_name": "glass_pickup", "status": "IN_PROGRESS"},
                ],
                "current_step": {"step_number": 2, "action_name": "glass_pickup"},
                "is_completed": False
            },
            "fps": 28.5
        }

        # Should execute cleanly without error
        self.window.live_monitor_view.update_frame(qimg, telemetry)
        self.assertEqual(self.window.live_monitor_view.fps_label.text(), "FPS: 28.5")
        self.assertIn("12 Joints Tracked", self.window.live_monitor_view.pose_status_label.text())


if __name__ == "__main__":
    unittest.main()
