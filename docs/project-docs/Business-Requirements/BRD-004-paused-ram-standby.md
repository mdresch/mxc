---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-004-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-004-*.md"
---

# BRD-004: Paused RAM standby, trimmed before suspend

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 7 (Requirement: Business)`  
> **Inputs:** [ADR-004](../../07-architecture/ADR-004-paused-ram-standby.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (BDR-01)  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-004-paused-ram-standby.md

**Source ADR:** [ADR-004](../../07-architecture/ADR-004-paused-ram-standby.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-004-2026-10-30.adjudication.json](../gates/approve-brd-004-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

Idle guests must stop burning processor time while staying ready to resume within 300 ms. RAM and image disks remain allocated as a standing cost.

## Business Rules (BRU)

- **BRU-004-01**: Paused standby guests measure 0.0% host CPU. *(from ADR-004 §4.2)*
- **BRU-004-02**: Paused standby guests measure 0.0% host GPU; absent partition counts as 0 with note. *(from ADR-004 §4.3)*
- **BRU-004-03**: Guest memory stays resident; 0 MB reading means Saved/Stopped, not Paused. *(from ADR-004 §4.4)*
- **BRU-004-04**: Working set trimmed before `Suspend-VM`; target about 1.0–1.2 GB (`BEN-10`). *(from ADR-004 §4.4)*
- **BRU-004-05**: `Resume-VM` completes within 300 ms without paging working set from disk. *(from ADR-004 §4.5)*
- **BRU-004-06**: Parent VHDX and session `.avhdx` stay allocated while Paused. *(from ADR-004 §4.7)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| 0.0% CPU on 10 standby VMs | Claimed in implementation plan; not re-measured here (`AC-03.1`) |
| GPU reading | No prior sample; first reading is the test |
| Paused RAM 1.0–1.2 GB vs under-700 MB lessons note | Two figures; one must be chosen for `BEN-10` |

## Traceability to architecture suite

- Primary user story anchor: `US-03` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).

## Out of Scope

- 800 ms caller TTFB (`ADR-002`).
- Warm checkpoint contents (`ADR-003`).
- NVMe deep tier (`HYP-mxc-018` horizon).
