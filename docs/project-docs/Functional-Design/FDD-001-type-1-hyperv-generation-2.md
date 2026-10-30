---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-001-type-1-hyperv-generation-2.md"
  - "docs/project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-001-type-1-hyperv-generation-2.md"
---

# FDD-001: Type-1 Hyper-V Generation 2 instead of a container namespace

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 7 (Requirement: Solution)`  
> **Inputs:** [ADR-001](../../07-architecture/ADR-001-type-1-hyperv-generation-2.md), [BRD-001](../Business-Requirements/BRD-001-type-1-hyperv-generation-2.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-001-type-1-hyperv-generation-2.md

**Source ADR:** [ADR-001](../../07-architecture/ADR-001-type-1-hyperv-generation-2.md) — Accepted.  
**Source BRD:** [BRD-001](../Business-Requirements/BRD-001-type-1-hyperv-generation-2.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-001-2026-10-30.adjudication.json](../gates/approve-fdd-001-2026-10-30.adjudication.json).

## Design

### Hyper-V partition model
* **Control plane:** `wxc-exec --features hyperv` (Rust Hyper-V backend under `src/mxc-sdk/src/backends/hyperv/`).
* **Guest class:** Generation 2 VM with its own kernel; not a container namespace on the host.
* **Idle posture:** Guest reaches `Paused` through the lifecycle controller; session acceptance while `Paused` is forbidden (resume is owned by ingress + pool).

### Verification hooks
| Check | Contract |
|---|---|
| Partition generation | Hyper-V reports Generation 2 for pool members |
| Subsystem probe | WMI query, COM+ activation, Windows service start, Group Policy refresh succeed in guest |
| Paused socket | Direct TCP to guest `:8080` fails while `Paused`; succeeds only after lease/resume |

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Container runtime requested for confidential pool | Reject provisioning; cite `ADR-001` and `BDR-03` |
| Guest left Running with no sessions | Violates sterility posture; pool manager must suspend per `ADR-004` |

## Out of Scope

- Ingress buffering, TTFB ceilings, and routing (`ADR-002`).
- Paused RAM, CPU, GPU, and disk footprint readings (`ADR-004`).
- Production image contents and bake (`ADR-003`).
