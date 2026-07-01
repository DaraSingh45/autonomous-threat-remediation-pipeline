from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.environ.get("AUDIT_DB_PATH", "/data/audit.db"))

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_records (
    audit_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    detection_id TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    remediation_id TEXT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    namespace TEXT,
    severity TEXT NOT NULL,
    event_type TEXT NOT NULL,
    action TEXT NOT NULL,
    mode TEXT NOT NULL,
    detection_source TEXT NOT NULL,
    rule_name TEXT,
    anomaly_score REAL,
    event_timestamp_ms INTEGER NOT NULL,
    detected_at_ms INTEGER NOT NULL,
    decided_at_ms INTEGER NOT NULL,
    remediation_started_ms INTEGER,
    completed_at_ms INTEGER,
    mttd_ms INTEGER,
    mttr_ms INTEGER,
    success INTEGER NOT NULL,
    details TEXT,
    raw_event TEXT,
    inserted_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_records(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_mode ON audit_records(mode);
CREATE INDEX IF NOT EXISTS idx_audit_inserted ON audit_records(inserted_at_ms);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    with _lock:
        conn.executescript(SCHEMA)
        conn.commit()


def insert_record(conn: sqlite3.Connection, record: dict) -> None:
    import time

    with _lock:
        conn.execute(
            """
            INSERT OR REPLACE INTO audit_records (
                audit_id, event_id, detection_id, decision_id, remediation_id,
                entity_type, entity_id, namespace, severity, event_type,
                action, mode, detection_source, rule_name, anomaly_score,
                event_timestamp_ms, detected_at_ms, decided_at_ms,
                remediation_started_ms, completed_at_ms, mttd_ms, mttr_ms,
                success, details, raw_event, inserted_at_ms
            ) VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?, ?,?,?, ?,?,?,?, ?,?,?,?)
            """,
            (
                record["audit_id"], record["event_id"], record["detection_id"], record["decision_id"],
                record.get("remediation_id"), record["entity_type"], record["entity_id"], record.get("namespace"),
                record["severity"], record["event_type"], record["action"], record["mode"],
                record["detection_source"], record.get("rule_name"), record.get("anomaly_score"),
                record["event_timestamp_ms"], record["detected_at_ms"], record["decided_at_ms"],
                record.get("remediation_started_ms"), record.get("completed_at_ms"),
                record.get("mttd_ms"), record.get("mttr_ms"),
                1 if record["success"] else 0, record.get("details"),
                json.dumps(record.get("raw_event") or {}), int(time.time() * 1000),
            ),
        )
        conn.commit()


def list_records(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list[dict]:
    cur = conn.execute(
        "SELECT * FROM audit_records ORDER BY inserted_at_ms DESC LIMIT ? OFFSET ?", (limit, offset)
    )
    return [dict(row) for row in cur.fetchall()]


def get_record(conn: sqlite3.Connection, audit_id: str) -> Optional[dict]:
    cur = conn.execute("SELECT * FROM audit_records WHERE audit_id = ?", (audit_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def stats_by_mode(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute(
        """
        SELECT mode,
               COUNT(*) AS total,
               AVG(mttd_ms) AS avg_mttd_ms,
               AVG(mttr_ms) AS avg_mttr_ms,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_count
        FROM audit_records
        WHERE action != 'monitor'
        GROUP BY mode
        """
    )
    return [dict(row) for row in cur.fetchall()]
