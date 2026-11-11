---
artifact_id: resource-foundation-utilization-control-protocol
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-5
pmbok_process: Control Resources
depends_on:
  - 7.C-2
  - 7.C-3
---

# Resource Utilization and Control Protocol — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c5-utilization-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c5-utilization-2026-11-10.adjudication.json).

## Planned vs actual

| Metric | Planned source | Actual source | Control action |
|---|---|---|---|
| Human hours by WBS | [Resource-Capacity-Estimates.md](Resource-Capacity-Estimates.md) | `implement-story` time log → [Story-Execution-Register.md](../../../../registers/Story-Execution-Register.md) | Reforecast schedule WD; update ROM in cost pack |
| Role utilization % | Staffing scenario **S1** or **S2** | Weekly PM snapshot | Trigger Q-RES-002 if &gt;110% for 2 weeks |
| Contractor spend | Role catalogue **market contractor** rate × hours | Procurement invoices | Variance in **7.D** |
| Sponsor / internal hours | Hours only (payroll EUR **N/A**) | Story-Execution-Register | Optional Finance valuation later |
| Agentic usage | Not baselined | Forecast § Agentic; Status Register §5 | No fold into labor without rebaseline |

## Thresholds

- **Yellow:** Story actual hours &gt; **high** WD × 6 h before AC closure.
- **Red:** Critical path slip &gt; **2 wks** likely vs Gantt without approved rebaseline.
- **Reserve:** Pull **R-ARC** or extra **R-PLT** only with SCH-RSV evidence.

## Change links

Schedule or scope changes follow **`approve-subsidiary-plan`** / adaptation gates; resource tables version with manifest bump on **7.C-7**.
