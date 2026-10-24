import pytest

from connect.db import connect
from connect.events import create_event
from connect.orchestrator import ConversationSession
from connect.seed import seed_demo


@pytest.fixture
def conn():
    c = connect(":memory:")
    seed_demo(c)
    return c


@pytest.fixture
def make_session(conn):
    """make_session(farmer_id, adapter=None, open_call=True) -> ConversationSession.

    Demo data: farmer N owns crop cycle N and advisory N (advisory 4 is not approved).
    """

    def _make(farmer_id: int, adapter=None, open_call: bool = True) -> ConversationSession:
        ev = create_event(conn, "advisory_approved", farmer_id, farmer_id, farmer_id)
        session = ConversationSession(conn, ev.conversation_id, adapter=adapter)
        if open_call:
            session.open()
        return session

    return _make
