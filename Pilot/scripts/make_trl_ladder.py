"""Generate docs/trl_ladder.svg: an animated 0-9 TRL ladder with the current level highlighted.

Usage:
    python scripts/make_trl_ladder.py          # uses connect.models.REPORTED_TRL
    python scripts/make_trl_ladder.py 4        # override the level

Run it whenever REPORTED_TRL changes. tests/test_trl_ladder.py fails if the SVG is out of date.
The animation is pure CSS inside the SVG, so it plays on GitHub/GitLab when embedded with <img>.
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "trl_ladder.svg"

# (label, colour) — the standard 0-9 scale used by the management team.
LEVELS = [
    ("Idea", "#2E9BD6"),
    ("Basic research", "#36A9B4"),
    ("Technology formulation", "#3DB48F"),
    ("Needs validation", "#4DB96B"),
    ("Small scale prototype", "#6CBB4A"),
    ("Large scale prototype", "#8FC13F"),
    ("Prototype system", "#B3C73A"),
    ("Demonstration system", "#D9D23F"),
    ("First of a kind commercial system", "#EDB93E"),
    ("Full commercial application", "#F2994A"),
]

# What each level means for Agrythm Connect.
NOTES = {
    0: "Farmer continuity after a field visit",
    1: "PRD and stakeholder research",
    2: "Architecture and provider-agnostic design",
    3: "Mock-data text prototype: trigger, context, safety gate, outcome",
    4: "Next: voice (STT/TTS), free LLM behind the safety gate",
    5: "Next: retries, fallback, operator screens, real audio replay",
    6: "Next: pilot with real farmers and human escalation",
    7: "Next: real Trust AI, wider rollout, paid providers",
}

W, TOP, PITCH, H_ROW = 760, 104, 58, 50


def _mix(hex_colour: str, amount: float) -> str:
    """Blend a colour towards white by `amount` (0 = unchanged, 1 = white)."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(c + (255 - c) * amount) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def _on(hex_colour: str) -> str:
    """Readable text colour (dark or white) for text placed on `hex_colour`."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#1F2933" if (0.299 * r + 0.587 * g + 0.114 * b) > 135 else "#FFFFFF"


def build_svg(current: int) -> str:
    if not 0 <= current <= 9:
        raise ValueError("TRL must be between 0 and 9")
    height = TOP + len(LEVELS) * PITCH + 20
    label, colour = LEVELS[current]
    out: list[str] = []
    add = out.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
        f'viewBox="0 0 {W} {height}" role="img" '
        f'aria-label="Technology Readiness Level ladder. Current level: TRL {current}, {escape(label)}.">')
    add(f"<title>Agrythm Connect: current Technology Readiness Level is TRL {current} ({escape(label)})</title>")
    add("""<style>
  text { font-family: "Segoe UI", -apple-system, Helvetica, Arial, sans-serif; }
  .row   { animation: slide .55s ease-out both; }
  .pulse { animation: pulse 1.6s ease-in-out infinite; }
  .arrow { animation: nudge 1.1s ease-in-out infinite; }
  .badge { animation: blink 1.6s ease-in-out infinite; }
  @keyframes slide { from { opacity: 0; transform: translateX(-28px); } to { opacity: 1; transform: none; } }
  @keyframes pulse { 0%, 100% { opacity: .15; } 50% { opacity: 1; } }
  @keyframes nudge { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(7px); } }
  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
  @media (prefers-reduced-motion: reduce) { .row, .pulse, .arrow, .badge { animation: none; } }
</style>""")
    add(f'<rect x="1" y="1" width="{W - 2}" height="{height - 2}" rx="16" fill="#FFFFFF" stroke="#D9DEE5" stroke-width="2"/>')
    add('<text x="32" y="44" font-size="24" font-weight="700" fill="#1F2933">Agrythm Connect: Technology Readiness Level</text>')
    add(f'<text x="32" y="72" font-size="15" fill="#4B5563">Current: <tspan font-weight="700" fill="#1F2933">'
        f'TRL {current} ({escape(label)})</tspan></text>')

    for i, (name, col) in enumerate(LEVELS):
        y = TOP + i * PITCH  # level 0 at the top, like the scale
        delay = f"{i * 0.12:.2f}s"
        state = "done" if i < current else "current" if i == current else "future"
        box_fill = col if state != "future" else "#D1D5DB"
        box_text = _on(box_fill) if state != "future" else "#4B5563"
        pill_fill = {"done": _mix(col, 0.82), "current": "#FFFFFF", "future": "#F3F4F6"}[state]
        pill_stroke = col if state != "future" else "#D1D5DB"
        label_fill = "#1F2933" if state != "future" else "#6B7280"
        note = NOTES.get(i)
        add(f'<g class="row" style="animation-delay:{delay}">')
        if state == "current":
            add(f'<g class="arrow"><path d="M8 {y + 13} L22 {y + 25} L8 {y + 37} Z" fill="{col}"/></g>')
        add(f'<rect x="32" y="{y}" width="60" height="{H_ROW}" rx="10" fill="{box_fill}"/>')
        add(f'<text x="62" y="{y + 34}" font-size="26" font-weight="700" text-anchor="middle" fill="{box_text}">{i}</text>')
        add(f'<rect x="104" y="{y}" width="624" height="{H_ROW}" rx="12" fill="{pill_fill}" '
            f'stroke="{pill_stroke}" stroke-width="{3 if state == "current" else 2}"/>')
        if state == "current":
            add(f'<rect class="pulse" x="101" y="{y - 3}" width="630" height="{H_ROW + 6}" rx="15" '
                f'fill="none" stroke="{col}" stroke-width="4"/>')
        label_y = y + 22 if note else y + 32
        add(f'<text x="124" y="{label_y}" font-size="19" font-weight="{700 if state != "future" else 500}" '
            f'fill="{label_fill}">{escape(name)}</text>')
        if note:
            add(f'<text x="124" y="{y + 41}" font-size="12.5" fill="{"#374151" if state != "future" else "#6B7280"}">'
                f'{escape(note)}</text>')
        if state == "done":
            add(f'<text x="708" y="{y + 31}" font-size="14" font-weight="700" text-anchor="end" fill="#2F6F4F">&#10003; DONE</text>')
        elif state == "current":
            add(f'<g class="badge"><rect x="580" y="{y + 11}" width="128" height="28" rx="14" fill="#1F2933"/>'
                f'<text x="644" y="{y + 30}" font-size="13" font-weight="700" text-anchor="middle" '
                f'fill="#FFFFFF">WE ARE HERE</text></g>')
        elif i == current + 1:
            add(f'<text x="708" y="{y + 31}" font-size="13" font-weight="700" text-anchor="end" fill="#6B7280">NEXT</text>')
        add("</g>")

    add("</svg>")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        current = int(argv[1])
    else:
        sys.path.insert(0, str(ROOT))
        from connect.models import REPORTED_TRL as current  # noqa: N811
    OUT.write_text(build_svg(current), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} (current TRL {current})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
