import pytest

from connect.events import EventError, create_event


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_valid_event_creates_exactly_one_conversation(conn):
    r = create_event(conn, "advisory_approved", 1, 1, 1)
    assert r.created
    assert count(conn, "events") == 1 and count(conn, "conversations") == 1
    conv = conn.execute("SELECT * FROM conversations WHERE id=?", (r.conversation_id,)).fetchone()
    assert (conv["farmer_id"], conv["crop_cycle_id"], conv["advisory_id"]) == (1, 1, 1)
    assert conv["state"] == "S01_SCHEDULED"


def test_duplicate_event_is_idempotent(conn):
    a = create_event(conn, "advisory_approved", 1, 1, 1)
    b = create_event(conn, "advisory_approved", 1, 1, 1)
    assert not b.created and a.conversation_id == b.conversation_id
    assert count(conn, "conversations") == 1


def test_different_event_types_each_get_one_conversation(conn):
    a = create_event(conn, "advisory_approved", 1, 1, 1)
    b = create_event(conn, "visit_complete", 1, 1, 1)
    assert a.conversation_id != b.conversation_id


def test_unapproved_advisory_is_rejected(conn):
    with pytest.raises(EventError, match="not approved"):
        create_event(conn, "advisory_approved", 4, 4, 4)
    assert count(conn, "conversations") == 0


def test_crop_cycle_of_another_farmer_is_rejected(conn):
    with pytest.raises(EventError, match="does not belong to farmer"):
        create_event(conn, "advisory_approved", 1, 2, 2)


def test_advisory_of_another_cycle_is_rejected(conn):
    with pytest.raises(EventError, match="does not belong to crop cycle"):
        create_event(conn, "advisory_approved", 1, 1, 2)


def test_unknown_farmer_is_rejected(conn):
    with pytest.raises(EventError, match="unknown farmer"):
        create_event(conn, "advisory_approved", 99, 1, 1)


def test_unsupported_and_future_event_types_are_rejected(conn):
    with pytest.raises(EventError):
        create_event(conn, "made_up", 1, 1, 1)
    with pytest.raises(EventError, match="later TRL"):
        create_event(conn, "risk_detected", 1, 1, 1)
    assert count(conn, "conversations") == 0
