---
artifact_id: cost-foundation-staged-budget-baseline
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.D-3
pmbok_process: Develop Budget
depends_on:
  - 7.D-2
---

# Staged Budget and Cost Baseline — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d3-staged-budget-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-cost-7d3-staged-budget-2026-11-10.adjudication.json).

## Phase-1 staged budget (by schedule milestone)

Cumulative **CAT-LAB likely** through each milestone gate ([Schedule-Gantt-Phase1.md](../../schedule-baseline/foundation/Schedule-Gantt-Phase1.md)).

| Stage / gate | Work complete through | Cumulative CP labor (likely) | Cumulative + OV (likely) | Release condition |
|---|---|---|---|---|
| Gate 0 | Planning packs approved | €0 execution | — | Stage 8 notice |
| MS-01 | 1.1.2 | €4,620 | + pro-rata OV | Story 1.1.2 AC |
| MS-02 | 1.3.2 | €11,220 | ~€12,400 | Image baseline |
| MS-03 | 1.4.3 | €20,460 | ~€22,500 | Pause proven |
| MS-04 | 1.2.3 | €30,360 | ~€33,300 | Ingress live |
| MS-05 | 1.5.3 | €40,710 | ~€44,400 | Sterile path |
| MS-06 | 1.6.4 | **€50,610** | **~€54,700** | Pool ops |
| MS-07 | 1.0 acceptance | €50,610 | **€58,710** incl. **CAT-LAB-OV** | Phase-1 baseline |

OV pro-rata is illustrative; **€8,100** includes **€2,280** PM (sponsor-paid, imputed). Hours optional — EUR in baseline reflects that **someone pays** for PM.

## Baseline composition (likely)

| Component | Amount (EUR) | Type |
|---|---|---|
| CAT-LAB critical path | **50,610** | Performance baseline |
| CAT-LAB-OV | **8,100** | Governance ROM (QA / gates / ARC) |
| **Subtotal performance baseline** | **58,710** | Subsidiary + PMP gates at 7.D-7 / `approve-pmp` |
| CAT-CONT (schedule reserves) | **18,000 – 28,000** envelope | **Contingency / management reserve** — not in performance baseline until drawn |
| CAT-INFRA | **0** | Host sunk |
| CAT-TOOL | **€71/mo** (**~€256** through ~3.6 mo CP) | Cursor, Gemini Antigravity, Claude Code, GitHub Basic |

## Management reserve and contingency

- **Contingency (known-unknowns):** **SCH-RSV-001…004** — cost mirror in [Cost-Estimates-by-Category.md](Cost-Estimates-by-Category.md); consume with schedule reserve evidence.
- **Management reserve:** **SCH-RSV-MGT** (~**€5,280** at likely) — sponsor/PM approval via adaptation or charter.

## Budget reconciliation

| Check | Result |
|---|---|
| Labor vs resource ROM | **€50,610** — match |
| Hours vs schedule | **468 h** likely — match |
| Unfunded scope | None identified beyond reserves |
| Excluded | Payroll-loaded valuation; agentic **CAT-AGT** |
| Funding authorization | **`approve-subsidiary-plan`** on cost pack + **`approve-pmp`** (Q-CST-003 closed) |

## Exclusions

No CapEx server budget in Phase-1 draft. No multi-year opex. Contractor SOWs gate **actual** cash outlay per **Q-RES-003**.
