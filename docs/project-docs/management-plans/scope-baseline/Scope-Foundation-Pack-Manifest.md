---
artifact_id: scope-foundation-pack-manifest
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_pack
governance_policy: approve-pmp
version: "1.0.0"
owner_role: Project Manager
depends_on: []
pack_status: pending
---

# Scope Foundation Pack — Manifest (PMP-BL-v1.0.0)

Project: **MXC Hyper-V for ADPA / SIDPA**. This manifest tracks the draft, review, and roll-up of the Scope foundation pack. Generation does not approve any artifact or authorize work.

**Pack state:** Authoring drafts are prepared for review. The pack remains pending; no artifact is approved, no hash is recorded, and no work is authorized by this scaffold.

## Stage 6.A process

| Gate | Deliverable | Review evidence | Status |
|---|---|---|---|
| 6.A-0 | Charter and approved initiating inputs | Charter approved 2026-10-30; Benefits Statement remains draft; confirm governing PMP approval record | blocked |
| 6.A-0P | [Scope-Pillar-Overview-and-Trace.md](foundation/Scope-Pillar-Overview-and-Trace.md) | Six architecture pillars and approved BRDs traced | draft |
| 6.A-1 | [Scope-Project-Scope-Statement.md](foundation/Scope-Project-Scope-Statement.md) | Boundaries and exclusions grounded in approved BRDs | draft |
| 6.A-2 | [Scope-WBS-Dictionary.md](foundation/Scope-WBS-Dictionary.md) | Proposed deliverable decomposition; no schedule commitments | draft |
| 6.A-3 | [Scope-Monitor-Control-Scope.md](foundation/Scope-Monitor-Control-Scope.md) | Change, variance, and traceability controls | draft |
| 6.A-4 | [Scope-Validate-Scope.md](foundation/Scope-Validate-Scope.md) | Acceptance evidence and verification sources | draft |
| 6.A-5 | [Scope-Domain-Checklist.md](foundation/Scope-Domain-Checklist.md) | PMBOK 8 Scope Performance Domain outcomes | draft |
| 6.A-6 | Pack roll-up | All artifacts reviewed; registry complete | pending |
| 6.A-7 | Scope plan approval | Human approval under the configured plan gate | pending |

## Upstream inputs

| Input | Current evidence | Stage 6.A treatment |
|---|---|---|
| [Project Charter](../../Project-Charter.md) | Approved by the Steering Committee on 2026-10-30; individual member names are not recorded | Charter authorization is established; drafts are not a baseline |
| [Business Case](../../Business-Case.md) | Approval record exists for 2026-10-29 | Use as source; preserve explicit financial unknowns |
| [Benefits Statement](../../Benefits-Statement.md) | Explicitly marked Draft | Do not treat benefits as approved or realized |
| [Business Drivers and Requirements](../../../hyperv/architecture/BDR.md) | Current project scope and business-driver source | Trace requirements; flag unresolved measures |
| [Architecture suite](../../../hyperv/architecture/ADR.md) | ADR-001 through ADR-006 are recorded in the consolidated suite | Trace decisions; do not expand beyond their accepted scope |
| BRD-001 through BRD-006 | Each states approved on 2026-10-30 | Use as requirement sources; resolve PMP-baseline provenance issue before baseline roll-up |

The PMP and Stage 7 documents contain conflicting lifecycle claims: the PMP says it must precede BRD/ADR/FDD/stories, while the Charter says it is not started and the BRDs cite `PMP-BL-v1.0.0`. Record the canonical PMP approval evidence before 6.A-6.

## Artifact registry

| Artifact | Substage | Version | Review status | Reviewer / date | SHA-256 after approval |
|---|---|---|---|---|---|
| Scope-Pillar-Overview-and-Trace.md | 6.A-0P | 1.0.0 | draft | TBD | TBD |
| Scope-Project-Scope-Statement.md | 6.A-1 | 1.0.0 | draft | TBD | TBD |
| Scope-WBS-Dictionary.md | 6.A-2 | 1.0.0 | draft | TBD | TBD |
| Scope-Monitor-Control-Scope.md | 6.A-3 | 1.0.0 | draft | TBD | TBD |
| Scope-Validate-Scope.md | 6.A-4 | 1.0.0 | draft | TBD | TBD |
| Scope-Domain-Checklist.md | 6.A-5 | 1.0.0 | draft | TBD | TBD |

## Roll-up and approval rules

1. Reconcile and obtain approval for the initiating inputs; until then, drafts may be reviewed but not baseline-approved.
2. Review each artifact against its cited inputs and record unresolved questions.
3. Change an artifact to approved only after its designated human review is recorded; calculate its SHA-256 after that review.
4. Complete 6.A-6 only when 6.A-0 is satisfied, every required artifact is approved, and registry hashes match the files.
5. Submit the Scope Management Plan for its configured human approval gate at 6.A-7. The plan gate does not substitute for artifact review.
6. Downstream packs may start only when their declared dependencies and evidence prerequisites are approved.

## Open questions and decisions

| ID | Question / decision | Owner | Due | Status |
|---|---|---|---|---|
| Q-SCOPE-001 | Approve the Benefits Statement and reconcile the PMP approval provenance before treating this pack as authorized | Project owner | TBD | open |
| Q-SCOPE-002 | Identify the canonical approval record for `PMP-BL-v1.0.0` and reconcile the PMP/Charter lifecycle statements | Project owner | TBD | open |
| Q-SCOPE-003 | Reconcile the RAM target and define the measurement window for the charter-selected surge threshold before validating affected requirements | Project owner | TBD | open |
| Q-SCOPE-004 | Confirm the canonical paths for architecture decisions; BRDs currently reference `docs/07-architecture/` while the suite is under `docs/hyperv/architecture/` | Project owner | TBD | open |
