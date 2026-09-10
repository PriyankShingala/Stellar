"""
Spatial-Temporal Action & Activity Classifier.
"""

import logging

logger = logging.getLogger("ActionClassifier")

class ActionClassifier:
    """Classifies spatial-temporal atomic actions (e.g. 'picking vial', 'pipetting', 'capping vial')."""
    def __init__(self, model_path: str = "ai/models/action_recognition/action_model.pt"):
        self.model_path = model_path
        logger.info("Action Classifier initialized.")

    def classify_action(self, pose_sequence, object_interactions):
        """
        Infer high-level human activity from spatial-temporal feature window.
        """
        return {"action_name": "IDLE", "confidence": 1.0}
