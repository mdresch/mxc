---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-001-type-1-hyperv-generation-2.md"
  - "docs/project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md"
  - "docs/07-architecture/ADR-001-type-1-hyperv-generation-2.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-001-type-1-hyperv-generation-2.md"
---

# Epic 001: Type-1 Hyper-V Generation 2 instead of a container namespace

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 7 (Requirement: Story)`  
> **Inputs:** [FDD-001](../project-docs/Functional-Design/FDD-001-type-1-hyperv-generation-2.md), [BRD-001](../project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md), [ADR-001](../07-architecture/ADR-001-type-1-hyperv-generation-2.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-001-type-1-hyperv-generation-2.md

**Source ADR:** [ADR-001](../07-architecture/ADR-001-type-1-hyperv-generation-2.md) — Accepted.  
**Source BRD/FDD:** [BRD-001](../project-docs/Business-Requirements/BRD-001-type-1-hyperv-generation-2.md) — Approved (2026-10-30) / [FDD-001](../project-docs/Functional-Design/FDD-001-type-1-hyperv-generation-2.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-001-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-001-2026-10-30.adjudication.json).

## Story 1.1 — Generation 2 isolation boundary

**WBS ID:** `1.1.1`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Platform Engineer, **I want** provision ADPA and SIDPA on Generation 2 Hyper-V guests, **so that** confidential workloads never share the host kernel.

**Acceptance Criteria:**
- Given a new pool member, when provisioned, then Hyper-V reports Generation 2 and a guest kernel distinct from the host.
- Given a shared-kernel container proposal for the same records, when evaluated against this epic, then it is rejected with reference to `BRU-001-02`.

## Story 1.2 — Windows subsystems on the guest

**WBS ID:** `1.1.2`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Software Release Engineer, **I want** run WMI, COM+, a Windows service, and Group Policy inside the guest, **so that** legacy Windows automation required by ADPA/SIDPA remains in scope.

**Acceptance Criteria:**
- Given the Generation 2 guest from Story 1.1, when each named subsystem is invoked, then the call succeeds in the guest.
- Given the same calls attempted in a container namespace baseline, then they fail or are unsupported, and the difference is recorded for `BEN-05`.

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
