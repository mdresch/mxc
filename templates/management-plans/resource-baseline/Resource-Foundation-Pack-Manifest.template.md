---
artifact_id: resource-foundation-pack-manifest
parent_plan_id: resource-management
baseline_id: "{{BASELINE_ID}}"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.0.0"
owner_role: Project Manager
depends_on:
  - scope-management
  - schedule-management
pack_status: pending
---

# Resource Foundation Pack — Manifest ({{BASELINE_ID}})

Project: **{{PROJECT_NAME}}**. Stage 7.C is gated by approved Scope and Schedule baselines; resource estimates must disclose the evidence and assumptions used.

**Parent plan:** [Resource Management Plan](../Resource-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Stage 7.C process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.C-0 | Approved Scope and Schedule baselines | Dependency references | pending |
| 7.C-0P | [Resource-Pillar-Overview-and-Trace.md](foundation/Resource-Pillar-Overview-and-Trace.template.md) | Outcomes and capacity priorities traced | pending |
| 7.C-1 | [Resource-Role-Catalogue.md](foundation/Resource-Role-Catalogue.template.md) | Roles, accountability, and authority | pending |
| 7.C-2 | [Resource-Capacity-Estimates.md](foundation/Resource-Capacity-Estimates.template.md) | Capacity and estimate basis | pending |
| 7.C-3 | [Resource-Tooling-and-Assignment-Register.md](foundation/Resource-Tooling-and-Assignment-Register.template.md) | Tools, environments, and assignments | pending |
| 7.C-4 | [Resource-Team-Operating-Charter.md](foundation/Resource-Team-Operating-Charter.template.md) | Team norms and escalation | pending |
| 7.C-5 | [Resource-Utilization-and-Control-Protocol.md](foundation/Resource-Utilization-and-Control-Protocol.template.md) | Planned/actual use and controls | pending |
| 7.C-6 | [Resource-Domain-Checklist.md](foundation/Resource-Domain-Checklist.template.md) | PMBOK 8 Resource outcomes reviewed | pending |
| 7.C-7 | Pack roll-up | Artifacts reviewed; registry complete | pending |
| 7.C-8 | Resource plan approval | Human approval under configured plan gate | pending |

## Artifact registry

| Artifact | Substage | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|
| Resource-Pillar-Overview-and-Trace.md | 7.C-0P | pending | TBD | TBD |
| Resource-Role-Catalogue.md | 7.C-1 | pending | TBD | TBD |
| Resource-Capacity-Estimates.md | 7.C-2 | pending | TBD | TBD |
| Resource-Tooling-and-Assignment-Register.md | 7.C-3 | pending | TBD | TBD |
| Resource-Team-Operating-Charter.md | 7.C-4 | pending | TBD | TBD |
| Resource-Utilization-and-Control-Protocol.md | 7.C-5 | pending | TBD | TBD |
| Resource-Domain-Checklist.md | 7.C-6 | pending | TBD | TBD |

## Roll-up and approval rules

Review each artifact against authorized inputs. Complete 7.C-7 only after all required artifacts are approved and hashes verified. At 7.C-8, roll the approved resource baseline, manifest version, artifact registry, hashes, open issues, and approval reference into the Resource Management Plan for its separate human approval. After that plan is approved, roll its baseline identifier, approval reference, manifest link, and unresolved constraints into the PMP baseline register.
