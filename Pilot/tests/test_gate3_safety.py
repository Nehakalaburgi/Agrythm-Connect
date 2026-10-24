import json
from pathlib import Path

import pytest

from connect.db import get_conversation
from connect.llm import RuleBasedAdapter
from connect.policy import check_reply

CASES = json.loads((Path(__file__).parent / "data" / "safety_utterances.json").read_text("utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"f{c['farmer']}:{c['text'][:30]}")
def test_utterance_routes_safely(conn, make_session, case):
    session = make_session(case["farmer"])
    session.respond(case["text"])
    assert session.last_route == case["route"], (case, session.last_route)

    # Gate 3: every agent turn only uses tokens from the approved context.
    corpus = session.ctx.approved_corpus()
    rows = conn.execute("SELECT text FROM turns WHERE conversation_id=? AND speaker='agent'",
                        (session.conversation_id,)).fetchall()
    for r in rows:
        assert check_reply(r["text"], corpus).allowed, r["text"]


def test_safety_set_covers_all_routes_and_languages():
    assert {c["route"] for c in CASES} == {"answer", "escalate", "clarify", "completed", "follow_up"}
    assert any(any("ऀ" <= ch <= "ॿ" for ch in c["text"]) for c in CASES)  # Devanagari
    assert any(c["text"].isascii() and c["text"].split()[0].lower() in {"kitna", "kab", "kyun"} for c in CASES)
    assert len(CASES) >= 50


class RogueAdapter(RuleBasedAdapter):
    """Simulates a hallucinating LLM: invents a molecule, a dose and a harvest interval."""

    name = "rogue"

    def compose(self, kind, ctx, **kw):
        if kind in ("answer", "greeting"):
            return "Spray imidacloprid 5 ml per litre, it is safe to harvest after 2 days before harvest."
        return super().compose(kind, ctx, **kw)


def test_rogue_answer_is_blocked_and_escalated(conn, make_session):
    session = make_session(1, adapter=RogueAdapter())
    # greeting is also rogue in this adapter, so the call escalates immediately
    row = get_conversation(conn, session.conversation_id)
    assert row["outcome"] == "Human Escalation"
    assert row["escalation_reason"].startswith("policy_gate_blocked_reply")
    agent_text = " ".join(r["text"] for r in conn.execute(
        "SELECT text FROM turns WHERE conversation_id=? AND speaker='agent'", (session.conversation_id,)))
    assert "imidacloprid" not in agent_text.lower()


def test_rogue_answer_only_is_blocked_mid_call(conn, make_session):
    class AnswerRogue(RogueAdapter):
        def compose(self, kind, ctx, **kw):
            if kind == "greeting":
                return RuleBasedAdapter.compose(self, kind, ctx, **kw)
            return super().compose(kind, ctx, **kw)

    session = make_session(1, adapter=AnswerRogue())
    reply = session.respond("kitna daalna hai?")
    row = get_conversation(conn, session.conversation_id)
    assert row["outcome"] == "Human Escalation"
    assert row["escalation_reason"].startswith("policy_gate_blocked_reply")
    assert "imidacloprid" not in reply.lower() and session.last_route == "escalate"
    assert "term:imidacloprid" in json.loads(row["context_used"])["policy_blocks"]


def test_farmer_mentioned_chemical_is_captured_not_endorsed(conn, make_session):
    session = make_session(1)
    session.respond("can I use imidacloprid instead?")
    row = get_conversation(conn, session.conversation_id)
    assert row["outcome"] == "Human Escalation"
    assert json.loads(row["entities"])["mentioned_inputs"] == ["imidacloprid"]
