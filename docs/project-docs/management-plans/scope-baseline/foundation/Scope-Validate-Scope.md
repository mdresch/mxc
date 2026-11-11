---
artifact_id: scope-foundation-validate-scope
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.1.0"
approval_status: approved
substage: 7.A-4
pmbok_process: Validate Scope
depends_on:
  - 7.A-1
  - 7.A-2
---

# Validate Scope — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a4-validate-scope-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-scope-7a4-validate-scope-2026-11-10.adjudication.json).

## Acceptance and verification matrix

| WBS ID | Story ID | Deliverable | Acceptance criteria source | Verification method | Evidence location |
|---|---|---|---|---|---|
| 1.1.1 | 1.1 | Generation 2 isolation boundary | Epic 001 Story 1.1 | Gate 001; Gen2 provision check | [epic-001](../../../../user-stories/epic-001-type-1-hyperv-generation-2.md) |
| 1.1.2 | 1.2 | Windows subsystems on the guest | Epic 001 Story 1.2 | Guest subsystem invocation | epic-001 |
| 1.2.1 | 2.1 | Cold wake TTFB | AC-01.1 | `jit_ingress_gateway` harness | epic-002 |
| 1.2.2 | 2.2 | No wake-caused 502/504 | AC-01.3 | Wake error budget test | epic-002 |
| 1.2.3 | 2.3 | Dual routing rules | HYP-mxc-004 | Path + port routing test | epic-002 |
| 1.3.1 | 3.1 | Clean production VHDX | Story 3.1 AC | `audit_production_image.ps1` | epic-003 |
| 1.3.2 | 3.2 | Warm baseline checkpoint | Story 3.2 AC | Registry + checkpoint inspect | epic-003 |
| 1.4.1 | 4.1 | Zero idle CPU | Story 4.1 AC | Paused CPU meter (Formulated) | epic-004 |
| 1.4.2 | 4.2 | Trimmed paused footprint | Story 4.2 AC | RAM at Paused (Formulated) | epic-004 |
| 1.4.3 | 4.3 | Sub-300 ms resume | Story 4.3 AC | `benchmark_jit_wake.py` | epic-004 |
| 1.5.1 | 5.1 | Ephemeral session disk | Story 5.1 AC | Diff disk attach test | epic-005 |
| 1.5.2 | 5.2 | Egress whitelist | Story 5.2 AC; AC-02.3 | ACL automation | epic-005 |
| 1.5.3 | 5.3 | Discard and reproduce | Story 5.3 AC | Session teardown + pool clean | epic-005 |
| 1.6.1 | 6.1 | Buffer replenishment | Story 6.1 AC | Pool watermark test | epic-006 |
| 1.6.2 | 6.2 | Surge expansion | Story 6.2 AC | Surge policy test | epic-006 |
| 1.6.3 | 6.3 | Wake hygiene | Story 6.3 AC | Wake hygiene metrics | epic-006 |
| 1.6.4 | 6.4 | Scale down | Story 6.4 AC | Scale-down cooldown test | epic-006 |
| 2.1 | — | Scope foundation pack | Pack 7.A | `approve-subsidiary-plan` (2026-11-10) | `scope-baseline/foundation/` |

## Definition of done

**Specification done (current phase):** WBS row exists; ADR/BRD/FDD/epic Approved; story **Ready for review**.

**Implementation done (future):** `implement-story` for WBS **1.N.S**; contract tests; audit register.

## Requirements traceability

`ADR-00N` → `BRD-00N` → `FDD-00N` → `epic-00N` → **Story ID** `N.S` → **WBS** `1.N.S`.

## Rejection and rework

- Gate revision → update epic AC → bump WBS dictionary version if scope boundary changes.
- Story implementation failure → governance loop; WBS ID stays stable unless story is split (new `.S` suffix).
