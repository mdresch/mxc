---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "12.1 Plan Procurement Management"
lifecycle_stage: "Stage 10 (Planning)"
governance_policy: approve-pmp
pmp_baseline: "PMP-BL-v1.0.0"
inputs:
  - "Project-Charter.md"
  - "resource-baseline/Resource-Foundation-Pack-Manifest.md"
  - "cost-baseline/Cost-Foundation-Pack-Manifest.md"
process: "Plan and formalize Procurement Management Plan"
outputs:
  - "Procurement-Management-Plan.md"
---

# Procurement Management Plan — mxc

> **PMBOK 8 Process:** `12.1 Plan Procurement Management` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 10`  
> **Sources:** Approved resource and cost baselines (**2026-11-10**)

## 1. Purpose & scope

Defines **make-or-buy**, **contractor engagement**, and **subscription procurement** rules for Phase-1 **mxc** under **`PMP-BL-v1.0.0`**. ROM labor assumes **contractor market rates** (payroll **N/A**); actual buy decisions require this plan plus **Q-RES-003** SOW when external spend occurs.

## 2. Make-or-buy summary (Phase 1)

| Category | Decision | Rationale | Funding |
|---|---|---|---|
| Core product engineering | **Make** (sponsor-led + agents) | IP retention; sandbox discipline | **CAT-LAB** contractor ROM / sponsor time |
| Security specialist surge | **Buy option** | SecOps depth on 1.5.x | SOW when engaged (**Q-RES-003**) |
| QA / contract review overlay | **Buy option** | **€4,320** ROM in **CAT-LAB-OV** | Procured QA if used |
| Architecture spikes | **Buy option** | **€1,500** ROM in **CAT-LAB-OV** | Fractional contractor |
| IDE / agent subscriptions | **Buy** (sponsor) | Fixed **€71/mo** | **CAT-TOOL** — sponsor direct pay |
| Hyper-V host / storage tier | **Make** (existing host) | CAT-INFRA placeholder €0–€2k | Sponsor infra budget |
| Cloud SaaS beyond table | **Defer** | Not in Phase-1 baseline | Requires cost rebaseline |

## 3. Contractor engagement process

| Step | Action | Evidence |
|---|---|---|
| 1 | Identify role need from [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md) | WBS assignment row |
| 2 | Confirm within **CAT-LAB** ROM or reserve trigger | Cost estimates by WBS |
| 3 | Draft SOW (scope, rate, hours cap, acceptance) | **Q-RES-003** closure |
| 4 | Sponsor approval before work | Gate or email record → PM file note |
| 5 | Track hours in [Story-Execution-Register.md](../../registers/Story-Execution-Register.md) | Variance vs ROM |
| 6 | Invoice reconcile to contractor rate × h | [Cost-Variance-and-Control-Protocol.md](cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md) |

**No PO, no work** for external roles beyond sponsor-imputed PM/governance overlay already in baseline.

## 4. Subscription procurement (CAT-TOOL)

| SKU | Monthly (EUR) | Buyer | Control |
|---|---|---|---|
| Cursor | 16 | Sponsor | Seat assigned in tooling register |
| Gemini Antigravity | 25 | Sponsor | Agent lane |
| Claude Code | 20 | Sponsor | Agentic coding |
| GitHub Basic | 10 | Sponsor | PR workflow |
| **Total** | **71** | Sponsor | Monthly variance ≠ €71 → PM updates estimates |

Subscriptions are **outside** **€58,710** labor performance baseline; sponsor pays vendor directly.

## 5. Contract types & terms (default)

| Type | Use |
|---|---|
| **Time & materials (capped)** | Short specialist bursts |
| **Fixed fee per story** | Optional when SOW ties to single WBS package |
| **Sponsor imputed labor** | PM overlay **€2,280** — no external PO |

All contracts **ex. VAT** unless invoice states otherwise; VAT handled per sponsor accounting.

## 6. PMP integration (2026-11-10)

| Element | Value |
|---|---|
| PMP register | **§2.12.1**, **§3.8** |
| Open constraint | **Q-RES-003** contractor mix / SOW template |
| Lock | **`approve-pmp`** **approved (2026-11-10)** |

## 7. Review & governance invariant

Procurement planning is verified under **`approve-pmp`**. Approved make/buy table does **not** issue purchase orders or authorize Stage 8 spend.

**Status:** **Approved (2026-11-10)** — rolled into PMP.
