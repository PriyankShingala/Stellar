"""
Stellar AI FlightDeck - Modern Glassmorphic Left Navigation Rail.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QFrame
)
from PySide6.QtCore import Qt, Signal
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, STATUS_SUCCESS
)


class NavigationSidebar(QWidget):
    """Persistent glass navigation rail with mission icons and engine status."""

    page_changed = Signal(int)  # Emits screen index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)

        # Style container
        self.setStyleSheet(f"""
            QWidget#sidebarContainer {{
                background-color: {GLASS_BG};
                border-right: 1px solid {GLASS_BORDER};
            }}
        """)
        self.setObjectName("sidebarContainer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(8)

        # 1. Brand & Emblem Header
        brand_box = QHBoxLayout()
        brand_box.setSpacing(12)

        # Orbital Emblem Icon
        logo_badge = QLabel("✦")
        logo_badge.setAlignment(Qt.AlignCenter)
        logo_badge.setFixedSize(36, 36)
        logo_badge.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F59E0B, stop:1 #8B5CF6);
            color: #07090E;
            font-size: 18px;
            font-weight: 900;
            border-radius: 10px;
        """)
        brand_box.addWidget(logo_badge)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        title_label = QLabel("STELLAR AI")
        title_label.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {TEXT_PRIMARY}; letter-spacing: 1.5px;")
        sub_label = QLabel("BAS HAR FLIGHTDECK")
        sub_label.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {TEXT_MUTED}; letter-spacing: 0.8px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(sub_label)
        brand_box.addLayout(title_layout)

        layout.addLayout(brand_box)
        layout.addSpacing(24)

        # Category label
        nav_cat = QLabel("MISSION NAVIGATION")
        nav_cat.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1.2px; padding-left: 8px;")
        layout.addWidget(nav_cat)
        layout.addSpacing(4)

        # 2. Navigation Buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.nav_buttons = []
        nav_items = [
            ("🏠  Mission Home", 0),
            ("🧪  Experiments", 1),
            ("🎯  Live Monitor", 2),
            ("📜  Mission Log", 3),
            ("⚙️  Settings", 4),
        ]

        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("class", "navBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_SECONDARY};
                    font-size: 13px;
                    font-weight: 600;
                    text-align: left;
                    padding-left: 14px;
                    border-radius: 10px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.05);
                    color: {TEXT_PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: rgba(245, 158, 11, 0.12);
                    color: {ACCENT_AMBER};
                    border-left: 3px solid {ACCENT_AMBER};
                }}
            """)
            btn.clicked.connect(lambda _, i=idx: self._on_nav_clicked(i))
            self.btn_group.addButton(btn, idx)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        # Check Mission Home by default
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

        layout.addStretch()

        # 3. Bottom Offline Engine Status Pill
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid {GLASS_BORDER};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        s_layout = QVBoxLayout(status_frame)
        s_layout.setContentsMargins(8, 8, 8, 8)
        s_layout.setSpacing(4)

        top_s = QHBoxLayout()
        led = QLabel("●")
        led.setStyleSheet(f"color: {STATUS_SUCCESS}; font-size: 10px;")
        lbl = QLabel("Offline AI Engine")
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 700;")
        top_s.addWidget(led)
        top_s.addWidget(lbl)
        top_s.addStretch()
        s_layout.addLayout(top_s)

        engine_desc = QLabel("12-Joint Pose • YOLOv8n\nSOP-WATER-001 Ready")
        engine_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; line-height: 1.3;")
        s_layout.addWidget(engine_desc)

        layout.addWidget(status_frame)

    def _on_nav_clicked(self, index: int):
        self.page_changed.emit(index)

    def set_active_index(self, index: int):
        """Programmatically switch checked button."""
        btn = self.btn_group.button(index)
        if btn:
            btn.setChecked(True)
