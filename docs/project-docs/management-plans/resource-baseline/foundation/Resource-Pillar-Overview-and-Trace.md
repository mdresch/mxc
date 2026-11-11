---
artifact_id: resource-foundation-pillar-overview-trace
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-0P
depends_on:
  - scope-baseline approved
  - schedule-baseline approved
---

# Resource Pillar Overview and Trace — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c0p-pillar-overview-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c0p-pillar-overview-2026-11-10.adjudication.json).

| Outcome / priority | WBS | Schedule window (1 FTE CP) | Primary human role | Resource implication |
|---|---|---|---|---|
| **MS-01** Gen2 ready | 1.1.1–1.1.2 | W0–W1.4 | R-PLT | Hyper-V host access; Rust toolchain; sandbox MCP |
| **MS-02** Image baseline | 1.3.1–1.3.2 | W1.4–W3.6 | R-REL (+ R-PLT handoff) | Imaging storage; VHDX pipeline; bake lock discipline |
| **MS-03** Paused proven | 1.4.1–1.4.3 | W3.6–W6.4 | R-PLT | Wake benchmarks; performance harness time |
| **MS-04** Ingress live | 1.2.1–1.2.3 | W6.4–W9.4 | R-PLT | Network test rig; dual-routing validation |
| **MS-05** Sterile path | 1.5.1–1.5.3 | W9.4–W12.4 | R-SEC | Security review bandwidth; egress lab |
| **MS-06** Pool ops | 1.6.1–1.6.4 | W12.4–W15.4 | R-SRE | Pool metrics stack; operational dashboards |
| **MS-07** Phase-1 baseline | 1.0 | ~W15.6 | R-PM + all leads | Acceptance rollup; no new FTE spike |

## Trace to schedule authority

- Activity IDs and owners: [Schedule-Activity-List-Phase1.md](../../schedule-baseline/foundation/Schedule-Activity-List-Phase1.md).
- WD demand by role: [Resource-Capacity-Estimates.md](Resource-Capacity-Estimates.md).
- Role skills and rates: [Resource-Role-Catalogue.md](Resource-Role-Catalogue.md).

## Review

Resource staffing follows **approved integration order** (not epic folder numeric order). Multi-role staffing does not shorten CP until **Q-SCH-003** is resolved and Gantt is regenerated.
