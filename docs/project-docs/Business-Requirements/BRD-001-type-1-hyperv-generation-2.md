---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-001-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-001-*.md"
---

# BRD-001: Type-1 Hyper-V Generation 2 instead of a container namespace

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-001](../../07-architecture/ADR-001-type-1-hyperv-generation-2.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (BDR-03)  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-001-type-1-hyperv-generation-2.md

**Source ADR:** [ADR-001](../../07-architecture/ADR-001-type-1-hyperv-generation-2.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-001-2026-10-30.adjudication.json](../gates/approve-brd-001-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

ADPA and SIDPA process confidential records. The business requires a hardware boundary that does not share the host kernel with neighbor workloads. The always-on server and the shared-kernel container are rejected for this bar.

## Business Rules (BRU)

- **BRU-001-01**: The production workload runs only in a Type-1 Hyper-V Generation 2 guest. *(from ADR-001 §4.1)*
- **BRU-001-02**: A shared-kernel container does not satisfy the isolation bar for these records. *(from ADR-001 §4.2)*
- **BRU-001-03**: WMI, COM+, a Windows service, and Group Policy must succeed inside that guest. *(from ADR-001 §4.3)*
- **BRU-001-04**: An idle guest is Paused, not left Running; it does not accept a new session while Paused. *(from ADR-001 §4.4)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Generation 2 guest in use for ADPA/SIDPA pools | Formulated (`HYP-mxc-006`); not re-measured for lifecycle docs |
| Named Windows subsystems succeed in guest vs container | Formulated (`HYP-mxc-009`, `BEN-05`); side-by-side check not run |
| Paused guest rejects direct service connection | Formulated (`HYP-mxc-021`, `BEN-11`); exposure comparison not run |

## Traceability to architecture suite


## Out of Scope

- Ingress buffering, TTFB ceilings, and routing (`ADR-002`).
- Paused RAM, CPU, GPU, and disk footprint readings (`ADR-004`).
- Production image contents and bake (`ADR-003`).
