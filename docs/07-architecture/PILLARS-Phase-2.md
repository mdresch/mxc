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
process: "Define Phase 2 topic pillars (TP-07 through TP-11) and establish high-level architectural coverage for predictive orchestration and fleet economics"
outputs:
  - "docs/07-architecture/PILLARS-Phase-2.md"
---

# Pillars Exercise — Phase 2: Predictive Orchestration & Enterprise Execution Fabric

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 5 (Pillars & Architecture)`  
> **Inputs:** [Project-Charter-Phase-2.md](../project-docs/Project-Charter-Phase-2.md), [Ideation-Document-Phase-2.md](../project-docs/Ideation-Document-Phase-2.md), [Benefits-Statement-Phase-2.md](../project-docs/Benefits-Statement-Phase-2.md)  
> **Outputs:** PILLARS-Phase-2.md, Pillar-to-ADR Coverage Matrix (Phase 2)

---

## 1. Executive Purpose

Phase 2 decomposes the next-generation micro-execution architecture into five mutually exclusive, collectively exhaustive (MECE) Topic Pillars (**TP-07** through **TP-11**). These pillars govern the architectural evolution from isolated paused micro-instances to an intelligent, high-density execution fabric.

---

## 2. Phase 2 Topic Pillars (TP-07 through TP-11)

### Topic Pillar 7: TP-07 Multi-Tier Standby Pools
- **Domain Focus:** Differentiated capacity tiering (Hot, Warm, Cold) and tenancy tiering.
- **Key Architectural Responsibilities:**
  - Hot tier ($< 5\text{ ms}$ dispatch) running standby instances for frequent tenants.
  - Warm tier ($\approx 200\text{ ms}$ unpause) paused RAM instances for standard workloads.
  - Cold tier ($2\text{--}4\text{ s}$ resume, 0 MB host RAM) disk checkpoint instances for rare tenants.
- **Governing ADR:** `ADR-009-multi-tier-standby-pools.md`

### Topic Pillar 8: TP-08 Predictive Wake & Forecasting
- **Domain Focus:** Zero perceived wake latency through early network frame snooping and temporal workload forecasting.
- **Key Architectural Responsibilities:**
  - Early TLS ClientHello / SNI parser triggering background unpause during handshake.
  - Time-series activity forecasting modeling tenant shift schedules, cron triggers, and historical usage.
  - Pre-warming standby instances $\ge 60\text{ seconds}$ before anticipated traffic bursts.
- **Governing ADR:** `ADR-010-predictive-wake-interception.md`

### Topic Pillar 9: TP-09 Host Memory Deduplication
- **Domain Focus:** Cross-fleet physical memory consolidation and page sharing.
- **Key Architectural Responsibilities:**
  - Hyper-V Memory Combining / Page Sharing across identical Windows Server 2025 micro-VMs.
  - Deduplicating read-only kernel (`ntoskrnl.exe`), .NET CLR, and system libraries.
  - Achieving 300–450 MB effective host physical RAM per paused guest.
- **Governing ADR:** `ADR-011-hyperv-memory-combining-deduplication.md`

### Topic Pillar 10: TP-10 Cryptographic Supply Chain
- **Domain Focus:** Build-to-runtime verification, SLSA Level 3 provenance, and tamper prevention.
- **Key Architectural Responsibilities:**
  - CycloneDX / SPDX SBOM generation during deterministic golden image baking.
  - Sigstore / Cosign cryptographic image signing and certificate transparency logging.
  - Runtime `PoolRegistrationGuard` enforcing cryptographic validation prior to instance pooling.
- **Governing ADR:** `ADR-012-cryptographic-supply-chain-slsa.md`

### Topic Pillar 11: TP-11 Fleet Economics & Scheduling
- **Domain Focus:** Autonomous dynamic sizing, host saturation balancing, and multi-tenant resource optimization.
- **Key Architectural Responsibilities:**
  - Closed-loop telemetry feedback controller monitoring host memory pressure and wake queues.
  - Dynamic watermark autotuning ($K_{\min}, K_{\max}$) per tier based on velocity and volatility.
  - Cooldown reaping, idle lease eviction, and NUMA-aware instance placement.
- **Governing ADR:** `ADR-013-autonomous-fleet-economics-scheduler.md`

---

## 3. Phase 2 Pillar-to-ADR Coverage Matrix

| Pillar ID | Pillar Name | Governing ADR | Target Epics / Work Packages | Status |
|---|---|---|---|:---:|
| **TP-07** | Multi-Tier Standby Pools | `ADR-009` | Epic 007 (WBS 8.0) | Planned |
| **TP-08** | Predictive Wake & Forecasting | `ADR-010` | Epic 008 (WBS 9.0) | Planned |
| **TP-09** | Host Memory Deduplication | `ADR-011` | Epic 009 (WBS 10.0) | Planned |
| **TP-10** | Cryptographic Supply Chain | `ADR-012` | Epic 010 (WBS 11.0) | Planned |
| **TP-11** | Fleet Economics & Scheduling | `ADR-013` | Epic 011 (WBS 12.0) | Planned |
