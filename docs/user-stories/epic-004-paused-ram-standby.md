---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-004-paused-ram-standby.md"
  - "docs/project-docs/Business-Requirements/BRD-004-paused-ram-standby.md"
  - "docs/07-architecture/ADR-004-paused-ram-standby.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-004-paused-ram-standby.md"
---

# Epic 004: Paused RAM standby, trimmed before suspend

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 7 (Requirement: Story)`  
> **Inputs:** [FDD-004](../project-docs/Functional-Design/FDD-004-paused-ram-standby.md), [BRD-004](../project-docs/Business-Requirements/BRD-004-paused-ram-standby.md), [ADR-004](../07-architecture/ADR-004-paused-ram-standby.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-004-paused-ram-standby.md

**Source ADR:** [ADR-004](../07-architecture/ADR-004-paused-ram-standby.md) — Accepted.  
**Source BRD/FDD:** [BRD-004](../project-docs/Business-Requirements/BRD-004-paused-ram-standby.md) — Approved (2026-10-30) / [FDD-004](../project-docs/Functional-Design/FDD-004-paused-ram-standby.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-004-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-004-2026-10-30.adjudication.json).
**Suite anchor:** [US-03](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.

## Story 4.1 — Zero idle CPU

**WBS ID:** `1.4.1`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Infrastructure Platform Engineer, **I want** keep dormant VMs Paused, **so that** idle guests consume no processor.

**Acceptance Criteria:**
- Given 10 standby VMs Paused, when host CPU is read, then total CPU for those guests is 0.0% (`AC-03.1`).

## Story 4.2 — Trimmed paused footprint

**WBS ID:** `1.4.2`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Infrastructure Platform Engineer, **I want** trim before suspend, **so that** paused guests hold a lean RAM allocation.

**Acceptance Criteria:**
- Given release restores `baseline-hot-ready` then suspends, when RAM is measured, then footprint is about 1.0–1.2 GB and the configured target is recorded (`AC-03.2`, `BEN-10`).

## Story 4.3 — Sub-300 ms resume

**WBS ID:** `1.4.3`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Infrastructure Platform Engineer, **I want** resume a Paused guest, **so that** wake stays inside the platform ceiling.

**Acceptance Criteria:**
- Given ingress dispatches wake, when `Resume-VM` completes, then elapsed time ≤ 300 ms (`AC-03.3`).

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
