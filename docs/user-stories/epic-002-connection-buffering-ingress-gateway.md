---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md"
  - "docs/project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md"
  - "docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md"
process: "Decompose solution requirements into testable user stories with explicit acceptance criteria"
outputs:
  - "docs/user-stories/epic-002-connection-buffering-ingress-gateway.md"
---

# Epic 002: Connection-buffering ingress gateway

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 7 (Requirement: Story)`  
> **Inputs:** [FDD-002](../project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md), [BRD-002](../project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md), [ADR-002](../07-architecture/ADR-002-connection-buffering-ingress-gateway.md)  
> **Process:** Decompose solution requirements into testable user stories with explicit acceptance criteria  
> **Outputs:** epic-002-connection-buffering-ingress-gateway.md

**Source ADR:** [ADR-002](../07-architecture/ADR-002-connection-buffering-ingress-gateway.md) — Accepted.  
**Source BRD/FDD:** [BRD-002](../project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md) — Approved (2026-10-30) / [FDD-002](../project-docs/Functional-Design/FDD-002-connection-buffering-ingress-gateway.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-user-stories` accepted `approve_user_stories` on 2026-10-30 (policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). Gate record: [approve-user-stories-002-2026-10-30.adjudication.json](../project-docs/gates/approve-user-stories-002-2026-10-30.adjudication.json).
**Suite anchor:** [US-01](../hyperv/architecture/USER_STORIES.md) in the monolith user-story document.

## Story 2.1 — Cold wake TTFB

**WBS ID:** `1.2.1`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Enterprise Automation Operator, **I want** POST to ADPA/SIDPA while the guest is Paused, **so that** I receive the first byte without a cold boot.

**Acceptance Criteria:**
- Given target VM Paused, when POST arrives, then gateway holds, wakes, and first byte ≤ 800 ms (`AC-01.1`).
- Given VM Running, when subsequent requests arrive, then proxy overhead ≤ 5 ms plus app time (`AC-01.2`).

## Story 2.2 — No wake-caused 502/504

**WBS ID:** `1.2.2`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** Enterprise Automation Operator, **I want** send HTTPS during wake, **so that** I do not see gateway 502 or 504 caused by wake latency.

**Acceptance Criteria:**
- Given normal conditions, when the guest wakes, then response is not HTTP 502 or 504 because of wake (`AC-01.3`, `BEN-03`).
- Given wake exceeds wake_timeout_ms, when timer fires, then HTTP 503 with Retry-After is returned.

## Story 2.3 — Dual routing rules

**WBS ID:** `1.2.3`  
**Status:** Ready for review — not yet run through `implement-story`  
**As a** DevOps Engineer, **I want** route by path and by catalogued listen port, **so that** the request reaches the owning image.

**Acceptance Criteria:**
- Given path `/api/v1/adpa`, when leased, then pool is `prod-adpa` and the check records path routing (`HYP-mxc-004`).
- Given listen port `:8091`, when accepted, then image is the catalogued ADPA PoC image and the check records port routing.

## Before running `implement-story`

Run `validate-intent-foundation` when the project enables it. Document approval and pipeline readiness are separate gates (`approve-brd`, `approve-fdd`, `approve-user-stories`).
