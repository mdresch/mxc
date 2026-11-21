---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification (Phase 2)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
spark_id: "SPARK-MXC-Phase2-vNext"
inputs:
  - "docs/project-docs/Intent-Refinement-Proposal.md"
  - "docs/registers/Continuous-Improvement-Register.md"
  - "docs/reports/Executive-Summary-Sub-ms-Resume-and-Bake-RAM-Optimization.docx"
process: "Capture Phase 2 strategic catalysts, high-density host architecture, and predictive execution fabric"
outputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
status: "Draft / Ready for Approval"
---

# Spark Capture — Phase 2: Predictive Orchestration, Memory Deduplication & Enterprise Execution Fabric

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification (Phase 2)` (Initiating)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Inputs:** [Intent-Refinement-Proposal.md](Intent-Refinement-Proposal.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md), [Executive-Summary-Report.pdf](../reports/Executive-Summary-Sub-ms-Resume-and-Bake-RAM-Optimization.pdf)  
> **Process:** Capture Phase 2 strategic catalysts, high-density host architecture, and predictive execution fabric  
> **Outputs:** Spark-Capture-Phase-2.md

**Date:** 2026-11-21  
**Captured by:** Menno Drescher  
**Project Name:** MXC Phase 2 — Micro-Execution Platform vNext  
**Preceding Lineage:** Phase 1 (`PMP-BL-v1.0.0` / Epics 001..006 Complete)  

---

## 1. Problem Statement & Strategic Motivation

Phase 1 established the core virtualization engine: Type-1 Hyper-V Gen2 VM isolation, JIT connection-buffering reverse proxy, clean production base image baking, sub-300ms paused RAM resume, transient differencing disk session sterility, and watermark pool replenishment.

While Phase 1 proved that a single paused standby instance can wake in under 300 ms with 0.0% idle CPU and ~1.0–1.2 GB RAM, deploying hundreds of isolated micro-instances across high-density enterprise host clusters introduces a second-generation challenge:
1. **Perceived Wake Latency vs. True Zero Wake:** 215–280 ms TTFB is fast, but real-time interactive enterprise workloads require 0 ms perceived wake latency.
2. **Physical Host Memory Saturation:** Scaling past 50–80 guests per 64 GB host exhausts physical RAM unless host-level memory deduplication and aggressive golden image compression floors are introduced.
3. **Multi-Tenancy Economics:** Treating all tenants equally in a single paused standby pool is economically inefficient; frequent tenants demand hot execution, whereas periodic tenants should sleep in cold saved states.
4. **Supply Chain Attestation:** Enterprise compliance demands an unbroken, cryptographically signed chain of custody (SLSA Level 3) from source repository to golden image snapshot.

---

## 2. Phase 2 Strategic Catalysts (Top 5 Architectural Pillars)

Derived from empirical outcomes (`OUTCOME-Phase-1-Actual-Outcomes.md`), the Continuous Improvement Register (`IMP-MXC-001`..`013`), and peer architectural reviews:

1. **Multi-Tier Standby Pool Hierarchy (`IMP-MXC-007` / `HYP-mxc-016`):**
   - **Hot Tier:** Running standby instances ($< 5\text{ ms}$ immediate dispatch) for frequent tenants.
   - **Warm Tier:** Paused RAM standby instances ($\approx 200\text{ ms}$ unpause) for standard active workloads.
   - **Cold Tier:** Saved VM disk checkpoints ($2\text{--}5\text{ s}$ resume, 0 MB host RAM) for periodic/rare tenants.
2. **Activity-Based Predictive Wake Engine (`IMP-MXC-008` / `IMP-MXC-002` / `IMP-MXC-013`):**
   - Combines early TLS ClientHello/SNI interception with historical machine-learning forecasting (time-of-day, shift schedule, user identity, scheduled batch triggers) to pre-warm instances 60 seconds before traffic bursts, delivering **0 ms perceived wake latency**.
3. **Hyper-V Host-Level Memory Combining & Page Deduplication (`IMP-MXC-009` / `IMP-MXC-006`):**
   - Leverages Hyper-V Page Sharing across identical Windows Server 2025 kernel (`ntoskrnl.exe`), .NET runtime, user32, and CLR binaries across 80+ fleet instances.
   - Compresses physical host consumption from 640–1024 MB down to **300–450 MB effective RAM per guest**, doubling practical host tenant density (120–160 micro-instances per 64 GB host).
4. **End-to-End Cryptographic Supply Chain & SLSA Attestation (`IMP-MXC-010` / `IMP-MXC-003`):**
   - Unbroken cryptographic chain of custody: Source Git commit $\rightarrow$ GitHub Actions/Azure DevOps Build $\rightarrow$ CycloneDX/SPDX SBOM $\rightarrow$ Image SHA-256 Digest $\rightarrow$ Sigstore/Cosign Signature $\rightarrow$ Runtime `PoolRegistrationGuard` Verification Gate.
5. **Autonomous Fleet Economics & Dynamic Sizing Scheduler (`IMP-MXC-011` / `IMP-MXC-004`):**
   - Continuous multi-tenant feedback control loop dynamically sizing Hot/Warm/Cold tier depth, managing eviction/reaping policies, and optimizing cost-per-session, host saturation, and resource margins.

---

## 3. High-Level Work Breakdown Structure (Phase 2 Candidate WBS)

- **WBS 8.0:** Multi-Tier Standby Pool Hierarchy (Hot / Warm / Cold).
- **WBS 9.0:** Predictive Wake Engine (Early TLS & Temporal Forecasting).
- **WBS 10.0:** Hyper-V Memory Combining & Host-Level Deduplication.
- **WBS 11.0:** Cryptographic Supply Chain & SLSA Image Attestation Pipeline.
- **WBS 12.0:** Autonomous Fleet Economics & Dynamic Sizing Controller.
- **WBS 13.0:** Ultra-Lean Golden Bake Memory Compression Floor (~512–640 MB).
- **WBS 14.0:** Pure In-Memory Ephemeral RAM-Disk Differencing Layers (`HYP-mxc-019`).
