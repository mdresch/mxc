---
artifact_id: scope-foundation-validate-scope
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: pending
substage: 6.A-4
pmbok_process: Validate Scope
depends_on:
  - 6.A-1
  - 6.A-2
---

# Validate Scope — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Validation evidence demonstrates acceptance; it does not replace formal human approval. Source BRDs are approved, but the Charter and integrated PMP approval state need reconciliation.

## Acceptance and verification matrix

| WBS ID | Deliverable | Acceptance criteria source | Verification method | Reviewer / approver | Evidence location |
|---|---|---|---|---|---|
| 2.0 | Isolated Generation 2 guest | BRD-001; US-02 / US-03 | Guest subsystem and isolation checks | TBD | Tests / execution evidence TBD |
| 3.0 | Connection-buffering ingress and wake | BRD-002; US-01 | Cold-wake timing, routing, HTTP result checks | TBD | Gateway logs / tests TBD |
| 4.0 | Production image and warm checkpoint | BRD-003; US-04 | Image inventory, hash, and health-checkpoint inspection | TBD | Image catalog / bake evidence TBD |
| 5.0 | Paused standby and footprint | BRD-004; US-03 | CPU/GPU/RAM/disk readings and resume timing | TBD | Host measurement evidence TBD |
| 6.0 | Session sterility and egress | BRD-005; US-02 | Discard tests, parent hash check, allow/deny probes | TBD | Security test evidence TBD |
| 7.0 | Pool replenishment and wake hygiene | BRD-006; US-03 / US-04 | Lease/refill, health, entropy/clock/pool checks | TBD | Integration test evidence TBD |
| 8.0 | Integrated acceptance | BRD-001 through BRD-006; USER_STORIES.md | End-to-end test against resolved criteria | TBD | Release evidence TBD |

## Definition of done

Minimum completion evidence includes a stable WBS/requirement link, repeatable test or inspection output, reviewer disposition, defect disposition, and a traceable governance record. The test owner and evidence retention location remain to be assigned.

## Requirements traceability

Use approved BRD-001 through BRD-006 and their linked architecture/user-story criteria as requirement sources. Record the exact criterion, test result, environment, date, and human acceptance decision. The `docs/hyperv/architecture/USER_STORIES.md` suite is the current story source.

## Rejection and rework

Record rejected deliverables as open issues with the failed criterion, owner, corrective action, and re-test evidence. Re-verify against the unchanged approved criterion; a changed criterion requires the relevant governance approval before acceptance.
