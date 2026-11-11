---
artifact_id: schedule-foundation-activity-list
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-2A
pmbok_process: Develop Schedule — define activities
depends_on:
  - 7.B-1
  - 7.B-2
---

# Schedule Activity List — mxc (Phase 1)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b2a-activity-list-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b2a-activity-list-2026-11-10.adjudication.json).

| Activity ID | WBS ID | Activity / deliverable | Predecessors | Estimate source | Owner | Acceptance evidence |
|---|---|---|---|---|---|---|
| 1.1.1 | 1.1.1 | Implement Gen2 isolation boundary (`implement-story`) | START | Basis § Gen2 | Platform | Epic 001 Story 1.1 |
| 1.1.2 | 1.1.2 | Validate Windows subsystems on guest | 1.1.1 | Basis § Gen2 | Platform | Epic 001 Story 1.2 |
| 1.3.1 | 1.3.1 | Build clean production VHDX | 1.1.2 | Basis § image; RSV-002 | Release | Story 3.1 AC |
| 1.3.2 | 1.3.2 | Publish warm baseline checkpoint | 1.3.1 | Basis § image | Release | Story 3.2 AC |
| 1.4.1 | 1.4.1 | Prove 0% idle CPU at Paused | 1.3.2 | Basis § pause; RSV-001 | Platform | Story 4.1 (Formulated) |
| 1.4.2 | 1.4.2 | Trim paused RAM footprint | 1.4.1 | Basis § pause; RSV-001 | Platform | Story 4.2 (Formulated) |
| 1.4.3 | 1.4.3 | Resume <300 ms benchmark | 1.4.2 | Parametric wake harness | Platform | Story 4.3; `benchmark_jit_wake.py` |
| 1.2.1 | 1.2.1 | Cold wake TTFB path | 1.4.3 | Basis § ingress | Platform | AC-01.1 |
| 1.2.2 | 1.2.2 | Eliminate wake 502/504 | 1.2.1 | Basis § ingress | Platform | AC-01.3 |
| 1.2.3 | 1.2.3 | Dual routing (path + port) | 1.2.2 | Basis § ingress; RSV-003 | Platform | HYP-mxc-004 |
| 1.5.1 | 1.5.1 | Ephemeral session differencing disk | 1.2.3 | Basis § sterility | SecOps | Story 5.1 |
| 1.5.2 | 1.5.2 | Egress whitelist enforcement | 1.5.1 | Basis § sterility | SecOps | Story 5.2; AC-02.3 |
| 1.5.3 | 1.5.3 | Discard and reproduce session | 1.5.2 | Basis § sterility | SecOps | Story 5.3 |
| 1.6.1 | 1.6.1 | Buffer replenishment | 1.5.3 | Basis § pool | SRE | Story 6.1 |
| 1.6.2 | 1.6.2 | Surge expansion | 1.6.1 | Basis § pool | SRE | Story 6.2 |
| 1.6.3 | 1.6.3 | Wake hygiene metrics | 1.6.2 | Basis § pool | SRE | Story 6.3 |
| 1.6.4 | 1.6.4 | Scale-down cooldown | 1.6.3 | Basis § pool | SRE | Story 6.4 |
| MS-07 | 1.0 | Phase-1 product implementation baseline complete | 1.6.4 | Roll-up | PM | All 1.N.S AC paths drafted or proven |

## Completeness review

- **17 / 17** story WBS rows have a primary activity.
- Milestones **MS-01…MS-06** are implicit gates between pillar groups (see pillar overview); **MS-07** closes WBS **1.0** implementation track.
- Governance pack **7.B** (WBS **2.2** — schedule foundation) is out of band for this activity list.
