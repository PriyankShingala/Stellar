"""
Experiments Catalog View.
Presents active and scheduled on-board science protocols for the astronaut crew.
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


class ExperimentsView(QWidget):
    """Protocol catalog screen allowing selection and initiation of SOP experiments."""

    select_protocol_requested = Signal(str)  # Emits protocol_id

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

        # Header
        head_box = QVBoxLayout()
        head_box.setSpacing(6)
        title = QLabel("BAS Science Payload Experiments")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {TEXT_PRIMARY};")
        subtitle = QLabel("Select an approved Standard Operating Procedure (SOP) to begin astronaut activity verification.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_MUTED};")
        head_box.addWidget(title)
        head_box.addWidget(subtitle)
        main_layout.addLayout(head_box)

        # 1. Primary Active Protocol Card
        active_card = GlassCard(radius=18, padding=24)

        top_row = QHBoxLayout()
        status_tag = QLabel("ACTIVE PAYLOAD")
        status_tag.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.15);
            color: {STATUS_SUCCESS};
            font-size: 11px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(16, 185, 129, 0.30);
        """)
        top_row.addWidget(status_tag)

        protocol_id = QLabel("SOP-WATER-001")
        protocol_id.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ACCENT_CYAN};")
        top_row.addWidget(protocol_id)
        top_row.addStretch()
        active_card.add_layout(top_row)

        card_title = QLabel("Bottle and Glass Water Transfer")
        card_title.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {TEXT_PRIMARY}; margin-top: 8px;")
        active_card.add_widget(card_title)

        card_desc = QLabel(
            "Evaluation of astronaut fluid handling in enclosed workstation. Verifies sequential acquisition of bottle and glass containers, fluid dispensation through dynamic tilt angle, and stable surface repositioning."
        )
        card_desc.setWordWrap(True)
        card_desc.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.5;")
        active_card.add_widget(card_desc)

        # Step breakdown pills
        steps_label = QLabel("MANDATORY VERIFICATION SEQUENCE (5 STEPS)")
        steps_label.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {TEXT_MUTED}; letter-spacing: 1px; margin-top: 12px;")
        active_card.add_widget(steps_label)

        steps_row = QHBoxLayout()
        steps_row.setSpacing(10)
        steps_data = [
            ("1", "Bottle Pickup"),
            ("2", "Glass Pickup"),
            ("3", "Fluid Pouring"),
            ("4", "Glass Put-Down"),
            ("5", "Bottle Put-Down"),
        ]
        for num, text in steps_data:
            pill = QLabel(f"{num}. {text}")
            pill.setStyleSheet(f"""
                background-color: rgba(255, 255, 255, 0.04);
                color: {TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                border-radius: 8px;
                border: 1px solid {GLASS_BORDER};
            """)
            steps_row.addWidget(pill)
        steps_row.addStretch()
        active_card.add_layout(steps_row)

        # Action row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        btn_select = QPushButton("🚀  Launch SOP-WATER-001")
        btn_select.setCursor(Qt.PointingHandCursor)
        btn_select.setFixedHeight(44)
        btn_select.setStyleSheet(f"""
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
        btn_select.clicked.connect(lambda: self.select_protocol_requested.emit("SOP-WATER-001"))
        action_row.addWidget(btn_select)
        action_row.addStretch()
        active_card.add_layout(action_row)

        main_layout.addWidget(active_card)

        # 2. Upcoming Protocols
        upcoming_sec = QLabel("FUTURE EXPERIMENT MODULES")
        upcoming_sec.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {TEXT_MUTED}; letter-spacing: 1.2px; margin-top: 10px;")
        main_layout.addWidget(upcoming_sec)

        grid = QHBoxLayout()
        grid.setSpacing(16)

        # Card 2
        card_bio = GlassCard(title="SOP-BIO-001: Biological Culture Pipetting", subtitle="Life Sciences Microgravity Rack")
        bio_desc = QLabel("Automated verification of micropipette tip mounting, aspiration, dispensing, and decontamination procedures.")
        bio_desc.setWordWrap(True)
        bio_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; line-height: 1.4;")
        card_bio.add_widget(bio_desc)
        tag_bio = QLabel("PLANNED / EXPEDITION 2")
        tag_bio.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED};")
        card_bio.add_widget(tag_bio)
        grid.addWidget(card_bio)

        # Card 3
        card_mat = GlassCard(title="SOP-MAT-001: Crystal Growth Ampoule Transfer", subtitle="Materials Science Glovebox")
        mat_desc = QLabel("Thermal shield verification and robotic glovebox transfer of semiconductor crystallization ampoules.")
        mat_desc.setWordWrap(True)
        mat_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; line-height: 1.4;")
        card_mat.add_widget(mat_desc)
        tag_mat = QLabel("PLANNED / EXPEDITION 2")
        tag_mat.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED};")
        card_mat.add_widget(tag_mat)
        grid.addWidget(card_mat)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        scroll_layout = QVBoxLayout(self)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll)
