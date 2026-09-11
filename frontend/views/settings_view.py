"""
Settings View.
Astronaut and workstation hardware configuration: camera device, AI thresholds, and offline privacy indicators.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from frontend.components.glass_card import GlassCard


class SettingsView(QWidget):
    """Configuration interface for hardware inputs and AI parameters."""

    camera_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title = QLabel("System Settings & Telemetry Calibration")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Configure sensor inputs, on-board inference parameters, and notification alerts.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        main_layout.addLayout(title_box)

        # 1. Video Sensor Configuration Card
        cam_card = GlassCard(title="OPTICAL SENSOR CONFIGURATION", subtitle="Webcam and Workstation Video Devices")

        cam_row = QHBoxLayout()
        cam_label = QLabel("Primary Camera Sensor:")
        cam_label.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")
        cam_row.addWidget(cam_label)

        self.cam_combo = QComboBox()
        self.cam_combo.setFixedWidth(220)
        self.cam_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_PRIMARY};
                border: 1px solid {GLASS_BORDER};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.cam_combo.addItem("Camera 0 (Default USB / Integrated)", 0)
        self.cam_combo.addItem("Camera 1 (Secondary Auxiliary)", 1)
        self.cam_combo.addItem("Camera 2 (External Rig)", 2)
        self.cam_combo.currentIndexChanged.connect(self._on_camera_changed)
        cam_row.addWidget(self.cam_combo)
        cam_row.addStretch()
        cam_card.add_layout(cam_row)

        cam_note = QLabel("Note: Stream changes will take effect upon the next pipeline start or restart.")
        cam_note.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        cam_card.add_widget(cam_note)
        main_layout.addWidget(cam_card)

        # 2. AI Inference Engine Parameters
        ai_card = GlassCard(title="NEURAL INFERENCE THRESHOLDS", subtitle="Perception & Kinematics Tuning")

        yolo_row = QHBoxLayout()
        yolo_lbl = QLabel("YOLOv8n Object Confidence Cutoff:")
        yolo_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")
        yolo_val = QLabel("0.25 (Calibrated for transparent glass & bottles)")
        yolo_val.setStyleSheet(f"font-size: 12px; color: {ACCENT_CYAN}; font-weight: 700;")
        yolo_row.addWidget(yolo_lbl)
        yolo_row.addWidget(yolo_val)
        yolo_row.addStretch()
        ai_card.add_layout(yolo_row)

        pose_row = QHBoxLayout()
        pose_lbl = QLabel("MediaPipe Pose Minimum Confidence:")
        pose_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")
        pose_val = QLabel("0.50 (12 major body joints with wrists as hand proxies)")
        pose_val.setStyleSheet(f"font-size: 12px; color: {ACCENT_CYAN}; font-weight: 700;")
        pose_row.addWidget(pose_lbl)
        pose_row.addWidget(pose_val)
        pose_row.addStretch()
        ai_card.add_layout(pose_row)

        temp_row = QHBoxLayout()
        temp_lbl = QLabel("Interaction Temporal Dropout Tolerance:")
        temp_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")
        temp_val = QLabel("5 Consecutive Frames (Smoothes momentary YOLO drops)")
        temp_val.setStyleSheet(f"font-size: 12px; color: {ACCENT_AMBER}; font-weight: 700;")
        temp_row.addWidget(temp_lbl)
        temp_row.addWidget(temp_val)
        temp_row.addStretch()
        ai_card.add_layout(temp_row)

        main_layout.addWidget(ai_card)

        # 3. Privacy & Offline Guarantee
        priv_card = GlassCard(title="OFFLINE SECURITY ASSURANCE", subtitle="Bharatiya Antariksh Station Protocols")
        priv_badge = QLabel("🔒 100% On-Device Neural Execution")
        priv_badge.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.12);
            color: {STATUS_SUCCESS};
            font-size: 12px;
            font-weight: 800;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid rgba(16, 185, 129, 0.30);
        """)
        priv_card.add_widget(priv_badge)

        priv_text = QLabel(
            "Stellar AI operates in strict air-gapped isolation. No video streams, biometric landmarks, or experiment data "
            "are transmitted to cloud networks. All pose estimation, object detection, and state machine validations occur "
            "locally on station compute."
        )
        priv_text.setWordWrap(True)
        priv_text.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.5;")
        priv_card.add_widget(priv_text)
        main_layout.addWidget(priv_card)

        main_layout.addStretch()

        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll)

    def _on_camera_changed(self, idx: int):
        val = self.cam_combo.currentData()
        self.camera_changed.emit(val)

    def get_selected_camera_index(self) -> int:
        return self.cam_combo.currentData()
