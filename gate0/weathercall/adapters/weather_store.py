"""Stores each day's weather in SQLite before it is used, so the call says exactly what was fetched and saved.

Wraps any WeatherProvider. A stored report for the same place, coordinates and day is reused (no second fetch, and every
farmer in one village hears the same numbers). Nothing is stored when the provider has no weather, and a provider
error counts as no weather, so that farmer is skipped instead of the run stopping.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime

from ..contracts import WeatherReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS weather(
  place_key TEXT, lat REAL, lon REAL, call_date TEXT, place_name TEXT, summary TEXT, temp_min_c INT, temp_max_c INT,
  rain_chance_pct INT, source TEXT, fetched_at TEXT,
  PRIMARY KEY(place_key, lat, lon, call_date));
"""


class StoredWeather:
    def __init__(self, inner, path: str = ":memory:"):
        self.inner = inner
        self.db = sqlite3.connect(path)
        self.db.executescript(_SCHEMA)
        self.provider_errors = 0

    def get_weather(self, place_name: str, latitude: float, longitude: float, call_date: date) -> WeatherReport | None:
        key = (place_name.strip().lower(), round(latitude, 3), round(longitude, 3), call_date.isoformat())
        row = self.db.execute("SELECT summary, temp_min_c, temp_max_c, rain_chance_pct, source FROM weather "
                              "WHERE place_key=? AND lat=? AND lon=? AND call_date=?", key).fetchone()
        if row:
            return WeatherReport(place_name, row[0], row[1], row[2], row[3], row[4])
        try:
            report = self.inner.get_weather(place_name, latitude, longitude, call_date)
        except Exception:
            self.provider_errors += 1
            return None
        if report is not None:
            self.db.execute("INSERT INTO weather VALUES(?,?,?,?,?,?,?,?,?,?,?)", (*key, place_name, report.summary,
                            report.temp_min_c, report.temp_max_c, report.rain_chance_pct, report.source,
                            datetime.now().isoformat(timespec="seconds")))
            self.db.commit()
        return report
