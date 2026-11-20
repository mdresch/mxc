---
artifact_id: cost-foundation-pack-manifest
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-pmp
version: "1.0.0"
owner_role: Project Manager
depends_on:
  - scope-management
  - schedule-management
  - resource-management
  - procurement-management
pack_status: pending
---

# Cost Foundation Pack — Manifest (PMP-BL-v1.0.0)

Project: **MXC**. Cost planning is gated by approved Scope and Schedule baselines and the Resource/Procurement evidence required by the Project Charter.

## Stage 6.D process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 6.D-0 | Approved Scope/Schedule and required Resource/Procurement outputs | Dependency and source references | pending |
| 6.D-0P | [Cost-Pillar-Overview-and-Trace.md](foundation/Cost-Pillar-Overview-and-Trace.md) | Outcomes and cost drivers traced | pending |
| 6.D-1 | [Cost-Categories-and-Estimating-Basis.md](foundation/Cost-Categories-and-Estimating-Basis.md) | Categories, units, estimating rules | pending |
| 6.D-2 | [Cost-Estimates-by-Category.md](foundation/Cost-Estimates-by-Category.md) | Evidence-based estimates and uncertainty | pending |
| 6.D-3 | [Cost-Staged-Budget-and-Baseline.md](foundation/Cost-Staged-Budget-and-Baseline.md) | Authorized budget and reserves | pending |
| 6.D-4 | [Cost-Variance-and-Control-Protocol.md](foundation/Cost-Variance-and-Control-Protocol.md) | Variance measures and change control | pending |
| 6.D-5 | [Cost-Domain-Checklist.md](foundation/Cost-Domain-Checklist.md) | PMBOK 8 Finance outcomes reviewed | pending |
| 6.D-6 | Pack roll-up | Artifacts reviewed; registry complete | pending |
| 6.D-7 | Cost plan approval | Human approval under configured plan gate | pending |

## Artifact registry

| Artifact | Substage | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|
| Cost-Pillar-Overview-and-Trace.md | 6.D-0P | pending | TBD | TBD |
| Cost-Categories-and-Estimating-Basis.md | 6.D-1 | pending | TBD | TBD |
| Cost-Estimates-by-Category.md | 6.D-2 | pending | TBD | TBD |
| Cost-Staged-Budget-and-Baseline.md | 6.D-3 | pending | TBD | TBD |
| Cost-Variance-and-Control-Protocol.md | 6.D-4 | pending | TBD | TBD |
| Cost-Domain-Checklist.md | 6.D-5 | pending | TBD | TBD |

## Roll-up and approval rules

Do not begin cost estimation until 6.D-0 prerequisites are evidenced. Each artifact remains pending until human review; complete 6.D-6 only when the registry and hashes are verified, then submit the Cost Management Plan at 6.D-7.
