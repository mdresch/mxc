---
register: "methodology-best-practice-ledger"
governed_by: "agent-learning ADR-036 section 4.3"
---

# Methodology Best-Practice Ledger — <project name>

**Maintenance Rule:** append-only. An entry is never edited. A status change is a new entry whose `supersedes` names the earlier entry of the same methodology; the latest entry in a chain is the current one. Git history is the guard against edits.

**Adoption Rule:** a practice is `adopted` only on `real-episodes` evidence whose `evidence_count` meets the outcome gate of the tier declared for the decision (low 3, standard 20, high 50, critical 100 by default). `source-doc` and `synthetic-demo` evidence can never be adopted. A new project therefore starts with `candidate` entries only, and may start with none.

**Relation to the Lessons Learned Register:** a Lessons Learned entry is a process lesson; a ledger entry is a practice of a learning methodology. A practice that is also a lesson links to the LL entry in `links`.

## How to add an entry
Append a section `## BP-###` (next number) with one `- field: value` line per field:

| Field | Value |
|---|---|
| `methodology` | catalog id, 1 to 32 (`docs/methodologies/catalog.json`) |
| `practice` | the practice, one sentence |
| `preconditions` | when it applies |
| `applies_to` | `store`, `lessons-learned`, `both` or `other` |
| `evidence_class` | `source-doc`, `synthetic-demo` or `real-episodes` |
| `evidence_ref` | where the evidence is |
| `evidence_count` | number of real episodes (0 for the other two classes) |
| `status` | `candidate`, `adopted` or `retired` |
| `tier` | `low`, `standard`, `high` or `critical`; required when `adopted` |
| `supersedes` | optional, the earlier `BP-###` this entry changes the status of |
| `links` | optional, comma-separated `LL-###` and `HYP-AL-###` identifiers that exist in the project |

The parser and tests live in `agent-learning` (`agent_learning.methodology_ledger`). A project that uses the `agent-learning` SDK can parse this register with `parse_ledger`.

---

<!-- Entries go below this line. The template ships none: it stores only template values. -->
