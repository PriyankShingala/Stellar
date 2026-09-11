"""
Mission Report View.
Celebration screen displayed upon 5/5 protocol completion with compliance audit details.
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


class MissionReportView(QWidget):
    """Post-mission debrief and compliance certification screen."""

    restart_requested = Signal()
    return_home_requested = Signal()

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

        # 1. Celebration Banner
        banner_card = QFrame()
        banner_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(16, 185, 129, 0.20),
                    stop:1 rgba(16, 23, 38, 0.85));
                border: 1.5px solid rgba(16, 185, 129, 0.45);
                border-radius: 20px;
                padding: 30px;
            }}
        """)
        b_layout = QVBoxLayout(banner_card)
        b_layout.setSpacing(12)
        b_layout.setAlignment(Qt.AlignCenter)

        star_badge = QLabel("✦ ✦ ✦")
        star_badge.setStyleSheet(f"font-size: 24px; color: {STATUS_SUCCESS};")
        star_badge.setAlignment(Qt.AlignCenter)
        b_layout.addWidget(star_badge)

        b_title = QLabel("MISSION PROTOCOL COMPLETED")
        b_title.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {TEXT_PRIMARY}; letter-spacing: 1px;")
        b_title.setAlignment(Qt.AlignCenter)
        b_layout.addWidget(b_title)

        b_sub = QLabel("All 5 mandatory steps of SOP-WATER-001 executed and verified in strict accordance with BAS flight rules.")
        b_sub.setStyleSheet(f"font-size: 14px; color: {STATUS_SUCCESS}; font-weight: 600;")
        b_sub.setAlignment(Qt.AlignCenter)
        b_layout.addWidget(b_sub)

        main_layout.addWidget(banner_card)

        # 2. Key Metrics Row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        m1 = self._build_metric_card("100%", "SOP ADHERENCE", STATUS_SUCCESS)
        m2 = self._build_metric_card("5 / 5", "STEPS VERIFIED", ACCENT_AMBER)
        m3 = self._build_metric_card("0", "DEVIATIONS", ACCENT_CYAN)
        m4 = self._build_metric_card("PASS", "FLIGHT CERT", STATUS_SUCCESS)

        metrics_row.addWidget(m1)
        metrics_row.addWidget(m2)
        metrics_row.addWidget(m3)
        metrics_row.addWidget(m4)
        main_layout.addLayout(metrics_row)

        # 3. Verified Step Audit Table Card
        steps_card = GlassCard(title="VERIFIED STEP LOG", subtitle="Chronological Step Verification")

        verified_steps = [
            ("01", "Pick up bottle", "Bottle proximity confirmed • Wrist grasp verified"),
            ("02", "Pick up glass", "Glass proximity confirmed • Bilateral hold maintained"),
            ("03", "Pour water", "Dynamic bottle inclination detected over glass aperture"),
            ("04", "Place down glass", "Glass released and stabilized on workstation"),
            ("05", "Place down bottle", "Bottle released • Protocol successfully terminated"),
        ]

        for num, title, detail in verified_steps:
            item_frame = QFrame()
            item_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border: 1px solid {GLASS_BORDER};
                    border-radius: 10px;
                    padding: 8px 14px;
                }}
            """)
            i_layout = QHBoxLayout(item_frame)
            i_layout.setSpacing(14)

            icon = QLabel("✓")
            icon.setStyleSheet(f"font-size: 14px; font-weight: 900; color: {STATUS_SUCCESS};")
            i_layout.addWidget(icon)

            num_lbl = QLabel(f"STEP {num}")
            num_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {ACCENT_AMBER};")
            i_layout.addWidget(num_lbl)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
            i_layout.addWidget(title_lbl)

            detail_lbl = QLabel(detail)
            detail_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
            i_layout.addWidget(detail_lbl)
            i_layout.addStretch()

            tag = QLabel("VERIFIED")
            tag.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {STATUS_SUCCESS};")
            i_layout.addWidget(tag)

            steps_card.add_widget(item_frame)

        main_layout.addWidget(steps_card)

        # 4. Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_restart = QPushButton("↺  Repeat Experiment")
        btn_restart.setCursor(Qt.PointingHandCursor)
        btn_restart.setFixedHeight(44)
        btn_restart.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_AMBER};
                color: #07090E;
                font-size: 13px;
                font-weight: 800;
                padding: 0 20px;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #FBBF24;
            }}
        """)
        btn_restart.clicked.connect(self.restart_requested.emit)
        btn_row.addWidget(btn_restart)

        btn_home = QPushButton("🏠  Return to Mission Home")
        btn_home.setCursor(Qt.PointingHandCursor)
        btn_home.setFixedHeight(44)
        btn_home.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                padding: 0 20px;
                border-radius: 10px;
                border: 1px solid {GLASS_BORDER};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.10);
            }}
        """)
        btn_home.clicked.connect(self.return_home_requested.emit)
        btn_row.addWidget(btn_home)
        btn_row.addStretch()

        main_layout.addLayout(btn_row)
        main_layout.addStretch()

        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll)

    def _build_metric_card(self, val: str, title: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: 14px;
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)

        v_lbl = QLabel(val)
        v_lbl.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {color};")
        v_lbl.setAlignment(Qt.AlignCenter)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px;")
        t_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(v_lbl)
        layout.addWidget(t_lbl)
        return frame
