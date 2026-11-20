---
artifact_id: scope-foundation-monitor-control
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: pending
substage: 6.A-3
pmbok_process: Monitor and Control Scope
depends_on:
  - 6.A-1
  - 6.A-2
---

# Monitor and Control Scope — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. The current Scope Statement/WBS are not approved; this protocol does not authorize scope. No change to an approved scope is effective until its governing human gate accepts it.

## Scope performance measures

Compare completed deliverables and verification evidence with the approved Scope Statement, WBS, BRDs, and user stories. Record the source revision, reviewer, and date for each comparison. The review cadence and accountable role must be confirmed in the Charter/PMP.

## Variance and change handling

| Condition | Required evidence | Impact analysis | Decision authority | Record |
|---|---|---|---|---|
| Proposed scope change | Change request with source, rationale, and affected WBS/BRDs | Scope, schedule, cost, quality, risk, security, and benefits | Human authority under the approved PMP | Change record and governed document update |
| Unplanned scope variance | Difference between accepted baseline and implementation/test evidence | Scope impact, acceptance gap, downstream traceability | Human authority under the approved PMP | Issue, decision, and corrective action |
| New or changed requirement | Requirement ID, source, acceptance delta, and impact analysis | WBS, affected architecture/BRDs/FDD/stories, tests | Human authority under the applicable approval gate | Requirements traceability and approval record |

Current source inconsistencies that require controlled resolution include the paused-RAM target, the pool surge threshold, and the relationship between path-based and listen-port routing.

## Traceability and staleness

Changes to accepted ADRs, BRDs, assumptions, or source requirements trigger an impact review of this WBS, the relevant scope statement, and dependent schedule/resource/cost work. Preserve prior baselines; update only after a recorded decision. The architecture suite currently resides at `docs/hyperv/architecture/ADR.md`; several BRDs refer to a different path, which must be reconciled.

## Escalation and audit trail

Record thresholds, escalation routes, and immutable links to issues, decisions, reviews, and approved baseline versions. The Charter and PMP do not yet provide an approved cadence or numeric scope-variance threshold; leave these unspecified until the owner decides.
