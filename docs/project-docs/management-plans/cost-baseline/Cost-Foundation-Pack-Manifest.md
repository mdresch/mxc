---
artifact_id: cost-foundation-pack-manifest
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.1.0"
owner_role: Project Manager
pack_status: approved
approval_status: approved
rollup_completed: "2026-11-10"
pack_approved: "2026-11-10"
pack_approval_gate: "../../gates/approve-subsidiary-plan-cost-7d7-pack-manifest-2026-11-10.adjudication.json"
depends_on:
  - scope-management
  - schedule-management
  - resource-management
---

# Cost Foundation Pack — Manifest (PMP-BL-v1.0.0)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d7-pack-manifest-2026-11-10.adjudication.json](../../gates/approve-subsidiary-plan-cost-7d7-pack-manifest-2026-11-10.adjudication.json).

Project: **mxc**. Authoritative roll-up of the **Cost** foundation pack (Stage **7.D**). **7.D-7** subsidiary approval formalizes the cost baseline pack; it does not authorize invoices, SOWs, or execution (Stage 8).

**Parent plan:** [Cost Management Plan](../Cost-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Roll-up summary (7.D-6)

**Completed:** 2026-11-10 — six foundation artifacts cross-linked to **approved scope/schedule**, **resource ROM**, and milestone staging. Fingerprints below are **SHA-256 after approval**.

| Roll-up element | Value |
|---|---|
| Scope / schedule prerequisite | Scope **v1.2.0** and schedule **v1.1.0** packs **approved** 2026-11-10 |
| Resource prerequisite | [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) **approved** 2026-11-10 — contractor market ROM |
| Costed WBS | **1.1.1–1.6.4** (17 packages) + governance overlay |
| Performance baseline (likely, ex. VAT) | **€58,710** (**CAT-LAB** **€50,610** + **CAT-LAB-OV** **€8,100**) |
| Subscriptions (**CAT-TOOL**) | **€71/mo** — Cursor **€16**, Gemini Antigravity **€25**, Claude Code **€20**, GitHub Basic **€10**; **~€256** Phase-1 |
| Contingency envelope | **€18k – €28k** (**CAT-CONT** ↔ **SCH-RSV-001…004** + **SCH-RSV-MGT**) |
| Cost baseline ID | `COST-BL-v1.0.0` under **`PMP-BL-v1.0.0`** |
| Manifest version | **1.1.0** |
| Subsidiary approval | **7.D-7** — `approve-subsidiary-plan` **Approved (2026-11-10)** |

## Cost baseline snapshot

- **Currency:** EUR **ex. VAT**; price date **2026-11-10**
- **Labor valuation:** Contractor market rates; **payroll N/A**
- **Staging:** MS-01…MS-07 cumulative labor per [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md)
- **Control:** Variance protocol tied to Story-Execution-Register hours

## Stage 7.D process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.D-0 | Approved Scope/Schedule + resource pack | Dependency references | **complete (2026-11-10)** |
| 7.D-0P | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.md) | Outcomes and cost drivers traced | **approved (2026-11-10)** |
| 7.D-1 | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.md) | Categories, units, estimating rules | **approved (2026-11-10)** |
| 7.D-2 | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.md) | WBS bottom-up + reserves in EUR | **approved (2026-11-10)** |
| 7.D-3 | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md) | Milestone staged baseline | **approved (2026-11-10)** |
| 7.D-4 | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.md) | Variance measures and change control | **approved (2026-11-10)** |
| 7.D-5 | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.md) | PMBOK 8 Finance outcomes reviewed | **approved (2026-11-10)** |
| 7.D-6 | Pack roll-up | This manifest | **complete (2026-11-10)** |
| 7.D-7 | Cost plan approval | `approve-subsidiary-plan` | **approved (2026-11-10)** |

## Upstream inputs

| Source | Status | Rolled into artifact(s) |
|---|---|---|
| [Scope-Foundation-Pack-Manifest.md](../scope-baseline/Scope-Foundation-Pack-Manifest.md) | Approved 2026-11-10 | WBS trace |
| [Schedule-Foundation-Pack-Manifest.md](../schedule-baseline/Schedule-Foundation-Pack-Manifest.md) | Approved 2026-11-10 | WD ranges, reserves |
| [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) | Approved 2026-11-10 | Rates, ROM |
| [Schedule-Reserve-Register.md](../schedule-baseline/foundation/Schedule-Reserve-Register.md) | Approved | CAT-CONT |

## Artifact registry

| Artifact | Substage | Version | Approval status | SHA-256 after approval (2026-11-10) |
|---|---|---|---|---|
| Cost-Pillar-Overview-and-Trace.md | 7.D-0P | 1.0.0 | approved (2026-11-10) | `92a0784d2cc23378d66748b37bcfbb994d365e5ffcad6b48cf00a7ed9d37a569` |
| Cost-Categories-and-Estimating-Basis.md | 7.D-1 | 1.0.0 | approved (2026-11-10) | `dc044c537ed26f137f3be21495edb4e522a0ecd2dafb2e4003a3e3f6a59129ee` |
| Cost-Estimates-by-Category.md | 7.D-2 | 1.0.0 | approved (2026-11-10) | `7bc521100b1ed959b24965078a2ee01f97e51994414d9ba10003183d9f6fb670` |
| Cost-Staged-Budget-and-Baseline.md | 7.D-3 | 1.0.0 | approved (2026-11-10) | `f4a451ffbcd48fe30016d58c3dfd5a7c6d98e6f1a86dca2514b3ee5e228943f8` |
| Cost-Variance-and-Control-Protocol.md | 7.D-4 | 1.0.0 | approved (2026-11-10) | `78a918f8c28b5aea02259d704f3827b5e3de058aa9c9db7869be1a588f7cd5c0` |
| Cost-Domain-Checklist.md | 7.D-5 | 1.0.0 | approved (2026-11-10) | `e7fab8b14dedb2706bb4d141352f7b922f9ad903457864c87b561216456845d2` |

**Reviewer / approval date:** **2026-11-10** — cost foundation pack approved; registry shows **SHA-256 after approval**.

## Consolidated open questions

| ID | Question | Owner | Status |
|---|---|---|---|
| Q-CST-001 | Sponsor / PM labor | Sponsor | **closed** — **€2,280** in **CAT-LAB-OV** (imputed; hours unlogged) |
| Q-CST-002 | CAT-TOOL **€71/mo** | Sponsor | **closed (2026-11-10)** — full SKU list in estimates § Q-CST-002 |
| Q-CST-003 | Funding | Sponsor | **closed** — `approve-subsidiary-plan` + `approve-pmp` |

**Cost pack open questions:** **none** — all **Q-CST-*** answered **2026-11-10**.

## Roll-up and approval rules

1. Draft and review each artifact against approved scope WBS, schedule WD, and resource rates.
2. Mark **approved** only after human review; recalculate SHA-256 **after approval**.
3. **7.D-6:** All required artifacts present and cross-referenced — **roll-up complete (2026-11-10)**.
4. **7.D-7:** **Complete (2026-11-10)** — rolled into [Cost-Management-Plan.md](../Cost-Management-Plan.md).
5. **PMP roll-up:** **Complete (2026-11-10)** — manifest link, **€58,710** performance snapshot, in [Project-Management-Plan.md](../../Project-Management-Plan.md) §3.4; **`approve-pmp`** lock **2026-11-10**.
6. Resource pack **7.C-8** may proceed in parallel; cost **7.D-7** does not require resource subsidiary approval but requires resource **draft** evidence.
