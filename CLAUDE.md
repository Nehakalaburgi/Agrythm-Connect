# CLAUDE.md — Agrythm Connect

Read this first in every session. Source of truth: `docs/PRD_SUMMARY.md` (condensed from the Agrythm Connect PRD) and `docs/TRL_PLAN.md`.

## What we are building
Agrythm Connect is a voice-first **farmer relationship and execution layer**. It receives an approved Agrythm event, builds farmer/farm/crop context, holds a bounded conversation in English/Hindi (Hinglish), captures a structured outcome, escalates uncertainty, and writes the result back to the system of record (Trust AI; mocked in SQLite for now).

## Current TRL: 3 (text-only loop, mock data)
Level names follow the management scale (0 Idea … 9 Full commercial application); level 3 is "Needs validation". `CURRENT_TRL` (engineering scope) and `REPORTED_TRL` (level shown to management in the README) are separate in `connect/models.py`. When the reported level changes: update `REPORTED_TRL`, the status text and table in `README.md`, `docs/TRL_PLAN.md`, then run `python scripts/make_trl_ladder.py` (a test fails if `docs/trl_ladder.svg` is stale).
Work only on what the current TRL's exit gate needs. Anything for a higher TRL goes into `docs/FUTURE.md`, not into code.

## Hard rules (system boundary — never break these)
1. The agent is NOT the agronomist. It only (a) explains the approved advisory, (b) answers from `approved_facts`, (c) asks for clarification, or (d) escalates.
2. Never generate a molecule, dose, compatibility claim or PHI/harvest-interval that is not in the approved advisory/facts. Every agent reply must pass `connect/policy.py::check_reply`.
3. When unsure: clarify, then escalate. Never guess.
4. Every conversation ends in exactly one machine-readable outcome: `Completed`, `Follow-up Required`, `Human Escalation`, `Unresolved`. A transcript alone is not an outcome.
5. Every state change goes through `transition()` and is written to `state_log`. Failure states must preserve what happened, what was captured, and the next action.
6. STT, LLM and TTS are replaceable adapters. Agrythm owns context, rules, workflow and data. No provider SDK calls outside `connect/adapters` style modules (currently `connect/llm.py`).
7. Seed advisories are DEMO placeholders, not agronomic guidance. Never invent real advisory content.

## Coding rules
- Python 3.11+, type hints, standard library first. Keep dependencies minimal and free.
- Test first. Every change needs tests; the safety test set (`tests/data/safety_utterances.json`) must pass before any commit.
- Small commits, one feature each. Explain assumptions before coding a new feature.
- Hindi text: Devanagari and Roman (Hinglish) must both work. Have a native speaker review any new Hindi templates.
- Record non-trivial decisions as ADRs in `docs/ADR/`.

## Commands
```
python -m pytest -q                 # all tests
python -m connect.cli --list        # list demo farmers
python -m connect.cli --farmer 1    # text conversation with the agent
```

## Layout
- `connect/models.py` outcomes, states, allowed transitions
- `connect/db.py` schema (SQLite stand-in for Trust AI) · `connect/seed.py` demo data
- `connect/events.py` trigger layer (Gate 1) · `connect/context.py` context builder (Gate 2)
- `connect/policy.py` safety gate (Gate 3) · `connect/llm.py` understanding + reply adapter
- `connect/orchestrator.py` conversation state machine and structured outcome (Gate 4)
