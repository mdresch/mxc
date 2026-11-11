---
artifact_id: cost-foundation-variance-control
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.D-4
pmbok_process: Monitor and Control Finances
depends_on:
  - 7.D-3
---

# Cost Variance and Control Protocol — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d4-variance-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-cost-7d4-variance-2026-11-10.adjudication.json).

| Measure | Planned source | Actual source | Cadence | Threshold | Owner | Action |
|---|---|---|---|---|---|---|
| **CV** (cost variance) | [Cost-Staged-Budget-and-Baseline.md](Cost-Staged-Budget-and-Baseline.md) by MS | Invoices + hours × rate | Per milestone | **>10%** over stage cumulative likely | PM | Reforecast; draw **CAT-CONT** only with reserve ID |
| **CPI** (hours efficiency) | WBS WD likely × 6 h | Story-Execution-Register actual h | Per story | Actual h **> high** WD × 6 | Lead specialist | Schedule rebaseline |
| **ROM drift** | Cost-Estimates CAT-LAB row | Revised WD from schedule | On rebaseline | Any CP change | PM | `approve-subsidiary-plan` cost pack bump |
| **Reserve burn** | CAT-CONT envelope | Linked SCH-RSV consume | On event | Each draw logged | PM | Update staged budget table |
| **Contractor spend** | Contractor rate × h | Procurement invoice | Monthly | Invoice **> SOW** | Procurement | Escalate sponsor |
| **CAT-TOOL actuals** | **€71/mo** plan | Monthly invoices | Monthly | **≠ €71/mo** sustained or new SKU | PM | Update estimates § Q-CST-002 |

## Change and forecast control

1. **Within story:** Lead records hours; no baseline change if within **high** WD cost.
2. **Cross-story / CP change:** Adaptation or scope gate → update forecast WD → **Cost-Estimates-by-Category** → manifest version bump → **7.D-7** if approved baseline changes.
3. **Contingency:** PM publishes reserve ID, WD consumed, EUR calc (WD × 6 × rate from role catalogue).
4. **Sponsor / PM labor:** Baselined **€2,280** (imputed); optional hour logs for trend only — variance vs imputed EUR if scope of gate work changes.
5. **Agentic:** **CAT-AGT** actuals monthly; never auto-increase **CAT-LAB** without rebaseline decision.

## Governance record

Cost baseline changes require subsidiary plan gate or integrated PMP rebaseline per [Project-Management-Plan.md](../../../Project-Management-Plan.md).
