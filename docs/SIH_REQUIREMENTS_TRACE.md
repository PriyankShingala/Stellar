# SIH 2026 Requirements Traceability Matrix

| SIH Requirement | System Component | Implementation Path | Verification Status |
| :--- | :--- | :--- | :--- |
| **Computer Vision / Object Detection** | `ai/inference/object_detector.py` | Detects lab equipment, vials, consumables | Skeleton Created |
| **Human Pose Estimation** | `ai/inference/pose_estimator.py` | Hand & body keypoint tracking | Skeleton Created |
| **Hand-Object Interaction Reasoning** | `ai/inference/interaction_reasoner.py` | Bounding box proximity & spatial contact | Skeleton Created |
| **Activity / Step Recognition** | `ai/inference/action_classifier.py` | Action classification from pose & tool features | Skeleton Created |
| **Deterministic Sequence Validation** | `ai/sequence_validator/` | FSM rule engine isolated from AI inference | Skeleton Created |
| **Offline Voice Alerts** | `backend/app/alerts/tts_engine.py` | Local Text-to-Speech (`pyttsx3`) audio alerts | Skeleton Created |
| **Event Logging** | `backend/app/logging_module/` | Thread-safe SQLite audit trail logger | Skeleton Created |
| **Local Video Streaming / Storage** | `backend/app/streaming/` | Multithreaded frame grabber & video recorder | Skeleton Created |
| **GUI Dashboard** | `frontend/app.py` | PySide6 desktop dashboard with live overlays | Skeleton Created |
| **Offline Execution** | System Wide | Zero external cloud APIs, 100% local weights | Architecture Verified |
