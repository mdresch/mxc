---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-003-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-003-*.md"
---

# BRD-003: Production base image separate from the developer image

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 7 (Requirement: Business)`  
> **Inputs:** [ADR-003](../../07-architecture/ADR-003-production-base-image.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (BDR-04 (packaging))  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-003-production-base-image.md

**Source ADR:** [ADR-003](../../07-architecture/ADR-003-production-base-image.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-003-2026-10-30.adjudication.json](../gates/approve-brd-003-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

Production must not run from the developer golden image. Attack surface and bake hygiene require a separate VHDX with no toolchain and a warm checkpoint.

## Business Rules (BRU)

- **BRU-003-01**: Production pool parent is `winserv2025-prod-adpa.vhdx`, not `winserv2025-mxc-dev.vhdx`. *(from ADR-003 §4.1)*
- **BRU-003-02**: Inventory finds no Scoop, cargo, git, compiler, uv, or source repositories on the production VHDX. *(from ADR-003 §4.3)*
- **BRU-003-03**: Checkpoint `baseline-hot-ready` is taken after smoke on `localhost:8080/health`. *(from ADR-003 §4.4)*
- **BRU-003-04**: Image signing and vulnerability scan stay future until `HYP-mxc-017` is implemented. *(from ADR-003 §4.6)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Production VHDX in catalog | Not present yet; `BEN-08` unrealized |
| Clean inventory (`AC-04.1`) | Blocked on finished bake |
| Warm checkpoint after smoke (`AC-04.2`) | Blocked on finished bake |

## Traceability to architecture suite

- Requirements matrix: `REQ-BDR-04` in [BDR.md](../../hyperv/architecture/BDR.md).
- Primary user story anchor: `US-04` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).

## Out of Scope

- Session `.avhdx` discard (`ADR-005`).
- Paused RAM footprint (`ADR-004`).
- Cosign/SBOM horizon (`HYP-mxc-017`).
