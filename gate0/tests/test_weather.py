import io
import json
import urllib.parse
from datetime import date

import pytest

from weathercall import ports as P
from weathercall.adapters.local import InMemoryFarmerSource, SQLiteLedger, demo_farmers
from weathercall.adapters.mock import MockTelephony, MockVoice
from weathercall.adapters.open_meteo import OpenMeteoWeather, geocode
from weathercall.adapters.sheet import load_farmers
from weathercall.adapters.weather_store import StoredWeather
from weathercall.config import Settings
from weathercall.contracts import FinalResult, SkipReason, WeatherReport
from weathercall.engine import Ports, run_morning

D = date(2026, 10, 27)
MANDYA_KA = {"name": "Mandya", "latitude": 12.52, "longitude": 76.9, "admin1": "Karnataka", "admin2": "Mandya"}
MANDYA_HR = {"name": "Mandya", "latitude": 28.97, "longitude": 77.19, "admin1": "Haryana", "admin2": "Sonipat"}


def fake(geo=None, daily=None):
    calls = []

    def opener(url, timeout):
        calls.append(url)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if "geocoding" in url:
            return io.BytesIO(json.dumps({"results": (geo or {}).get(q["name"][0], [])}).encode())
        return io.BytesIO(json.dumps({"daily": daily}).encode())
    opener.calls = calls
    return opener


def daily(code=3, tmin=18.2, tmax=28.5, rain=10, day="2026-10-27"):
    return {"time": [day], "weather_code": [code], "temperature_2m_min": [tmin], "temperature_2m_max": [tmax],
            "precipitation_probability_max": [rain]}


def test_geocode_picks_the_village_in_the_farmers_state_and_district():
    op = fake(geo={"Mandya": [MANDYA_HR, MANDYA_KA]})
    p = geocode("Mandya", "Mandya", "Karnataka", op)
    assert (p.latitude, p.longitude, p.level) == (12.52, 76.9, "village") and "Karnataka" in p.matched


def test_geocode_wrong_state_only_is_no_match():
    assert geocode("Mandya", "Mandya", "Karnataka", fake(geo={"Mandya": [MANDYA_HR]})) is None


def test_geocode_falls_back_to_district_centre():
    p = geocode("Tinyvillage", "Mandya", "Karnataka", fake(geo={"Mandya": [MANDYA_KA]}))
    assert p.level == "district" and p.latitude == 12.52


def test_forecast_parsed_into_report():
    w = OpenMeteoWeather(fake(daily=daily())).get_weather("Mandya", 12.52, 76.9, D)
    assert w == WeatherReport("Mandya", "cloudy", 18, 28, 10, "open-meteo")
    assert isinstance(OpenMeteoWeather(), P.WeatherProvider)


@pytest.mark.parametrize("bad", [daily(rain=None), daily(code=1234), daily(tmin=30, tmax=20), daily(day="2026-10-28"),
                                 {}, None])
def test_incomplete_or_odd_forecast_means_no_weather(bad):
    assert OpenMeteoWeather(fake(daily=bad)).get_weather("Mandya", 12.52, 76.9, D) is None


def test_no_coordinates_means_no_weather_and_no_request():
    op = fake(daily=daily())
    assert OpenMeteoWeather(op).get_weather("Mandya", 0.0, 0.0, D) is None and op.calls == []


class Counting:
    def __init__(self, report=None, boom=False):
        self.report, self.boom, self.n = report, boom, 0

    def get_weather(self, *a):
        self.n += 1
        if self.boom:
            raise TimeoutError("down")
        return self.report


def test_weather_is_stored_and_reused():
    inner = Counting(WeatherReport("Mandya", "clear", 20, 31, 0, "open-meteo"))
    s = StoredWeather(inner)
    first, again = s.get_weather("Mandya", 12.52, 76.9, D), s.get_weather("Mandya", 12.52, 76.9, D)
    assert first == again and inner.n == 1
    assert s.db.execute("SELECT summary, temp_max_c FROM weather").fetchall() == [("clear", 31)]


def test_missing_or_failing_weather_is_not_stored():
    for inner in (Counting(None), Counting(boom=True)):
        s = StoredWeather(inner)
        assert s.get_weather("X", 1.0, 1.0, D) is None
        assert s.db.execute("SELECT COUNT(*) FROM weather").fetchone()[0] == 0


def test_call_only_when_weather_stored():
    farmers = demo_farmers()[:2]
    class OnlyFirst:
        def get_weather(self, place, lat, lon, day):
            return WeatherReport(place, "clear", 20, 30, 0, "t") if place == "Mandya" else None
    ports = Ports(InMemoryFarmerSource(farmers), SQLiteLedger(), StoredWeather(OnlyFirst()), MockVoice(),
                  MockTelephony())
    v = run_morning(D, ports, Settings())
    rows = {r.farmer_id: r for r in v.rows}
    assert rows["F001"].result is FinalResult.ANSWERED
    assert rows["F002"].skip_reason is SkipReason.NO_WEATHER
    assert list(ports.telephony._count) == ["FAKE-0001"]


def test_sheet_fills_coordinates_from_geocoder(tmp_path):
    f = tmp_path / "f.csv"
    f.write_text("Farmer ID,Farmer Name,Mobile Number,Village,District,State,Preferred Calling Language,Call Consent\n"
                 "F1,A,9876543210,Mandya,Mandya,Karnataka,Hindi,Yes\n"
                 "F2,B,9876543211,Nowhere,Nodistrict,Karnataka,Hindi,Yes\n", encoding="utf-8")
    matches = {}
    a, b = load_farmers(f, lambda v, d, s: geocode(v, d, s, fake(geo={"Mandya": [MANDYA_KA]})), matches)
    assert (a.latitude, a.longitude) == (12.52, 76.9) and (b.latitude, b.longitude) == (0.0, 0.0)
    assert "Karnataka" in matches["F1"] and matches["F2"] == "no confident match"
