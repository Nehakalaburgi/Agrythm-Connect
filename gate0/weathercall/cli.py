"""Run one mock morning cycle: python -m weathercall.cli [--date YYYY-MM-DD] [--sample-message]"""
from __future__ import annotations

import argparse
from datetime import date

from .adapters import build_ports
from .config import Settings
from .engine import run_morning


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gate Zero morning weather call (mock providers by default)")
    p.add_argument("--date", type=date.fromisoformat, default=date.today())
    a = p.parse_args(argv)
    ports = build_ports()
    view = run_morning(a.date, ports, Settings.from_env())
    print(f"{view.call_date}: total {view.total} | answered {view.answered} | unanswered {view.unanswered} "
          f"| failed {view.failed} | skipped {view.skipped}")
    for r in view.rows:
        extra = f" ({r.skip_reason.value})" if r.skip_reason else f" after {r.attempts} attempt(s)"
        print(f"  {r.farmer_id}  {r.result.value}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
