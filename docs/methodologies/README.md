# Learning methodologies (catalog, tailoring matrix, labeling contract)

Copied from `agent-learning` (ADR-036). The template holds the layout and the data about methodologies; it holds no example runs and no evidence.

| File | What it is |
|---|---|
| `catalog.json` | One entry per learning methodology (32). Each has a canonical `state`, an `example_class` derived from it (`runnable`, `proof_of_concept` or `documented`), the ADR and hypothesis where they exist, and a `path` (runnable and proof-of-concept) or a `reason` and `reopening_condition` (documented). |
| `Tailoring-Matrix.md` | Candidate pairings of a need in the store or in lessons learned with a methodology. Every row is a `hypothesis`. |
| `../registers/Methodology-Best-Practice-Ledger.template.md` | The append-only ledger of practices. It starts empty. |

## Paths in the catalog
The `path` values (`examples/methodologies/<NN>-<slug>`) name the example directories in the `agent-learning` repository, where the scripts run against its SDK. They are not copied here. A project that adds its own examples puts them under its own `examples/methodologies/` and updates the matching entries.

## Labeling contract for any example you add
- The script's docstring carries `STATUS`, `CODE` (`sdk` for runnable, `sketch` for proof of concept), `DATA: SYNTHETIC`, `IDEATION ROW: #N`, `ADR`, `HYPOTHESIS`, and `NOT EVIDENCE: this run does not validate or invalidate the methodology`.
- It runs offline, writes no file, names no durable store, and never changes a methodology's state or a hypothesis status.
- Its README has `Falsification` and `Real data needed` sections.

## Honest evidence
Examples are synthetic and prove nothing. A practice becomes `adopted` only on real episodes that meet the tier gate (see the ledger template). Until then every pairing in the matrix is a hypothesis.
