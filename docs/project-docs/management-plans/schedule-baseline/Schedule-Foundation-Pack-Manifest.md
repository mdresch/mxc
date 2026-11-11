---
artifact_id: schedule-foundation-pack-manifest
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.1.0"
owner_role: Project Manager
pack_status: approved
approval_status: approved
rollup_completed: "2026-11-10"
pack_approved: "2026-11-10"
pack_approval_gate: "../../gates/approve-subsidiary-plan-schedule-7b7-pack-manifest-2026-11-10.adjudication.json"
depends_on:
  - scope-management
---

# Schedule Foundation Pack — Manifest (PMP-BL-v1.0.0)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b7-pack-manifest-2026-11-10.adjudication.json](../../gates/approve-subsidiary-plan-schedule-7b7-pack-manifest-2026-11-10.adjudication.json).

Project: **mxc**. Authoritative roll-up of the **Schedule** foundation pack (Stage **7.B**). **7.B-7** subsidiary approval formalizes the schedule baseline pack; it does not authorize product execution (Stage 8).

**Parent plan:** [Schedule Management Plan](../Schedule-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Roll-up summary (7.B-6)

**Completed:** 2026-11-10 — eight foundation artifacts drafted, cross-linked to the **approved scope baseline**, and registered below. Fingerprints below are **SHA-256 after approval**.

| Roll-up element | Value |
|---|---|
| Scope prerequisite | [Scope-Foundation-Pack-Manifest.md](../scope-baseline/Scope-Foundation-Pack-Manifest.md) **approved** 2026-11-10 |
| Scheduled WBS | **1.1.1–1.6.4** (17 story activities); governance **2.2** schedule pack out of band |
| Phase-1 milestones | **MS-01 … MS-07** |
| Critical path (likely) | **~78 WD** single FTE; **~15.6 relative weeks** in Gantt model |
| Reserves | **SCH-RSV-001 … 004** + 10% **SCH-RSV-MGT** |
| Manifest version | **1.1.0** |
| Subsidiary approval | **7.B-7** — `approve-subsidiary-plan` **Approved (2026-11-10)** |

## Schedule baseline snapshot

- **Sequencing:** TP-01 → TP-03 → TP-04 → TP-02 → TP-05 → TP-06 (FS chain per network).
- **Estimating:** Analogous + parametric; triangular WD ranges; no story-point history.
- **Calendar:** Relative week model from data date **T0 = 2026-11-10**; **no committed calendar finish**.
- **Control:** Reforecast on `implement-story` actuals; reserves consumed with evidence.

## Stage 7.B process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.B-0 | Approved scope + duration evidence | Scope pack; harness references | **complete** |
| 7.B-0P | [Schedule-Pillar-Overview-and-Trace.md](foundation/Schedule-Pillar-Overview-and-Trace.md) | MS-01…07 traced to WBS | **approved (2026-11-10)** |
| 7.B-1 | [Schedule-Basis-of-Estimates.md](foundation/Schedule-Basis-of-Estimates.md) | Methods and limits | **approved (2026-11-10)** |
| 7.B-2 | [Schedule-Network-Phase1.md](foundation/Schedule-Network-Phase1.md) | 17-step FS network | **approved (2026-11-10)** |
| 7.B-2A | [Schedule-Activity-List-Phase1.md](foundation/Schedule-Activity-List-Phase1.md) | 17 activities | **approved (2026-11-10)** |
| 7.B-2B | [Schedule-Gantt-Phase1.md](foundation/Schedule-Gantt-Phase1.md) | Relative week CP | **approved (2026-11-10)** |
| 7.B-3 | [Schedule-Reserve-Register.md](foundation/Schedule-Reserve-Register.md) | Named RSV rows | **approved (2026-11-10)** |
| 7.B-4 | [Schedule-Baseline-WBS-Forecast.md](foundation/Schedule-Baseline-WBS-Forecast.md) | Per-story WD ranges | **approved (2026-11-10)** |
| 7.B-5 | [Schedule-Domain-Checklist.md](foundation/Schedule-Domain-Checklist.md) | PMBOK 8 schedule domain | **approved (2026-11-10)** |
| 7.B-6 | Pack roll-up | This manifest | **complete** |
| 7.B-7 | Schedule plan approval | `approve-subsidiary-plan` | **approved (2026-11-10)** |

## Upstream inputs

| Source | Status | Rolled into artifact(s) |
|---|---|---|
| [Scope-Management-Plan.md](../Scope-Management-Plan.md) | Approved 2026-11-10 | All 7.B artifacts |
| [Scope-WBS-Dictionary.md](../scope-baseline/foundation/Scope-WBS-Dictionary.md) | Approved | Activity list, forecast |
| ADR/BRD/FDD/epic **001–006** | Approved / Accepted | Network, reserves |
| [JIT-Scale-to-Zero-Lesson.md](../../JIT-Scale-to-Zero-Lesson.md) | Draft lesson | Basis (wake narrative) |

## Milestone roll-up

| Milestone | Approx. week (1 FTE) | WBS gate |
|---|---|---|
| MS-01 Gen2 ready | ~W1.4 | 1.1.2 |
| MS-02 Image baseline | ~W3.6 | 1.3.2 |
| MS-03 Paused proven | ~W6.4 | 1.4.3 |
| MS-04 Ingress live | ~W9.4 | 1.2.3 |
| MS-05 Sterile path | ~W12.4 | 1.5.3 |
| MS-06 Pool ops | ~W15.4 | 1.6.4 |
| MS-07 Phase-1 baseline | ~W15.6 | 1.0 roll-up |

## Artifact registry

| Artifact | Substage | Version | Approval status | SHA-256 after approval (2026-11-10) |
|---|---|---|---|---|
| Schedule-Pillar-Overview-and-Trace.md | 7.B-0P | 1.0.0 | approved (2026-11-10) | `9690fff623b7ab41e9837a2b757e56ac78eec2e1912e8f77788d40fb12347f90` |
| Schedule-Basis-of-Estimates.md | 7.B-1 | 1.0.0 | approved (2026-11-10) | `df5cf5a243c64790413765b07ada37188d9bf3842754e55ab103ab4bc9511f04` |
| Schedule-Network-Phase1.md | 7.B-2 | 1.0.0 | approved (2026-11-10) | `6281e482a1abf70182398be59cbb64c9357567c3b4e6e51e60fc58b0eb55fadf` |
| Schedule-Activity-List-Phase1.md | 7.B-2A | 1.0.0 | approved (2026-11-10) | `5b83c8762730a0276ab91a65cd7db3fe9c20c813ef3046d605062d1a765ff9d1` |
| Schedule-Gantt-Phase1.md | 7.B-2B | 1.0.0 | approved (2026-11-10) | `264afa79a0383d40448ff52a24708b3d9583e559febad1fd3c2c90ed27ab3365` |
| Schedule-Reserve-Register.md | 7.B-3 | 1.0.0 | approved (2026-11-10) | `a2f3677447fcb66488c0a6cf71e0ed03838f82b6fd44f7159a458e96f6d4118f` |
| Schedule-Baseline-WBS-Forecast.md | 7.B-4 | 1.0.0 | approved (2026-11-10) | `aacaf449de566c03234703fc9a415f609a8d585b18d559dfae3ce718a82ca0c3` |
| Schedule-Domain-Checklist.md | 7.B-5 | 1.0.0 | approved (2026-11-10) | `5315b841fed1405a5bc4897b5d089d183e71902861265f06cf5c9cc13de0e1b0` |

**Reviewer / approval date:** **2026-11-10** — schedule foundation pack approved; registry shows **SHA-256 after approval**.

## Consolidated open questions

| ID | Source | Question | Owner | Status |
|---|---|---|---|---|
| Q-SCH-001 | Domain checklist | No velocity / story points | PM | open |
| Q-SCH-002 | Gantt | Calendar dates vs Stage 8 | Sponsor | open |
| Q-SCH-003 | Gantt | Multi-FTE parallel model | PM | open |
| Q-SCH-004 | Manifest | Run `approve-subsidiary-plan` | PM | **closed (2026-11-10)** |

## Roll-up and approval rules

1. Draft and review each artifact against approved scope WBS and cited duration evidence.
2. Mark **approved** only after human review; recalculate SHA-256 **after approval**.
3. **7.B-6:** All required artifacts present and cross-referenced — **roll-up complete**.
4. **7.B-7:** **Complete (2026-11-10)** — rolled into [Schedule-Management-Plan.md](../Schedule-Management-Plan.md).
5. **PMP roll-up:** **Complete (2026-11-10)** — manifest link, constraints, and §3.2 register in [Project-Management-Plan.md](../../Project-Management-Plan.md); integrated **`approve-pmp`** lock **2026-11-10**.
6. Cost and resource foundation packs (7.D / 7.C) may use this forecast; schedule **7.B-7** **approved**.
