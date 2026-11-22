---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-009-multi-tier-standby-pools.md"
  - "docs/project-docs/Business-Requirements/BRD-007-multi-tier-standby-pools.md"
process: "Specify state machines, promotion/demotion algorithms, and pool controller interfaces for multi-tier standby pools"
outputs:
  - "docs/project-docs/Functional-Design/FDD-007-multi-tier-standby-pools.md"
status: "Approved"
---

# FDD-007: Multi-Tier Standby Pools (Hot, Warm, Cold)

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md), [BRD-007](../Business-Requirements/BRD-007-multi-tier-standby-pools.md)  
> **Process:** Specify state machines, promotion/demotion algorithms, and pool controller interfaces  
> **Outputs:** FDD-007-multi-tier-standby-pools.md

**Source ADR:** [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md) — Multi-Tier Standby Pool Hierarchy  
**Source BRD:** [BRD-007](../Business-Requirements/BRD-007-multi-tier-standby-pools.md)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved  

---

## 1. Technical Architecture & Interfaces

### 1.1 State Machine Extensions
The `PoolInstanceState` enumeration in `scripts/lib/watermark_pool.py` is extended to support five runtime states:

$$\begin{aligned}
\text{ColdProvisioned} &\longrightarrow \text{Differencing disk on NVMe (0.0 MB RAM)} \\
\text{ColdSaved} &\longrightarrow \text{Hyper-V Saved State checkpoint on disk (0.0 MB RAM)} \\
\text{WarmPaused} &\longrightarrow \text{Hyper-V Suspend-VM paused state (1024--1228 MB RAM, 0.0\% CPU)} \\
\text{HotRunning} &\longrightarrow \text{Running idle loop state (1024--1228 MB RAM, minimal CPU)} \\
\text{ActiveLeased} &\longrightarrow \text{Actively serving client request on transient child .avhdx}
\end{aligned}$$

### 1.2 Multi-Tier Pool Configuration Schema (`pool_config.json`)
```json
{
  "hot_pool_min": 1,
  "hot_pool_max": 3,
  "warm_pool_min": 2,
  "warm_pool_max": 5,
  "cold_pool_inventory": 20,
  "idle_demotion_seconds": 600,
  "tier_routing_rules": {
    "platinum": "HotRunning",
    "gold": "WarmPaused",
    "silver": "ColdSaved"
  }
}
```

### 1.3 State Transition Workflow
```
[ ColdSaved ]  ---( promotion / pre-warm )--->  [ WarmPaused ]  ---( promote to hot )--->  [ HotRunning ]
      |                                              |                                            |
      | (cold lease)                                 | (warm lease)                               | (hot lease: <= 5ms)
      v                                              v                                            v
[ ActiveLeased ] <----------------------------- [ ActiveLeased ] <------------------------ [ ActiveLeased ]
      |                                              |
      +-----( session teardown & discard )---------->+-----( idle >= 600s demotion )--------> [ ColdSaved ]
```

---

## 2. Algorithmic Logic & Methods

1. **`WatermarkPoolManager.lease_instance_tiered(tier: str) -> PoolInstance`**:
   - Evaluates tenant tier mapping.
   - If tier is `platinum`: selects and leases `HotRunning` instance ($\le 5\text{ ms}$). Triggers background promotion from `WarmPaused` to `HotRunning`.
   - If tier is `gold`: selects `WarmPaused` instance, calls `Resume-VM` ($\approx 200\text{ ms}$), promotes to `ActiveLeased`. Triggers background promotion from `ColdSaved` to `WarmPaused`.
   - If tier is `silver`: selects `ColdSaved` instance, restores from disk checkpoint ($2\text{--}4\text{ s}$), promotes to `ActiveLeased`.
2. **`WatermarkPoolManager.demote_idle_warm_instances() -> int`**:
   - Scans `WarmPaused` instances.
   - Any instance where `idle_duration >= idle_demotion_seconds` (600s) executes `Save-VM` and transitions to `ColdSaved`. Releases host RAM.

---

## 3. Error Handling & Invariants

| Condition | System Behavior |
|---|---|
| Requested tier has 0 ready instances | Automatically fall back to next available tier (`Hot` $\rightarrow$ `Warm` $\rightarrow$ `Cold`); log tier fallback telemetry. |
| Host physical RAM saturation $\ge 85\%$ | Block `ColdSaved` $\rightarrow$ `WarmPaused` promotion; aggressively demote idle Warm instances. |
| Session teardown failure | Mark instance `Quarantined`; purge child `.avhdx`; recreate pristine `ColdSaved` checkpoint. |
