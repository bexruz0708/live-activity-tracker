import json
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = os.getenv("DB_PATH", "data.db")
TZ = ZoneInfo("Asia/Tashkent")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS windows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                label TEXT NOT NULL,
                n_samples INTEGER NOT NULL,
                sample_rate REAL NOT NULL,
                user_agent TEXT,
                samples_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def insert_window(user_id, session_id, label, samples, sample_rate, user_agent):
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO windows
            (created_at, user_id, session_id, label, n_samples, sample_rate, user_agent, samples_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(TZ).isoformat(timespec="seconds"),
                user_id,
                session_id,
                label,
                len(samples),
                sample_rate,
                user_agent,
                json.dumps(samples),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def stats():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT label, COUNT(*) AS windows, COUNT(DISTINCT session_id) AS sessions
            FROM windows GROUP BY label
            """
        ).fetchall()
        users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM windows").fetchone()[0]
    finally:
        conn.close()
    by_label = {r["label"]: {"windows": r["windows"], "sessions": r["sessions"]} for r in rows}
    return {"by_label": by_label, "users": users}