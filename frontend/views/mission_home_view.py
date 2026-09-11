"""
Mission Home View.
Cinematic welcome dashboard with astronaut training console header, active mission card, and quick start action.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    STATUS_SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from frontend.components.glass_card import GlassCard


class MissionHomeView(QWidget):
    """Futuristic mission home screen for Stellar AI."""

    start_mission_requested = Signal()
    view_experiments_requested = Signal()

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

        # 1. Hero Welcome Banner
        hero_card = QFrame()
        hero_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(16, 23, 38, 0.90),
                    stop:1 rgba(24, 34, 58, 0.75));
                border: 1px solid {GLASS_BORDER};
                border-radius: 20px;
                padding: 24px;
            }}
        """)
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setSpacing(12)

        # Pre-badge
        badge_row = QHBoxLayout()
        badge = QLabel("BHARATIYA ANTARIKSH STATION • HAR SUBSYSTEM")
        badge.setStyleSheet(f"""
            background-color: rgba(245, 158, 11, 0.15);
            color: {ACCENT_AMBER};
            font-size: 11px;
            font-weight: 800;
            padding: 4px 12px;
            border-radius: 9999px;
            letter-spacing: 1px;
        """)
        badge_row.addWidget(badge)
        badge_row.addStretch()
        hero_layout.addLayout(badge_row)

        hero_title = QLabel("Astronaut Training & Autonomous Protocol Assistant")
        hero_title.setStyleSheet(f"font-size: 26px; font-weight: 800; color: {TEXT_PRIMARY}; letter-spacing: -0.5px;")
        hero_layout.addWidget(hero_title)

        hero_desc = QLabel(
            "Welcome to Stellar AI. This autonomous on-board vision suite monitors astronaut science protocols "
            "in real-time using 12-joint pose kinematics and YOLOv8n object interaction tracking—operating 100% offline."
        )
        hero_desc.setWordWrap(True)
        hero_desc.setStyleSheet(f"font-size: 14px; color: {TEXT_SECONDARY}; line-height: 1.5; max-width: 900px;")
        hero_layout.addWidget(hero_desc)

        hero_layout.addSpacing(6)

        # Hero Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.btn_start = QPushButton("🚀  Launch Live Protocol Monitor")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedHeight(46)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_AMBER};
                color: #07090E;
                font-size: 14px;
                font-weight: 800;
                padding: 0 24px;
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #FBBF24;
            }}
            QPushButton:pressed {{
                background-color: #D97706;
            }}
        """)
        self.btn_start.clicked.connect(self.start_mission_requested.emit)
        btn_row.addWidget(self.btn_start)

        self.btn_exp = QPushButton("Browse Experiments")
        self.btn_exp.setCursor(Qt.PointingHandCursor)
        self.btn_exp.setFixedHeight(46)
        self.btn_exp.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.06);
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                padding: 0 20px;
                border-radius: 12px;
                border: 1px solid {GLASS_BORDER};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.12);
            }}
        """)
        self.btn_exp.clicked.connect(self.view_experiments_requested.emit)
        btn_row.addWidget(self.btn_exp)

        btn_row.addStretch()
        hero_layout.addLayout(btn_row)

        main_layout.addWidget(hero_card)

        # 2. Active Protocol Highlight Section
        sec_title = QLabel("ACTIVE EXPERIMENT ASSIGNMENT")
        sec_title.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {TEXT_MUTED}; letter-spacing: 1.2px;")
        main_layout.addWidget(sec_title)

        active_card = GlassCard(
            title="SOP-WATER-001: Bottle and Glass Water Transfer",
            subtitle="Standard Operating Procedure for microgravity fluid transfer verification"
        )

        steps_grid = QHBoxLayout()
        steps_grid.setSpacing(12)

        steps_summary = [
            ("01", "Pick up bottle", "Hand proximity to bottle"),
            ("02", "Pick up glass", "Hand proximity to glass"),
            ("03", "Pour water", "Tilt geometry & elevation"),
            ("04", "Place down glass", "Disengagement of glass"),
            ("05", "Place down bottle", "Disengagement of bottle"),
        ]

        for num, title, note in steps_summary:
            box = QFrame()
            box.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid {GLASS_BORDER};
                    border-radius: 10px;
                    padding: 10px;
                }}
            """)
            b_layout = QVBoxLayout(box)
            b_layout.setSpacing(4)

            n_lbl = QLabel(f"STEP {num}")
            n_lbl.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {ACCENT_AMBER};")
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
            sub = QLabel(note)
            sub.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")

            b_layout.addWidget(n_lbl)
            b_layout.addWidget(t_lbl)
            b_layout.addWidget(sub)
            steps_grid.addWidget(box)

        active_card.add_layout(steps_grid)
        main_layout.addWidget(active_card)

        # 3. System Capabilities Overview
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        c1 = GlassCard(title="🎯 12-Joint Pose Kinematics")
        c1_desc = QLabel(
            "MediaPipe Pose tracker calibrated strictly to 12 major anatomical joints. Wrists serve as hand position proxies without CPU-heavy finger landmarks."
        )
        c1_desc.setWordWrap(True)
        c1_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        c1.add_widget(c1_desc)
        cards_row.addWidget(c1)

        c2 = GlassCard(title="🔍 YOLOv8n Object Detector")
        c2_desc = QLabel(
            "Ultra-lightweight neural detector targeted for laboratory equipment (bottle & glass). Employs 5-frame temporal dropout tolerance."
        )
        c2_desc.setWordWrap(True)
        c2_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        c2.add_widget(c2_desc)
        cards_row.addWidget(c2)

        c3 = GlassCard(title="🛡️ Deterministic Validator")
        c3_desc = QLabel(
            "Rule-based state machine enforcing exact protocol sequence. Instantly identifies wrong-order steps and skipped requirements with zero hallucinations."
        )
        c3_desc.setWordWrap(True)
        c3_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        c3.add_widget(c3_desc)
        cards_row.addWidget(c3)

        main_layout.addLayout(cards_row)
        main_layout.addStretch()

        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll)
