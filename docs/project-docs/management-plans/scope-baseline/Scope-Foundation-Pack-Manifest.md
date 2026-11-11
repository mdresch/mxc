---
artifact_id: scope-foundation-pack-manifest
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.2.0"
owner_role: Project Manager
pack_status: approved
approval_status: approved
rollup_completed: "2026-11-10"
pack_approved: "2026-11-10"
pack_approval_gate: "../../gates/approve-subsidiary-plan-scope-7a7-pack-manifest-2026-11-10.adjudication.json"
depends_on: []
---

# Scope Foundation Pack — Manifest (PMP-BL-v1.0.0)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a7-pack-manifest-2026-11-10.adjudication.json](../../gates/approve-subsidiary-plan-scope-7a7-pack-manifest-2026-11-10.adjudication.json).

Project: **mxc**. This manifest is the **authoritative roll-up** of the Scope foundation pack (Stage **7.A**). **7.A-7** subsidiary approval formalizes the scope baseline pack; it does not authorize product execution.

**Parent plan:** [Scope Management Plan](../Scope-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Roll-up summary (7.A-6)

**Completed:** 2026-11-10 — all six foundation artifacts are drafted, cross-linked, registered, and **approved** under `approve-subsidiary-plan`. Registry fingerprints below are **SHA-256 after approval**.

| Roll-up element | Value |
|---|---|
| Product scope root | WBS **1.0** — MXC JIT Hyper-V sandbox |
| Pillar packages | WBS **1.1–1.6** ↔ ADR/BRD/FDD/epic **001–006** (Approved / Accepted 2026-10-30) |
| User-story packages | **17** work packages **1.N.S** (see WBS dictionary story index) |
| Controlling documents | Scope statement, monitor/control, validate scope, domain checklist |
| Manifest version | **1.2.0** |
| Subsidiary approval | **7.A-7** — `approve-subsidiary-plan` **Approved (2026-11-10)** |

**7.A-0 initiating inputs:** **partial** — business case approved; charter, benefits, and stakeholder register not fully gated (recorded honestly in upstream table).

## Scope baseline snapshot

- **In scope (product):** Six topic pillars TP-01–TP-06 per [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.md).
- **Out of scope:** Shared-kernel containers, always-on default, dev tools on prod image, currency ROI, unnamed MFA, unapproved hypotheses as proof.
- **Validation posture:** Specification validated by governance gates on ADR/BRD/FDD/epics; implementation validation deferred to `implement-story` per [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.md).
- **Change control:** Per [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.md) — `approve-*` + paired classify/escalate for material drift.
- **Domain readiness:** [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.md) — 6 pass, 2 gap (charter/benefits; execution policies idle).

## Artifact dependency chain

```text
7.A-0P  Pillar overview & trace
   ↓
7.A-1   Project scope statement
   ↓
7.A-2   WBS dictionary (17 story IDs)
   ↓
7.A-3   Monitor & control scope ──┐
7.A-4   Validate scope           ├── 7.A-5  Domain checklist
   ↓                              │
7.A-6   This manifest roll-up ←──┘
   ↓
7.A-7   approve-subsidiary-plan → Scope Management Plan → PMP
```

## Stage 7.A process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.A-0 | Charter and approved initiating inputs | Source links and approval references | **partial** |
| 7.A-0P | [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.md) | TP-01–TP-06 traced to ADR/epic | **approved (2026-11-10)** |
| 7.A-1 | [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.md) | Boundaries, exclusions, WBS 1.x | **approved (2026-11-10)** |
| 7.A-2 | [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.md) | **17** story WBS rows + index | **approved (2026-11-10)** |
| 7.A-3 | [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.md) | Change and variance paths | **approved (2026-11-10)** |
| 7.A-4 | [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.md) | Per-story validation matrix | **approved (2026-11-10)** |
| 7.A-5 | [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.md) | PMBOK 8 scope domain | **approved (2026-11-10)** |
| 7.A-6 | Pack roll-up | Registry complete; hashes recorded | **complete** |
| 7.A-7 | Scope plan approval | `approve-subsidiary-plan` | **approved (2026-11-10)** |

## Upstream inputs

| Source | Status | Rolled into artifact(s) |
|---|---|---|
| [Spark-Capture.md](../../Spark-Capture.md) | Captured | 7.A-1 purpose; 7.A-0P |
| [Business-Case.md](../../Business-Case.md) | Approved 2026-10-29 | 7.A-0P; exclusions |
| [Benefits-Statement.md](../../Benefits-Statement.md) | Draft | 7.A-0 gaps; checklist gap |
| [Stakeholder-Register.md](../../Stakeholder-Register.md) | Draft | 7.A-0; checklist gap |
| [Project-Charter.md](../../Project-Charter.md) | Not gate-complete | 7.A-1 constraints |
| [ADR-001 … ADR-006](../../../../07-architecture/) | Accepted 2026-10-30 | All foundation artifacts |
| [BRD-001 … BRD-006](../../Business-Requirements/) | Approved 2026-10-30 | WBS 1.1–1.6 |
| [FDD-001 … FDD-006](../../Functional-Design/) | Approved 2026-10-30 | Validate scope |
| [epic-001 … epic-006](../../../user-stories/) | Approved 2026-10-30 | WBS **1.N.S**; story `WBS ID` lines |
| [Project-Details-Not-In-ADR.md](../../Project-Details-Not-In-ADR.md) | Draft | Exclusions; open Q table |

## WBS roll-up (authorized product scope)

| WBS | Epic | Stories (Story ID → WBS) |
|---|---|---|
| 1.1 | 001 | 1.1→1.1.1, 1.2→1.1.2 |
| 1.2 | 002 | 2.1→1.2.1, 2.2→1.2.2, 2.3→1.2.3 |
| 1.3 | 003 | 3.1→1.3.1, 3.2→1.3.2 |
| 1.4 | 004 | 4.1→1.4.1, 4.2→1.4.2, 4.3→1.4.3 |
| 1.5 | 005 | 5.1→1.5.1, 5.2→1.5.2, 5.3→1.5.3 |
| 1.6 | 006 | 6.1→1.6.1 … 6.4→1.6.4 |

Authoritative detail: [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.md) v1.1.0.

## Artifact registry

| Artifact | Substage | Version | Approval status | SHA-256 after approval (2026-11-10) |
|---|---|---|---|---|
| Scope-Pillar-Overview-and-Trace.md | 7.A-0P | 1.0.0 | approved | `a1d8e2bf058556335344277eab7c24205e8c76ef4d0ff7b7c25cae20ed14360c` |
| Scope-Project-Scope-Statement.md | 7.A-1 | 1.0.0 | approved | `f83f8edcd728c07d8c488e849eb7d9b47ddf0a510a300ab3ec8489cb55ec8f42` |
| Scope-WBS-Dictionary.md | 7.A-2 | 1.1.0 | approved | `fcb7f9f40e11f6226a24348b9b8573caef61546e106e19afecefc061226b6f5f` |
| Scope-Monitor-Control-Scope.md | 7.A-3 | 1.0.0 | approved | `8229b0735ee042a06868d1bacdd8e93c30dcd93906ab3625b7375c5baf321ef1` |
| Scope-Validate-Scope.md | 7.A-4 | 1.1.0 | approved | `062043ee7eb6dbf7ef335e1e549f7ee405028c6f527730b14d8082aa8437e2c9` |
| Scope-Domain-Checklist.md | 7.A-5 | 1.0.0 | approved | `c4381f5e9649de708678ee3496f232ae3f61d501d2e75fe236240e94e02a4b75` |

**Reviewer / approval date:** **2026-11-10** — scope foundation pack and [Scope Management Plan](../Scope-Management-Plan.md) approved under `approve-subsidiary-plan` (eight gate records in `docs/project-docs/gates/`).

## Consolidated open questions (from pack)

| ID | Source | Question | Owner | Status |
|---|---|---|---|---|
| Q-SCOPE-001 | Scope statement | Charter/benefits gate before subsidiary approval | Menno Drescher | open |
| Q-SCOPE-002 | Pillar trace / PD-not-in-ADR | `BEN-08` / production VHDX catalog | Release | open |
| Q-SCOPE-003 | Manifest | Run `approve-subsidiary-plan` | PM | **closed (2026-11-10)** |
| Q-SCOPE-004 | Domain checklist | Execution-stage policies idle | Governance | open |
| WBS-001 | WBS dictionary | Governance WBS 2.x vs schedule/cost split | PM | open |

## Roll-up and approval rules

1. Draft and review each artifact against its cited inputs and record unresolved questions.
2. Change an artifact to **approved** only after designated human review; recalculate SHA-256 **after approval**.
3. **7.A-6 (this document):** All required artifacts are present, versioned, cross-referenced, and fingerprinted — **roll-up complete**.
4. **7.A-7:** **Complete (2026-11-10)** — scope boundary, manifest (**v1.2.0**), registry, and approval references rolled into [Scope-Management-Plan.md](../Scope-Management-Plan.md).
5. **PMP roll-up:** **Complete (2026-11-10)** — §3.1 in [Project-Management-Plan.md](../../Project-Management-Plan.md); integrated **`approve-pmp`** lock **2026-11-10**.
6. Schedule, cost, and resource foundation packs may proceed; scope pack **7.A-7** is **approved**.
