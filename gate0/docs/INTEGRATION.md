# Joining Gate Zero to the final product

Gate Zero is built so the final product only has to supply two things. This page is the checklist.

## The four contracts (defined in `weathercall/contracts.py`)
| # | Contract | Direction | Gate Zero today | Final product |
|---|---|---|---|---|
| 1 | Create call request (`CallRequest`) | into Gate Zero | the morning scheduler | Trust AI or an operator sends requests to `process_request` |
| 2 | Get approved farmer context (`FarmerContext`) | Gate Zero reads | `InMemoryFarmerSource` with fake farmers | `TrustAIFarmerSource` |
| 3 | Write call attempts and results (`CallAttempt`, `FarmerDayResult`) | Gate Zero writes | `SQLiteLedger` | `TrustAILedger` |
| 4 | View operational status (`CallStatusView`) | read-only | `SQLiteLedger.status` | `TrustAILedger.status` |

## What changes at merge time
1. Implement `TrustAIFarmerSource` and `TrustAILedger` (stubs already exist in `adapters/trust_ai_stub.py` and already satisfy the ports).
2. Set `GATE0_FARMERS=trust_ai` and `GATE0_LEDGER=trust_ai`.
3. Map fields (confirm each with the platform team):

| Gate Zero field | Trust AI side (to confirm) |
|---|---|
| `farmer_id` | farmer identifier |
| `language` | preferred language |
| `place_name`, `latitude`, `longitude` | farm or village location |
| `consent`, `active` | consent record and farmer status |
| `phone` | contact number (kept out of logs and status views) |
| `CallAttempt` fields | call attempt record |
| `FarmerDayResult` | per-farmer daily outcome |

## What does not change
Engine, message script, weather, voice and telephony adapters, tests, configuration.

## Rules that protect the merge
- The core must not import adapters, databases or provider SDKs (a test enforces it).
- Changes to a contract are a team decision: update `contracts.py`, this page and the tests together.
- Add real providers as adapters only.
