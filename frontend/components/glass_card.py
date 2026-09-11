"""
Glassmorphic Card Widget Container.
Provides a translucent frosted glass panel with subtle 1px border and optional headers.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from frontend.styles.theme import (
    GLASS_BG, GLASS_BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class GlassCard(QFrame):
    """Reusable frosted glass container card."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        header_widget: QWidget = None,
        padding: int = 20,
        radius: int = 16,
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.setObjectName("glassCard")
        self.setProperty("class", "glassCard")

        self.setStyleSheet(f"""
            QFrame#glassCard {{
                background-color: {GLASS_BG};
                border: 1px solid {GLASS_BORDER};
                border-radius: {radius}px;
            }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(padding, padding, padding, padding)
        self.main_layout.setSpacing(14)

        # Header bar if title or header_widget provided
        if title or header_widget:
            self.header_layout = QHBoxLayout()
            self.header_layout.setContentsMargins(0, 0, 0, 0)
            self.header_layout.setSpacing(10)

            title_box = QVBoxLayout()
            title_box.setSpacing(2)

            if title:
                self.title_label = QLabel(title)
                self.title_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};")
                title_box.addWidget(self.title_label)

            if subtitle:
                self.sub_label = QLabel(subtitle)
                self.sub_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-weight: 500;")
                title_box.addWidget(self.sub_label)

            self.header_layout.addLayout(title_box)
            self.header_layout.addStretch()

            if header_widget:
                self.header_layout.addWidget(header_widget)

            self.main_layout.addLayout(self.header_layout)

        # Content container
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        self.main_layout.addLayout(self.content_layout)

    def add_widget(self, widget: QWidget):
        """Add child widget to card content area."""
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add sub-layout to card content area."""
        self.content_layout.addLayout(layout)
