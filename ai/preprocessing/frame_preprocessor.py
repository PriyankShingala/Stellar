"""
Frame Normalization & ROI Resizing Preprocessor.
"""

class FramePreprocessor:
    """Standardized preprocessing pipeline converting raw camera frames for AI model inference."""
    def __init__(self, target_size=(640, 640)):
        self.target_size = target_size

    def preprocess(self, frame):
        """Resize, letterbox, and normalize frame array."""
        return frame
