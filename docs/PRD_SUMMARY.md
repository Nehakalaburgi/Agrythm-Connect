# PRD summary (for engineers and AI pair programmers)

Condensed from *Agrythm Connect PRD*. When this file and the PRD disagree, the PRD wins.

**Thesis:** preserve contextual farmer continuity after a field interaction without continuous manual calling. Connect is the engagement layer; Trust AI is the crop system of record.

## Pipeline
Trigger → Context Builder → Conversation Orchestrator → STT / Reasoning / TTS → Structured Outcome → Trust AI update. Provider layers are replaceable.

## Must-have V1 gates (acceptance)
| Gate | Meaning | Where tested |
|---|---|---|
| 1 Trigger integrity | An approved visit/advisory event creates exactly one conversation for the right farmer and crop cycle | `tests/test_gate1_trigger.py` |
| 2 Context integrity | Name, crop, field context and approved advisory are retrieved correctly before the call | `tests/test_gate2_context.py` |
| 3 Safety integrity | No unsupported molecule, dose, compatibility, PHI or agronomic recommendation outside approved context | `tests/test_gate3_safety.py`, `tests/test_policy.py` |
| 4 Conversation outcome | Each interaction produces a structured outcome and next action, not only a transcript | `tests/test_gate4_outcomes.py` |
| 5 Recovery | Missed call, network interruption, failed processing keep state and expose retry/fallback | TRL 5 |
| 6 Live pilot proof | Real farmers complete end-to-end conversations | TRL 6 |

## Outcomes (exactly one per conversation)
`Completed` · `Follow-up Required` · `Human Escalation` · `Unresolved`

## Mandatory states
S01 Scheduled · S02 Calling · S03 Connected · S04 Completed · S05 No Answer · S06 Retry Scheduled · S07 Network Interrupted · S08 Processing Failed · S09 Fallback Sent · S10 Clarification Required · S11 Human Escalation · S12 Awaiting Human · S13 Resolved · S14 Closed

States S05–S09 exist in the transition table now but are exercised from TRL 5.

## Not in V1
Autonomous diagnosis or pesticide prescription · replacing agronomists · open-ended agronomy chatbot · ERP/inventory/logistics · independent dose/PHI decisions · fully remote claims before field validation.

## Flows
A field-led (current) · B missed-call recovery (TRL 5) · C advisory question · D retention loop · E remote-intelligence (future) · F learning loop.
