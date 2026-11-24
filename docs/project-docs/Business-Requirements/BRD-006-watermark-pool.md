---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-006-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-006-*.md"
---

# BRD-006: Watermark pool, replenish, and wake hygiene

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-006](../../07-architecture/ADR-006-watermark-pool.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (Elasticity (REQ-BDR-05))  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-006-watermark-pool.md

**Source ADR:** [ADR-006](../../07-architecture/ADR-006-watermark-pool.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-006-2026-10-30.adjudication.json](../gates/approve-brd-006-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

Bursts must not cold-boot the next caller. The pool refills in about 1.5 seconds and runs hygiene before traffic.

## Business Rules (BRU)

- **BRU-006-01**: Leasing the last ready guest triggers background promotion to `StandbyPaused` in about 1.5 s. *(from ADR-006 §4.2)*
- **BRU-006-02**: Surge expands toward configured K_max; the check records whether 5 rps or 10 rps/5 s was configured. *(from ADR-006 §4.3)*
- **BRU-006-03**: First `/health` after wake reports entropy reseed, clock sync, and DB pools cleared. *(from ADR-006 §4.5)*
- **BRU-006-04**: Surplus guests leave after configured idle time; check records 300 s or 180 s. *(from ADR-006 §4.6)*
- **BRU-006-05**: Forecast pre-warm stays future (`HYP-mxc-020`); explicit `mxc-pool-warm` is allowed. *(from ADR-006 §4.4)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Refill latency | About 1.5 s in suite; not captured in new run (`BEN-09`) |
| Surge threshold | Two figures documented; `BEN-09` cannot pass until one is chosen |
| Cooldown | 180 s in `AC-05.4` vs 300 s in `HYP-mxc-014`; check must record which applied |

## Traceability to architecture suite

- Requirements matrix: `REQ-BDR-05` in [BDR.md](../../hyperv/architecture/BDR.md).
- Primary user story anchor: `US-05` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).

## Out of Scope

- Paused RAM size per guest (`ADR-004`).
- `.avhdx` discard rules (`ADR-005`).
- Forecast model (`HYP-mxc-020` horizon).
