"""
Stellar-AI Desktop Dashboard Main Application Launcher (PySide6).
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("StellarGUI")

def main():
    logger.info("Initializing Stellar-AI Desktop Dashboard...")
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
        from PySide6.QtCore import Qt

        app = QApplication(sys.argv)
        window = QMainWindow()
        window.setWindowTitle("Stellar-AI | On-Board BAS Experiment Assistant")
        window.resize(1280, 720)

        central_widget = QWidget()
        layout = QVBoxLayout()

        title_label = QLabel("Stellar-AI Offline Human Activity Recognition System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)

        status_label = QLabel("System Status: Ready | Protocol: SOP-BIO-001 Loaded")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)

        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)

        window.show()
        logger.info("Dashboard displayed successfully.")
        return app.exec()
    except ImportError:
        logger.warning("PySide6 is not installed. Run 'pip install -r requirements.txt' to launch GUI.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
