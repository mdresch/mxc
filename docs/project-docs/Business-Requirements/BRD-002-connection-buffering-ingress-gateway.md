---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-002-*.md"
  - "Project-Management-Plan.md"
process: "Define functional and non-functional business requirements and stakeholder rules"
outputs:
  - "BRD-002-*.md"
---

# BRD-002: Connection-buffering ingress gateway

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md), suite [BDR.md](../../hyperv/architecture/BDR.md) (BDR-02)  
> **Process:** Define functional and non-functional business requirements and stakeholder rules  
> **Outputs:** BRD-002-connection-buffering-ingress-gateway.md

**Source ADR:** [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md) — Accepted (`approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`)).  
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-brd` accepted `approve_brd` on 2026-10-30 (policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). Gate record: [approve-brd-002-2026-10-30.adjudication.json](../gates/approve-brd-002-2026-10-30.adjudication.json).
**Stakeholders:** Menno Drescher (product owner / architect); SecOps and SRE consumers named in suite user stories.

## Business Need

Callers send ordinary HTTPS while guests are Paused. The business requires sub-second response without cold-boot waits and without wake-caused gateway failures.

## Business Rules (BRU)

- **BRU-002-01**: The gateway holds the client request while the target guest is Paused. *(from ADR-002 §4.2)*
- **BRU-002-02**: First byte from a Paused guest arrives within 800 ms; warm traffic is measured separately. *(from ADR-002 §4.3)*
- **BRU-002-03**: Path and listen-port routing both apply; the check records which rule fired. *(from ADR-002 §4.5)*
- **BRU-002-04**: Wake does not produce HTTP 502 or 504; HTTP 503 after wake timeout is a different case. *(from ADR-002 §4.4)*
- **BRU-002-05**: Username, password, and a second factor use the same wake; typing time is outside the ceilings. *(from ADR-002 §4.6)*

## Stakeholder Success Metrics

| Metric | Current state |
|---|---|
| Cold TTFB from Paused guest | Formulated (`HYP-mxc-003`); ≤ 800 ms ceiling in `AC-01.1` |
| Resume-VM duration included in TTFB path | Owned by `ADR-004`; ≤ 300 ms in `AC-03.3` |
| Second-factor product for sign-in scripts | Unnamed; `BEN-06` cannot be scripted yet |

## Traceability to architecture suite

- Requirements matrix: `REQ-BDR-01` in [BDR.md](../../hyperv/architecture/BDR.md).
- Primary user story anchor: `US-01` in [USER_STORIES.md](../../hyperv/architecture/USER_STORIES.md).

## Out of Scope

- 300 ms `Resume-VM` measurement (`ADR-004`).
- Kerberos whitelist details (`ADR-005`).
- Clock step before sign-in (`ADR-006`).
