---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
pmp_status: approved
pmp_approved: "2026-11-10"
pmp_approval_gate: "gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json"
pmp_sha256_at_approval: "ef84ce08e60d5c47f1b13f99475c1a9f2171525bd7bcff83f0d1d4bce06ecf1a"
subsidiary_baselines_integrated:
  - scope: "2026-11-10"
  - schedule: "2026-11-10"
  - resource: "2026-11-10"
  - cost: "2026-11-10"
operational_subsidiary_plans_integrated:
  - quality: "2026-11-10"
  - communications: "2026-11-10"
  - risk: "2026-11-10"
  - procurement: "2026-11-10"
  - stakeholder: "2026-11-10"
inputs:
  - "Project-Charter.md"
  - "docs/project-docs/management-plans/*.md"
process: "Integrate subsidiary management plans, establish baselines, define governance gates"
outputs:
  - "Project-Management-Plan.md"
---

# Project Management Plan (PMP) — SIDPA Project

> **PMBOK 8 Process:** `4.2 Develop Project Management Plan` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 7 (Planning: Integrated PMP & Baselines)`  
> **Baseline Identifier:** `PMP-BL-v1.0.0`  
> **Inputs:** Project-Charter.md, Subsidiary Management Plans  
> **Process:** Integrate subsidiary management plans, establish baselines, define governance gates  
> **Outputs:** Project-Management-Plan.md

## 1. Executive Summary & Baselines

- **Project Title:** **mxc** — JIT Hyper-V product (SIDPA lifecycle)
- **Baseline ID:** `PMP-BL-v1.0.0`
- **Scope Baseline:** **Approved (2026-11-10)** — [Scope foundation pack v1.2.0](management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md); WBS **1.0**, pillars **1.1–1.6**, **17** story packages **1.1.1–1.6.4**; authority [Scope Management Plan](management-plans/Scope-Management-Plan.md).
- **Schedule Baseline:** **Approved (2026-11-10)** — [Schedule foundation pack v1.1.0](management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md); integration path **1.1.1 → … → 1.6.4**; **~78 WD likely** (~**15.6** relative weeks @ 1 FTE, human effort only); milestones **MS-01 … MS-07**; reserves **SCH-RSV-001 … 004** + 10% management; authority [Schedule Management Plan](management-plans/Schedule-Management-Plan.md). **Not** a calendar commitment or Stage 8 execution authorization.
- **Cost Baseline:** **Approved (2026-11-10)** — **`COST-BL-v1.0.0`** — **€58,710** likely performance (ex. VAT: **€50,610** CP + **€8,100** governance OV) — [Cost foundation pack v1.1.0](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md); **CAT-TOOL** **€71/mo**; contingency **€18k–€28k**; authority [Cost Management Plan](management-plans/Cost-Management-Plan.md).
- **Resource Baseline:** **Approved (2026-11-10)** — [Resource foundation pack v1.0.0](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md); contractor market ROM **€50,610** CP labor; authority [Resource Management Plan](management-plans/Resource-Management-Plan.md). **Q-RES-003/004** remain open constraints.
- **Operational subsidiary plans (approved 2026-11-10):** [Quality](management-plans/Quality-Management-Plan.md), [Communications](management-plans/Communications-Management-Plan.md), [Risk](management-plans/Risk-Management-Plan.md) (11 risks **RSK-01…11**), [Procurement](management-plans/Procurement-Management-Plan.md), [Stakeholder engagement](management-plans/Stakeholder-Engagement-Plan.md) — rolled into PMP §2.8–§2.13 and §3.5–§3.9; **approved** at PMP gate **2026-11-10**.
- **Integrated PMP lock:** **Approved (2026-11-10)** — `approve_pmp` accepted on 2026-11-10 (policy `46c60639-c24f-4045-8ace-a3dbe2142e61`, human acceptance). Gate: [approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json](gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json). **Stage 8** still required for execution.

## 2. Integrated Subsidiary Management Plans

| Approval package | [PMP-Approval-Package-Manifest.md](management-plans/PMP-Approval-Package-Manifest.md) — **`approve_pmp` accepted 2026-11-10** |
|---|---|

### 2.5.1 Scope Management Plan

**Document Link:** [management-plans/Scope-Management-Plan.md](management-plans/Scope-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Pack manifest | [Scope-Foundation-Pack-Manifest.md](management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md) **v1.2.0**, `pack_status: approved` |
| Subsidiary gate | [approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json) |
| PMP register | §3.1 — integrated **2026-11-10** |
| Execution | **Stage 8** not issued — scope approval does not authorize `implement-story` |

### 2.6.1 Schedule Management Plan

**Document Link:** [management-plans/Schedule-Management-Plan.md](management-plans/Schedule-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Pack manifest | [Schedule-Foundation-Pack-Manifest.md](management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md) **v1.1.0**, `pack_status: approved` |
| Critical path (likely) | **~78 WD** human developer effort; network [Schedule-Network-Phase1.md](management-plans/schedule-baseline/foundation/Schedule-Network-Phase1.md) |
| Agentic effort | **Not estimated** in baseline — actuals only ([forecast § Agentic](management-plans/schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md)) |
| Living execution policy | [Agentic-Parallel-Execution-Policy.md](Agentic-Parallel-Execution-Policy.md) (Tier A/B; not in frozen pack) |
| Subsidiary gate | [approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json) |
| PMP register | §3.2 — integrated **2026-11-10** |
| Execution | **Stage 8** not issued — schedule WD ranges are not delivery commitments |

### 2.7.1 Cost Management Plan

**Document Link:** [management-plans/Cost-Management-Plan.md](management-plans/Cost-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Pack manifest | [Cost-Foundation-Pack-Manifest.md](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md) **v1.1.0**, `pack_status: approved` |
| Performance baseline (likely) | **€58,710** ex. VAT (**CAT-LAB** + **CAT-LAB-OV** **€8,100**) |
| Contingency envelope | **€18k – €28k** (**CAT-CONT** ↔ schedule reserves) |
| Labor basis | Contractor market rates; payroll **N/A** — [Resource-Role-Catalogue.md](management-plans/resource-baseline/foundation/Resource-Role-Catalogue.md) |
| Staging | [Cost-Staged-Budget-and-Baseline.md](management-plans/cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md) MS-01…MS-07 |
| Subsidiary gate | [approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json) |
| PMP register | §3.4 — integrated **2026-11-10** |
| Execution | **Stage 8** not issued — cost baseline does not authorize invoices or SOWs |

### 2.8.1 Quality Management Plan

**Document Link:** [management-plans/Quality-Management-Plan.md](management-plans/Quality-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Validation authority | [Scope-Validate-Scope.md](management-plans/scope-baseline/foundation/Scope-Validate-Scope.md) |
| Quality gates | **QG-01** (planning) → **QG-04** (pool hygiene) |
| QG-01 status | **Passed (2026-11-10)** — integrated PMP approved |
| Sandbox discipline | MXC Hyper-V guest; contract-first |
| PMP register | §3.5 — integrated **2026-11-10** |
| Execution | Stage 8 + `implement-story` still required |

### 2.9.1 Resource Management Plan

**Document Link:** [management-plans/Resource-Management-Plan.md](management-plans/Resource-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Pack manifest | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0**, `pack_status: approved` |
| CP labor ROM | **€50,610** contractor market |
| Subsidiary gate | [approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json) |
| PMP register | §3.3 — integrated **2026-11-10** |
| Execution | **Stage 8** not issued — ROM does not authorize SOWs |

### 2.10.1 Communications Management Plan

**Document Link:** [management-plans/Communications-Management-Plan.md](management-plans/Communications-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Source of truth | [Project-Status-Register.md](../registers/Project-Status-Register.md), registers first |
| Primary channels | GitHub PR, in-repo markdown, gate JSON |
| Cadence | Status register at natural pauses; monthly **CAT-TOOL** variance |
| PMP register | §3.6 — integrated **2026-11-10** |
| Cross-ref | [Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md) |

### 2.11.1 Risk Management Plan

**Document Link:** [management-plans/Risk-Management-Plan.md](management-plans/Risk-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Phase-1 register | **RSK-01 … RSK-11** in plan §3 |
| Reserve link | [Schedule-Reserve-Register.md](management-plans/schedule-baseline/foundation/Schedule-Reserve-Register.md) |
| Cost contingency | **CAT-CONT** **€18k – €28k** envelope |
| PMP register | §3.7 — integrated **2026-11-10** |
| Open items | **Q-SCH-001**, **Q-RES-003**, agentic collision **RSK-10** |

### 2.12.1 Procurement Management Plan

**Document Link:** [management-plans/Procurement-Management-Plan.md](management-plans/Procurement-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Make/buy | Core **make**; specialists **buy** on SOW (**Q-RES-003**) |
| Subscriptions | **CAT-TOOL** **€71/mo** — sponsor direct |
| Contractor ROM | Aligns with **CAT-LAB** / role catalogue |
| PMP register | §3.8 — integrated **2026-11-10** |
| Execution | No PO authority until Stage 8 + SOW |

### 2.13.2 Stakeholder Engagement Plan

**Document Link:** [management-plans/Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md)

| Roll-up item | Record |
|---|---|
| Register | [Stakeholder-Register.md](Stakeholder-Register.md) + **SH-01…06** in plan |
| Approval touchpoints | `approve-subsidiary-plan`, **`approve-pmp`**, Stage 8 |
| PMP register | §3.9 — integrated **2026-11-10** |
| Gaps | Charter/benefits gates (**Q-SCOPE-002/004**) |

## 3. Subsidiary baseline register (`PMP-BL-v1.0.0`)

Authoritative PMP pointers for approved foundation packs. Full artifact SHA-256 registries remain on each pack manifest.

### 3.1 Scope (7.A)

| Field | Value |
|---|---|
| Baseline identifier | `PMP-BL-v1.0.0` |
| Manifest | [Scope-Foundation-Pack-Manifest.md](management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md) **v1.2.0** |
| Subsidiary plan approval | 2026-11-10 — policy `1c0b25f8-af6e-4573-a101-9f5568f28792` |
| Gate record | [approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json) |
| Product WBS in baseline | **1.1.1–1.6.4** (17 packages) |
| Unresolved constraints | Q-SCOPE-002, Q-SCOPE-004, **WBS-001** (governance 2.x vs schedule/cost split) — see manifest |

### 3.2 Schedule (7.B)

| Field | Value |
|---|---|
| Baseline identifier | `PMP-BL-v1.0.0` |
| Manifest | [Schedule-Foundation-Pack-Manifest.md](management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md) **v1.1.0** |
| Subsidiary plan approval | 2026-11-10 — policy `1c0b25f8-af6e-4573-a101-9f5568f28792` |
| Gate record | [approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json) |
| Sequencing | TP-01 → TP-03 → TP-04 → TP-02 → TP-05 → TP-06 (FS) |
| Duration snapshot | **~78 WD likely** on CP; **MS-07** ~W15.6 @ 1 FTE ([Gantt model](management-plans/schedule-baseline/foundation/Schedule-Gantt-Phase1.md)) |
| Reserves | [Schedule-Reserve-Register.md](management-plans/schedule-baseline/foundation/Schedule-Reserve-Register.md) |
| Unresolved constraints | **Q-SCH-001** (no human velocity history), **Q-SCH-002** (calendar vs Stage 8), **Q-SCH-003** (multi-FTE / agentic calendar) — see [Schedule-Domain-Checklist.md](management-plans/schedule-baseline/foundation/Schedule-Domain-Checklist.md) |

### 3.3 Resource (7.C)

| Field | Value |
|---|---|
| Baseline identifier | `PMP-BL-v1.0.0` |
| Manifest | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0** |
| Gate record | [approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json) |
| CP labor ROM | **€50,610** contractor market (aligns with **CAT-LAB**) |
| Subsidiary plan approval | 2026-11-10 — policy `1c0b25f8-af6e-4573-a101-9f5568f28792` |
| Unresolved constraints | **Q-RES-003** (SOW), **Q-RES-004** (observability) — see manifest |

### 3.4 Cost (7.D)

| Field | Value |
|---|---|
| Cost baseline ID | `COST-BL-v1.0.0` |
| PMP baseline | `PMP-BL-v1.0.0` |
| Manifest | [Cost-Foundation-Pack-Manifest.md](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md) **v1.1.0** |
| Subsidiary plan | [Cost-Management-Plan.md](management-plans/Cost-Management-Plan.md) — **approved** |
| Performance baseline (likely) | **€58,710** EUR ex. VAT |
| CP labor + OV | **€50,610** + **€8,100** (**CAT-LAB-OV**) |
| CP cost range | **~€28.5k – ~€66.2k** (WD low/high) |
| Contingency (**CAT-CONT**) | **€18k – €28k** envelope — not baselined until **SCH-RSV-*** draw |
| Categories authority | [Cost-Categories-and-Estimating-Basis.md](management-plans/cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md) |
| Milestone staging | MS-07 **€58,710** (CP **€50,610** + OV **€8,100**) |
| Subsidiary plan approval | 2026-11-10 — policy `1c0b25f8-af6e-4573-a101-9f5568f28792` |
| Gate record | [approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json](gates/approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json) |
| CAT-TOOL (subscriptions) | **€71/mo** (Cursor €16, Gemini Antigravity €25, Claude Code €20, GitHub Basic €10); **~€256** Phase-1 |
| Authorization model | Funding via this PMP + approved subsidiary plans — **Q-CST-001…003 closed** |

### 3.5 Quality (8.1 — draft roll-up 2026-11-10)

| Field | Value |
|---|---|
| Subsidiary plan | [Quality-Management-Plan.md](management-plans/Quality-Management-Plan.md) — **approved (2026-11-10)** |
| Acceptance matrix | [Scope-Validate-Scope.md](management-plans/scope-baseline/foundation/Scope-Validate-Scope.md) |
| Active gates | **QG-02…04** at execution; **QG-01** **passed (2026-11-10)** |
| Agentic policy | [Agentic-Parallel-Execution-Policy.md](Agentic-Parallel-Execution-Policy.md) |

### 3.6 Communications (10.1)

| Field | Value |
|---|---|
| Subsidiary plan | [Communications-Management-Plan.md](management-plans/Communications-Management-Plan.md) — **approved (2026-11-10)** |
| Orientation artifact | [Project-Status-Register.md](../registers/Project-Status-Register.md) |
| Story queue | [Implementation-Story-Queue.md](../registers/Implementation-Story-Queue.md) |

### 3.7 Risk (11.1)

| Field | Value |
|---|---|
| Subsidiary plan | [Risk-Management-Plan.md](management-plans/Risk-Management-Plan.md) — **approved (2026-11-10)** |
| Register count | **11** Phase-1 risks |
| Reserve authority | PM + sponsor on **SCH-RSV-*** trigger |

### 3.8 Procurement (12.1)

| Field | Value |
|---|---|
| Subsidiary plan | [Procurement-Management-Plan.md](management-plans/Procurement-Management-Plan.md) — **approved (2026-11-10)** |
| Open constraint | **Q-RES-003** SOW / contractor mix |
| Subscription control | **€71/mo** plan — see cost pack **Q-CST-002** |

### 3.9 Stakeholder (13.2)

| Field | Value |
|---|---|
| Subsidiary plan | [Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md) — **approved (2026-11-10)** |
| Register | [Stakeholder-Register.md](Stakeholder-Register.md) |
| Sponsor gate acceptor | **SH-01** (human acceptance on subsidiary + PMP gates) |

## 4. Feedback Loop from Adaptation
When an **Adaptation Plan** (Stage 17) is approved, this PMP and its subsidiary plans are updated with tailored operational changes evaluated through the Governance Change Impact Matrix, which in turn trigger refined ADRs, BRDs, FDDs, and Stories for the next cycle. Prior baselines are archived to `management-plans/history/{baseline_id}/`.

## 5. Governance Authorization

**Status:** **Approved (2026-11-10)** — integrated PMP **`PMP-BL-v1.0.0`** locked under `approve-pmp` (policy `46c60639-c24f-4045-8ace-a3dbe2142e61`, human acceptance). Gate: [gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json](gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json). PMP SHA-256 at approval: `ef84ce08e60d5c47f1b13f99475c1a9f2171525bd7bcff83f0d1d4bce06ecf1a`.

This integrated PMP was formally evaluated and approved via `approve-pmp` (`FULL` Bayesian authority, `requires_human_approval: true`) before technical specifications (ADR, BRD, FDD, Stories) are finalized. All downstream technical requirements must record `pmp_baseline: 'PMP-BL-v1.0.0'` (Invariant 6). Prior baselines remain recoverable from history archives (Invariant 7).
