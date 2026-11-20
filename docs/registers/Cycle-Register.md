---
register: "cycle-register"
governed_by: "ADR-035 (Cycle Identification and Cross-Cycle Artifact Traceability)"
---

# Cycle Register — <project name>

An append-only record of every pass through the Intent-to-Outcome loop. A **cycle** is one pass opened by a trigger (`initial`, `adaptation` or `refinement`) that ends in exactly one outcome. Rows are never edited or deleted. The **latest row for a `cycle_id` defines its current state.**

**Rules**
- `cycle_id` has the form `CYC-NNN`, is monotonic and is never reused. A rolled-back or abandoned cycle keeps its identifier.
- At most one cycle is `OPEN`. Opening a second is refused.
- Every state change cites a human-approved episode in `episode_ref`.
- States: `OPEN`, `CLOSED_BASELINED` (ended with a baseline approved by `approve-pmp`), `ROLLED_BACK`, `ABANDONED`.
- Pins are `{artifact, version, content_hash}` for the Ideation Document, the Business Case, the Project Charter, the document that hosts the tailoring matrix, and, for an `adaptation` cycle, the approved Adaptation Plan. Hashes use the canonical LF-normalized scheme and live here and in `Episode.metadata`, never inside the governed file.
- Never invent provenance. A pin rebuilt from history is marked `reconstructed: true`. One that cannot be recovered is marked `unrecoverable`.
- A cycle is not a hypothesis generation. `CYC-NNN` and a hypothesis recurrence depth are separate counters.

**Lookup rule.** For an artifact version `(path, version, content_hash)`: match a pin set first, then the artifact's approval `Episode.metadata.cycle_id`, then its validated frontmatter `cycle_id` and `baseline_id`. Then read the latest row for that `cycle_id`.

## Rows

| cycle_id | state | date | trigger | episode_ref | baseline_id | opening_pin_set | closing_pin_set | prior_cycle |
|---|---|---|---|---|---|---|---|---|
| CYC-001 | OPEN | <date the project starts> | initial | <episode id of the Charter approval, once it exists> | none yet | <pins, added as the upstream documents are approved> | | none |

## Pin sets

### CYC-001 opening pins
| artifact | version | content_hash | note |
|---|---|---|---|
| docs/project-docs/Ideation-Document.md | <version> | <hash> | |
| docs/project-docs/Business-Case.md | <version> | <hash> | |
| docs/project-docs/Project-Charter.md | <version> | <hash> | |
| <document hosting the tailoring matrix> | <version> | <hash> | |
