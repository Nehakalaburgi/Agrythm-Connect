# Gate Zero: morning weather call

A standalone prototype. Each morning a voice call goes to each consented farmer and gives the day's weather in Hindi or English, saying clearly that it is an AI. There is no Trust AI and no advice in this scope. Target: complete by 15 Nov 2026.

## What it does
1. Finds the farmers to call today.
2. Skips anyone without consent, inactive, without a phone, already handled today, or with no weather available. Each skip is recorded with its reason.
3. Builds a 30 to 40 second message in the farmer's language.
4. Turns it into speech and places the call. If not answered, tries again up to the configured number of attempts.
5. Records every attempt and one final result per farmer: answered, unanswered, failed or skipped.
6. Gives a status view (counts and a row per farmer, no phone numbers) for the monitoring page.

## Quick start (no keys needed)
```
pip install -r requirements.txt
python -m pytest -q
python -m weathercall.cli --date 2026-11-05
```
This runs a full morning with mock providers and 10 fake farmers, including a no-consent farmer, an inactive farmer, a place with no weather, a busy line and a farmer who never answers.

## How it is built to merge later
```
 scheduler / operator / Trust AI
            |  contract 1: call request
            v
     +-------------+   contract 2   +--------------+
     |   engine    |<---------------| FarmerSource |  local now, Trust AI later
     |  (the core) |   contract 3,4 +--------------+
     |             |--------------->| CallLedger   |  SQLite now, Trust AI later
     +------+------+                +--------------+
            |
   WeatherProvider · VoiceProvider · TelephonyProvider   (mock now, real providers next)
```
The core never imports an adapter. Full wiring guide: [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Folder layout
- `weathercall/contracts.py` the four agreed contracts and shared types
- `weathercall/ports.py` the sockets adapters plug into
- `weathercall/engine.py` the call logic (eligibility, retries, idempotence, recording)
- `weathercall/script.py` message text (Hindi and English)
- `weathercall/config.py` settings from environment
- `weathercall/adapters/` mock providers, local stand-ins, Trust AI placeholders
- `tests/` automated tests
- `docs/` integration guide and decisions

## Configuration
Copy `.env.example` to `.env`. Adapter names and settings are chosen there. Provider keys stay in `.env` on the server and are never committed.

## Safety and privacy
Consent required. The voice says it is an AI. No phone numbers or farmer details in logs, errors or the status view. Fake data only in this repository.

## Known limitations
- Real weather, voice and telephony providers are not chosen or connected yet.
- Retries, wait gap, call time and weather-missing behaviour are placeholders pending the client.
- Hindi wording is a draft and needs native-speaker review.
- The monitoring page is not built yet; the status view it will read already exists.

## Plan and tracking
Sprints and tasks are in Jira (project SCRUM). Weekly progress is also noted in `docs/DECISIONS.md`.
