import json

import pytest

from connect.context import ContextError, build_context
from connect.events import create_event


def test_context_has_correct_farmer_crop_and_approved_advisory(conn):
    r = create_event(conn, "advisory_approved", 1, 1, 1)
    ctx = build_context(conn, r.conversation_id)
    assert ctx.farmer_name == "Ramesh Yadav"
    assert ctx.crop == "tomato" and ctx.stage == "flowering" and ctx.acres == 2.5
    assert ctx.advisory_id == 1 and ctx.approved_by == "Demo SME"
    assert "leaf spotting" in ctx.observation_notes
    assert set(ctx.approved_facts) == {"dose", "timing", "why"}


def test_language_selects_advisory_text(conn):
    hi = build_context(conn, create_event(conn, "advisory_approved", 1, 1, 1).conversation_id)
    en = build_context(conn, create_event(conn, "advisory_approved", 5, 5, 5).conversation_id)
    assert hi.language == "hi" and hi.advisory_text == hi.advisory_hi
    assert en.language == "en" and en.advisory_text == en.advisory_en
    assert "नीम" in hi.fact("dose") and en.fact("dose") is None


def test_approved_corpus_contains_advisory_and_facts(conn):
    ctx = build_context(conn, create_event(conn, "advisory_approved", 1, 1, 1).conversation_id)
    corpus = ctx.approved_corpus()
    assert "3 ml per litre" in corpus and "3 मिली" in corpus


def test_unapproved_advisory_after_trigger_is_refused(conn):
    r = create_event(conn, "advisory_approved", 1, 1, 1)
    conn.execute("UPDATE advisories SET approved=0 WHERE id=1")
    with pytest.raises(ContextError, match="not approved"):
        build_context(conn, r.conversation_id)


def test_mismatched_cycle_is_refused(conn):
    r = create_event(conn, "advisory_approved", 1, 1, 1)
    conn.execute("UPDATE conversations SET crop_cycle_id=2 WHERE id=?", (r.conversation_id,))
    with pytest.raises(ContextError):
        build_context(conn, r.conversation_id)


def test_malformed_approved_facts_are_refused(conn):
    r = create_event(conn, "advisory_approved", 1, 1, 1)
    conn.execute("UPDATE advisories SET approved_facts=? WHERE id=1",
                 (json.dumps({"dose": {"en": "only english"}}),))
    with pytest.raises(ContextError, match="en' and 'hi"):
        build_context(conn, r.conversation_id)


def test_previous_conversations_are_included(conn, make_session):
    first = make_session(1)
    first.respond("haan theek hai")
    second = create_event(conn, "visit_complete", 1, 1, 1)
    ctx = build_context(conn, second.conversation_id)
    assert len(ctx.previous) == 1 and ctx.previous[0]["outcome"] == "Completed"
