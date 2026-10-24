"""Context builder — Gate 2 (context integrity).

Builds the pack the agent is allowed to use. Fails loudly (before any call) if anything is
missing, mismatched or unapproved.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field


class ContextError(ValueError):
    pass


@dataclass
class ContextPack:
    conversation_id: int
    event_type: str
    farmer_id: int
    farmer_name: str
    village: str | None
    language: str
    farm_name: str
    acres: float | None
    crop_cycle_id: int
    crop: str
    stage: str | None
    observation_notes: str | None
    observed_by: str | None
    advisory_id: int
    advisory_en: str
    advisory_hi: str
    approved_facts: dict
    approved_by: str | None
    followup_days: int
    previous: list = field(default_factory=list)

    @property
    def advisory_text(self) -> str:
        return self.advisory_hi if self.language == "hi" else self.advisory_en

    def fact(self, topic: str | None) -> str | None:
        f = self.approved_facts.get(topic or "")
        return f.get(self.language) if f else None

    def approved_corpus(self) -> str:
        """Everything the agent is allowed to say (used by the policy gate)."""
        parts = [self.advisory_en, self.advisory_hi]
        for f in self.approved_facts.values():
            parts.extend([f.get("en", ""), f.get("hi", "")])
        return "\n".join(parts)

    def audit_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "event_type": self.event_type,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "language": self.language,
            "crop_cycle_id": self.crop_cycle_id,
            "crop": self.crop,
            "stage": self.stage,
            "advisory_id": self.advisory_id,
            "approved_by": self.approved_by,
            "approved_fact_topics": sorted(self.approved_facts),
            "previous_conversations": len(self.previous),
        }


def build_context(conn: sqlite3.Connection, conversation_id: int) -> ContextPack:
    conv = conn.execute(
        "SELECT c.id, c.farmer_id, c.crop_cycle_id, c.advisory_id, e.type AS event_type "
        "FROM conversations c JOIN events e ON e.id=c.event_id WHERE c.id=?",
        (conversation_id,),
    ).fetchone()
    if conv is None:
        raise ContextError(f"conversation {conversation_id} not found")

    farmer = conn.execute("SELECT * FROM farmers WHERE id=?", (conv["farmer_id"],)).fetchone()
    if farmer is None:
        raise ContextError(f"farmer {conv['farmer_id']} not found")

    cycle = conn.execute(
        "SELECT cc.*, f.name AS farm_name, f.acres, f.farmer_id AS owner "
        "FROM crop_cycles cc JOIN farms f ON f.id=cc.farm_id WHERE cc.id=?",
        (conv["crop_cycle_id"],),
    ).fetchone()
    if cycle is None:
        raise ContextError(f"crop cycle {conv['crop_cycle_id']} not found")
    if cycle["owner"] != farmer["id"]:
        raise ContextError("crop cycle does not belong to this farmer")

    adv = conn.execute("SELECT * FROM advisories WHERE id=?", (conv["advisory_id"],)).fetchone()
    if adv is None or adv["crop_cycle_id"] != cycle["id"]:
        raise ContextError("advisory missing or does not belong to this crop cycle")
    if not adv["approved"]:
        raise ContextError("advisory is not approved; the agent may not use it")

    try:
        facts = json.loads(adv["approved_facts"] or "{}")
    except json.JSONDecodeError as exc:
        raise ContextError(f"approved_facts is not valid JSON: {exc}") from exc
    for topic, f in facts.items():
        if not isinstance(f, dict) or not f.get("en") or not f.get("hi"):
            raise ContextError(f"approved fact '{topic}' needs both 'en' and 'hi' text")

    obs = None
    if adv["observation_id"]:
        obs = conn.execute("SELECT * FROM observations WHERE id=?", (adv["observation_id"],)).fetchone()
    if obs is None:
        obs = conn.execute(
            "SELECT * FROM observations WHERE crop_cycle_id=? ORDER BY observed_at DESC, id DESC LIMIT 1",
            (cycle["id"],),
        ).fetchone()

    previous = [
        dict(r)
        for r in conn.execute(
            "SELECT id, outcome, summary, next_action FROM conversations "
            "WHERE farmer_id=? AND id<>? AND outcome IS NOT NULL ORDER BY id DESC LIMIT 3",
            (farmer["id"], conversation_id),
        )
    ]

    return ContextPack(
        conversation_id=conversation_id,
        event_type=conv["event_type"],
        farmer_id=farmer["id"],
        farmer_name=farmer["name"],
        village=farmer["village"],
        language=farmer["language"],
        farm_name=cycle["farm_name"],
        acres=cycle["acres"],
        crop_cycle_id=cycle["id"],
        crop=cycle["crop"],
        stage=cycle["stage"],
        observation_notes=obs["notes"] if obs else None,
        observed_by=obs["observed_by"] if obs else None,
        advisory_id=adv["id"],
        advisory_en=adv["text_en"],
        advisory_hi=adv["text_hi"],
        approved_facts=facts,
        approved_by=adv["approved_by"],
        followup_days=adv["followup_days"],
        previous=previous,
    )
