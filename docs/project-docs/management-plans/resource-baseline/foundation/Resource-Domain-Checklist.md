---
artifact_id: resource-foundation-domain-checklist
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-6
depends_on:
  - 7.C-1
  - 7.C-2
  - 7.C-3
  - 7.C-4
  - 7.C-5
---

# Resource Domain Checklist — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c6-domain-checklist-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c6-domain-checklist-2026-11-10.adjudication.json).

| Outcome / check | Evidence | Owner | Result | Action |
|---|---|---|---|---|
| Resource roles and decision rights are understood | [Resource-Role-Catalogue.md](Resource-Role-Catalogue.md) § RACI | PM | **pass (draft)** | Ratify names at Stage 8 |
| Skills/competencies defined per execution role | Role catalogue § Skills | PM | **pass (draft)** | — |
| Capacity matched to approved schedule | [Resource-Capacity-Estimates.md](Resource-Capacity-Estimates.md) vs forecast 78 WD | PM | **pass (draft)** | **Q-RES-002 closed** — estimates accepted; S1/S2 remain documented options |
| Hourly rates disclosed for planning | Role catalogue § Rates — **contractor market** only | Sponsor | **pass (draft)** | Payroll **N/A**; Q-RES-001 closed |
| Team collaboration and performance supported | [Resource-Team-Operating-Charter.md](Resource-Team-Operating-Charter.md) | PM | **pass (draft)** | — |
| Physical and virtual resources registered | [Resource-Tooling-and-Assignment-Register.md](Resource-Tooling-and-Assignment-Register.md) | R-PLT | **pass (draft)** | Q-RES-004 metrics |
| Utilization and conflicts monitored | [Resource-Utilization-and-Control-Protocol.md](Resource-Utilization-and-Control-Protocol.md) | PM | **pass (draft)** | Wire Story-Execution-Register |

## Gaps and disposition

| ID | Gap | Owner | Gate |
|---|---|---|---|
| Q-RES-001 | Payroll rates unavailable | Finance | **closed (N/A)** — use contractor market ROM |
| Q-RES-002 | Staffing estimates accepted | PM | **closed (2026-11-10)** |
| Q-RES-003 | Contractor mix | Procurement | SOW |
| Q-RES-004 | Observability tool for 1.6.x | R-SRE | Story 1.6.1 |

Checklist completion is not pack approval.
