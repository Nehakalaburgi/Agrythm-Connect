# ADR 0002 — Intent → outcome rules (needs SME review)

**Status:** proposed · **TRL:** 3

| Farmer says | Intent | Outcome | Next action |
|---|---|---|---|
| Understood, will act | confirm | Completed | execution check after `followup_days` |
| Already did it | done | Completed | none |
| Will do later | delay | Follow-up Required | reminder call (1/2/7 days from what they said) |
| Will not / cannot do it | reject | Human Escalation | SME callback; barrier captured (cost, time, labour, input unavailable) |
| New symptom or problem | new_issue | Human Escalation | SME callback |
| Question answered from approved facts | question | stays open | wait for commitment |
| Question not covered by approved facts, or a decision (double dose, other chemical, mixing, harvest interval) | question | Human Escalation | SME callback |
| Not understood after 2 clarifications | not_understood | Human Escalation | SME callback |
| Hangs up / no commitment captured | — | Unresolved | retry call |

## Why rejection escalates
Non-adherence to an approved advisory needs agronomic judgment (is the advice still right for this farmer's constraint?), so it is not left to automation.

## Open questions for the agronomist
1. Should "reject because of cost" go to an SME, or to operations/FPO?
2. Default follow-up interval per advisory type.
3. Which topics deserve approved facts (dose, timing, mixing, harvest interval, why)?
