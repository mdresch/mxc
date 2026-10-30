---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v<X.Y.Z>"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
inputs:
  - "Ideation-Document.md (Hypotheses)"
  - "Project-Management-Plan.md"
  - "BRD-*.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-*.md"
---

# ADR <NNN>: <Title>

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Inputs:** Ideation-Document.md (Hypotheses), Project-Management-Plan.md, BRD-*.md  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-*.md


**Governing Baseline:** `PMP-BL-v<X.Y.Z>` (Invariant 6)

## 1. Executive Brief
<One paragraph: what's real today, what gap this closes, what the decision actually is. State it as a finding, not a proposal — if you haven't verified the "what's real today" part against actual code/docs yet, you're not ready to write this section.>

## 2. Status
**Proposed (<date>)** — awaiting <real approver>'s explicit review and sign-off, per <this project's own governance rule, cited>.

<Do not write "Accepted" here until that sign-off actually happened. If this project has a real `approve-adr` policy, its recommendation goes here too, once run — but the recommendation is an input to the decision, never a substitute for it. Say so explicitly, every time.>

## 3. Context
<Real, cited facts only. Every claim needs a file path, a line number, a command output, or an explicit "not independently verified, named as plausible" caveat. If a reviewer's claim turns out wrong when checked, say what you checked and what you found — don't just fix it silently.>

## 4. Decision
<Numbered subsections. Each decision should be traceable to a fact in §3. Name what you are NOT deciding (explicitly out of scope) as clearly as what you are.>

### 4.N Review triggers (if any apply)
<Only include this if a real, nameable future event would make this ADR's own facts stale — e.g. "revisit before first production deployment." Don't invent a generic review cadence; tie it to something concrete.>

## 5. Alternatives Considered
| Alternative | Reason for rejection |
|---|---|
| <a real alternative that was actually considered> | <the real reason, not a strawman> |

## 6. Consequences
### Positive
### Negative
<Negative consequences are not optional filler — if you can't think of a real one, you probably haven't scrutinized the decision enough yet.>

## 7. References
<Every file this ADR cites, as a real link/path. Link related ADRs. Cite the gap-tracking document (coverage overview, backlog, whatever this project uses) that justified writing this ADR in the first place.>
