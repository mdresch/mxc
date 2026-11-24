---
artifact_id: schedule-foundation-pack-manifest
parent_plan_id: schedule-management
baseline_id: "{{BASELINE_ID}}"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.0.0"
owner_role: Project Manager
depends_on:
  - scope-management
pack_status: pending
---

# Schedule Foundation Pack — Manifest ({{BASELINE_ID}})

Project: **{{PROJECT_NAME}}**. Stage 7.B foundation work is gated by the approved Scope baseline and evidence that activities and durations can be responsibly estimated.

**Parent plan:** [Schedule Management Plan](../Schedule-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Stage 7.B process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.B-0 | Approved Scope plan and WBS; duration evidence available | Dependency and evidence references | pending |
| 7.B-0P | [Schedule-Pillar-Overview-and-Trace.md](foundation/Schedule-Pillar-Overview-and-Trace.template.md) | Outcomes and milestones traced | pending |
| 7.B-1 | [Schedule-Basis-of-Estimates.md](foundation/Schedule-Basis-of-Estimates.template.md) | Data, method, and uncertainty disclosed | pending |
| 7.B-2 | [Schedule-Network-Phase1.md](foundation/Schedule-Network-Phase1.template.md) | Precedence and dependencies validated | pending |
| 7.B-2A | [Schedule-Activity-List-Phase1.md](foundation/Schedule-Activity-List-Phase1.template.md) | WBS-linked activities and owners | pending |
| 7.B-2B | [Schedule-Gantt-Phase1.md](foundation/Schedule-Gantt-Phase1.template.md) | Calendar model reconciles to network | pending |
| 7.B-3 | [Schedule-Reserve-Register.md](foundation/Schedule-Reserve-Register.template.md) | Reserve assumptions and triggers | pending |
| 7.B-4 | [Schedule-Baseline-WBS-Forecast.md](foundation/Schedule-Baseline-WBS-Forecast.template.md) | Forecast traces to WBS and estimates | pending |
| 7.B-5 | [Schedule-Domain-Checklist.md](foundation/Schedule-Domain-Checklist.template.md) | PMBOK 8 Schedule outcomes reviewed | pending |
| 7.B-6 | Pack roll-up | Artifacts reviewed; registry complete | pending |
| 7.B-7 | Schedule plan approval | Human approval under configured plan gate | pending |

## Prerequisites and evidence

Reference the approved Scope plan/WBS and real duration data. If evidence is insufficient, keep 7.B-0 blocked and do not manufacture estimates.

## Artifact registry

| Artifact | Substage | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|
| Schedule-Pillar-Overview-and-Trace.md | 7.B-0P | pending | TBD | TBD |
| Schedule-Basis-of-Estimates.md | 7.B-1 | pending | TBD | TBD |
| Schedule-Network-Phase1.md | 7.B-2 | pending | TBD | TBD |
| Schedule-Activity-List-Phase1.md | 7.B-2A | pending | TBD | TBD |
| Schedule-Gantt-Phase1.md | 7.B-2B | pending | TBD | TBD |
| Schedule-Reserve-Register.md | 7.B-3 | pending | TBD | TBD |
| Schedule-Baseline-WBS-Forecast.md | 7.B-4 | pending | TBD | TBD |
| Schedule-Domain-Checklist.md | 7.B-5 | pending | TBD | TBD |

## Roll-up and approval rules

Each artifact remains pending until human-reviewed. Complete 7.B-6 only when all required artifacts and hashes are verified. At 7.B-7, roll the approved schedule baseline, manifest version, artifact registry, hashes, open issues, and approval reference into the Schedule Management Plan for its separate human approval. After that plan is approved, roll its baseline identifier, approval reference, manifest link, and unresolved constraints into the PMP baseline register.
