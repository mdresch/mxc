---
artifact_id: scope-foundation-wbs-dictionary
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: pending
substage: 6.A-2
pmbok_process: Develop Scope Structure
depends_on:
  - 6.A-1
---

# Scope WBS and Dictionary — MXC Hyper-V for ADPA / SIDPA

**Status:** Proposed WBS for review only. The Charter was approved on 2026-10-30; this is neither an approved scope baseline nor an execution schedule.

## Decomposition rules

Decompose to observable deliverables traced to BRD-001 through BRD-006. The entries below are top-level work packages pending owner decomposition. Use lower-level packages only after the scope statement is authorized. Duration, cost, and resource estimates belong in their respective baselines and are intentionally absent.

## Work breakdown structure

| WBS ID | Parent | Deliverable / work package | Included work | Exclusions / interface | Acceptance source | Owner | Status |
|---|---|---|---|---|---|---|---|
| 1.0 | — | Governed project scope and requirements trace | Charter reconciliation, scope baseline, traceability, decision records | Does not authorize implementation | Project Charter; PMP gate | Project owner | draft |
| 2.0 | — | Isolated Hyper-V guest | Generation 2 guest and required Windows subsystem behavior | Does not include shared-kernel container alternative | BRD-001; US-02 / US-03 | TBD | draft |
| 3.0 | — | Connection-buffering ingress and wake | Request hold, pool/image routing, wake, HTTP response behavior | Does not include a global edge proxy horizon | BRD-002; US-01 | TBD | draft |
| 4.0 | — | Production image and warm checkpoint | Separate image, clean inventory, bake evidence, health checkpoint | Signing/scanning remains future unless separately authorized | BRD-003; US-04 | TBD | draft |
| 5.0 | — | Paused standby and footprint | Idle state, memory trimming, resume and host measurements | Does not claim zero RAM or disk consumption | BRD-004; US-03 | TBD | draft |
| 6.0 | — | Session sterility and egress control | Transient session storage, discard, parent integrity, egress rules | Does not include future cryptographic scrubbing | BRD-005; US-02 | TBD | draft |
| 7.0 | — | Pool replenishment and wake hygiene | Watermark behavior, readiness, health, stale-state cleanup | Does not select unresolved surge threshold | BRD-006; US-03 / US-04 | TBD | draft |
| 8.0 | — | Integrated acceptance evidence | Cross-package test, operational evidence, and disposition | Requires approved acceptance rules for unresolved measures | BRD-001 through BRD-006; USER_STORIES.md | TBD | draft |

## Dictionary completeness checks

- Each work package has a unique stable identifier and one accountable owner.
- Deliverables cover the approved scope without overlap or unexplained gaps.
- Requirements and acceptance sources are traceable.
- Estimates and execution authorization are not implied by this dictionary.

## Open decomposition issues

| ID | Issue | Affected WBS | Owner | Status |
|---|---|---|---|---|
| Q-WBS-001 | Confirm WBS ownership and decomposition level after Charter approval | All | Project owner | open |
| Q-WBS-002 | Reconcile unresolved RAM, surge, and routing acceptance rules | 3.0, 5.0, 7.0 | Project owner | open |
| Q-WBS-003 | Add lower-level work packages from approved stories without introducing unsupported estimates | All | Project owner | open |
