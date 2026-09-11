"""
Mission Log View.
Chronological event stream displaying audit records, step transitions, and AI perception events.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_ERROR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from frontend.components.glass_card import GlassCard


class MissionLogView(QWidget):
    """Chronological event log view for mission flight records."""

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(20)

        # Header & Actions
        head_row = QHBoxLayout()
        head_box = QVBoxLayout()
        head_box.setSpacing(4)
        title = QLabel("Mission Flight Audit Log")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT_PRIMARY};")
        sub = QLabel("Chronological record of verified SOP transitions, sensor events, and safety alerts.")
        sub.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED};")
        head_box.addWidget(title)
        head_box.addWidget(sub)
        head_row.addLayout(head_box)

        head_row.addStretch()

        btn_clear = QPushButton("Clear Entries")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setFixedHeight(36)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 600;
                padding: 0 14px;
                border-radius: 8px;
                border: 1px solid {GLASS_BORDER};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
                color: {TEXT_PRIMARY};
            }}
        """)
        btn_clear.clicked.connect(self.clear_logs)
        head_row.addWidget(btn_clear)
        main_layout.addLayout(head_row)

        # Scrollable Log Stream Container
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.log_container = QWidget()
        self.log_container.setStyleSheet("background: transparent;")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(10)
        self.log_layout.addStretch()

        self.scroll.setWidget(self.log_container)
        main_layout.addWidget(self.scroll)

        # Add initial system boot entries
        self.add_log_entry("SYSTEM_INIT", "Stellar AI FlightDeck core initialized. 12-Joint Pose & YOLOv8n active.", "INFO")
        self.add_log_entry("PROTOCOL_READY", "Protocol SOP-WATER-001 'Bottle and Glass Water Transfer' loaded.", "INFO")

    def add_log_entry(self, event_type: str, message: str, level: str = "INFO"):
        """Append an event entry to the log stream."""
        now_str = datetime.now().strftime("%H:%M:%S")

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 10px;
                padding: 10px 14px;
            }}
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(14)

        # Time pill
        time_lbl = QLabel(now_str)
        time_lbl.setStyleSheet(f"font-family: monospace; font-size: 11px; color: {TEXT_MUTED}; font-weight: 600;")
        row.addWidget(time_lbl)

        # Level tag
        level_tag = QLabel(event_type)
        if level == "SUCCESS":
            color = STATUS_SUCCESS
            bg = "rgba(16, 185, 129, 0.15)"
        elif level in ("WARNING", "VIOLATION"):
            color = STATUS_WARNING
            bg = "rgba(245, 158, 11, 0.15)"
        elif level == "ERROR":
            color = STATUS_ERROR
            bg = "rgba(239, 68, 68, 0.15)"
        else:
            color = ACCENT_CYAN
            bg = "rgba(56, 189, 248, 0.12)"

        level_tag.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            font-size: 10px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 5px;
        """)
        row.addWidget(level_tag)

        # Message text
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_PRIMARY};")
        row.addWidget(msg_lbl, 1)

        # Insert before stretch at bottom
        count = self.log_layout.count()
        self.log_layout.insertWidget(max(0, count - 1), card)

    def clear_logs(self):
        """Clear all log entries."""
        while self.log_layout.count() > 1:
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
