---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-003-production-base-image.md"
  - "docs/project-docs/Business-Requirements/BRD-003-production-base-image.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-003-production-base-image.md"
---

# FDD-003: Production base image separate from the developer image

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-003](../../07-architecture/ADR-003-production-base-image.md), [BRD-003](../Business-Requirements/BRD-003-production-base-image.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-003-production-base-image.md

**Source ADR:** [ADR-003](../../07-architecture/ADR-003-production-base-image.md) — Accepted.  
**Source BRD:** [BRD-003](../Business-Requirements/BRD-003-production-base-image.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-003-2026-10-30.adjudication.json](../gates/approve-fdd-003-2026-10-30.adjudication.json).

## Design

### Bake pipeline (suite `FDD.md` §2.3, `US-04`)
* Scripts: `bake_production_adpa_image.ps1` (`AC-04.2`), `audit_production_image.ps1` (`AC-04.1`).
* Output VHDX: `winserv2025-prod-adpa.vhdx` with ADPA/SIDPA Windows service on `:8080`.
* After smoke and DB handle close: checkpoint `baseline-hot-ready`.
* Developer lineage remains on `winserv2025-mxc-dev.vhdx` (`img-mxc-dev-v2.3`).

### Documentation-only until bake completes
Supply-chain signing (`HYP-mxc-017`) has no implementation in tree today.

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Audit finds forbidden toolchain | Fail bake gate; do not register image in production pool |
| Prod pool pointed at dev VHDX | Reject pool registration; cite `BRU-003-01` |

## Out of Scope

- Session `.avhdx` discard (`ADR-005`).
- Paused RAM footprint (`ADR-004`).
- Cosign/SBOM horizon (`HYP-mxc-017`).
