---
artifact_id: pmp-approval-package-manifest
parent_plan_id: project-management-plan
baseline_id: "PMP-BL-v1.0.0"
route: approval_package
governance_policy: approve-pmp
version: "1.0.0"
pack_status: approved
pmp_baseline: "PMP-BL-v1.0.0"
prepared: "2026-11-10"
depends_on:
  - scope-baseline approved
  - schedule-baseline approved
  - resource-baseline approved
  - cost-baseline approved
  - operational-subsidiary-plans approved
  - approve-pmp 2026-11-10
---

# PMP Approval Package — Manifest (`PMP-BL-v1.0.0`)

**Purpose:** Sponsor checklist and inventory for integrated **`approve-pmp`** on [Project-Management-Plan.md](../Project-Management-Plan.md). This manifest is **not** the PMP itself; it bundles what the gate must verify.

**Agent:** `mxc-governance` | **Policy:** `approve-pmp` (`46c60639-c24f-4045-8ace-a3dbe2142e61`)

## 1. Integrated document

| Item | Path | Status |
|---|---|---|
| Integrated PMP | [Project-Management-Plan.md](../Project-Management-Plan.md) | Roll-up complete **2026-11-10** |
| Baseline ID | `PMP-BL-v1.0.0` | Declared in PMP frontmatter |
| Cost baseline ID | `COST-BL-v1.0.0` | Nested in PMP §3.4 |

## 2. Foundation packs (subsidiary `approve-subsidiary-plan` — approved)

| PMBOK focus | Plan | Manifest | Gate (management plan) |
|---|---|---|---|
| Scope 5.x | [Scope-Management-Plan.md](Scope-Management-Plan.md) | [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) **v1.2.0** | [approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-scope-scope-management-plan-2026-11-10.adjudication.json) |
| Schedule 6.x | [Schedule-Management-Plan.md](Schedule-Management-Plan.md) | [Schedule-Foundation-Pack-Manifest.md](schedule-baseline/Schedule-Foundation-Pack-Manifest.md) **v1.1.0** | [approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-schedule-schedule-management-plan-2026-11-10.adjudication.json) |
| Resource 9.x | [Resource-Management-Plan.md](Resource-Management-Plan.md) | [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0** | [approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-resource-resource-management-plan-2026-11-10.adjudication.json) |
| Cost 7.x | [Cost-Management-Plan.md](Cost-Management-Plan.md) | [Cost-Foundation-Pack-Manifest.md](cost-baseline/Cost-Foundation-Pack-Manifest.md) **v1.1.0** | [approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json](../gates/approve-subsidiary-plan-cost-cost-management-plan-2026-11-10.adjudication.json) |

## 3. Operational subsidiary plans (PMP roll-up — draft complete)

| PMBOK | Plan | PMP roll-up |
|---|---|---|
| Quality 8.1 | [Quality-Management-Plan.md](Quality-Management-Plan.md) | §2.8.1, §3.5 |
| Communications 10.1 | [Communications-Management-Plan.md](Communications-Management-Plan.md) | §2.10.1, §3.6 |
| Risk 11.1 | [Risk-Management-Plan.md](Risk-Management-Plan.md) | §2.11.1, §3.7 |
| Procurement 12.1 | [Procurement-Management-Plan.md](Procurement-Management-Plan.md) | §2.12.1, §3.8 |
| Stakeholder 13.2 | [Stakeholder-Engagement-Plan.md](Stakeholder-Engagement-Plan.md) | §2.13.2, §3.9 |

## 4. Planning snapshot (locked at approval)

| Element | Value |
|---|---|
| Product WBS in baseline | **1.1.1–1.6.4** (17 packages) |
| CP duration (likely) | **~78 WD** human effort |
| Performance cost (likely) | **€58,710** ex. VAT |
| Subscriptions | **€71/mo** (**CAT-TOOL**) |
| Contingency envelope | **€18k – €28k** (**CAT-CONT**) |
| Agentic effort | **Actuals only** — not in schedule/cost baseline |

## 5. Gate evaluation criteria (`approve-pmp`)

| Criterion | Evidence (mxc) | Honest notes |
|---|---|---|
| **subsidiary_plan_completeness** | Nine subsidiary plans + PMP §2–§3 | Foundation **7.A–7.D** + operational five **approved** at PMP gate **2026-11-10** |
| **baseline_coherence** | Scope WBS ↔ schedule WD ↔ cost ROM ↔ resource rates | Open constraints documented — not hidden |
| **adaptation_responsiveness** | PMP §4 feedback loop; [Adaptation-Plan.md](../Adaptation-Plan.md) shell | Stage 17 template — adaptation triggers defined, not yet exercised |
| **governance_traceability** | [Project-Charter.md](../Project-Charter.md), [Business-Case.md](../Business-Case.md), BRD/epic chain | **Charter `approve-charter` not fully gated** — recorded as accepted planning risk |

## 6. Documented open constraints (accepted at approval)

| ID | Topic | Disposition |
|---|---|---|
| Q-SCOPE-002 / charter | Charter not fully gated | Accepted; refresh at `approve-charter` |
| Q-SCH-001…003 | Schedule honesty items | In schedule domain checklist |
| Q-RES-003 / Q-RES-004 | SOW mix; observability | Procurement + story 1.6.1 |
| WBS-001 | Governance 2.x split | Scope manifest |
| RSK-11 | PMP lock | **closed (2026-11-10)** |
| **QG-01** | Planning quality gate | **closed (2026-11-10)** |

## 7. What approval does / does not do

| **`approve-pmp` YES** | **`approve-pmp` NO** |
|---|---|
| Locks **`PMP-BL-v1.0.0`** as integrated planning baseline (Invariant 6) | Does **not** issue **Stage 8** execution authorization |
| Completes **QG-01** (planning baseline gate) | Does **not** authorize contractor POs without **Q-RES-003** SOW |
| Records sponsor human acceptance on gate JSON | Does **not** remove need for per-story `implement-story` |
| Enables formal Stage 8 **readiness** path | Does **not** supersede approved ADR/BRD/FDD/epics (already gated) |

## 8. Sponsor attestation (human)

| Field | Value |
|---|---|
| Action requested | **`approve_pmp`** under policy `46c60639-c24f-4045-8ace-a3dbe2142e61` |
| Reviewed package | This manifest + [Project-Management-Plan.md](../Project-Management-Plan.md) |
| Gate record (post-adjudication) | `docs/project-docs/gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json` |

**Approved:** **2026-11-10** — gate [approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json](../gates/approve-pmp-pmp-bl-v1-0-0-2026-11-10.adjudication.json). PMP SHA-256 at lock: `ef84ce08e60d5c47f1b13f99475c1a9f2171525bd7bcff83f0d1d4bce06ecf1a` (full file, post-adjudication).
