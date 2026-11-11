---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-004-paused-ram-standby.md"
  - "docs/project-docs/Business-Requirements/BRD-004-paused-ram-standby.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-004-paused-ram-standby.md"
---

# FDD-004: Paused RAM standby, trimmed before suspend

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-004](../../07-architecture/ADR-004-paused-ram-standby.md), [BRD-004](../Business-Requirements/BRD-004-paused-ram-standby.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-004-paused-ram-standby.md

**Source ADR:** [ADR-004](../../07-architecture/ADR-004-paused-ram-standby.md) — Accepted.  
**Source BRD:** [BRD-004](../Business-Requirements/BRD-004-paused-ram-standby.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-004-2026-10-30.adjudication.json](../gates/approve-fdd-004-2026-10-30.adjudication.json).

## Design

### Pause and resume (`FDD.md` §2.2, `wxc-exec`)
* Trim working set (`EmptyWorkingSet` or `/admin/pre-trim`) while vCPUs run, then `Suspend-VM`.
* `Resume-VM` on lease; pages remain in host RAM.
* `pool-release` restores `baseline-hot-ready` then suspends so paused size equals checkpoint size when restore succeeds.

### States excluded
`Save-VM` and `Stopped` are not the warm standby path for this ADR.

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Resume waits on disk page-in | Fail `HYP-mxc-002`; do not claim 300 ms ceiling |
| Balloon trim after pause | Invalid; trim must occur before `Suspend-VM` |

## Out of Scope

- 800 ms caller TTFB (`ADR-002`).
- Warm checkpoint contents (`ADR-003`).
- NVMe deep tier (`HYP-mxc-018` horizon).
