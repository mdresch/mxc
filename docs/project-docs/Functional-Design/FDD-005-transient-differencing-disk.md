---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-005-transient-differencing-disk.md"
  - "docs/project-docs/Business-Requirements/BRD-005-transient-differencing-disk.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-005-transient-differencing-disk.md"
---

# FDD-005: Transient differencing disk and egress whitelist

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-005](../../07-architecture/ADR-005-transient-differencing-disk.md), [BRD-005](../Business-Requirements/BRD-005-transient-differencing-disk.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-005-transient-differencing-disk.md

**Source ADR:** [ADR-005](../../07-architecture/ADR-005-transient-differencing-disk.md) — Accepted.  
**Source BRD:** [BRD-005](../Business-Requirements/BRD-005-transient-differencing-disk.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-005-2026-10-30.adjudication.json](../gates/approve-fdd-005-2026-10-30.adjudication.json).

## Design

### Differencing disk lifecycle (`FDD.md` §2.2)
* Lease: active `.avhdx` on `baseline-hot-ready`.
* Release or 300 s idle with `active_open_requests == 0`: delete `.avhdx`, restore checkpoint.
* Optional whole-guest removal reproduces from approved parent (`HYP-mxc-022`).

### Egress whitelist (guest firewall)
* Ingress: `:8080` from proxy only.
* Egress allow: `:1433`, `:5432`, private blob `:443`, `:53`, `:88`.
* Default deny public internet.

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Session file remains after release | Fail `AC-02.1` / `BEN-07` |
| Egress to public IP | Drop and log; fail `AC-02.3` |

## Out of Scope

- Entropy reseed, clock step, DB pool purge on wake (`ADR-006`).
- Ingress TTFB (`ADR-002`).
- Memory scratch disk horizon (`HYP-mxc-019`).
