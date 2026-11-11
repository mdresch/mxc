---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "7.1 Plan Cost Management"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-subsidiary-plan
inputs:
  - "Project-Charter.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
  - "resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "cost-baseline/Cost-Foundation-Pack-Manifest.md"
process: "Plan and formalize Cost Management Plan"
outputs:
  - "Cost-Management-Plan.md"
pmp_baseline: "PMP-BL-v1.0.0"
---

# Cost Management Plan — mxc

> **PMBOK 8 Process:** `7.1 Plan Cost Management` (Planning)  
> **Governance Policy:** `approve-subsidiary-plan` (foundation pack); rolls into `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** [Project-Charter.md](../Project-Charter.md), approved scope/schedule packs, [Resource Foundation Pack](resource-baseline/Resource-Foundation-Pack-Manifest.md), [Cost Foundation Pack](cost-baseline/Cost-Foundation-Pack-Manifest.md)

## 1. Purpose & scope of this plan

Defines how Phase-1 **mxc** costs are estimated, baselined, staged by milestone, and controlled for WBS **1.1.1–1.6.4**, rolled into the [Project Management Plan](../Project-Management-Plan.md) at **`PMP-BL-v1.0.0`**.

## 2. Cost baseline contents (Stage 7.D)

| Artifact | Location |
|---|---|
| Pillar overview & trace | [Cost-Pillar-Overview-and-Trace.md](cost-baseline/foundation/Cost-Pillar-Overview-and-Trace.md) |
| Categories & basis | [Cost-Categories-and-Estimating-Basis.md](cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md) |
| Estimates by category | [Cost-Estimates-by-Category.md](cost-baseline/foundation/Cost-Estimates-by-Category.md) |
| Staged budget & baseline | [Cost-Staged-Budget-and-Baseline.md](cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md) |
| Variance & control | [Cost-Variance-and-Control-Protocol.md](cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md) |
| Domain checklist | [Cost-Domain-Checklist.md](cost-baseline/foundation/Cost-Domain-Checklist.md) |

**Pack manifest:** [Cost-Foundation-Pack-Manifest.md](cost-baseline/Cost-Foundation-Pack-Manifest.md) — **v1.1.0**, **`pack_status: approved`** (7.D-7 complete 2026-11-10).

## 3. Cost management standards

- **Categories:** **CAT-LAB**, **CAT-LAB-OV**, **CAT-CONT**, **CAT-INFRA**, **CAT-TOOL**, **CAT-AGT** — see categories artifact.
- **Units:** EUR **ex. VAT**; labor = schedule **WD × 6 h × contractor market rate**; payroll loaded **N/A**.
- **Traceability:** Per-WBS rows reconcile to [Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md) and [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md).
- **Reserves:** Schedule **SCH-RSV-*** cost mirror in **CAT-CONT** — draw only with reserve consumption evidence.
- **Agentic:** **CAT-AGT** actuals only; not in performance baseline.
- **PM cost:** **€2,280** inside **CAT-LAB-OV** — sponsor/project imputed at contractor **€95/h** (~24 h); not timesheet-driven.
- **CAT-TOOL (Q-CST-002):** **€71/mo** — Cursor **€16**, Gemini Antigravity **€25**, Claude Code **€20**, GitHub Basic **€10**; **~€256** over CP window; outside **€58,710** labor baseline ([Cost-Estimates-by-Category.md](cost-baseline/foundation/Cost-Estimates-by-Category.md) § Q-CST-002).

## 4. Control & reforecast

- **Variance:** [Cost-Variance-and-Control-Protocol.md](cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md) — CPI/CV vs staged MS gates.
- **Actuals:** Story hours → [Story-Execution-Register.md](../../registers/Story-Execution-Register.md); contractor invoices → procurement records.
- **Rebaseline:** WD or rate changes via subsidiary plan / adaptation gates; manifest version bump.

## 5. Foundation pack roll-up (7.D-6 — 2026-11-10)

| Element | Value |
|---|---|
| Draft cost baseline ID | `COST-BL-v1.0.0` |
| CP labor (**CAT-LAB**) | **€50,610** (likely) |
| Governance overlay (**CAT-LAB-OV**) | **€8,100** |
| **Performance baseline (likely)** | **€58,710** |
| Contingency envelope (**CAT-CONT**) | **€18k – €28k** (not in performance baseline until drawn) |
| CP cost range | **~€28.5k – ~€66.2k** (low/high WD) |
| Milestone staging | MS-01 **€4,620** → MS-06 **€50,610** CP cum. — see staged budget |
| Authorization | **Q-CST-003** — subsidiary plans + **`approve-pmp`** (not a separate funding letter) |

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | [Project-Management-Plan.md](../Project-Management-Plan.md) **§3.4** and **§2.7.1** |
| Integrated PMP lock | **`approve-pmp`** **approved (2026-11-10)** |
| Gate record | [approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json) |
| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **approved (2026-11-10)** |

## 7. Review & governance invariant

This subsidiary plan integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Foundation pack approval uses **`approve-subsidiary-plan`**; integrated PMP lock uses **`approve-pmp`**. **Approved** cost baseline does **not** authorize invoices or override Stage 8 rules.

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json).
**PMP roll-up:** **€58,710** performance baseline (**€50,610** CP + **€8,100** OV), manifest **v1.1.0**, integrated into [Project-Management-Plan.md](../Project-Management-Plan.md) **2026-11-10** (**`approve-pmp`** lock **2026-11-10**).
