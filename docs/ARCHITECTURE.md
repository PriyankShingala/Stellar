# Stellar-AI System Architecture Blueprint

## System Overview
Stellar-AI is an offline, real-time, edge-deployable Human Activity Recognition (HAR) system designed for on-board Bio-Autonomous Systems (BAS) space experiments.

```
+-----------------------------------------------------------------------+
|                           FRONTEND (PySide6)                          |
|  Live Video Overlay  |  Active SOP Checklist  |  Alert Bar  | Logs    |
+-----------------------------------+-----------------------------------+
                                    | IPC / Event Bus
+-----------------------------------v-----------------------------------+
|                        BACKEND ORCHESTRATOR                           |
| Frame Grabber | Recorder | TTS Voice Engine | SQLite Audit Event Logger|
+-----------------------------------+-----------------------------------+
                                    | Data Stream
+-----------------------------------v-----------------------------------+
|                           AI SUBSYSTEM                                |
|  +---------------------------------+  +----------------------------+  |
|  |           INFERENCE             |  |    SEQUENCE VALIDATOR      |  |
|  | - Object Detection (YOLO)       |  |  (Isolated Rule Engine)    |  |
|  | - Pose Estimation (YOLO-Pose)   |  | - Protocol YAML Parser     |  |
|  | - Hand-Object Interaction       |  | - Finite State Machine     |  |
|  | - Action Classification         |  | - Out-of-Order Detection   |  |
|  +---------------------------------+  +----------------------------+  |
+-----------------------------------------------------------------------+
```

## Key Subsystem Descriptions

1. **Frontend (`frontend/`)**: Cross-platform desktop interface displaying real-time video feeds annotated with bounding boxes, pose skeletons, current SOP step progress, and offline audio/visual warnings.
2. **Backend (`backend/`)**: System coordinator running background threads for frame capture, local video archiving, offline text-to-speech alert dispatching, and SQLite database logging.
3. **AI Perception & Inference (`ai/inference/`)**: Computer vision models executing locally via ONNX Runtime / PyTorch. Performs detection of lab consumables, hand pose keypoint tracking, spatial contact evaluation, and atomic action classification.
4. **Deterministic Sequence Validator (`ai/sequence_validator/`)**: Strictly isolated rule engine executing a Finite State Machine (FSM). Validates detected user actions against configured SOP step rules, raising deterministic compliance alerts when steps are skipped or performed out of order.
5. **Database & Audit (`database/`)**: Audit trail logging storing timestamped events, step completions, operator actions, and compliance violations into a local SQLite database (`stellar_audit.db`).
