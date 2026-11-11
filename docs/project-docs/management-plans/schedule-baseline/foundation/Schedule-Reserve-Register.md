---
artifact_id: schedule-foundation-reserve-register
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-3
depends_on:
  - 7.B-1
  - 7.B-4
---

# Schedule Reserve Register — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b3-reserve-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b3-reserve-2026-11-10.adjudication.json).

| Reserve ID | Risk / uncertainty | Amount or range (WD) | Trigger | Release authority | Source |
|---|---|---|---|---|---|
| SCH-RSV-001 | Formulated pause metrics (1.4.1, 1.4.2) need instrumentation | 5–10 | Meter cannot prove AC | Platform lead | Epic 004; scope open gaps |
| SCH-RSV-002 | `BEN-08` / production catalog VHDX blocks 1.3.1 | 5–15 | Catalog asset missing >5 WD | Release | Project-Details-Not-In-ADR |
| SCH-RSV-003 | HYP-mxc-004 dual routing complexity | 3–7 | Routing test fails integration | Platform lead | Epic 002 Story 2.3 |
| SCH-RSV-004 | Cross-team review / audit latency | 2–5 | `approve-audit-record` queued | PM | Governance pipeline |
| SCH-RSV-MGT | Management reserve (unidentified) | **10%** of likely CP (~8 WD) | PM-approved scope change | PM | PMBOK contingency vs management |

## Review

- Contingency **consumes** against the linked WBS rows; update [Schedule-Baseline-WBS-Forecast.md](Schedule-Baseline-WBS-Forecast.md) when consumed.
- **SCH-RSV-MGT** requires **adaptation plan** or charter sponsor approval to draw down.
- No reserve converts to a **public commitment date** without approved schedule baseline.
