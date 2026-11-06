"""Tiny SQLite run store. On Streamlit Community Cloud the filesystem is ephemeral
(wiped on restart/redeploy), so the app has a 'Load demo history' button."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("VENDOR_DB", os.path.join(os.path.dirname(__file__), "runs.db"))


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute(
        """CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            legal_name TEXT, country TEXT, status TEXT, manual_review INTEGER,
            scenario TEXT, headline TEXT, n_checks INTEGER, n_passed INTEGER,
            duration_ms REAL, drafted_by TEXT,
            submission TEXT, result TEXT, email TEXT)"""
    )
    return c


def save_run(sub, stages, decision, email, scenario=None, duration_ms=0.0):
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO runs (created_at, legal_name, country, status, manual_review, scenario, headline,
               n_checks, n_passed, duration_ms, drafted_by, submission, result, email)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), sub.get("legal_name"), sub.get("country"),
             decision["status"], int(decision["manual_review"]), scenario, decision["headline"],
             decision["n_checks"], decision["n_passed"], duration_ms, (email or {}).get("drafted_by"),
             json.dumps(sub), json.dumps({"stages": stages, "decision": decision}), json.dumps(email)),
        )
        return cur.lastrowid


def list_runs(limit=500):
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id, created_at, legal_name, country, status, manual_review, scenario, headline, "
            "n_checks, n_passed, duration_ms, drafted_by FROM runs ORDER BY id DESC LIMIT ?", (limit,))]


def get_run(run_id):
    with _conn() as c:
        r = c.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["submission"] = json.loads(d["submission"])
    d["result"] = json.loads(d["result"])
    d["email"] = json.loads(d["email"]) if d["email"] else None
    return d


def latest_run_for(legal_name, country):
    """Most recent earlier run for the same business (used for resubmission diffing)."""
    with _conn() as c:
        r = c.execute(
            "SELECT id FROM runs WHERE lower(legal_name)=lower(?) AND country=? ORDER BY id DESC LIMIT 1",
            (legal_name, country)).fetchone()
    return get_run(r["id"]) if r else None


def count():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM runs").fetchone()[0]


def clear():
    with _conn() as c:
        c.execute("DELETE FROM runs")
