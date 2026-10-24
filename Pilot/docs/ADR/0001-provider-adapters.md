# ADR 0001 — Provider-agnostic adapters

**Status:** accepted · **TRL:** 3

## Context
The PRD requires that Agrythm owns context, rules, workflow and data, while STT, TTS and LLM vendors stay replaceable and can be benchmarked behind the same interfaces. We also want a zero-cost prototype.

## Decision
- `connect/llm.py` defines `LLMAdapter` with two methods: `understand(utterance, ctx)` and `compose(kind, ctx, **kw)`.
- TRL 3 ships `RuleBasedAdapter` (deterministic, free, offline). Free LLM tiers and open-source models plug in at TRL 4 behind the same interface.
- Whatever an adapter composes passes through `policy.check_reply` before the farmer hears it. Closing messages are fixed templates that bypass the adapter.
- STT/TTS adapters follow the same pattern at TRL 4.

## Consequences
A rogue or hallucinating adapter cannot reach the farmer with an unapproved dose or molecule (tested with `RogueAdapter`). Swapping providers does not change conversation state, rules or audit history.
