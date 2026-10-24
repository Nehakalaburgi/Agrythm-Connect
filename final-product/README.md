# Final product (upcoming)

The full Agrythm Connect, integrated with Trust AI. Nothing is built here yet.

## Plan
1. Take over the Gate Zero core (`gate0/weathercall`) as a package, unchanged.
2. Implement the Trust AI adapters for the two platform-facing ports (farmer source and call ledger) following [`../gate0/docs/INTEGRATION.md`](../gate0/docs/INTEGRATION.md).
3. Bring in the conversation layer from [`../Pilot/`](../Pilot/) for farmer replies and structured outcomes.
4. Add the operator screens, fallback channels and retries described in the PRD.

## Rule
Do not copy Gate Zero code into this folder. Import it, so there is one version of the call engine.
