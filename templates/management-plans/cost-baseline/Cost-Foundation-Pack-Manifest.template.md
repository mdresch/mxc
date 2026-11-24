---
artifact_id: cost-foundation-pack-manifest
parent_plan_id: cost-management
baseline_id: "{{BASELINE_ID}}"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.0.0"
owner_role: Project Manager
depends_on:
  - scope-management
  - schedule-management
  - resource-management
  - procurement-management
pack_status: pending
---

# Cost Foundation Pack — Manifest ({{BASELINE_ID}})

Project: **{{PROJECT_NAME}}**. Cost planning is gated by approved Scope and Schedule baselines and the Resource/Procurement evidence required by the Project Charter.

**Parent plan:** [Cost Management Plan](../Cost-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Stage 7.D process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.D-0 | Approved Scope/Schedule and required Resource/Procurement outputs | Dependency and source references | pending |
| 7.D-0P | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.template.md) | Outcomes and cost drivers traced | pending |
| 7.D-1 | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.template.md) | Categories, units, estimating rules | pending |
| 7.D-2 | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.template.md) | Evidence-based estimates and uncertainty | pending |
| 7.D-3 | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.template.md) | Authorized budget and reserves | pending |
| 7.D-4 | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.template.md) | Variance measures and change control | pending |
| 7.D-5 | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.template.md) | PMBOK 8 Finance outcomes reviewed | pending |
| 7.D-6 | Pack roll-up | Artifacts reviewed; registry complete | pending |
| 7.D-7 | Cost plan approval | Human approval under configured plan gate | pending |

## Artifact registry

| Artifact | Substage | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|
| Cost-Pillar-Overview-and-Trace.md | 7.D-0P | pending | TBD | TBD |
| Cost-Categories-and-Estimating-Basis.md | 7.D-1 | pending | TBD | TBD |
| Cost-Estimates-by-Category.md | 7.D-2 | pending | TBD | TBD |
| Cost-Staged-Budget-and-Baseline.md | 7.D-3 | pending | TBD | TBD |
| Cost-Variance-and-Control-Protocol.md | 7.D-4 | pending | TBD | TBD |
| Cost-Domain-Checklist.md | 7.D-5 | pending | TBD | TBD |

## Roll-up and approval rules

Do not begin cost estimation until 7.D-0 prerequisites are evidenced. Each artifact remains pending until human review; complete 7.D-6 only when the registry and hashes are verified. At 7.D-7, roll the approved cost baseline, manifest version, artifact registry, hashes, open issues, and approval reference into the Cost Management Plan for its separate human approval. After that plan is approved, roll its baseline identifier, approval reference, manifest link, and unresolved constraints into the PMP baseline register.
