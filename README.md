# Agrythm Connect

Voice-first farmer relationship and execution layer. This repository holds three areas of work, each in its own folder.

| Folder | What it is | Status |
|---|---|---|
| [`Pilot/`](Pilot/) | The earlier text-only prototype: farmer context, safety gate, conversation, structured outcomes (Gates 1 to 4 of the original plan). | Built, tested, kept as is |
| [`gate0/`](gate0/) | **Gate Zero**: a morning weather voice call to consented farmers. Standalone, no Trust AI, built to plug into the final product later. | In progress, due 15 Nov 2026 |
| [`final-product/`](final-product/) | The full Agrythm Connect, integrated with Trust AI. | Upcoming |

## How they fit together
Gate Zero is not a throw-away. Its core talks to the outside world only through four agreed contracts and a small set of ports (farmer source, call ledger, weather, voice, telephony). Today those are backed by local stand-ins. In the final product the farmer source and call ledger are re-pointed at Trust AI, and the weather, voice and telephony adapters carry over unchanged. See [`gate0/docs/INTEGRATION.md`](gate0/docs/INTEGRATION.md).

## Quick start
```
# Gate Zero (mock providers, no keys needed)
cd gate0
pip install -r requirements.txt
python -m pytest -q
python -m weathercall.cli --date 2026-11-05

# Earlier prototype
cd Pilot
pip install -r requirements.txt
python -m pytest -q
python -m connect.cli --farmer 1
```

## Ground rules for the whole repository
- Farmer personal data and provider keys never go into GitHub. Use `.env` (ignored) and the `.env.example` files.
- The voice always says it is an AI, and only consented farmers are called.
- Each area has its own `CLAUDE.md` with working rules. Read the one for the folder you are in.
- Decisions that matter are recorded as short notes (ADRs) in that area's `docs/`.
