---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Architectural Strategy Formulation (Phase 2)"
lifecycle_stage: "Stage 5 (Pillars & Architecture)"
governance_policy: "approve-adr"
status: "Approved"
inputs:
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/ADR-008-authentication-gated-session-provisioning.md"
  - "docs/07-architecture/ADR-009-multi-tier-standby-pools.md"
  - "docs/07-architecture/ADR-010-predictive-wake-interception.md"
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
process: "Define Phase 2 topic pillars (TP-07 through TP-11), trace ADR-008 through ADR-011, and establish full requirements coverage to BRDs, FDDs, and Epics"
outputs:
  - "docs/07-architecture/PILLARS-Phase-2.md"
---

# Pillars Exercise — Phase 2: Predictive Orchestration & Enterprise Execution Fabric

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 5 (Pillars & Architecture)`  
> **Inputs:** [Project-Charter-Phase-2.md](../project-docs/Project-Charter-Phase-2.md), [Ideation-Document-Phase-2.md](../project-docs/Ideation-Document-Phase-2.md), [Benefits-Statement-Phase-2.md](../project-docs/Benefits-Statement-Phase-2.md), ADR-008..011  
> **Outputs:** PILLARS-Phase-2.md, Full-Traceability Architecture Matrix (Phase 2)

---

## 1. Executive Purpose & Scope

Phase 2 advances the MXC Micro-Execution Platform from an isolated standby micro-VM foundation (`PMP-BL-v1.0.0`) into an intelligent, high-density, multi-tenant enterprise execution fabric (`PMP-BL-v2.0.0`). 

To maintain strict architectural governance, all strategic catalysts and work packages are structured across five new Topic Pillars (**TP-07** through **TP-11**), while incorporating the security and authentication leasing model established in **`ADR-008`**.

---

## 2. Topic Pillars & Architectural Coverage (Phase 2)

### Topic Pillar 7: TP-07 Multi-Tier Standby Pools
- **Domain Focus:** Differentiated capacity tiering (Hot, Warm, Cold) and tenancy tiering.
- **Key Architectural Responsibilities:**
  - Hot tier ($< 5\text{ ms}$ dispatch) running standby instances for frequent tenants.
  - Warm tier ($\approx 200\text{ ms}$ unpause) paused RAM instances for standard workloads.
  - Cold tier ($2\text{--}4\text{ s}$ resume, 0 MB host RAM) disk checkpoint instances for rare tenants.
- **Governing Architecture:** [ADR-009-multi-tier-standby-pools.md](ADR-009-multi-tier-standby-pools.md)
- **Requirements Chain:** [BRD-007](../project-docs/Business-Requirements/BRD-007-multi-tier-standby-pools.md) $\rightarrow$ [FDD-007](../project-docs/Functional-Design/FDD-007-multi-tier-standby-pools.md) $\rightarrow$ [Epic 007](../user-stories/epic-007-multi-tier-standby-pools.md) (WBS 8.0)

### Topic Pillar 8: TP-08 Predictive Wake & Forecasting
- **Domain Focus:** Zero perceived wake latency through early network frame snooping and temporal workload forecasting.
- **Key Architectural Responsibilities:**
  - Early TLS `ClientHello` / SNI parser triggering background unpause during handshake.
  - Time-series activity forecasting modeling tenant shift schedules, cron triggers, and historical usage.
  - Pre-warming standby instances $\ge 60\text{ seconds}$ before anticipated traffic bursts.
- **Governing Architecture:** [ADR-010-predictive-wake-interception.md](ADR-010-predictive-wake-interception.md)
- **Requirements Chain:** [BRD-008](../project-docs/Business-Requirements/BRD-008-predictive-wake-forecasting.md) $\rightarrow$ [FDD-008](../project-docs/Functional-Design/FDD-008-predictive-wake-forecasting.md) $\rightarrow$ [Epic 008](../user-stories/epic-008-predictive-wake-forecasting.md) (WBS 9.0)

### Topic Pillar 9: TP-09 Host Memory Deduplication
- **Domain Focus:** Cross-fleet physical memory consolidation and page sharing.
- **Key Architectural Responsibilities:**
  - Hyper-V Memory Combining / Page Sharing across identical Windows Server 2025 micro-VMs.
  - Deduplicating read-only kernel (`ntoskrnl.exe`), .NET CLR, and system libraries.
  - Achieving 300–450 MB effective host physical RAM per paused guest.
- **Governing Architecture:** [ADR-011-hyperv-memory-combining-deduplication.md](ADR-011-hyperv-memory-combining-deduplication.md)
- **Requirements Chain:** [BRD-009](../project-docs/Business-Requirements/BRD-009-memory-combining-deduplication.md) $\rightarrow$ [FDD-009](../project-docs/Functional-Design/FDD-009-memory-combining-deduplication.md) $\rightarrow$ [Epic 009](../user-stories/epic-009-memory-combining-deduplication.md) (WBS 10.0)

### Cross-Cutting Security Enhancement: ADR-008 Identity-Bound Ingress
- **Domain Focus:** Authentication-gated session provisioning, OIDC assertion verification, and identity-bound VM leasing.
- **Key Architectural Responsibilities:**
  - Hold incoming connection until user proves identity via enterprise IdP.
  - Lease VM only upon valid authentication; route based on claims.
  - Provide opt-in identity-to-VM binding for personalized interactive desktops.
- **Governing Architecture:** [ADR-008-authentication-gated-session-provisioning.md](ADR-008-authentication-gated-session-provisioning.md) (touches `TP-02` Ingress and `TP-05` Session Sterility).

### Topic Pillar 10: TP-10 Cryptographic Supply Chain (Future Horizon)
- **Domain Focus:** Build-to-runtime verification, SLSA Level 3 provenance, and tamper prevention.
- **Governing Architecture:** `ADR-012-cryptographic-supply-chain-slsa.md` (WBS 11.0 / Epic 010)

### Topic Pillar 11: TP-11 Fleet Economics & Scheduling (Future Horizon)
- **Domain Focus:** Autonomous dynamic sizing, host saturation balancing, and multi-tenant resource optimization.
- **Governing Architecture:** `ADR-013-autonomous-fleet-economics-scheduler.md` (WBS 12.0 / Epic 011)

---

## 3. End-to-End Traceability Matrix (Pillars $\rightarrow$ ADRs $\rightarrow$ BRDs $\rightarrow$ FDDs $\rightarrow$ Epics)

The table below details the full alignment across the architecture and requirements hierarchy:

| Topic Pillar | Architecture Decision (ADR) | Business Requirements (BRD) | Functional Design (FDD) | User Story Epic (Backlog) | WBS Index | Target Status |
|---|---|---|---|---|:---:|:---:|
| **TP-02 / TP-05** | [ADR-008](ADR-008-authentication-gated-session-provisioning.md) (Auth Gate) | [BRD-012](../project-docs/Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md) | [FDD-012](../project-docs/Functional-Design/FDD-012-auth-gated-identity-bound-leasing.md) | [Epic 012](../user-stories/epic-012-auth-gated-identity-bound-leasing.md) | 3.4 / 13.0 | Approved — Ready for Implementation |
| **TP-07** | [ADR-009](ADR-009-multi-tier-standby-pools.md) (Multi-Tier) | [BRD-007](../project-docs/Business-Requirements/BRD-007-multi-tier-standby-pools.md) | [FDD-007](../project-docs/Functional-Design/FDD-007-multi-tier-standby-pools.md) | [Epic 007](../user-stories/epic-007-multi-tier-standby-pools.md) | 8.0 | Complete |
| **TP-08** | [ADR-010](ADR-010-predictive-wake-interception.md) (Predictive Wake) | [BRD-008](../project-docs/Business-Requirements/BRD-008-predictive-wake-forecasting.md) | [FDD-008](../project-docs/Functional-Design/FDD-008-predictive-wake-forecasting.md) | [Epic 008](../user-stories/epic-008-predictive-wake-forecasting.md) | 9.0 | Complete |
| **TP-09** | [ADR-011](ADR-011-hyperv-memory-combining-deduplication.md) (Page Sharing) | [BRD-009](../project-docs/Business-Requirements/BRD-009-memory-combining-deduplication.md) | [FDD-009](../project-docs/Functional-Design/FDD-009-memory-combining-deduplication.md) | [Epic 009](../user-stories/epic-009-memory-combining-deduplication.md) | 10.0 | Complete |
| **TP-10** | [ADR-012](ADR-012-cryptographic-supply-chain-slsa.md) (SLSA Provenance) | [BRD-010](../project-docs/Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md) | [FDD-010](../project-docs/Functional-Design/FDD-010-cryptographic-supply-chain-slsa.md) | [Epic 010](../user-stories/epic-010-cryptographic-supply-chain-slsa.md) | 11.0 | Complete |
| **TP-11** | [ADR-013](ADR-013-autonomous-fleet-economics-scheduler.md) (Fleet Economics) | [BRD-011](../project-docs/Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md) | [FDD-011](../project-docs/Functional-Design/FDD-011-autonomous-fleet-economics-scheduler.md) | [Epic 011](../user-stories/epic-011-autonomous-fleet-economics-scheduler.md) | 12.0 | Approved — Ready for Implementation |

---

## 4. Numbering Lineage & Reconciliation Note

- **Phase 1 Foundation:** Closed with Epics 001..006, BRD-001..006, FDD-001..006, and ADR-001..006.
- **ADR-008 Context:** `ADR-008` (Authentication-Gated Provisioning) was approved during Phase 1 as an opt-in ingress policy; because `ADR-007` was never allocated, `ADR-008` stood alone as a secondary security gate.
- **Phase 2 Work Packages:** Execution continues with sequential work package numbering:
  - **Epic 007 / BRD-007 / FDD-007** implements `ADR-009` (Multi-Tier Standby Pools).
  - **Epic 008 / BRD-008 / FDD-008** implements `ADR-010` (Predictive Wake Interception).
  - **Epic 009 / BRD-009 / FDD-009** implements `ADR-011` (Memory Combining & Deduplication).
