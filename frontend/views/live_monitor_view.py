"""
Live Monitor View.
The centerpiece astronaut training screen: video feed, 12-joint pose overlay,
YOLOv8n bottle/glass boxes, real-time HOI state, and deterministic step guidance.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_ERROR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from frontend.components.glass_card import GlassCard
from frontend.components.mission_timeline import MissionTimeline
from frontend.components.video_viewport import VideoViewport


class LiveMonitorView(QWidget):
    """Real-time mission execution screen with camera stream and AI analytics."""

    start_stream_requested = Signal()
    stop_stream_requested = Signal()
    reset_protocol_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. Top Section: 5-Step Mission Timeline
        self.timeline = MissionTimeline(self)
        main_layout.addWidget(self.timeline)

        # 2. Main Center Split Layout (Left: Video + Controls | Right: Guidance & HOI)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        # ----------------- LEFT COLUMN: VIDEO VIEWPORT -----------------
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        # Video frame viewport
        self.viewport = VideoViewport(self)
        left_col.addWidget(self.viewport, 1)

        # Video Control & Telemetry Bar
        ctrl_card = QFrame()
        ctrl_card.setFixedHeight(58)
        ctrl_card.setStyleSheet(f"""
            QFrame {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 6px 14px;
            }}
        """)
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(12, 0, 12, 0)
        ctrl_layout.setSpacing(14)

        self.btn_stream = QPushButton("▶  Start Pipeline")
        self.btn_stream.setCursor(Qt.PointingHandCursor)
        self.btn_stream.setFixedHeight(38)
        self.btn_stream.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_AMBER};
                color: #07090E;
                font-size: 12px;
                font-weight: 800;
                padding: 0 16px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #FBBF24;
            }}
        """)
        self.btn_stream.clicked.connect(self._toggle_stream)
        ctrl_layout.addWidget(self.btn_stream)

        self.btn_reset = QPushButton("↺  Reset SOP")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setFixedHeight(38)
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 700;
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid {GLASS_BORDER};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
            }}
        """)
        self.btn_reset.clicked.connect(self.reset_protocol_requested.emit)
        ctrl_layout.addWidget(self.btn_reset)

        # Telemetry pills in control bar
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {ACCENT_CYAN};")
        ctrl_layout.addWidget(self.fps_label)

        self.pose_status_label = QLabel("Pose: Searching")
        self.pose_status_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_MUTED};")
        ctrl_layout.addWidget(self.pose_status_label)

        ctrl_layout.addStretch()

        self.camera_badge = QLabel("CAM 0 • ACTIVE")
        self.camera_badge.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 700;
            color: {TEXT_MUTED};
            padding: 3px 8px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.04);
        """)
        ctrl_layout.addWidget(self.camera_badge)

        left_col.addWidget(ctrl_card)
        center_layout.addLayout(left_col, 65)

        # ----------------- RIGHT COLUMN: GUIDANCE & HOI -----------------
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # Card 1: Active Step Guidance
        self.guidance_card = GlassCard(title="ACTIVE STEP GUIDANCE", subtitle="Astronaut Action Directive")
        self.step_display_num = QLabel("STEP 01 OF 05")
        self.step_display_num.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {ACCENT_AMBER}; letter-spacing: 1px;")
        self.guidance_card.add_widget(self.step_display_num)

        self.step_title = QLabel("Pick up bottle")
        self.step_title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {TEXT_PRIMARY};")
        self.guidance_card.add_widget(self.step_title)

        self.step_instruction = QLabel(
            "Reach toward the water bottle with either hand and grasp it firmly. Hand proximity will trigger pickup."
        )
        self.step_instruction.setWordWrap(True)
        self.step_instruction.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        self.guidance_card.add_widget(self.step_instruction)
        right_col.addWidget(self.guidance_card)

        # Card 2: Human-Object Interaction (HOI) State
        self.hoi_card = GlassCard(title="INTERACTION TELEMETRY", subtitle="Wrist-Object Proximity & Kinematics")

        # Hands status
        hands_box = QHBoxLayout()
        self.left_hand_pill = QLabel("L-WRIST: IDLE")
        self.left_hand_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))
        self.right_hand_pill = QLabel("R-WRIST: IDLE")
        self.right_hand_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))
        hands_box.addWidget(self.left_hand_pill)
        hands_box.addWidget(self.right_hand_pill)
        self.hoi_card.add_layout(hands_box)

        # Objects status
        objects_box = QHBoxLayout()
        self.bottle_status_pill = QLabel("BOTTLE: NOT DETECTED")
        self.bottle_status_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))
        self.glass_status_pill = QLabel("GLASS: NOT DETECTED")
        self.glass_status_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))
        objects_box.addWidget(self.bottle_status_pill)
        objects_box.addWidget(self.glass_status_pill)
        self.hoi_card.add_layout(objects_box)

        # Pouring Indicator
        self.pouring_badge = QLabel("POURING: INACTIVE")
        self.pouring_badge.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))
        self.hoi_card.add_widget(self.pouring_badge)

        right_col.addWidget(self.hoi_card)

        # Card 3: Compliance & Deviations
        self.compliance_card = GlassCard(title="SEQUENCE COMPLIANCE", subtitle="Rule Verification Audit")
        self.compliance_alert = QLabel("✓ Protocol Sequence in Compliance")
        self.compliance_alert.setWordWrap(True)
        self.compliance_alert.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.12);
            color: {STATUS_SUCCESS};
            font-size: 12px;
            font-weight: 700;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(16, 185, 129, 0.30);
        """)
        self.compliance_card.add_widget(self.compliance_alert)
        right_col.addWidget(self.compliance_card)

        right_col.addStretch()
        center_layout.addLayout(right_col, 35)

        main_layout.addLayout(center_layout)

        self._is_streaming = False

    def _pill_style(self, color: str, bg: str) -> str:
        return f"""
            background-color: {bg};
            color: {color};
            font-size: 11px;
            font-weight: 700;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        """

    def _toggle_stream(self):
        if not self._is_streaming:
            self.start_stream_requested.emit()
            self.set_streaming_ui(True)
        else:
            self.stop_stream_requested.emit()
            self.set_streaming_ui(False)

    def set_streaming_ui(self, active: bool):
        self._is_streaming = active
        if active:
            self.btn_stream.setText("⏹  Stop Pipeline")
            self.btn_stream.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(239, 68, 68, 0.20);
                    color: {STATUS_ERROR};
                    font-size: 12px;
                    font-weight: 800;
                    padding: 0 16px;
                    border-radius: 8px;
                    border: 1px solid rgba(239, 68, 68, 0.40);
                }}
                QPushButton:hover {{
                    background-color: rgba(239, 68, 68, 0.35);
                }}
            """)
            self.camera_badge.setText("CAM 0 • STREAMING")
            self.camera_badge.setStyleSheet(f"""
                font-size: 11px; font-weight: 800; color: {STATUS_SUCCESS};
                padding: 3px 8px; border-radius: 6px; background: rgba(16, 185, 129, 0.15);
            """)
        else:
            self.btn_stream.setText("▶  Start Pipeline")
            self.btn_stream.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_AMBER};
                    color: #07090E;
                    font-size: 12px;
                    font-weight: 800;
                    padding: 0 16px;
                    border-radius: 8px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #FBBF24;
                }}
            """)
            self.camera_badge.setText("CAM 0 • IDLE")
            self.camera_badge.setStyleSheet(f"""
                font-size: 11px; font-weight: 700; color: {TEXT_MUTED};
                padding: 3px 8px; border-radius: 6px; background: rgba(255, 255, 255, 0.04);
            """)
            self.fps_label.setText("FPS: --")
            self.viewport.set_standby()

    def update_frame(self, image: QImage, telemetry: dict):
        """Called every frame from PipelineController."""
        # 1. Update video viewport
        self.viewport.update_frame(image)

        # 2. Update FPS
        fps = telemetry.get("fps", 0.0)
        self.fps_label.setText(f"FPS: {fps:.1f}")

        # 3. Update Pose Status
        pose = telemetry.get("pose", {})
        if pose and pose.get("detected"):
            self.pose_status_label.setText("Pose: 12 Joints Tracked")
            self.pose_status_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {STATUS_SUCCESS};")
        else:
            self.pose_status_label.setText("Pose: Searching")
            self.pose_status_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_MUTED};")

        # 4. Update Interaction Reasoner Telemetry
        reasoner = telemetry.get("reasoner", {})
        if reasoner:
            self._update_hoi_ui(reasoner)

        # 5. Update Sequence Validator & Timeline
        val_state = telemetry.get("validator", {})
        if val_state:
            self.timeline.update_from_validator_state(val_state)
            self._update_guidance(val_state)

    def _update_hoi_ui(self, reasoner: dict):
        held = reasoner.get("held_objects", {})
        is_pouring = reasoner.get("is_pouring", False)

        # Left hand
        l_held = held.get("left")
        if l_held:
            self.left_hand_pill.setText(f"L-WRIST: HOLDING {l_held.upper()}")
            self.left_hand_pill.setStyleSheet(self._pill_style(ACCENT_AMBER, "rgba(245,158,11,0.15)"))
        else:
            self.left_hand_pill.setText("L-WRIST: FREE")
            self.left_hand_pill.setStyleSheet(self._pill_style(TEXT_SECONDARY, "rgba(255,255,255,0.06)"))

        # Right hand
        r_held = held.get("right")
        if r_held:
            self.right_hand_pill.setText(f"R-WRIST: HOLDING {r_held.upper()}")
            self.right_hand_pill.setStyleSheet(self._pill_style(ACCENT_AMBER, "rgba(245,158,11,0.15)"))
        else:
            self.right_hand_pill.setText("R-WRIST: FREE")
            self.right_hand_pill.setStyleSheet(self._pill_style(TEXT_SECONDARY, "rgba(255,255,255,0.06)"))

        # Object presence
        prox = reasoner.get("proximity_matrix", {})
        bottle_seen = "bottle" in prox
        glass_seen = "glass" in prox

        if bottle_seen:
            self.bottle_status_pill.setText("BOTTLE: DETECTED")
            self.bottle_status_pill.setStyleSheet(self._pill_style(STATUS_SUCCESS, "rgba(16,185,129,0.15)"))
        else:
            self.bottle_status_pill.setText("BOTTLE: SEARCHING")
            self.bottle_status_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))

        if glass_seen:
            self.glass_status_pill.setText("GLASS: DETECTED")
            self.glass_status_pill.setStyleSheet(self._pill_style(STATUS_SUCCESS, "rgba(16,185,129,0.15)"))
        else:
            self.glass_status_pill.setText("GLASS: SEARCHING")
            self.glass_status_pill.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))

        # Pouring
        if is_pouring:
            self.pouring_badge.setText("POURING DETECTED (ACTIVE)")
            self.pouring_badge.setStyleSheet(self._pill_style(STATUS_SUCCESS, "rgba(16,185,129,0.25)"))
        else:
            self.pouring_badge.setText("POURING: INACTIVE")
            self.pouring_badge.setStyleSheet(self._pill_style(TEXT_MUTED, "rgba(255,255,255,0.04)"))

    def _update_guidance(self, val_state: dict):
        steps = val_state.get("steps", [])
        curr_step = val_state.get("current_step")
        is_completed = val_state.get("is_completed", False)

        if is_completed:
            self.step_display_num.setText("MISSION ACCOMPLISHED")
            self.step_display_num.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {STATUS_SUCCESS}; letter-spacing: 1px;")
            self.step_title.setText("All 5 Steps Completed!")
            self.step_instruction.setText("All protocol steps verified successfully. The experiment audit log is ready for review.")
            return

        if curr_step:
            num = curr_step.get("step_number", 1)
            action = curr_step.get("action_name", "")
            self.step_display_num.setText(f"STEP 0{num} OF 05")

            guidance_map = {
                "bottle_pickup": ("Pick up bottle", "Reach for the water bottle and hold it firmly."),
                "glass_pickup": ("Pick up glass", "With other hand, reach for the glass container and lift it."),
                "pouring": ("Pour water into glass", "Tilt bottle over glass mouth to initiate water transfer."),
                "glass_put_down": ("Place down glass", "Return the glass to the surface and release grip."),
                "bottle_put_down": ("Place down bottle", "Return the bottle to the surface and release grip.")
            }

            title, inst = guidance_map.get(action, (action.replace("_", " ").title(), "Execute the designated action."))
            self.step_title.setText(title)
            self.step_instruction.setText(inst)

    def show_deviation_alert(self, deviation_data: dict):
        """Display sequence deviation warning."""
        msg = deviation_data.get("status_message", "Unexpected sequence event.")
        self.compliance_alert.setText(f"⚠️ Sequence Warning:\n{msg}")
        self.compliance_alert.setStyleSheet(f"""
            background-color: rgba(239, 68, 68, 0.15);
            color: {STATUS_ERROR};
            font-size: 12px;
            font-weight: 700;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(239, 68, 68, 0.40);
        """)

    def reset_compliance_alert(self):
        """Restore compliance alert to green state."""
        self.compliance_alert.setText("✓ Protocol Sequence in Compliance")
        self.compliance_alert.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.12);
            color: {STATUS_SUCCESS};
            font-size: 12px;
            font-weight: 700;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid rgba(16, 185, 129, 0.30);
        """)
