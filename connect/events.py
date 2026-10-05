"""Trigger layer — Gate 1 (trigger integrity).

A valid, approved event creates exactly one conversation for the right farmer and crop cycle.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .db import now
from .models import State

ACCEPTED_TYPES = {"visit_complete", "advisory_approved", "follow_up_due"}
FUTURE_TYPES = {"risk_detected"}  # sensor / satellite events: parked in docs/FUTURE.md


class EventError(ValueError):
    pass


@dataclass
class EventResult:
    event_id: int
    conversation_id: int
    created: bool  # False when an identical event already existed (idempotent)


def create_event(
    conn: sqlite3.Connection,
    type: str,
    farmer_id: int,
    crop_cycle_id: int,
    advisory_id: int,
    dedupe_key: str | None = None,
) -> EventResult:
    if type in FUTURE_TYPES:
        raise EventError(f"event type '{type}' is not supported before a later TRL")
    if type not in ACCEPTED_TYPES:
        raise EventError(f"unknown event type '{type}'")

    if conn.execute("SELECT 1 FROM farmers WHERE id=?", (farmer_id,)).fetchone() is None:
        raise EventError(f"unknown farmer {farmer_id}")

    cycle = conn.execute(
        "SELECT cc.id FROM crop_cycles cc JOIN farms f ON f.id=cc.farm_id "
        "WHERE cc.id=? AND f.farmer_id=?",
        (crop_cycle_id, farmer_id),
    ).fetchone()
    if cycle is None:
        raise EventError(f"crop cycle {crop_cycle_id} does not belong to farmer {farmer_id}")

    adv = conn.execute(
        "SELECT approved FROM advisories WHERE id=? AND crop_cycle_id=?",
        (advisory_id, crop_cycle_id),
    ).fetchone()
    if adv is None:
        raise EventError(f"advisory {advisory_id} does not belong to crop cycle {crop_cycle_id}")
    if not adv["approved"]:
        raise EventError(f"advisory {advisory_id} is not approved")

    key = dedupe_key or f"{type}:{crop_cycle_id}:{advisory_id}"
    existing = conn.execute(
        "SELECT e.id AS eid, c.id AS cid FROM events e JOIN conversations c ON c.event_id=e.id "
        "WHERE e.dedupe_key=?",
        (key,),
    ).fetchone()
    if existing:
        return EventResult(existing["eid"], existing["cid"], created=False)

    ts = now()
    with conn:
        eid = conn.execute(
            "INSERT INTO events(type,farmer_id,crop_cycle_id,advisory_id,dedupe_key,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (type, farmer_id, crop_cycle_id, advisory_id, key, ts),
        ).lastrowid
        cid = conn.execute(
            "INSERT INTO conversations(event_id,farmer_id,crop_cycle_id,advisory_id,state,"
            "created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (eid, farmer_id, crop_cycle_id, advisory_id, State.SCHEDULED.value, ts, ts),
        ).lastrowid
        conn.execute(
            "INSERT INTO state_log(conversation_id,from_state,to_state,note,created_at) "
            "VALUES(?,?,?,?,?)",
            (cid, None, State.SCHEDULED.value, f"created by event {type}", ts),
        )
    return EventResult(eid, cid, created=True)
