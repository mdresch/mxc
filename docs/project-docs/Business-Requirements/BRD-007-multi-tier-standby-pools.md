---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-009-multi-tier-standby-pools.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/user-stories/epic-007-multi-tier-standby-pools.md"
process: "Define business requirements, SLA tiers, and operational rules for multi-tier standby pools"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-007-multi-tier-standby-pools.md"
status: "Approved"
---

# BRD-007: Multi-Tier Standby Pools (Hot, Warm, Cold)

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 2)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md), [Project-Charter-Phase-2.md](../Project-Charter-Phase-2.md), [Benefits-Statement-Phase-2.md](../Benefits-Statement-Phase-2.md)  
> **Process:** Define business requirements, SLA tiers, and operational rules  
> **Outputs:** BRD-007-multi-tier-standby-pools.md

**Source ADR:** [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md) — Multi-Tier Standby Pool Hierarchy  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved  
**Stakeholders:** Menno Drescher (Product Owner / Architect), Enterprise Tenant SREs, Capacity Planners  

---

## 1. Business Need

Treating every tenant identically in a single paused standby pool is economically inefficient. High-priority interactive tenants demand immediate dispatch ($< 5\text{ ms}$), while batch and periodic tenants unnecessarily consume host memory if held in paused RAM. Multi-tier standby pools partition capacity across Hot, Warm, and Cold states to optimize infrastructure costs, enforce tenant SLAs, and double practical tenant density.

---

## 2. Business Rules (BRU)

- **BRU-007-01 (Tier Differentiation):** The platform must partition standby instance inventory across three distinct states:
  - **Hot (Running):** Immediate dispatch ($\le 5\text{ ms}$ TTFB) for Platinum SLA tenants.
  - **Warm (Paused):** Sub-second unpause ($\le 250\text{ ms}$ TTFB) for Gold SLA tenants.
  - **Cold (Saved VM Checkpoint):** On-demand disk restore ($\le 4.0\text{ s}$) consuming 0.0 MB host RAM for Silver / Batch tenants.
- **BRU-007-02 (Capacity Distribution Ratios):** Standby fleet allocation must dynamically target:
  - 5% to 10% Hot instances.
  - 20% to 30% Warm instances.
  - 60% to 75% Cold saved state instances.
- **BRU-007-03 (Tenant Tier Mapping):** Incoming requests must be classified at the ingress proxy based on authenticated tenant metadata and routed to the corresponding standby tier.
- **BRU-007-04 (Dynamic Promotion):** Anticipated or surging tenant demand must trigger asynchronous promotion from Cold to Warm without blocking concurrent traffic.
- **BRU-007-05 (Idle Demotion):** Instances in `WarmPaused` exceeding the configured idle threshold ($\ge 600\text{ s}$) must demote to `ColdSaved` to release physical host RAM.

---

## 3. Stakeholder Success Metrics

| Metric | Business Target | Baseline Reference |
|---|---|---|
| **Hot Dispatch TTFB** | $\le 5\text{ ms}$ | `BEN-17` / `AC-7.2.1` |
| **Warm Resume TTFB** | $\le 250\text{ ms}$ | `BEN-17` / `AC-7.2.2` |
| **Cold Checkpoint Restore** | $\le 4.0\text{ s}$ | `BEN-17` / `AC-7.2.3` |
| **Fleet Host Density** | $\ge 120$ micro-VMs per 64 GB host | `BEN-15` |
| **Idle Memory Savings** | $\ge 40\%$ host RAM reduction vs. all-warm | `HYP-mxc-015` |

---

## 4. Traceability

- **Topic Pillar:** `TP-07` Multi-Tier Standby Pools
- **Architectural Decision:** [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md)
- **User Story Epic:** [epic-007-multi-tier-standby-pools.md](../../user-stories/epic-007-multi-tier-standby-pools.md) (WBS 8.0)
- **Hypotheses:** `HYP-mxc-015`

---

## 5. Out of Scope

- Time-series workload forecasting (`BRD-008`).
- Hypervisor-level page sharing deduplication (`BRD-009`).
- Cryptographic image provenance attestation (`ADR-012`).
