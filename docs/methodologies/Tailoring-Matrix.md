# Methodology Tailoring Matrix (template)

Candidate pairings of a need in the store or in lessons learned with a learning methodology from `catalog.json`. Copied from `agent-learning` (ADR-036 section 4.4).

**Status of every row:** `hypothesis`. No row is a finding. A row becomes a finding only through real episodes that meet the outcome gate of the declared tier, recorded in the project's Methodology Best-Practice Ledger (`docs/registers/Methodology-Best-Practice-Ledger.md`). Nothing here changes a methodology's state in the Ideation Document.

**Before relying on a row:** add a `candidate` entry for it to the project's ledger and put its `BP-###` in the `Ledger` column. The ledger starts empty in this template, so the column starts as "add a candidate entry first".

## Pairings

| Need | Applies to | Methodology (catalog ids) | Hypothesis | Falsifiable by | Ledger | Status |
|---|---|---|---|---|---|---|
| Cold start of a new `TaskPolicy` in the store | store | #15 warm-start | HYP-AL-008 | Episodes to reach the gate, against a cold start | add a candidate entry first | hypothesis |
| Positive-only history stalls a policy | store | #9, #10 | HYP-AL-002, HYP-AL-009 | Crossing the gate on the same dataset | add a candidate entry first | hypothesis |
| Drift in stored outcomes | store | #30 | HYP-AL-021 | Recovery after a shifted reward sequence | add a candidate entry first | hypothesis |
| Retrieving the lessons relevant to a decision | lessons-learned | #26 | HYP-AL-024 | Accuracy against a recency baseline | add a candidate entry first | hypothesis |
| Turning review critique into evidence | lessons-learned | #8 | HYP-AL-005 | Convergence against REINFORCE on the same episodes | add a candidate entry first | hypothesis |
| Choosing which findings need a human | lessons-learned | #32, #28 | HYP-AL-023, HYP-AL-019 | Errors caught at equal review budget | add a candidate entry first | hypothesis |

## Reading the matrix
- **Need** is a place in the store or in lessons learned where a learning methodology might help. **Methodology** is the catalog id in `docs/methodologies/catalog.json`.
- **Falsifiable by** is the test that would drop the pairing, taken from the hypothesis in the `agent-learning` Ideation Document. Replace the hypothesis ids with your own when you register them.
- A pairing whose methodology is only `documented` has no example; the row is still a hypothesis.
