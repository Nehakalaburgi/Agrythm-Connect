import json

import pytest

from connect.db import get_conversation
from connect.models import TRANSITIONS, IllegalTransition, Outcome, State
from connect.orchestrator import transition

OUTCOMES = {o.value for o in Outcome}


def states(conn, cid):
    return [r["to_state"] for r in conn.execute(
        "SELECT to_state FROM state_log WHERE conversation_id=? ORDER BY id", (cid,))]


def test_completed_outcome_is_structured(conn, make_session):
    s = make_session(1)
    s.respond("haan theek hai")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Completed" and row["state"] == "S04_COMPLETED"
    assert row["intent"] == "confirm" and row["confidence"] >= 0.5
    assert row["summary"] and row["next_action"] == "execution_check_in_3d"
    ctx_used = json.loads(row["context_used"])
    assert ctx_used["context"]["advisory_id"] == 1 and ctx_used["adapter"] == "rule-based"
    fu = conn.execute("SELECT * FROM follow_ups WHERE conversation_id=?", (s.conversation_id,)).fetchall()
    assert len(fu) == 1 and fu[0]["kind"] == "execution_check"
    assert states(conn, s.conversation_id) == [
        "S01_SCHEDULED", "S02_CALLING", "S03_CONNECTED", "S04_COMPLETED"]


def test_done_completes_without_follow_up(conn, make_session):
    s = make_session(1)
    s.respond("kar diya")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Completed" and row["next_action"] == "none"
    assert json.loads(row["entities"])["action_status"] == "done"
    assert conn.execute("SELECT COUNT(*) FROM follow_ups").fetchone()[0] == 0


@pytest.mark.parametrize("text,days", [("kal karunga", 1), ("agle hafte karunga", 7), ("baad mein", 2)])
def test_delay_creates_follow_up_required(conn, make_session, text, days):
    s = make_session(1)
    s.respond(text)
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Follow-up Required"
    assert row["next_action"] == f"reminder_call_in_{days}d"
    assert conn.execute("SELECT kind FROM follow_ups WHERE conversation_id=?",
                        (s.conversation_id,)).fetchone()["kind"] == "reminder"


def test_escalation_is_recorded_with_reason_and_state(conn, make_session):
    s = make_session(1)
    s.respond("dose double kar du?")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Human Escalation" and row["state"] == "S12_AWAITING_HUMAN"
    assert row["escalation_reason"] == "agronomic_question_outside_approved_context:decision"
    assert row["next_action"] == "sme_callback_within_24h"
    esc = conn.execute("SELECT * FROM escalations WHERE conversation_id=?", (s.conversation_id,)).fetchone()
    assert esc["status"] == "awaiting_human" and esc["reason"] == row["escalation_reason"]
    assert states(conn, s.conversation_id)[-2:] == ["S11_HUMAN_ESCALATION", "S12_AWAITING_HUMAN"]


def test_rejection_captures_barrier_and_escalates(conn, make_session):
    s = make_session(1)
    s.respond("nahi karunga, paise nahi hain")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Human Escalation"
    assert json.loads(row["entities"])["barrier"] == "cost"


def test_hang_up_without_commitment_is_unresolved(conn, make_session):
    s = make_session(1)
    s.hang_up()
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Unresolved" and row["next_action"] == "retry_call"
    assert row["state"] == "S04_COMPLETED"


def test_question_answered_but_no_commitment_is_unresolved(conn, make_session):
    s = make_session(1)
    s.respond("kab spray karna hai?")
    assert get_conversation(conn, s.conversation_id)["outcome"] is None  # still open
    s.hang_up()
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Unresolved"
    assert "timing" in json.loads(row["context_used"])["approved_facts_used"]


def test_answer_then_confirm_completes(conn, make_session):
    s = make_session(1)
    s.respond("kitna daalna hai?")
    s.respond("theek hai, kar dunga")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Completed"
    assert json.loads(row["context_used"])["approved_facts_used"] == ["dose"]


def test_clarification_loop_then_escalation(conn, make_session):
    s = make_session(1)
    s.respond("samajh nahi aaya")
    s.respond("phir se batao")
    assert s._state() == State.CONNECTED and not s.closed
    s.respond("samajh nahi aaya")
    row = get_conversation(conn, s.conversation_id)
    assert row["outcome"] == "Human Escalation"
    assert row["escalation_reason"] == "farmer_did_not_understand_after_clarification"
    assert "S10_CLARIFICATION_REQUIRED" in states(conn, s.conversation_id)


def test_every_end_state_has_one_of_four_outcomes(conn, make_session):
    for farmer, text in [(1, "haan"), (2, "kal"), (3, "mix kar sakte hain kya?"), (5, None)]:
        s = make_session(farmer)
        s.respond(text) if text else s.hang_up()
        assert get_conversation(conn, s.conversation_id)["outcome"] in OUTCOMES


def test_all_four_outcomes_are_reachable(conn, make_session):
    seen = set()
    for farmer, text in [(1, "haan"), (2, "kal"), (3, "mix kar sakte hain kya?"), (5, None)]:
        s = make_session(farmer)
        s.respond(text) if text else s.hang_up()
        seen.add(get_conversation(conn, s.conversation_id)["outcome"])
    assert seen == OUTCOMES


def test_english_farmer_gets_english_conversation(conn, make_session):
    s = make_session(5)
    first = conn.execute("SELECT text FROM turns WHERE conversation_id=? ORDER BY id LIMIT 1",
                         (s.conversation_id,)).fetchone()["text"]
    assert first.startswith("Hello Lakshmi Narayan") and "Agrythm" in first
    assert "Tie the plants to stakes" in first and "recorded" in first
    assert "नमस्ते" in conn.execute(
        "SELECT text FROM turns WHERE conversation_id=? ORDER BY id LIMIT 1",
        (make_session(1).conversation_id,)).fetchone()["text"]


def test_illegal_transitions_are_rejected_and_not_logged(conn, make_session):
    s = make_session(1)
    before = len(states(conn, s.conversation_id))
    with pytest.raises(IllegalTransition):
        transition(conn, s.conversation_id, State.SCHEDULED)
    with pytest.raises(IllegalTransition):
        transition(conn, s.conversation_id, State.RESOLVED)
    assert len(states(conn, s.conversation_id)) == before


def test_transition_table_covers_all_14_states():
    assert set(TRANSITIONS) == set(State) and len(State) == 14


def test_database_rejects_invalid_outcome(conn, make_session):
    s = make_session(1)
    with pytest.raises(Exception):
        conn.execute("UPDATE conversations SET outcome='Conversation happened' WHERE id=?",
                     (s.conversation_id,))


def test_every_turn_is_logged_for_audit(conn, make_session):
    s = make_session(1)
    s.respond("kab spray karna hai?")
    s.respond("haan theek hai")
    rows = conn.execute("SELECT speaker, intent FROM turns WHERE conversation_id=? ORDER BY id",
                        (s.conversation_id,)).fetchall()
    assert [r["speaker"] for r in rows] == ["agent", "farmer", "agent", "farmer", "agent"]
    assert rows[1]["intent"] == "question" and rows[3]["intent"] == "confirm"
