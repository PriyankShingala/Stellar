"""
Mission Timeline Component for SOP-WATER-001.
Renders the 5 sequential protocol steps with real-time status pills and animated progress connectors.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, STATUS_ERROR, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


STEP_DEFINITIONS = [
    ("01", "Pick up bottle"),
    ("02", "Pick up glass"),
    ("03", "Pour water"),
    ("04", "Place down glass"),
    ("05", "Place down bottle"),
]


class StepNodeWidget(QFrame):
    """Single step card inside the timeline."""

    def __init__(self, step_num: str, step_title: str, parent=None):
        super().__init__(parent)
        self.step_num = step_num
        self.step_title = step_title

        self.setFixedHeight(64)
        self.setMinimumWidth(130)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Number circle / indicator badge
        self.badge = QLabel(step_num)
        self.badge.setFixedSize(30, 30)
        self.badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge)

        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.num_label = QLabel(f"STEP {step_num}")
        self.num_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 0.8px;")

        self.title_label = QLabel(step_title)
        self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_SECONDARY};")

        text_layout.addWidget(self.num_label)
        text_layout.addWidget(self.title_label)
        layout.addLayout(text_layout)

        # Initial pending styling
        self.set_state("PENDING")

    def set_state(self, state: str):
        """Update node visual appearance based on status."""
        state = state.upper()

        if state == "COMPLETED":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(16, 185, 129, 0.12);
                    border: 1px solid rgba(16, 185, 129, 0.40);
                    border-radius: 12px;
                }}
            """)
            self.badge.setText("✓")
            self.badge.setStyleSheet(f"""
                background-color: {STATUS_SUCCESS};
                color: #07090E;
                font-size: 13px;
                font-weight: 900;
                border-radius: 15px;
            """)
            self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {STATUS_SUCCESS};")
            self.num_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {STATUS_SUCCESS};")

        elif state == "IN_PROGRESS":
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(245, 158, 11, 0.14);
                    border: 1.5px solid {ACCENT_AMBER};
                    border-radius: 12px;
                }}
            """)
            self.badge.setText(self.step_num)
            self.badge.setStyleSheet(f"""
                background-color: {ACCENT_AMBER};
                color: #07090E;
                font-size: 12px;
                font-weight: 900;
                border-radius: 15px;
            """)
            self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {TEXT_PRIMARY};")
            self.num_label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {ACCENT_AMBER};")

        elif state in ("VIOLATED", "ERROR"):
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(239, 68, 68, 0.15);
                    border: 1.5px solid {STATUS_ERROR};
                    border-radius: 12px;
                }}
            """)
            self.badge.setText("✕")
            self.badge.setStyleSheet(f"""
                background-color: {STATUS_ERROR};
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 900;
                border-radius: 15px;
            """)
            self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {STATUS_ERROR};")
            self.num_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {STATUS_ERROR};")

        else:  # PENDING
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid {GLASS_BORDER};
                    border-radius: 12px;
                }}
            """)
            self.badge.setText(self.step_num)
            self.badge.setStyleSheet(f"""
                background-color: rgba(255, 255, 255, 0.08);
                color: {TEXT_MUTED};
                font-size: 12px;
                font-weight: 700;
                border-radius: 15px;
            """)
            self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {TEXT_MUTED};")
            self.num_label.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED};")


class MissionTimeline(QFrame):
    """Horizontal 5-step SOP progress bar container."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(84)

        self.setStyleSheet(f"""
            QFrame#timelineFrame {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 14px;
            }}
        """)
        self.setObjectName("timelineFrame")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.nodes = []
        self.connectors = []

        for i, (num, title) in enumerate(STEP_DEFINITIONS):
            node = StepNodeWidget(num, title, self)
            self.nodes.append(node)
            layout.addWidget(node, 1)

            # Connector line between nodes (except after last)
            if i < len(STEP_DEFINITIONS) - 1:
                conn = QFrame()
                conn.setFixedHeight(2)
                conn.setStyleSheet(f"background-color: {GLASS_BORDER};")
                self.connectors.append(conn)
                layout.addWidget(conn)

        # Set step 1 to in-progress initially
        self.reset_timeline()

    def reset_timeline(self):
        """Reset all steps to pending, with first step ready."""
        for i, node in enumerate(self.nodes):
            if i == 0:
                node.set_state("IN_PROGRESS")
            else:
                node.set_state("PENDING")

        for conn in self.connectors:
            conn.setStyleSheet(f"background-color: {GLASS_BORDER};")

    def update_from_validator_state(self, validator_state: dict):
        """Update nodes and connector styling from SequenceValidator state dict."""
        if not validator_state:
            return

        steps = validator_state.get("steps", [])
        for i, step_info in enumerate(steps):
            if i >= len(self.nodes):
                break

            status = step_info.get("status", "PENDING").upper()
            self.nodes[i].set_state(status)

            # Update connector line leading out of this step
            if i < len(self.connectors):
                if status == "COMPLETED":
                    self.connectors[i].setStyleSheet(f"background-color: {STATUS_SUCCESS};")
                else:
                    self.connectors[i].setStyleSheet(f"background-color: {GLASS_BORDER};")
