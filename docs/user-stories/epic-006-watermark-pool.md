---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-006-watermark-pool.md"
  - "docs/project-docs/Business-Requirements/BRD-006-watermark-pool.md"
  - "docs/07-architecture/ADR-006-watermark-pool.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-006-watermark-pool.md"
---

# Epic 006: Watermark pool, replenish, and wake hygiene

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Inputs:** [FDD-006](../project-docs/Functional-Design/FDD-006-watermark-pool.md), [BRD-006](../project-docs/Business-Requirements/BRD-006-watermark-pool.md), [ADR-006](../07-architecture/ADR-006-watermark-pool.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-006-watermark-pool.md

**Source ADR:** [ADR-006](../07-architecture/ADR-006-watermark-pool.md) — Accepted.  
**Source BRD/FDD:** [BRD-006](../project-docs/Business-Requirements/BRD-006-watermark-pool.md) — Approved (2026-10-30) / [FDD-006](../project-docs/Functional-Design/FDD-006-watermark-pool.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-006-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-006-2026-10-30.adjudication.json).
**Suite anchor:** [US-05](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.

## Story 6.1 — Buffer replenishment

**Status:** Ready for review — not yet run through `implement-story`  
**As a** SRE, **I want** lease the last ready guest, **so that** the next caller finds a Paused standby without blocking the in-flight request.

**Acceptance Criteria:**
- Given K_min met, when a guest is leased, then another reaches `StandbyPaused` in about 1.5 s in background (`AC-05.1`).

## Story 6.2 — Surge expansion

**Status:** Ready for review — not yet run through `implement-story`  
**As a** SRE, **I want** handle request bursts, **so that** concurrent callers avoid cold boot.

**Acceptance Criteria:**
- Given configured surge threshold (record 5 rps or 10 rps/5 s), when tripped or queue depth > 0, then ready count expands up to K_max (`AC-05.2`, `BEN-09`).

## Story 6.3 — Wake hygiene

**Status:** Ready for review — not yet run through `implement-story`  
**As a** SRE, **I want** wake a guest from checkpoint, **so that** cryptography, time, and DB pools are safe before traffic.

**Acceptance Criteria:**
- Given restore from `baseline-hot-ready`, when `/health` first succeeds, then entropy reseeded, clock synced, and DB pools cleared (`AC-02.4`).

## Story 6.4 — Scale down

**Status:** Ready for review — not yet run through `implement-story`  
**As a** SRE, **I want** cool surplus guests, **so that** host RAM returns toward baseline.

**Acceptance Criteria:**
- Given traffic normalized, when idle exceeds configured cooldown (record 180 s or 300 s), then surplus above K_min is reaped (`AC-05.4`).

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
