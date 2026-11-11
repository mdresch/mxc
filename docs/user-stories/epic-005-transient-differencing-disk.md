---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-005-transient-differencing-disk.md"
  - "docs/project-docs/Business-Requirements/BRD-005-transient-differencing-disk.md"
  - "docs/07-architecture/ADR-005-transient-differencing-disk.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-005-transient-differencing-disk.md"
---

# Epic 005: Transient differencing disk and egress whitelist

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Inputs:** [FDD-005](../project-docs/Functional-Design/FDD-005-transient-differencing-disk.md), [BRD-005](../project-docs/Business-Requirements/BRD-005-transient-differencing-disk.md), [ADR-005](../07-architecture/ADR-005-transient-differencing-disk.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-005-transient-differencing-disk.md

**Source ADR:** [ADR-005](../07-architecture/ADR-005-transient-differencing-disk.md) — Accepted.  
**Source BRD/FDD:** [BRD-005](../project-docs/Business-Requirements/BRD-005-transient-differencing-disk.md) — Approved (2026-10-30) / [FDD-005](../project-docs/Functional-Design/FDD-005-transient-differencing-disk.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-005-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-005-2026-10-30.adjudication.json).
**Suite anchor:** [US-02](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.

## Story 5.1 — Ephemeral session disk

**Status:** Ready for review — not yet run through `implement-story`  
**As a** CISO, **I want** run a session that writes disk state, **so that** no residue remains after release.

**Acceptance Criteria:**
- Given files written on `.avhdx`, when session ends or 300 s idle with no open requests, then `.avhdx` is deleted (`AC-02.1`).
- Given parent `winserv2025-prod-adpa.vhdx`, when SHA-256 compared before and after, then hash is unchanged (`AC-02.2`).

## Story 5.2 — Egress whitelist

**Status:** Ready for review — not yet run through `implement-story`  
**As a** CISO, **I want** control guest outbound traffic, **so that** only approved internal endpoints are reachable.

**Acceptance Criteria:**
- Given active guest, when connection targets public internet, then it is dropped (`AC-02.3`).
- Given SQL, PostgreSQL, private blob, DNS, and Kerberos to approved endpoints, then connections are allowed.

## Story 5.3 — Discard and reproduce

**Status:** Ready for review — not yet run through `implement-story`  
**As a** SecOps Engineer, **I want** end a session by two discard paths, **so that** the next session does not inherit the previous disk.

**Acceptance Criteria:**
- Given Path A whole-guest removal, when next guest is provisioned, then parent is approved production image (`BEN-12`).
- Given Path B `.avhdx` only, when next session starts, then parent is still approved production image and guest may remain.

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
