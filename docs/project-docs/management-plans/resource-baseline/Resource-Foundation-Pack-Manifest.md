---
artifact_id: resource-foundation-pack-manifest
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.0.0"
owner_role: Project Manager
rollup_completed: "2026-11-10"
depends_on:
  - scope-management
  - schedule-management
pack_status: approved
approval_status: approved
pack_approved: "2026-11-10"
pack_approval_gate: "../../gates/approve-subsidiary-plan-resource-7c8-pack-manifest-2026-11-10.adjudication.json"
---

# Resource Foundation Pack — Manifest (PMP-BL-v1.0.0)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c8-pack-manifest-2026-11-10.adjudication.json](../../gates/approve-subsidiary-plan-resource-7c8-pack-manifest-2026-11-10.adjudication.json).

Project: **mxc**. Stage 7.C is gated by approved Scope and Schedule baselines; resource estimates must disclose the evidence and assumptions used.

**Parent plan:** [Resource Management Plan](../Resource-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Stage 7.C process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.C-0 | Approved Scope and Schedule baselines | Dependency references | **complete (2026-11-10)** |
| 7.C-0P | [Resource-Pillar-Overview-and-Trace.md](foundation/Resource-Pillar-Overview-and-Trace.md) | Outcomes and capacity priorities traced | **approved (2026-11-10)** |
| 7.C-1 | [Resource-Role-Catalogue.md](foundation/Resource-Role-Catalogue.md) | Roles, skills, EUR rates, WBS assignment | **approved (2026-11-10)** |
| 7.C-2 | [Resource-Capacity-Estimates.md](foundation/Resource-Capacity-Estimates.md) | Capacity and ROM labor vs 78 WD CP | **approved (2026-11-10)** |
| 7.C-3 | [Resource-Tooling-and-Assignment-Register.md](foundation/Resource-Tooling-and-Assignment-Register.md) | Tools, environments, and assignments | **approved (2026-11-10)** |
| 7.C-4 | [Resource-Team-Operating-Charter.md](foundation/Resource-Team-Operating-Charter.md) | Team norms and escalation | **approved (2026-11-10)** |
| 7.C-5 | [Resource-Utilization-and-Control-Protocol.md](foundation/Resource-Utilization-and-Control-Protocol.md) | Planned/actual use and controls | **approved (2026-11-10)** |
| 7.C-6 | [Resource-Domain-Checklist.md](foundation/Resource-Domain-Checklist.md) | PMBOK 8 Resource outcomes reviewed | **approved (2026-11-10)** |
| 7.C-7 | Pack roll-up | Artifacts reviewed; registry complete | **complete (2026-11-10)** |
| 7.C-8 | Resource plan approval | `approve-subsidiary-plan` | **approved (2026-11-10)** |

## Artifact registry

| Artifact | Substage | Version | Approval status | SHA-256 after approval (2026-11-10) |
|---|---|---|---|---|
| Resource-Pillar-Overview-and-Trace.md | 7.C-0P | 1.0.0 | approved (2026-11-10) | `924b52864b854b8470969741e91ed9f055115a5cd882e2777afe38161b11cd10` |
| Resource-Role-Catalogue.md | 7.C-1 | 1.0.0 | approved (2026-11-10) | `1dc89acda00a77f9d54ba4f2080701708c44b831dfbfc5f9403377727dce990f` |
| Resource-Capacity-Estimates.md | 7.C-2 | 1.0.0 | approved (2026-11-10) | `47dc580846141ea7e71fd95db446f4f580cb4df2614c1e0c9c37f1d2887342d2` |
| Resource-Tooling-and-Assignment-Register.md | 7.C-3 | 1.0.0 | approved (2026-11-10) | `5bfef2b87a7b7f30a4756349b5cf363da8195938a9f7947be1cc2fe18f6baef4` |
| Resource-Team-Operating-Charter.md | 7.C-4 | 1.0.0 | approved (2026-11-10) | `5f5e5b79dac6a59f0606cbf8686f9cb6b7f6b4389c8ee651af51afc0a5a4dcd5` |
| Resource-Utilization-and-Control-Protocol.md | 7.C-5 | 1.0.0 | approved (2026-11-10) | `76912deeb68228025ad553e50cdb5ca4c30abd03d3c300cca2ceb0f8ad2aae65` |
| Resource-Domain-Checklist.md | 7.C-6 | 1.0.0 | approved (2026-11-10) | `fb984e12c22f77806385cd102713456f900629c89551089b5e6b516bfc6ef622` |

**Reviewer / approval date:** **2026-11-10** — resource foundation pack approved; registry shows **SHA-256 after approval**.

## Consolidated open questions

| ID | Source | Question | Owner | Status |
|---|---|---|---|---|
| Q-RES-001 | Role catalogue | Payroll EUR rates | Finance | **closed (N/A)** — contractor market rates used for ROM |
| Q-RES-002 | Capacity | Staffing model | PM | **closed (2026-11-10)** — sponsor accepted draft estimates as fair/honest |
| Q-RES-003 | Tooling | Contractor mix per role | PM + Procurement | open |
| Q-RES-004 | Tooling | Observability for 1.6.x | R-SRE |

## Roll-up and approval rules

Review each artifact against authorized inputs. Complete 7.C-7 only after all required artifacts are approved and hashes verified. At 7.C-8, roll the approved resource baseline, manifest version, artifact registry, hashes, open issues, and approval reference into the Resource Management Plan for its separate human approval. After that plan is approved, roll its baseline identifier, approval reference, manifest link, and unresolved constraints into the PMP baseline register.
