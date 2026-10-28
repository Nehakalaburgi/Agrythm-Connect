import io
import json
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date, datetime

import pytest

from weathercall.adapters.local import InMemoryFarmerSource, SQLiteLedger
from weathercall.adapters.mock import MockTelephony, MockVoice, MockWeather
from weathercall.adapters.sarvam_campaign import IST, CampaignStore, SarvamCampaigns
from weathercall.campaign import push, sync
from weathercall.config import Settings
from weathercall.contracts import FarmerContext, FinalResult, Language, SkipReason
from weathercall.engine import Ports
from weathercall.schedule import task_xml

D = date(2026, 10, 27)
ENV = {"SARVAM_AGENT_API_KEY": "sk-agent", "SARVAM_ORG_ID": "org1", "SARVAM_WORKSPACE_ID": "ws1",
       "SARVAM_APP_ID": "app1", "SARVAM_CONNECTION_ID": "conn1", "SARVAM_AGENT_PHONE": "+918000000000"}


def farmer(i, place="Mandya", consent=True, lang=Language.HI):
    return FarmerContext(f"F{i}", f"Name{i}", lang, place, 12.5, 76.9, consent, True, f"98765432{i:02d}")


class FakeSarvam:
    def __init__(self, attempts=None):
        self.requests, self.attempt_items = [], attempts or []

    def __call__(self, req, timeout):
        self.requests.append(req)
        path = urllib.parse.urlparse(req.full_url).path
        if path.endswith("/campaigns"):
            return io.BytesIO(json.dumps({"campaign_id": "camp-1", "status": "scheduled"}).encode())
        if path.endswith("/cohorts/stream"):
            return io.BytesIO(json.dumps({"cohort_id": "coh-1", "status": "processing"}).encode())
        return io.BytesIO(json.dumps({"items": self.attempt_items, "next_page_uri": ""}).encode())

    def bodies(self, suffix):
        return [json.loads(r.data) for r in self.requests if urllib.parse.urlparse(r.full_url).path.endswith(suffix)]


def setup(farmers, attempts=None):
    http = FakeSarvam(attempts)
    api = SarvamCampaigns(env=ENV, opener=http)
    store = CampaignStore()
    store.save_campaign("camp-1", D, 4, "09:00", "11:00")
    ports = Ports(InMemoryFarmerSource(farmers), SQLiteLedger(), MockWeather(), MockVoice(), MockTelephony())
    return ports, store, api, http


def test_create_campaign_window_retries_and_timezone():
    http = FakeSarvam()
    cid = SarvamCampaigns(env=ENV, opener=http).create_campaign("Gate0", D, 4, "09:00", "11:00", 3, 30)
    body = http.bodies("/campaigns")[0]
    assert cid == "camp-1"
    assert body["start_timestamp"] == "2026-10-27T09:00:00+05:30" and body["end_timestamp"] == "2026-10-30T11:00:00+05:30"
    assert body["allowed_schedule"]["allowed_start_time"] == "09:00" and body["allowed_schedule"]["timezone"] == "Asia/Kolkata"
    assert len(body["allowed_schedule"]["allowed_days"]) == 7
    rc = body["app_config"]["retry_config"]
    assert rc["max_retries"] == 2 and rc["retry_interval_minutes"] == 30 and rc["retry_on"]["no_answer"]["enabled"]
    assert body["app_config"]["connection_configs"][0]["phone_numbers"] == ["+918000000000"]


def test_push_sends_only_eligible_farmers_with_their_message_once():
    ports, store, api, http = setup([farmer(1), farmer(2, lang=Language.EN, place="Mysuru"),
                                     farmer(3, consent=False), farmer(4, place="Nowhere")])
    out = push(D, ports, Settings(), store, api)
    users = http.bodies("/cohorts/stream")[0]["users"]
    assert [u["user_identifier"] for u in users] == ["F1", "F2"]
    assert users[0]["user_phone_number"] == "+919876543201"
    assert users[0]["app_overrides"]["initial_language_name"] == "Hindi" and "एआई" in users[0]["app_overrides"]["initial_bot_message"]
    assert users[1]["app_overrides"]["initial_language_name"] == "English" and "AI" in users[1]["app_overrides"]["initial_bot_message"]
    rows = {r.farmer_id: r for r in ports.ledger.status(D).rows}
    assert rows["F3"].skip_reason is SkipReason.NO_CONSENT and rows["F4"].skip_reason is SkipReason.NO_WEATHER
    assert "pushed 2" in out[0]
    push(D, ports, Settings(), store, api)                    # a second run the same day pushes nobody
    assert len(http.bodies("/cohorts/stream")) == 1
    assert "98765432" not in repr(store.db.execute("SELECT * FROM sarvam_queue").fetchall())


def test_push_without_campaign_does_nothing():
    ports, _, api, http = setup([farmer(1)])
    out = push(D, ports, Settings(), CampaignStore(), api)
    assert "no Sarvam campaign" in out[0] and http.requests == []


def attempt(fid, status, n, nxt="UNKNOWN", dur=0):
    return {"attempt_id": f"a-{fid}-{n}", "user_identifier": fid, "connectivity_status": status, "retry_attempt": n,
            "next_action_status": nxt, "duration_in_seconds": dur, "failure_reason": "NO_FAILURE_REASON",
            "user_contact": "+919999999999"}


def test_sync_records_final_results_and_leaves_retries_pending():
    farmers = [farmer(1), farmer(2), farmer(3), farmer(4)]
    items = [attempt("F1", "no_answer", 1, "retry"), attempt("F1", "connected", 2, dur=38),
             attempt("F2", "no_answer", 1, "retry"), attempt("F2", "busy", 2, "retry"), attempt("F2", "no_answer", 3),
             attempt("F3", "no_answer", 1, "retry")]
    ports, store, api, _ = setup(farmers, items)
    push(D, ports, Settings(), store, api)
    during = datetime(2026, 10, 27, 10, 0, tzinfo=IST)
    out = sync(D, ports, store, api, now=during)
    rows = {r.farmer_id: r for r in ports.ledger.status(D).rows}
    assert (rows["F1"].result, rows["F1"].attempts) == (FinalResult.ANSWERED, 2)
    assert (rows["F2"].result, rows["F2"].attempts) == (FinalResult.UNANSWERED, 3)
    assert "F3" not in rows and "F4" not in rows and "still in progress 2" in out[0]
    dur = ports.ledger.db.execute("SELECT duration_s, provider_call_id FROM attempts WHERE farmer_id='F1' AND attempt_no=2")
    assert dur.fetchone() == (38, "a-F1-2")
    after = datetime(2026, 10, 27, 13, 0, tzinfo=IST)
    sync(D, ports, store, api, now=after)                    # F4 was never dialled in the window -> failed
    rows = {r.farmer_id: r for r in ports.ledger.status(D).rows}
    assert rows["F4"].result is FinalResult.FAILED and "F3" not in rows
    assert ports.ledger.db.execute("SELECT COUNT(*) FROM attempts WHERE farmer_id='F1'").fetchone()[0] == 2


def test_api_errors_keep_only_the_code():
    def reject(req, timeout):
        body = io.BytesIO(json.dumps({"error": {"code": "invalid_phone", "message": "bad +919876543210"}}).encode())
        raise urllib.error.HTTPError(req.full_url, 422, "Unprocessable", {}, body)
    with pytest.raises(RuntimeError) as e:
        SarvamCampaigns(env=ENV, opener=reject).create_campaign("x", D, 1, "09:00", "11:00", 1, 30)
    assert "422 invalid_phone" in str(e.value) and "9876543210" not in str(e.value)


def test_campaign_task_runs_daily_push_and_one_extra_day(tmp_path):
    xml = task_xml(D, 4, "08:30", r"C:\Python\python.exe", tmp_path, mode="campaign")
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    root = ET.fromstring(xml.split("?>", 1)[1])
    trig = root.find("t:Triggers/t:CalendarTrigger", ns)
    assert trig.find("t:StartBoundary", ns).text == "2026-10-27T08:30:00"
    assert trig.find("t:EndBoundary", ns).text == "2026-10-31T23:59:59"
    assert "weathercall.campaign daily" in root.find("t:Actions/t:Exec/t:Arguments", ns).text
