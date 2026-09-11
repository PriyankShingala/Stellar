"""
Stellar AI - Modern Astronaut Training & BAS Experiment Assistant.
Main PySide6 Application Entry Point.
"""

import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt

from frontend.styles.theme import GLOBAL_QSS, BG_VOID
from frontend.components.sidebar import NavigationSidebar
from frontend.components.top_bar import TopBar
from frontend.controllers.pipeline_controller import PipelineController

from frontend.views.mission_home_view import MissionHomeView
from frontend.views.experiments_view import ExperimentsView
from frontend.views.live_monitor_view import LiveMonitorView
from frontend.views.mission_report_view import MissionReportView
from frontend.views.mission_log_view import MissionLogView
from frontend.views.settings_view import SettingsView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("StellarApp")


class MainWindow(QMainWindow):
    """Main application window for Stellar AI FlightDeck."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stellar AI | On-Board BAS Experiment Assistant")
        self.resize(1340, 840)
        self.setMinimumSize(1100, 700)

        # Core Controller
        self.camera_index = 0
        self.pipeline_controller = PipelineController(self)

        # Central layout container
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet(f"background-color: {BG_VOID};")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Persistent Navigation Rail
        self.sidebar = NavigationSidebar(self)
        self.sidebar.page_changed.connect(self._on_navigate)
        root_layout.addWidget(self.sidebar)

        # 2. Right Content Column (TopBar + QStackedWidget)
        right_column = QVBoxLayout()
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(0)

        self.top_bar = TopBar(self)
        right_column.addWidget(self.top_bar)

        # Stacked Pages
        self.stacked_widget = QStackedWidget(self)

        self.home_view = MissionHomeView(self)
        self.experiments_view = ExperimentsView(self)
        self.live_monitor_view = LiveMonitorView(self)
        self.log_view = MissionLogView(self)
        self.settings_view = SettingsView(self)
        self.report_view = MissionReportView(self)

        self.stacked_widget.addWidget(self.home_view)         # 0
        self.stacked_widget.addWidget(self.experiments_view)  # 1
        self.stacked_widget.addWidget(self.live_monitor_view) # 2
        self.stacked_widget.addWidget(self.log_view)          # 3
        self.stacked_widget.addWidget(self.settings_view)      # 4
        self.stacked_widget.addWidget(self.report_view)        # 5

        right_column.addWidget(self.stacked_widget, 1)
        root_layout.addLayout(right_column, 1)

        self._wire_signals()

    def _wire_signals(self):
        """Connect controllers and views."""
        # 1. Pipeline Controller to Views
        self.pipeline_controller.frame_ready.connect(self._on_frame_ready)
        self.pipeline_controller.step_advanced.connect(self._on_step_advanced)
        self.pipeline_controller.deviation_detected.connect(self._on_deviation_detected)
        self.pipeline_controller.mission_completed.connect(self._on_mission_completed)
        self.pipeline_controller.error_occurred.connect(self._on_pipeline_error)

        # 2. Live Monitor Actions
        self.live_monitor_view.start_stream_requested.connect(self._start_pipeline)
        self.live_monitor_view.stop_stream_requested.connect(self._stop_pipeline)
        self.live_monitor_view.reset_protocol_requested.connect(self._reset_protocol)

        # 3. Home & Experiment Navigation Requests
        self.home_view.start_mission_requested.connect(self._on_quick_launch)
        self.home_view.view_experiments_requested.connect(lambda: self._navigate_to(1))
        self.experiments_view.select_protocol_requested.connect(lambda _: self._on_quick_launch())

        # 4. Report View Actions
        self.report_view.restart_requested.connect(self._on_repeat_mission)
        self.report_view.return_home_requested.connect(lambda: self._navigate_to(0))

        # 5. Settings
        self.settings_view.camera_changed.connect(self._on_camera_changed)

    def _on_navigate(self, index: int):
        self.stacked_widget.setCurrentIndex(index)

    def _navigate_to(self, index: int):
        self.sidebar.set_active_index(index)
        self.stacked_widget.setCurrentIndex(index)

    def _on_quick_launch(self):
        """Navigate to Live Monitor and start pipeline."""
        self._navigate_to(2)
        if not self.pipeline_controller.is_running():
            self.live_monitor_view.set_streaming_ui(True)
            self._start_pipeline()

    def _start_pipeline(self):
        self.top_bar.start_mission_timer()
        self.top_bar.update_state("MONITORING", is_active=True)
        self.log_view.add_log_entry("STREAM_START", f"Camera {self.camera_index} stream active. Real-time inference running.", "SUCCESS")
        self.pipeline_controller.start_pipeline(camera_index=self.camera_index)

    def _stop_pipeline(self):
        self.top_bar.stop_mission_timer()
        self.top_bar.update_state("STANDBY", is_active=False)
        self.log_view.add_log_entry("STREAM_PAUSE", "Camera pipeline paused by operator.", "INFO")
        self.pipeline_controller.stop_pipeline()

    def _reset_protocol(self):
        self.pipeline_controller.reset_mission()
        self.live_monitor_view.timeline.reset_timeline()
        self.live_monitor_view.reset_compliance_alert()
        self.top_bar.update_state("READY", is_active=False)
        self.log_view.add_log_entry("SOP_RESET", "Protocol SOP-WATER-001 reset to Step 01 (bottle_pickup).", "INFO")

    def _on_repeat_mission(self):
        self._reset_protocol()
        self._navigate_to(2)
        self.live_monitor_view.set_streaming_ui(True)
        self._start_pipeline()

    def _on_camera_changed(self, cam_idx: int):
        self.camera_index = cam_idx
        self.log_view.add_log_entry("CONFIG", f"Selected optical camera sensor changed to Index {cam_idx}.", "INFO")
        if self.pipeline_controller.is_running():
            self._stop_pipeline()
            self._start_pipeline()

    def _on_frame_ready(self, q_image, telemetry: dict):
        if self.stacked_widget.currentIndex() == 2:
            self.live_monitor_view.update_frame(q_image, telemetry)

    def _on_step_advanced(self, step_data: dict):
        msg = step_data.get("status_message", "Step transitioned.")
        step_num = step_data.get("current_step_number")
        self.log_view.add_log_entry(f"STEP_0{step_num}_OK" if step_num else "STEP_OK", msg, "SUCCESS")

    def _on_deviation_detected(self, deviation_data: dict):
        dev_type = deviation_data.get("deviation_type", "VIOLATION")
        msg = deviation_data.get("status_message", "Sequence violation.")
        self.live_monitor_view.show_deviation_alert(deviation_data)
        self.log_view.add_log_entry(dev_type, msg, "WARNING")

    def _on_mission_completed(self, val_state: dict):
        logger.info("All 5 protocol steps successfully completed!")
        self.top_bar.stop_mission_timer()
        self.top_bar.update_state("MISSION COMPLETED", is_completed=True)
        self.log_view.add_log_entry("MISSION_SUCCESS", "All 5/5 steps of SOP-WATER-001 verified! Certification granted.", "SUCCESS")
        self._stop_pipeline()
        self.live_monitor_view.set_streaming_ui(False)
        self.stacked_widget.setCurrentIndex(5)  # Navigate to MissionReportView

    def _on_pipeline_error(self, err_msg: str):
        logger.error(f"Pipeline error: {err_msg}")
        self.live_monitor_view.set_streaming_ui(False)
        self.top_bar.update_state("SENSOR ERROR", is_active=False)
        self.log_view.add_log_entry("SENSOR_ERROR", err_msg, "ERROR")

    def closeEvent(self, event):
        """Clean resource destruction on window close."""
        logger.info("Closing application. Releasing pipeline resources...")
        self.pipeline_controller.stop_pipeline()
        event.accept()


def main():
    logger.info("Launching Stellar AI Astronaut FlightDeck...")
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
