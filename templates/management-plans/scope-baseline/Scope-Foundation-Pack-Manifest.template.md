---
artifact_id: scope-foundation-pack-manifest
parent_plan_id: scope-management
baseline_id: "{{BASELINE_ID}}"
route: foundation_pack
governance_policy: approve-subsidiary-plan
version: "1.0.0"
owner_role: Project Manager
depends_on: []
pack_status: pending
---

# Scope Foundation Pack — Manifest ({{BASELINE_ID}})

Project: **{{PROJECT_NAME}}**. This manifest tracks the draft, review, and roll-up of the Scope foundation pack. Generation does not approve any artifact or authorize work.

**Parent plan:** [Scope Management Plan](../Scope-Management-Plan.md). **PMP destination:** [Project Management Plan](../../Project-Management-Plan.md).

## Stage 7.A process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 7.A-0 | Charter and approved initiating inputs | Source links and approval references | pending |
| 7.A-0P | [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.template.md) | Strategic outcomes traced to deliverables | pending |
| 7.A-1 | [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.template.md) | Boundaries, exclusions, assumptions, acceptance | pending |
| 7.A-2 | [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.template.md) | Deliverable decomposition and dictionary entries | pending |
| 7.A-3 | [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.template.md) | Change, variance, and traceability controls | pending |
| 7.A-4 | [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.template.md) | Acceptance evidence and verification owners | pending |
| 7.A-5 | [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.template.md) | PMBOK 8 Scope Performance Domain outcomes | pending |
| 7.A-6 | Pack roll-up | All artifacts reviewed; registry complete | pending |
| 7.A-7 | Scope plan approval | Human approval under the configured plan gate | pending |

## Upstream inputs

List the approved charter, business case, benefits, requirements, architecture decisions, and other authorized scope sources. Record missing or conflicting inputs as open issues; do not infer approval.

## Artifact registry

| Artifact | Substage | Version | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|---|
| Scope-Pillar-Overview-and-Trace.md | 7.A-0P | 1.0.0 | pending | TBD | TBD |
| Scope-Project-Scope-Statement.md | 7.A-1 | 1.0.0 | pending | TBD | TBD |
| Scope-WBS-Dictionary.md | 7.A-2 | 1.0.0 | pending | TBD | TBD |
| Scope-Monitor-Control-Scope.md | 7.A-3 | 1.0.0 | pending | TBD | TBD |
| Scope-Validate-Scope.md | 7.A-4 | 1.0.0 | pending | TBD | TBD |
| Scope-Domain-Checklist.md | 7.A-5 | 1.0.0 | pending | TBD | TBD |

## Roll-up and approval rules

1. Draft and review each artifact against its cited inputs and record unresolved questions.
2. Change an artifact to approved only after its designated human review is recorded; calculate its SHA-256 after that review.
3. Complete 7.A-6 only when every required artifact is approved and the registry hashes match the files.
4. At 7.A-7, roll the approved scope boundary, manifest version, artifact registry, hashes, open issues, and approval reference into the Scope Management Plan. Submit the plan for its configured human approval; the plan gate does not substitute for artifact review.
5. After the Scope Management Plan is approved, roll its baseline identifier, approval reference, manifest link, and unresolved constraints into the PMP baseline register.
6. Downstream packs may start only when their declared dependencies are approved.

## Open questions and decisions

| ID | Question / decision | Owner | Due | Status |
|---|---|---|---|---|
| Q-SCOPE-001 | TBD | TBD | TBD | open |
