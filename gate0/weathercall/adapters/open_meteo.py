"""Open-Meteo weather and place lookup. Free, no API key. https://open-meteo.com

- geocode() turns Village + District + State into coordinates. Names repeat across India (there is a Mandya in
  Haryana too), so a match must sit in the farmer's state and district; otherwise there is no match and no call.
- OpenMeteoWeather returns today's forecast, or None when any field is missing or implausible, so a farmer is
  only called when real weather is in hand.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date

from ..contracts import WeatherReport

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes in short spoken words
_WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "cloudy", 45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 56: "freezing drizzle", 57: "freezing drizzle",
        61: "light rain", 63: "rainy", 65: "heavy rain", 66: "freezing rain", 67: "freezing rain",
        71: "light snow", 73: "snowy", 75: "heavy snow", 77: "snowy",
        80: "light showers", 81: "showers", 82: "heavy showers", 85: "snow showers", 86: "snow showers",
        95: "thunderstorms", 96: "thunderstorms with hail", 99: "thunderstorms with hail"}


def _get(url: str, params: dict, opener=urllib.request.urlopen) -> dict:
    with opener(f"{url}?{urllib.parse.urlencode(params)}", timeout=20) as resp:
        return json.load(resp)


def _same(a: object, b: str) -> bool:
    norm = lambda s: "".join(ch for ch in str(s or "").lower() if ch.isalnum())  # noqa: E731
    return bool(b) and norm(a) == norm(b)


@dataclass(frozen=True)
class Place:
    latitude: float
    longitude: float
    matched: str        # e.g. "Mandya, Mandya, Karnataka (village)" for a human to check
    level: str          # village | district


def geocode(village: str, district: str, state: str, opener=urllib.request.urlopen) -> Place | None:
    """Village first; if the village is unknown, the district centre. None when nothing matches confidently."""
    for name, level in ((village, "village"), (district, "district")):
        if not name:
            continue
        results = _get(GEOCODE_URL, {"name": name, "count": 10, "language": "en", "format": "json",
                                     "countryCode": "IN"}, opener).get("results") or []
        in_state = [r for r in results if not state or _same(r.get("admin1"), state)]
        in_district = [r for r in in_state
                       if not district or any(_same(r.get(k), district) for k in ("admin2", "admin3", "name"))]
        # without a district to check, accept only a single match inside the state
        pick = in_district[0] if in_district else (in_state[0] if not district and len(in_state) == 1 else None)
        if pick:
            where = ", ".join(str(pick.get(k)) for k in ("name", "admin2", "admin1") if pick.get(k))
            return Place(float(pick["latitude"]), float(pick["longitude"]), f"{where} ({level})", level)
    return None


class OpenMeteoWeather:
    def __init__(self, opener=urllib.request.urlopen):
        self._open = opener

    def get_weather(self, place_name: str, latitude: float, longitude: float, call_date: date) -> WeatherReport | None:
        if not latitude and not longitude:
            return None                     # no coordinates: never guess a place by name alone
        d = call_date.isoformat()
        daily = _get(FORECAST_URL, {
            "latitude": latitude, "longitude": longitude, "timezone": "Asia/Kolkata", "start_date": d, "end_date": d,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        }, self._open).get("daily") or {}
        try:
            code = daily["weather_code"][0]
            tmax, tmin = daily["temperature_2m_max"][0], daily["temperature_2m_min"][0]
            rain = daily["precipitation_probability_max"][0]
            if daily["time"][0] != d or None in (code, tmax, tmin, rain):
                return None
        except (KeyError, IndexError, TypeError):
            return None
        summary = _WMO.get(int(code))
        if summary is None or not (-10 <= tmin <= tmax <= 55) or not (0 <= rain <= 100):
            return None
        return WeatherReport(place_name, summary, round(tmin), round(tmax), round(rain), "open-meteo")
