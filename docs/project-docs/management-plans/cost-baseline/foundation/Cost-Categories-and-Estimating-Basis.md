---
artifact_id: cost-foundation-categories-estimating-basis
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.D-1
pmbok_process: Plan Financial Management
depends_on:
  - 7.D-0P
  - resource-baseline approved
---

# Cost Categories and Estimating Basis — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d1-categories-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-cost-7d1-categories-2026-11-10.adjudication.json).

| Category ID | Category | Unit | Included elements | Exclusions | Evidence | Method |
|---|---|---|---|---|---|---|
| **CAT-LAB** | Labor — CP execution | EUR | Lead specialist hours on WBS **1.1.1–1.6.4** | Agentic tokens; payroll valuation of sponsor time | [Resource-Capacity-Estimates.md](../../resource-baseline/foundation/Resource-Capacity-Estimates.md); schedule forecast WD | Bottom-up: WD × **6 h** × **contractor market** rate ([Resource-Role-Catalogue.md](../../resource-baseline/foundation/Resource-Role-Catalogue.md)) |
| **CAT-LAB-OV** | Labor — governance overlay | EUR | R-QA, R-PM (gate ROM), R-ARC hours **not** on CP rows — **€8,100** likely | Sponsor **unlogged** calendar time; duplicate CP lead hours | Resource capacity § overlay | Parametric **14 WD** × contractor market rates |
| **CAT-CONT** | Contingency — schedule reserves | EUR | Cost of **SCH-RSV-001…004** + **SCH-RSV-MGT** when consumed | Unapproved scope growth | [Schedule-Reserve-Register.md](../../schedule-baseline/foundation/Schedule-Reserve-Register.md) | WD reserve × **6 h** × blended **€110/h** planning rate |
| **CAT-INFRA** | Infrastructure opex (Phase 1) | EUR | Host power, storage growth for VHDX | CapEx server purchase | Charter; existing Type-1 host | Analogous placeholder — **€0** committed until metering |
| **CAT-TOOL** | Tooling & subscriptions | EUR / month | **€71/mo** — Cursor **€16**, Gemini Antigravity **€25**, Claude Code **€20**, GitHub Basic **€10** | CapEx; **CAT-AGT** overage | Tooling register; estimates § Q-CST-002 | **~€256** Phase-1 (~3.6 mo); **not** inside **€58,710** labor baseline |
| **CAT-AGT** | Agentic compute | EUR | Model / token usage | Human labor | Schedule § Agentic actuals | **Actuals only** — no Phase-1 estimate |

## Assumptions and controls

| Topic | Rule |
|---|---|
| **Tax / VAT** | ROM **ex. VAT**; invoices per Procurement |
| **Exchange** | Single currency **EUR** — no FX |
| **Sponsor / PM labor** | **Not on schedule**; hours **not logged**; **€2,280** imputed in **CAT-LAB-OV** at contractor PM rate (**someone pays** — sponsor/project) |
| **Uncertainty** | Triangular **low / likely / high** per WBS WD maps to cost range in [Cost-Estimates-by-Category.md](Cost-Estimates-by-Category.md) |
| **Sunk cost** | Existing Hyper-V host and many dev seats treated as **sunk** for Phase-1 ROM |
| **CAT-TOOL (Q-CST-002)** | **€71/mo** recurring (sponsor **2026-11-10**); Phase-1 **~€256** — see [Cost-Estimates-by-Category.md](Cost-Estimates-by-Category.md) § Q-CST-002 |
| **Authorization** | Figures are **planning baseline draft** — release via **7.D-7** + **`approve-pmp`** on integrated PMP |
| **Reforecast** | `implement-story` actual hours trump analogous WD; rebaseline via change control |
