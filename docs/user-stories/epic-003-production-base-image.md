---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-003-production-base-image.md"
  - "docs/project-docs/Business-Requirements/BRD-003-production-base-image.md"
  - "docs/07-architecture/ADR-003-production-base-image.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-003-production-base-image.md"
---

# Epic 003: Production base image separate from the developer image

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 7 (Requirement: Story)`  
> **Inputs:** [FDD-003](../project-docs/Functional-Design/FDD-003-production-base-image.md), [BRD-003](../project-docs/Business-Requirements/BRD-003-production-base-image.md), [ADR-003](../07-architecture/ADR-003-production-base-image.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-003-production-base-image.md

**Source ADR:** [ADR-003](../07-architecture/ADR-003-production-base-image.md) — Accepted.  
**Source BRD/FDD:** [BRD-003](../project-docs/Business-Requirements/BRD-003-production-base-image.md) — Approved (2026-10-30) / [FDD-003](../project-docs/Functional-Design/FDD-003-production-base-image.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-003-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-003-2026-10-30.adjudication.json).
**Suite anchor:** [US-04](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.

## Story 3.1 — Clean production VHDX

**Status:** Ready for review — not yet run through `implement-story`  
**As a** Software Release Engineer, **I want** audit a baked production VHDX, **so that** production carries no developer debris.

**Acceptance Criteria:**
- Given `winserv2025-prod-adpa.vhdx`, when audit runs, then Scoop, uv, cargo, git, compilers, and source repos are absent (`AC-04.1`).

## Story 3.2 — Warm baseline checkpoint

**Status:** Ready for review — not yet run through `implement-story`  
**As a** Software Release Engineer, **I want** bake and checkpoint the production image, **so that** first wake avoids JIT compile stall.

**Acceptance Criteria:**
- Given bake completes, when service answers smoke on `localhost:8080/health`, then DB handles are closed and `baseline-hot-ready` is captured (`AC-04.2`).

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
