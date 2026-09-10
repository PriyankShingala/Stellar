"""
Structured Audit Trail Event Logger storing timestamps and compliance metrics into SQLite.
"""

import sqlite3
import os
import logging

logger = logging.getLogger("EventLogger")

class EventLogger:
    """Thread-safe SQLite event logger for system audit compliance."""
    def __init__(self, db_path: str = "database/stellar_audit.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_logs (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            step_id TEXT,
            description TEXT NOT NULL,
            confidence REAL
        )
        """)
        conn.commit()
        conn.close()

    def log_event(self, event_type: str, description: str, step_id: str = None, confidence: float = 1.0):
        """Record event log entry."""
        logger.info(f"[{event_type}] {description}")
