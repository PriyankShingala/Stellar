-- SQLite Audit Database Schema for Stellar-AI / PRAYOG-AI

CREATE TABLE IF NOT EXISTS experiment_sessions (
    session_id TEXT PRIMARY KEY,
    protocol_id TEXT NOT NULL,
    operator_id TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'IN_PROGRESS'
);

CREATE TABLE IF NOT EXISTS event_logs (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL, -- 'ACTION_DETECTED', 'STEP_COMPLETED', 'SEQUENCE_VIOLATION', 'SYSTEM_ALERT'
    step_id TEXT,
    description TEXT NOT NULL,
    confidence REAL,
    FOREIGN KEY(session_id) REFERENCES experiment_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS step_durations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL,
    status TEXT DEFAULT 'PASSED', -- 'PASSED', 'TIMED_OUT', 'SKIPPED', 'VIOLATED'
    FOREIGN KEY(session_id) REFERENCES experiment_sessions(session_id)
);
