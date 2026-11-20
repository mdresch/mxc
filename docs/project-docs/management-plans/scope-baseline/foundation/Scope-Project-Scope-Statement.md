---
artifact_id: scope-foundation-project-scope-statement
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: pending
substage: 6.A-1
pmbok_process: Define Scope
depends_on:
  - 6.A-0P
---

# Project Scope Statement — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review, not an approved scope baseline. The Charter was approved on 2026-10-30; reconcile the remaining initiating-input and PMP approval issues before pack approval.

## Purpose and objectives

The approved Charter authorizes planning for a just-in-time, scale-to-zero production Hyper-V sandbox for ADPA / SIDPA workloads. Existing business and architecture documents describe a dedicated Generation 2 guest, a held-request wake path, clean production images, paused standby, session cleanup, and pool replenishment. This statement summarizes those sources for review; it is not an approved scope baseline.

## Product and project scope

The Charter includes these capabilities in scope. This proposed statement is still a draft, not an approved scope baseline:

- Dedicated Type-1 Hyper-V Generation 2 guest for the named Windows workloads and required Windows subsystems (BRD-001).
- Connection-buffering ingress, documented path/port routing, paused-guest wake, and response behavior (BRD-002).
- Separate production image, clean inventory, warm health checkpoint, and image-bake evidence (BRD-003).
- Paused standby footprint and resume measurements (BRD-004).
- Transient session differencing disk, cleanup alternatives, and restricted egress (BRD-005).
- Watermark pool replenishment, wake hygiene, and health reporting (BRD-006).
- Cross-cutting integration and acceptance evidence for the approved requirements.

Project-management work includes requirements traceability, baseline review, test evidence, and governance records. It does not imply a schedule or cost commitment.

## Exclusions

| Excluded item | Reason / authority | Reconsideration trigger |
|---|---|---|
| Future research hypotheses HYP-mxc-015 through HYP-mxc-020 | Business Case excludes them from current benefit claims | Separate review and explicit scope authorization |
| Unsubstantiated currency savings, ROI, or host-density claims | No total project budget, license price, host count, or agreed density measure is recorded; USD 25,000 is a PM spending authority, not a total budget | Approved financial evidence and Cost foundation |
| Production image signing / vulnerability-scan horizon | BRD-003 leaves signing and scanning as future work | Separate accepted requirement and approval |
| Unnamed second-factor product | Benefits Statement says the factor is not specified | Product decision and updated acceptance evidence |

## Constraints, assumptions, and dependencies

| Type | Statement | Source / owner | Validation status |
|---|---|---|---|
| Constraint | Production workload uses a dedicated Type-1 Hyper-V Generation 2 guest; a shared-kernel container is rejected for these workloads | ADR-001 / BRD-001; approved Project Charter | Charter approved; this statement remains draft |
| Constraint | The production image, paused guest, and session disks consume standing resources; zero CPU does not mean zero resource cost | Business Case; ADR-004 | Recorded; quantify later in Resource/Cost work |
| Confirmed boundary | ADPA and SIDPA are both included in this project; path-based pool routing and listener-port image selection are separate acceptance checks | Approved Project Charter; Benefits Statement | Confirmed as project scope; verification evidence remains pending |
| Dependency | A production image and its warm checkpoint are required for image and session acceptance | ADR-003 / BRD-003 | Production image not yet present |
| Dependency | Approved Scope and Schedule baselines precede Resource and Cost planning | Project Charter / PMP workflow | Schedule evidence is explicitly not yet available |
| Governance gap | Benefits Statement remains draft; PMP approval provenance is unresolved | Project-Charter.md; Benefits-Statement.md; Project-Management-Plan.md | Open |

## Acceptance conditions

Acceptance is to be measured against the approved BRD and user-story evidence, not this draft. Current candidate thresholds include `Resume-VM` within 300 ms, first byte within 800 ms, no wake-caused 502/504, and a production image without developer tooling. The RAM target conflicts across source documents, and the surge measurement window remains undefined. The Charter treats path-based pool routing and listener-port image selection as separate checks; both await verification. Do not mark unresolved or untested outcomes as passed.

## Open scope decisions

| ID | Decision needed | Owner | Status |
|---|---|---|---|
| Q-SCOPE-001 | Approve the Benefits Statement and reconcile PMP approval provenance before pack authorization | Project owner | open |
| Q-SCOPE-002 | Confirm whether separate work-package tracking is needed for ADPA and SIDPA under the shared charter | Project owner | open |
| Q-SCOPE-003 | Reconcile the 1.0–1.2 GB and under-700 MB RAM targets | Project owner | open |
| Q-SCOPE-004 | Define the measurement window for the charter-selected surge threshold above 5 requests/second; upstream documents also record at least 10 in 5 seconds | Project owner | open |
| Q-SCOPE-005 | Verify path-based pool routing and listener-port image selection as separate acceptance checks | Project owner | pending evidence |
