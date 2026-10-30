---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v<X.Y.Z>"
lifecycle_stage: "Stage 7 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "ADR-*.md"
  - "BRD-*.md"
  - "Quality Management Plan"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-*.md"
---

# FDD-<NNN>: <Title>

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 7 (Requirement: Solution)`  
> **Inputs:** ADR-*.md, BRD-*.md, Quality Management Plan  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-*.md


**Source ADR:** [ADR-<NNN>](../../07-architecture/ADR-<NNN>-<slug>.md)
**Source BRD:** [BRD-<NNN>](../Business-Requirements/BRD-<NNN>-<slug>.md)
**Governing Baseline:** `PMP-BL-v<X.Y.Z>` (Invariant 6)
**Status:** Draft — technical design derived from an Accepted ADR

## Design: <name>
<Real interfaces/schemas, matching what the ADR actually described. If the ADR named a specific interface, show it verbatim/verified, don't redraw it from memory.>

## Documentation-only items — no code deliverable
<If some of the BRD's business rules have no code deliverable (a convention for future work, a process expectation), say so explicitly here. Don't force every BRU into a design section.>

## Error Handling / Compatibility
| Condition | Behavior |
|---|---|

## Out of Scope
<Same as BRD. Don't introduce new scope here.>

---
**Before writing this FDD**, check: does this ADR's own Decision section actually describe something buildable *now*, or is every decision a convention for future work with no current trigger? If the latter, this FDD's own job is to say that honestly (see ADR-032/FDD-032/Epic-3 in the source projects as the real precedent for "zero stories, by design") — not invent a design to fill the template.
