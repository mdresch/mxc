---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-07"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
process: "Formulate architectural decisions for multi-tier standby pool hierarchy (Hot, Warm, Cold)"
outputs:
  - "docs/07-architecture/ADR-009-multi-tier-standby-pools.md"
status: "Approved"
---

# ADR 009: Multi-Tier Standby Pool Hierarchy (Hot, Warm, Cold)

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-07` Multi-Tier Standby Pools. Also touches `TP-04` and `TP-06`.  
> **Inputs:** [Spark-Capture-Phase-2.md](../project-docs/Spark-Capture-Phase-2.md), [Ideation-Document-Phase-2.md](../project-docs/Ideation-Document-Phase-2.md), [Benefits-Statement-Phase-2.md](../project-docs/Benefits-Statement-Phase-2.md)  
> **Outputs:** ADR-009-multi-tier-standby-pools.md

---

## 1. Executive Summary

Phase 1 treated all standby tenants identically within a single paused RAM state (`StandbyPaused`). Phase 2 introduces a three-tier standby hierarchy:
- **Hot Tier:** Running, actively scheduled standby instances delivering immediate dispatch ($\le 5\text{ ms}$) for critical, frequent tenants.
- **Warm Tier:** Paused RAM standby instances delivering $\approx 200\text{ ms}$ unpause for standard active workloads.
- **Cold Tier:** Saved VM disk checkpoints consuming **0 MB host RAM** and resuming in $2\text{--}4\text{ s}$ for periodic or rarely used tenants.

This architecture enables dynamic economic optimization, increasing practical tenant density on 64 GB host hardware from ~40 to $\ge 120$ micro-instances.

---

## 2. Decision & Architectural Mechanics

1. **State Machine Definition:**
   - `ColdSaved` $\longrightarrow$ Hyper-V Saved State checkpoint on NVMe differencing disk; 0 MB host RAM allocation; resume time 2.0–4.0 s.
   - `WarmPaused` $\longrightarrow$ Hyper-V `Suspend-VM` paused RAM state; 1024–1228 MB RAM allocation; 0.0% CPU; resume time 200–250 ms.
   - `HotRunning` $\longrightarrow$ Running VM in idle wait loop; minimal CPU; resume/dispatch time $\le 5\text{ ms}$.
   - `ActiveLeased` $\longrightarrow$ Leased to tenant session on transient child `.avhdx`.
2. **Tier Allocation Ratios:**
   - Fleet target distribution: **5–10% Hot**, **20–30% Warm**, and **60–75% Cold**.
   - Tenant classification engine maps incoming SLA tier (Platinum $\rightarrow$ Hot, Gold $\rightarrow$ Warm, Standard/Batch $\rightarrow$ Cold).
3. **Promotion & Demotion Lifecycle:**
   - Activity trigger promotes `ColdSaved` $\rightarrow$ `WarmPaused` in background ahead of scheduled work.
   - Idle timeout ($\ge 600\text{ s}$) demotes `WarmPaused` $\rightarrow$ `ColdSaved` to reclaim host RAM.

---

## 3. Consequences & Trade-Offs

- **Positive:** Reduces idle host RAM per provisioned tenant by $\ge 40\%$, enabling 2x–3x fleet density. Eliminates wake latency for high-priority tenants.
- **Negative:** Cold tier introduces a 2–4s latency penalty if an unexpected request arrives without predictive pre-warming.
- **Mitigation:** Paired with `ADR-010` (Predictive Wake Interception) to ensure Cold instances are restored before incoming client traffic lands.
