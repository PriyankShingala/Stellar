# Offline AI Model Checkpoints Directory

This directory stores pre-trained offline model weights for Stellar-AI.

## Directory Layout
- `object_detection/`: YOLOv8 / Faster-RCNN `.pt` or `.onnx` weights for lab equipment & consumables detection.
- `pose_estimation/`: Keypoint & skeletal pose estimation model weights (`yolov8-pose.onnx` / MediaPipe assets).
- `action_recognition/`: Action classification model checkpoints (`action_classifier.pt` / ONNX model).

## Instructions
1. Download required model checkpoints during environment setup using setup scripts.
2. Place offline `.pt` or `.onnx` files into their respective subfolders.
3. Verify paths in `backend/config/default_config.yaml`.

> **Note:** `.pt`, `.onnx`, and `.engine` files are excluded from Git version control via `.gitignore`.
