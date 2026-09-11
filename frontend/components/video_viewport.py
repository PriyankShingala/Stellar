"""
Video Viewport Widget.
Hardware-friendly camera display widget with aspect ratio scaling, rounded corners, and cinematic standby HUD.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QFont
from frontend.styles.theme import (
    BG_CARD, GLASS_BORDER, ACCENT_AMBER, ACCENT_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class VideoViewport(QFrame):
    """Aspect-ratio preserved video frame viewport with standby mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoViewport")
        self.setMinimumSize(640, 360)

        self.setStyleSheet(f"""
            QFrame#videoViewport {{
                background-color: #030407;
                border: 1px solid {GLASS_BORDER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video label that holds the pixmap
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: transparent; border-radius: 16px;")
        layout.addWidget(self.video_label)

        self.current_pixmap = None
        self.is_streaming = False
        self.set_standby("MISSION FEED READY // STANDBY")

    def update_frame(self, image: QImage):
        """Update live camera frame from incoming QImage."""
        if image is None or image.isNull():
            return

        self.is_streaming = True
        self.current_pixmap = QPixmap.fromImage(image)
        self._render_current_pixmap()

    def _render_current_pixmap(self):
        """Scale and display the pixmap maintaining aspect ratio."""
        if self.current_pixmap and not self.current_pixmap.isNull():
            target_size = self.video_label.size()
            scaled = self.current_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled)

    def set_standby(self, message: str = "AWAITING MISSION START"):
        """Show futuristic standby HUD when stream is idle."""
        self.is_streaming = False
        self.current_pixmap = None

        # Build standby placeholder pixmap
        w = max(self.width(), 640)
        h = max(self.height(), 360)
        pix = QPixmap(w, h)
        pix.fill(QColor(7, 9, 14))

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw subtle grid/reticle
        painter.setPen(QColor(255, 255, 255, 12))
        cx, cy = w // 2, h // 2
        painter.drawEllipse(cx - 80, cy - 80, 160, 160)
        painter.drawEllipse(cx - 130, cy - 130, 260, 260)
        painter.drawLine(cx - 150, cy, cx + 150, cy)
        painter.drawLine(cx, cy - 150, cx, cy + 150)

        # Text
        font = QFont("Segoe UI", 12, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        painter.setFont(font)
        painter.setPen(QColor(56, 189, 248, 200))
        painter.drawText(0, cy - 15, w, 30, Qt.AlignCenter, message)

        font_sub = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font_sub)
        painter.setPen(QColor(148, 163, 184, 180))
        painter.drawText(0, cy + 20, w, 30, Qt.AlignCenter, "Offline AI Pipeline • 12-Joint Pose • YOLOv8n Object Detector")

        painter.end()
        self.video_label.setPixmap(pix)

    def resizeEvent(self, event):
        """Handle dynamic widget resize smoothly."""
        super().resizeEvent(event)
        if self.is_streaming and self.current_pixmap:
            self._render_current_pixmap()
        elif not self.is_streaming:
            self.set_standby()
