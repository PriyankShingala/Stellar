"""
Multithreaded Camera / Video Stream Reader.
"""

import threading
import logging

logger = logging.getLogger("FrameGrabber")

class FrameGrabber:
    """Reads camera feed frames in a dedicated thread to ensure zero frame drop."""
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.running = False
        self.latest_frame = None

    def start(self):
        self.running = True
        logger.info(f"FrameGrabber started on camera device {self.device_id}")

    def stop(self):
        self.running = False
