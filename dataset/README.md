# Stellar-AI Dataset Directory

This directory stores datasets for training, validating, and fine-tuning object detection and action recognition models.

## Structure
- `raw/`: Unprocessed video recordings of lab experiment actions.
- `annotated/`: Label files (YOLO format `.txt` or COCO format `.json`).
- `splits/`: Train / Validation / Test split manifests.

> **Note:** Raw media files are excluded from Git version control via `.gitignore`.
