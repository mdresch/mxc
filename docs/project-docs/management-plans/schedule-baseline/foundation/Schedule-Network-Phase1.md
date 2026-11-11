---
artifact_id: schedule-foundation-network
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-2
pmbok_process: Develop Schedule — sequence activities
depends_on:
  - 7.B-1
  - scope-management
---

# Schedule Network — mxc (Phase 1)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b2-network-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b2-network-2026-11-10.adjudication.json).

## Precedence table

| Predecessor | Successor | Rel. | Rationale / source | Validated by |
|---|---|---|---|---|
| START | 1.1.1 | FS | Need Gen2 isolation boundary first | ADR-001; epic 001 |
| 1.1.1 | 1.1.2 | FS | Subsystems validated on same guest class | Epic 001 Story 1.2 |
| 1.1.2 | 1.3.1 | FS | Production image targets authorized guest | ADR-003 |
| 1.3.1 | 1.3.2 | FS | Checkpoint requires clean base image | Epic 003 Story 3.2 |
| 1.3.2 | 1.4.1 | FS | Pause/trim needs deployable image | ADR-004 |
| 1.4.1 | 1.4.2 | FS | Trim builds on pause discipline | Epic 004 |
| 1.4.2 | 1.4.3 | FS | Resume proof after footprint work | `benchmark_jit_wake.py` |
| 1.4.3 | 1.2.1 | FS | Ingress buffers wake from Paused guest | ADR-002 |
| 1.2.1 | 1.2.2 | FS | Error budget after TTFB path | AC-01.3 |
| 1.2.2 | 1.2.3 | FS | Routing after stable wake | HYP-mxc-004 |
| 1.2.3 | 1.5.1 | FS | Sessions attach diff disk through live path | ADR-005 |
| 1.5.1 | 1.5.2 | FS | Egress rules on session stack | US-02 |
| 1.5.2 | 1.5.3 | FS | Discard proves sterility | Story 5.3 |
| 1.5.3 | 1.6.1 | FS | Pool manages session-capable guests | ADR-006 |
| 1.6.1 | 1.6.2 | FS | Surge after replenish baseline | Epic 006 |
| 1.6.2 | 1.6.3 | FS | Hygiene after surge policy | Story 6.3 |
| 1.6.3 | 1.6.4 | FS | Scale-down closes loop | Story 6.4 |
| 1.6.4 | MS-07 | FS | Phase-1 product track complete | Scope WBS 1.0 |

## Dependency assumptions

- **No circular** dependencies; cross-pillar order follows [Schedule-Pillar-Overview-and-Trace.md](Schedule-Pillar-Overview-and-Trace.md).
- **External:** catalog VHDX for **1.3.1** may slip via **SCH-RSV-002** (reserve register).
- **Governance** gates on scope are complete; implementation gates (`implement-story`, tests) sit **inside** each activity duration.

## Critical path (Phase 1, single-threaded)

**Critical path:** `1.1.1 → … → 1.6.4 → MS-07` (17 story activities, longest FS chain). Float = 0 on this chain in the draft single-resource model; parallel staffing may create non-critical branches later.
