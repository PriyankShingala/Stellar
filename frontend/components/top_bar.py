"""
Global Top Mission Bar Component.
Displays active experiment breadcrumb, mission elapsed timer, and live status pills.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt, QTimer, QTime
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class TopBar(QWidget):
    """Global top navigation and telemetry status header."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)

        self.setStyleSheet(f"""
            QWidget#topBarContainer {{
                background-color: {GLASS_BG};
                border-bottom: 1px solid {GLASS_BORDER};
            }}
        """)
        self.setObjectName("topBarContainer")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # 1. Left: Mission Breadcrumb
        self.mission_label = QLabel("Active Protocol:")
        self.mission_label.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED}; font-weight: 500;")
        layout.addWidget(self.mission_label)

        self.protocol_badge = QLabel("SOP-WATER-001 • Bottle and Glass Water Transfer")
        self.protocol_badge.setStyleSheet(f"""
            background-color: rgba(56, 189, 248, 0.12);
            color: {ACCENT_CYAN};
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.25);
        """)
        layout.addWidget(self.protocol_badge)

        layout.addStretch()

        # 2. Center: State Pill
        self.state_pill = QLabel("SYSTEM: READY")
        self.state_pill.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.12);
            color: {STATUS_SUCCESS};
            font-size: 11px;
            font-weight: 800;
            padding: 4px 12px;
            border-radius: 9999px;
            border: 1px solid rgba(16, 185, 129, 0.30);
            letter-spacing: 0.8px;
        """)
        layout.addWidget(self.state_pill)

        layout.addSpacing(10)

        # 3. Right: Mission Elapsed Time (MET) Clock
        self.clock_label = QLabel("MET 00:00:00")
        self.clock_label.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-family: monospace;
            font-size: 13px;
            font-weight: 600;
            background-color: rgba(255, 255, 255, 0.04);
            padding: 5px 10px;
            border-radius: 6px;
            border: 1px solid {GLASS_BORDER};
        """)
        layout.addWidget(self.clock_label)

        # Timer logic
        self.elapsed_seconds = 0
        self.timer_active = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_clock)
        self.timer.start(1000)

    def _update_clock(self):
        if self.timer_active:
            self.elapsed_seconds += 1
            hrs = self.elapsed_seconds // 3600
            mins = (self.elapsed_seconds % 3600) // 60
            secs = self.elapsed_seconds % 60
            self.clock_label.setText(f"MET {hrs:02d}:{mins:02d}:{secs:02d}")

    def start_mission_timer(self):
        self.elapsed_seconds = 0
        self.timer_active = True
        self.clock_label.setText("MET 00:00:00")

    def stop_mission_timer(self):
        self.timer_active = False

    def update_state(self, state_text: str, is_active: bool = False, is_completed: bool = False):
        if is_completed:
            color = STATUS_SUCCESS
            bg = "rgba(16, 185, 129, 0.15)"
            border = "rgba(16, 185, 129, 0.35)"
        elif is_active:
            color = ACCENT_AMBER
            bg = "rgba(245, 158, 11, 0.15)"
            border = "rgba(245, 158, 11, 0.35)"
        else:
            color = ACCENT_CYAN
            bg = "rgba(56, 189, 248, 0.12)"
            border = "rgba(56, 189, 248, 0.25)"

        self.state_pill.setText(state_text.upper())
        self.state_pill.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            font-size: 11px;
            font-weight: 800;
            padding: 4px 12px;
            border-radius: 9999px;
            border: 1px solid {border};
            letter-spacing: 0.8px;
        """)
