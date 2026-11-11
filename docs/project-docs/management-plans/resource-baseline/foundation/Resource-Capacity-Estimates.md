---
artifact_id: resource-foundation-capacity-estimates
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-2
pmbok_process: Estimate Resources
depends_on:
  - 7.C-1
  - schedule-baseline approved
---

# Resource Capacity Estimates — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c2-capacity-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c2-capacity-2026-11-10.adjudication.json).

| Role ID | WBS scope (primary) | Demand (likely WD) | Demand (likely h) | Schedule window (1 FTE CP) | Available capacity (default plan) | Gap |
|---|---|---|---|---|---|---|
| **R-PLT** | 1.1.x, 1.2.x, 1.4.x | **36** | **216** | ~W0–W9.4 (through ingress) | 1.0 FTE × ~15.6 wks = 78 WD if sole assignee | **−42 WD** vs sole FTE—see mix below |
| **R-REL** | 1.3.x | **11** | **66** | ~W1.4–W3.6 | 0.25 FTE equivalent over phase | OK if dedicated slice |
| **R-SEC** | 1.5.x | **15** | **90** | ~W9.4–W12.4 | 0.3 FTE equivalent | OK |
| **R-SRE** | 1.6.x | **15** | **90** | ~W12.4–W15.4 | 0.3 FTE equivalent | OK |
| **R-QA** | All stories (embedded + review) | **8** | **48** | Distributed | 0.15 FTE equivalent | Planning overlay (~10% of CP) |
| **R-PM** | 2.x governance + MS-07 | **4** | **24** | Continuous light touch | Sponsor / PM time | OK |
| **R-ARC** | Advisory spikes | **2** | **12** | On demand | Fractional | OK |

**Roll-up check:** 36 + 11 + 15 + 15 + 8 + 4 + 2 = **91 WD** role-sum vs **~78 WD** CP (single-threaded integration). Overlap is **intentional** when roles are **not** one person; **single-assignee CP** model uses **R-PLT** for platform stories only → **77 WD** (matches schedule roll-up).

## Per-activity demand (detail)

**ROM** charges **lead specialist** rate for full **likely WD** unless split hours are recorded in actuals. Reporting specialists add overlay hours in governance/QA rows—not second-counted in CP ROM below.

| WBS ID | Lead specialist | Reporting to lead | Likely WD | Likely h | ROM (contractor, lead rate) |
|---|---|---|---|---|---|
| 1.1.1 | R-PLT | R-QA | 4 | 24 | €2,640 |
| 1.1.2 | R-PLT | R-QA | 3 | 18 | €1,980 |
| 1.3.1 | R-REL | R-PLT, R-QA | 7 | 42 | €4,200 |
| 1.3.2 | R-REL | R-PLT, R-QA | 4 | 24 | €2,400 |
| 1.4.1 | R-PLT | R-SRE, R-QA | 4 | 24 | €2,640 |
| 1.4.2 | R-PLT | R-SRE, R-QA | 5 | 30 | €3,300 |
| 1.4.3 | R-PLT | R-SRE, R-QA | 5 | 30 | €3,300 |
| 1.2.1 | R-PLT | R-SRE, R-QA | 6 | 36 | €3,960 |
| 1.2.2 | R-PLT | R-SRE, R-QA | 4 | 24 | €2,640 |
| 1.2.3 | R-PLT | R-SEC, R-ARC, R-QA | 5 | 30 | €3,300 |
| 1.5.1 | R-SEC | R-PLT, R-QA | 5 | 30 | €3,450 |
| 1.5.2 | R-SEC | R-PLT, R-QA | 6 | 36 | €4,140 |
| 1.5.3 | R-SEC | R-PLT, R-REL, R-QA | 4 | 24 | €2,760 |
| 1.6.1 | R-SRE | R-PLT, R-REL, R-QA | 4 | 24 | €2,640 |
| 1.6.2 | R-SRE | R-PLT, R-QA | 4 | 24 | €2,640 |
| 1.6.3 | R-SRE | R-PLT, R-QA | 3 | 18 | €1,980 |
| 1.6.4 | R-SRE | R-PLT, R-PM, R-QA | 4 | 24 | €2,640 |
| **CP subtotal** | — | **78** | **468** | — | **€50,610** (all contractor ROM, ex. VAT) |

ROM on CP rows only; **€8,100** governance overlay (**R-QA / R-PM / R-ARC** WD) rolls to **CAT-LAB-OV**, including **€2,280** imputed **R-PM** (sponsor pays; hours unlogged). See [Cost-Estimates-by-Category.md](../../cost-baseline/foundation/Cost-Estimates-by-Category.md).

## Staffing scenarios

| Scenario | Description | Calendar effect | Cost profile |
|---|---|---|---|
| **S1 — Solo integrator** | One **R-PLT** performs entire CP (78 WD) | ~15.6 wks @ 1 FTE | Lowest variety; pillar specialists advisory only |
| **S2 — Pillar specialists (recommended draft)** | Primary roles per table; **Tier A** sequential integration | Same CP if integration stays serial; specialists parallelize prep in Tier B | Contractor mix per role; ROM ~**€51k** labor CP + overlays |
| **S3 — Multi-FTE platform** | 2× R-PLT on non-CP branches | May compress calendar (Q-SCH-003) | Higher burn; regenerate Gantt |

## Assumptions and constraints

- **Calendar:** 5 WD/week; no holiday model ([Schedule-Gantt-Phase1.md](../../schedule-baseline/foundation/Schedule-Gantt-Phase1.md)).
- **Availability:** Default **100%** allocation to mxc Phase-1 when Stage 8 issued unless charter states otherwise.
- **Agentic capacity:** Not modeled as FTE; see V-AGT and schedule agentic actuals.
- **Reserves:** Schedule reserves (**SCH-RSV-*** ) may add **R-PLT** or **R-ARC** hours—size at consume time.
- **Reforecast:** Replace WD cells from `implement-story` human actuals; recalc hours and ROM in same table.
