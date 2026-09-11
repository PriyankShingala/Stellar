"""
Pipeline Controller for Stellar AI.
Runs PoseEstimator, ObjectDetector, InteractionReasoner, and SequenceValidator on a background QThread.
Emits real-time QImage frames and structured telemetry to the UI layer with zero lag.
"""

import time
import logging
import cv2
import numpy as np
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage

from ai.inference.pose_estimator import PoseEstimator
from ai.inference.object_detector import ObjectDetector
from ai.inference.interaction_reasoner import InteractionReasoner
from ai.sequence_validator.sequence_validator import SequenceValidator

logger = logging.getLogger("PipelineController")


class PipelineWorker(QThread):
    """Worker thread running camera capture and the 4 AI perception/reasoning stages."""

    frame_ready = Signal(QImage, dict)
    step_advanced = Signal(dict)
    deviation_detected = Signal(dict)
    mission_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._is_running = True
        self._completed_emitted = False

        # Instantiate AI Core components
        self.pose_estimator = None
        self.object_detector = None
        self.interaction_reasoner = None
        self.sequence_validator = None

    def _get_validator_state(self) -> dict:
        """Extract comprehensive serializable state from SequenceValidator."""
        if not self.sequence_validator:
            return {}

        sm = self.sequence_validator.state_machine
        step_states = sm.get_step_states()
        steps_info = []
        for s in sm.steps:
            sid = s["step_id"]
            st = step_states.get(sid, "PENDING")
            steps_info.append({
                "step_number": s["step_number"],
                "step_id": sid,
                "action_name": s["action_name"],
                "status": st
            })

        return {
            "protocol_id": sm.protocol_id,
            "title": sm.title,
            "current_step_index": sm.current_step_index,
            "current_step": sm.get_current_step(),
            "is_completed": sm.is_completed(),
            "step_states": step_states,
            "steps": steps_info
        }

    def reset_protocol(self):
        """Reset the sequence validator and reasoner."""
        if self.sequence_validator:
            self.sequence_validator.reset()
        if self.interaction_reasoner:
            self.interaction_reasoner.reset()
        self._completed_emitted = False
        logger.info("Pipeline models reset to initial protocol state.")

    def stop(self):
        """Signal thread to stop."""
        self._is_running = False

    def run(self):
        """Main camera ingestion and inference loop."""
        logger.info(f"Initializing AI Pipeline on Camera {self.camera_index}...")

        try:
            self.pose_estimator = PoseEstimator(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.object_detector = ObjectDetector(conf_threshold=0.25)
            self.interaction_reasoner = InteractionReasoner()
            self.sequence_validator = SequenceValidator()
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.error_occurred.emit(f"Model initialization error: {str(e)}")
            return

        # Open webcam
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            err_msg = f"Camera {self.camera_index} could not be opened. Verify device is connected."
            logger.error(err_msg)
            self.error_occurred.emit(err_msg)
            return

        # Proven 5-frame warm-up
        logger.info("Warming up camera sensor (5 frames)...")
        for _ in range(5):
            ret, _ = cap.read()
            if not ret:
                err_msg = f"Camera {self.camera_index} failed to deliver warm-up frames."
                logger.error(err_msg)
                self.error_occurred.emit(err_msg)
                cap.release()
                return

        logger.info("Camera warm-up complete. Pipeline active.")
        fps_prev_time = time.time()

        try:
            while self._is_running:
                loop_start = time.time()
                ret, frame = cap.read()

                if not ret or frame is None:
                    err_msg = "Invalid or empty camera frame received. Terminating stream."
                    logger.warning(err_msg)
                    self.error_occurred.emit(err_msg)
                    break

                # 1. Pose Landmark Estimation
                pose_results = self.pose_estimator.estimate_pose(frame)

                # 2. Object Detection (YOLOv8n)
                object_detections = self.object_detector.detect(frame)

                # 3. Deterministic Interaction Reasoning
                reasoner_output = self.interaction_reasoner.update(pose_results, object_detections)

                # 4. SOP Sequence Validation
                validator_events = self.sequence_validator.process_interaction(reasoner_output)

                # Calculate instantaneous FPS
                elapsed = time.time() - loop_start
                fps = 1.0 / max(elapsed, 1e-4)

                # Prepare annotated frame for UI visualization
                display_frame = frame.copy()
                self.pose_estimator.draw_landmarks(display_frame, pose_results, draw_rack_bounds=False)
                self.object_detector.draw_detections(display_frame, object_detections)

                # Convert BGR OpenCV image to QImage
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

                val_state = self._get_validator_state()

                # Dispatch telemetry package
                telemetry = {
                    "pose": pose_results,
                    "objects": object_detections,
                    "reasoner": reasoner_output,
                    "validator": val_state,
                    "events": validator_events,
                    "fps": fps
                }
                self.frame_ready.emit(q_image, telemetry)

                # Event dispatching
                for res in validator_events:
                    if res.get("valid") is True:
                        self.step_advanced.emit(res)
                    elif res.get("deviation_type") not in ("NONE", None):
                        self.deviation_detected.emit(res)

                # Mission completion trigger
                if val_state.get("is_completed") and not self._completed_emitted:
                    self._completed_emitted = True
                    self.mission_completed.emit(val_state)

        except Exception as e:
            logger.exception(f"Unexpected error in pipeline loop: {e}")
            self.error_occurred.emit(f"Pipeline error: {str(e)}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            if self.pose_estimator:
                self.pose_estimator.close()
            logger.info("PipelineWorker resources cleanly released.")


class PipelineController(QObject):
    """High-level controller managing the pipeline thread and routing data to views."""

    frame_ready = Signal(QImage, dict)
    step_advanced = Signal(dict)
    deviation_detected = Signal(dict)
    mission_completed = Signal(dict)
    error_occurred = Signal(str)
    pipeline_started = Signal()
    pipeline_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None

    def is_running(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def start_pipeline(self, camera_index: int = 0):
        """Start background inference worker thread."""
        if self.is_running():
            logger.warning("Pipeline is already running.")
            return

        self.worker = PipelineWorker(camera_index=camera_index)
        self.worker.frame_ready.connect(self.frame_ready)
        self.worker.step_advanced.connect(self.step_advanced)
        self.worker.deviation_detected.connect(self.deviation_detected)
        self.worker.mission_completed.connect(self.mission_completed)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.finished.connect(self._on_worker_finished)

        self.worker.start()
        self.pipeline_started.emit()
        logger.info("Pipeline thread started.")

    def stop_pipeline(self):
        """Stop background worker thread cleanly."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
            self.worker = None
            self.pipeline_stopped.emit()
            logger.info("Pipeline thread stopped.")

    def reset_mission(self):
        """Reset the active protocol sequence."""
        if self.worker:
            self.worker.reset_protocol()

    def _on_worker_error(self, err: str):
        self.error_occurred.emit(err)

    def _on_worker_finished(self):
        self.pipeline_stopped.emit()
