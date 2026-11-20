---
artifact_id: scope-foundation-pillar-overview-trace
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: pending
substage: 6.A-0P
depends_on: []
---

# Scope Pillar Overview and Trace — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. The Charter was approved on 2026-10-30. This trace is not an approved scope baseline or authorization for implementation.

## Strategic outcomes and scope pillars

| Outcome / pillar | Authorized source | Measurable objective | Scope deliverables | Open gap |
|---|---|---|---|---|
| TP-01 Isolation | ADR-001; BRD-001; BDR-03 | Dedicated Type-1 Hyper-V Generation 2 guest; named Windows subsystems work | Guest isolation and subsystem validation | Charter authorization not recorded |
| TP-02 Ingress | ADR-002; BRD-002; BDR-02; approved Charter | Wake path and first-byte thresholds | Request hold, separate path-to-pool and listener-port-to-image checks, wake, and response path | Verify both routing behaviors independently |
| TP-03 Image supply | ADR-003; BRD-003; BDR-04 | Production image excludes developer tooling and has a warm checkpoint | Production image bake and inventory | Production image is not yet in the catalog |
| TP-04 Paused footprint | ADR-004; BRD-004; BDR-01 | Paused CPU/GPU, RAM, disk, and resume behavior | Trim, pause, measurement, and resume | RAM targets conflict; GPU has no sample |
| TP-05 Session sterility | ADR-005; BRD-005; BDR-04 | Session writes do not survive release; egress is constrained | Transient disk, cleanup, and egress validation | Both discard paths need verification |
| TP-06 Pool and wake hygiene | ADR-006; BRD-006; BDR-05 | Refill and wake hygiene | Pool selection, replenishment, and health checks | Surge thresholds remain unresolved |

## Trace to scope bands and milestones

The project sources do not yet provide an approved WBS or milestone baseline. The mapping below is a proposed review structure only; do not assign dates or effort here.

| Outcome | WBS reference | Milestone / gate | Acceptance source |
|---|---|---|---|
| TP-01 Isolation | 2.0 | TBD | BRD-001; US-02 / US-03 |
| TP-02 Ingress | 3.0 | TBD | BRD-002; US-01 |
| TP-03 Image supply | 4.0 | TBD | BRD-003; US-04 |
| TP-04 Paused footprint | 5.0 | TBD | BRD-004; US-03 |
| TP-05 Session sterility | 6.0 | TBD | BRD-005; US-02 |
| TP-06 Pool and wake hygiene | 7.0 | TBD | BRD-006; US-03 / US-04 |

## Review checks

- Every scope outcome traces to an approved initiating source.
- No future-horizon item is presented as authorized scope.
- Conflicts and untraced deliverables are listed as open questions.

This draft does not yet meet the first check for baseline approval: the Benefits Statement remains draft, and the governing PMP approval provenance is unresolved. The Charter is approved.
