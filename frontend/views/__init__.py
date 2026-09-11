"""
Views package for Stellar AI desktop application.
"""
from frontend.views.mission_home_view import MissionHomeView
from frontend.views.experiments_view import ExperimentsView
from frontend.views.live_monitor_view import LiveMonitorView
from frontend.views.mission_report_view import MissionReportView
from frontend.views.mission_log_view import MissionLogView
from frontend.views.settings_view import SettingsView

__all__ = [
    "MissionHomeView",
    "ExperimentsView",
    "LiveMonitorView",
    "MissionReportView",
    "MissionLogView",
    "SettingsView",
]
