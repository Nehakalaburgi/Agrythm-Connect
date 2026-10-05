"""SQLite stand-in for the Trust AI system of record (TRL 3)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS farmers(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, village TEXT,
  language TEXT NOT NULL CHECK(language IN ('hi','en')), phone TEXT);
CREATE TABLE IF NOT EXISTS farms(
  id INTEGER PRIMARY KEY, farmer_id INTEGER NOT NULL REFERENCES farmers(id),
  name TEXT NOT NULL, acres REAL);
CREATE TABLE IF NOT EXISTS crop_cycles(
  id INTEGER PRIMARY KEY, farm_id INTEGER NOT NULL REFERENCES farms(id),
  crop TEXT NOT NULL, stage TEXT, sowing_date TEXT);
CREATE TABLE IF NOT EXISTS observations(
  id INTEGER PRIMARY KEY, crop_cycle_id INTEGER NOT NULL REFERENCES crop_cycles(id),
  observed_by TEXT, notes TEXT, observed_at TEXT);
CREATE TABLE IF NOT EXISTS advisories(
  id INTEGER PRIMARY KEY, crop_cycle_id INTEGER NOT NULL REFERENCES crop_cycles(id),
  observation_id INTEGER REFERENCES observations(id),
  text_en TEXT NOT NULL, text_hi TEXT NOT NULL,
  approved_facts TEXT NOT NULL DEFAULT '{}',
  approved INTEGER NOT NULL DEFAULT 0, approved_by TEXT,
  followup_days INTEGER NOT NULL DEFAULT 3);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY, type TEXT NOT NULL,
  farmer_id INTEGER NOT NULL REFERENCES farmers(id),
  crop_cycle_id INTEGER NOT NULL REFERENCES crop_cycles(id),
  advisory_id INTEGER NOT NULL REFERENCES advisories(id),
  dedupe_key TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS conversations(
  id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL UNIQUE REFERENCES events(id),
  farmer_id INTEGER NOT NULL, crop_cycle_id INTEGER NOT NULL, advisory_id INTEGER NOT NULL,
  state TEXT NOT NULL,
  outcome TEXT CHECK(outcome IS NULL OR outcome IN
    ('Completed','Follow-up Required','Human Escalation','Unresolved')),
  intent TEXT, confidence REAL, summary TEXT, next_action TEXT,
  escalation_reason TEXT, entities TEXT, context_used TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS turns(
  id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  speaker TEXT NOT NULL CHECK(speaker IN ('agent','farmer')),
  text TEXT NOT NULL, intent TEXT, confidence REAL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS state_log(
  id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  from_state TEXT, to_state TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS escalations(
  id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  reason TEXT NOT NULL, recommended_handling TEXT,
  status TEXT NOT NULL DEFAULT 'awaiting_human', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS follow_ups(
  id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  farmer_id INTEGER NOT NULL, crop_cycle_id INTEGER NOT NULL,
  kind TEXT NOT NULL, due_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled');
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    return conn


def get_conversation(conn: sqlite3.Connection, conversation_id: int) -> dict:
    row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    if row is None:
        raise KeyError(f"conversation {conversation_id} not found")
    return dict(row)
