---
artifact_id: scope-foundation-wbs-dictionary
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.1.0"
approval_status: approved
substage: 7.A-2
pmbok_process: Develop Scope Structure
depends_on:
  - 7.A-1
---

# Scope WBS and Dictionary — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a2-wbs-dictionary-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-scope-7a2-wbs-dictionary-2026-11-10.adjudication.json).

## Decomposition rules

- **Product root:** `1.0` = MXC JIT Hyper-V sandbox.
- **Pillar / epic:** `1.{N}` where **N** is 1–6 (ADR/epic **00N**).
- **User story:** `1.{N}.{S}` where **S** is the story minor number from the epic (e.g. Story **2.3** → WBS **`1.2.3`**).
- **Story ID** (narrative label `N.S`) is recorded beside each WBS row for traceability to [epic-00N](../../../../user-stories/).
- Duration, cost, and resource estimates belong in schedule/cost/resource packs—not in this dictionary.

## Work breakdown structure

| WBS ID | Parent | Story ID | Deliverable / work package | Acceptance source | Owner | Status |
|---|---|---|---|---|---|---|
| 1.0 | — | — | MXC JIT Hyper-V sandbox | Approved epics 001–006 | Platform | approved-spec |
| 1.1 | 1.0 | — | **TP-01** Gen2 isolation (epic 001) | [epic-001](../../../../user-stories/epic-001-type-1-hyperv-generation-2.md) | Platform | approved-spec |
| 1.1.1 | 1.1 | 1.1 | Generation 2 isolation boundary | Story 1.1 AC; BRU-001 | Platform | ready-for-review |
| 1.1.2 | 1.1 | 1.2 | Windows subsystems on the guest | Story 1.2 AC; BEN-05 | Platform | ready-for-review |
| 1.2 | 1.0 | — | **TP-02** Ingress gateway (epic 002) | [epic-002](../../../../user-stories/epic-002-connection-buffering-ingress-gateway.md); US-01 | Platform | approved-spec |
| 1.2.1 | 1.2 | 2.1 | Cold wake TTFB | AC-01.1 | Platform | ready-for-review |
| 1.2.2 | 1.2 | 2.2 | No wake-caused 502/504 | AC-01.3; BEN-03 | Platform | ready-for-review |
| 1.2.3 | 1.2 | 2.3 | Dual routing rules | HYP-mxc-004 path+port | Platform | ready-for-review |
| 1.3 | 1.0 | — | **TP-03** Production image (epic 003) | [epic-003](../../../../user-stories/epic-003-production-base-image.md) | Release | approved-spec |
| 1.3.1 | 1.3 | 3.1 | Clean production VHDX | Story 3.1 AC | Release | ready-for-review |
| 1.3.2 | 1.3 | 3.2 | Warm baseline checkpoint | Story 3.2 AC | Release | ready-for-review |
| 1.4 | 1.0 | — | **TP-04** Paused standby (epic 004) | [epic-004](../../../../user-stories/epic-004-paused-ram-standby.md); US-03 | Platform | approved-spec |
| 1.4.1 | 1.4 | 4.1 | Zero idle CPU | Story 4.1 AC | Platform | ready-for-review |
| 1.4.2 | 1.4 | 4.2 | Trimmed paused footprint | Story 4.2 AC | Platform | ready-for-review |
| 1.4.3 | 1.4 | 4.3 | Sub-300 ms resume | Story 4.3 AC | Platform | ready-for-review |
| 1.5 | 1.0 | — | **TP-05** Session sterility (epic 005) | [epic-005](../../../../user-stories/epic-005-transient-differencing-disk.md); US-02 | SecOps | approved-spec |
| 1.5.1 | 1.5 | 5.1 | Ephemeral session disk | Story 5.1 AC | SecOps | ready-for-review |
| 1.5.2 | 1.5 | 5.2 | Egress whitelist | Story 5.2 AC; AC-02.3 | SecOps | ready-for-review |
| 1.5.3 | 1.5 | 5.3 | Discard and reproduce | Story 5.3 AC | SecOps | ready-for-review |
| 1.6 | 1.0 | — | **TP-06** Watermark pool (epic 006) | [epic-006](../../../../user-stories/epic-006-watermark-pool.md); US-05 | SRE | approved-spec |
| 1.6.1 | 1.6 | 6.1 | Buffer replenishment | Story 6.1 AC | SRE | ready-for-review |
| 1.6.2 | 1.6 | 6.2 | Surge expansion | Story 6.2 AC | SRE | ready-for-review |
| 1.6.3 | 1.6 | 6.3 | Wake hygiene | Story 6.3 AC | SRE | ready-for-review |
| 1.6.4 | 1.6 | 6.4 | Scale down | Story 6.4 AC | SRE | ready-for-review |
| 2.0 | — | — | SIDPA governance & PMP | `approve-pmp` | PM | in-progress |
| 2.1 | 2.0 | — | Scope foundation pack (7.A) | `approve-subsidiary-plan` | PM | approved (2026-11-10) |
| 2.2 | 2.0 | — | Schedule foundation pack (7.B) | `approve-subsidiary-plan` | PM | approved (2026-11-10) |

## Story index (quick lookup)

| Story ID | WBS ID | Epic |
|---|---|---|
| 1.1 | 1.1.1 | 001 |
| 1.2 | 1.1.2 | 001 |
| 2.1 | 1.2.1 | 002 |
| 2.2 | 1.2.2 | 002 |
| 2.3 | 1.2.3 | 002 |
| 3.1 | 1.3.1 | 003 |
| 3.2 | 1.3.2 | 003 |
| 4.1 | 1.4.1 | 004 |
| 4.2 | 1.4.2 | 004 |
| 4.3 | 1.4.3 | 004 |
| 5.1 | 1.5.1 | 005 |
| 5.2 | 1.5.2 | 005 |
| 5.3 | 1.5.3 | 005 |
| 6.1 | 1.6.1 | 006 |
| 6.2 | 1.6.2 | 006 |
| 6.3 | 1.6.3 | 006 |
| 6.4 | 1.6.4 | 006 |

## Dictionary completeness checks

- **17 / 17** approved user stories have stable WBS IDs under **1.N.S**.
- Pillar summaries **1.1–1.6** roll up child story packages.
- **implement-story** not run—`ready-for-review` is not implementation complete.

## Open decomposition issues

| ID | Issue | Affected WBS | Owner | Status |
|---|---|---|---|---|
| WBS-001 | `2.0` governance WBS overlaps schedule/cost packs—split at roll-up | 2.0 | PM | open |
