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

## Real farmers, Sarvam voice and the daily trigger
1. Put the farmer sheet (CSV or Excel) in `gate0/data/`. This folder is git-ignored. Columns: Farmer ID, Farmer Name, Mobile Number, Village, District, State, Preferred Calling Language (Hindi or English), Call Consent (Yes or No), and optionally Active, Latitude, Longitude. See `farmers.example.csv`.
2. Copy `.env.example` to `.env` and set `GATE0_FARMERS=sheet`, `GATE0_FARMERS_FILE=data/<your file>`, `GATE0_VOICE=sarvam` and `SARVAM_API_KEY=<key>`.
3. Set `GATE0_WEATHER=open_meteo` and check the weather first, without calling anyone: `python -m weathercall.weather_check`. It shows the place matched for each farmer and saves the forecast. Farmers marked NO WEATHER will not be called.
4. Dry run for one day: `python -m weathercall.cli --date 2026-10-27`.
5. Calls scheduled by Sarvam (recommended): `python -m weathercall.campaign create --start 2026-10-27 --days 4`, then `python -m weathercall.schedule activate --start 2026-10-27 --days 4 --mode campaign`. See `docs/SARVAM_SETUP.md` section 3.
   Or our code dials directly. Turn on the trigger (Windows): `python -m weathercall.schedule activate --start 2026-10-27 --days 4 --time 09:00`. It checks the setup and warns about anything still mocked.
6. Check it with `python -m weathercall.schedule status`. Turn it off with `python -m weathercall.schedule deactivate`. Each day's summary is in `logs/run-YYYY-MM-DD.log`.

The task only runs while you are logged in, and it is skipped if the computer is off at the call time.

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
