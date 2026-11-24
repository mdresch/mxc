---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-005-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-005-*.md"
---

# BRD-005: Transient differencing disk and egress whitelist

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-005](../../07-architecture/ADR-005-transient-differencing-disk.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (BDR-04)  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-005-transient-differencing-disk.md

**Source ADR:** [ADR-005](../../07-architecture/ADR-005-transient-differencing-disk.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-005-2026-10-30.adjudication.json](../gates/approve-brd-005-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

Session residue must not survive release. Persistent data uses approved internal endpoints only.

## Business Rules (BRU)

- **BRU-005-01**: Session writes occur only on a transient `.avhdx` anchored at `baseline-hot-ready`. *(from ADR-005 §4.1–4.2)*
- **BRU-005-02**: Whole-guest or `.avhdx`-only discard both reproduce the next session from the approved production image. *(from ADR-005 §4.3–4.4)*
- **BRU-005-03**: Public internet egress is denied; named internal ports are allowed. *(from ADR-005 §4.5)*
- **BRU-005-04**: Hung requests past 900 s return HTTP 504 and trigger reap (distinct from wake 504). *(from ADR-005 §4.6)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Session file gone after release | Formulated (`HYP-mxc-013`); packet capture for ACL not renewed |
| Parent hash unchanged (`AC-02.2`) | Formulated |
| Both discard paths (`BEN-12`) | Open while production image unfinished |

## Traceability to architecture suite

- Requirements matrix: `REQ-BDR-02, REQ-BDR-03` in [BDR.md](../../hyperv/architecture/BDR.md).
- Primary user story anchor: `US-02` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).

## Out of Scope

- Entropy reseed, clock step, DB pool purge on wake (`ADR-006`).
- Ingress TTFB (`ADR-002`).
- Memory scratch disk horizon (`HYP-mxc-019`).
