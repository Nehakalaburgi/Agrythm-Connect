# Decisions and open items

## Decided
| Date | Decision |
|---|---|
| 20 Oct 2026 | Gate Zero is a standalone prototype with weather calls only, no Trust AI. |
| 22 Oct 2026 | Delivery date is 15 Nov 2026. |
| 24 Oct 2026 | Repository has three folders: `Pilot/`, `gate0/`, `final-product/`. Gate Zero is built to merge into the final product through contracts and ports. |
| 26 Oct 2026 | Farmers come from a CSV or Excel sheet kept outside git (`GATE0_FARMERS=sheet`), with the columns from the client's prototype data requirements. |
| 26 Oct 2026 | Sarvam is the voice and telephony provider: a Sarvam Voice Agent places the call and speaks our script as its first line (`GATE0_VOICE=sarvam_agent`, `GATE0_TELEPHONY=sarvam_agent`). Setup in `docs/SARVAM_SETUP.md`. Plain Bulbul TTS (`GATE0_VOICE=sarvam`) stays available for audio checks. |
| 26 Oct 2026 | Trial run: daily at 09:00 for 4 days, triggered by Windows Task Scheduler (`python -m weathercall.schedule activate`). 09:00 is still to be confirmed with the client. |
| 26 Oct 2026 | Weather comes from Open-Meteo (`GATE0_WEATHER=open_meteo`): free, no key, a full daily forecast including the morning low. OpenWeather was tried and dropped: its free plan only gives 3-hour slots from the next slot onward and needed a key. Each day's forecast is saved in SQLite before use. A farmer is called only when complete weather is saved for their place; otherwise skipped as `weather_unavailable`. |
| 26 Oct 2026 | Places are matched by Village, then District, always inside the sheet's State and District, because names repeat (a Mandya exists in Haryana too). No confident match means no weather and no call. Latitude/Longitude in the sheet override the lookup. |
| 26 Oct 2026 | Scheduling and dialling move to Sarvam Campaigns (`GATE0_CALL_MODE=campaign`). One campaign covers the trial (09:00 to 11:00 IST, retries in Sarvam). Each morning at 08:30 our job pushes that day's eligible farmers with fresh weather and syncs yesterday's results. Chosen over pre-loading 4 days (stale forecasts, consent changes missed) and over the agent fetching weather itself (no control of wording, no 'no weather, no call'). |
| 26 Oct 2026 | A voice provider failure marks that farmer `failed` for the day and the run continues (engine change for hard rule 5). |

## Open with the client (Chetan Sir)
| Item | Placeholder now |
|---|---|
| Number of attempts | 3 |
| Wait between attempts | 30 minutes |
| Morning call time | 09:00 (team trial choice) |
| Behaviour when weather is missing | skip the farmer and record why |
| Telephony and weather providers and budget | mocks only (voice: Sarvam) |

## Open internally
- Campaign mode still needs a small daily job (08:30) on our side; move it from the laptop to an always-on machine or a cloud scheduler before the real pilot.
- Weather words ("cloudy", "light rain") are English inside the Hindi message. Hindi weather words are needed, with native review.
- The Sarvam agent can hear and answer the farmer, not just play a message. Its instruction limits it to weather only; check transcripts during testing.
- Cost per call on Sarvam credits: measure on the first test call.
- Retries wait in line per farmer (3 tries x 30 min holds up everyone after). Change to retry rounds before real telephony is connected.
- Per-farmer "Preferred Calling Time" from the sheet is read but not used yet; everyone is called at the campaign time.
- Sarvam speaker voice: default `priya`; confirm it suits the Hindi script, which uses feminine verbs.
- Native-speaker review of the Hindi message.
- Which sprint-time tasks are changed by the answers above.
