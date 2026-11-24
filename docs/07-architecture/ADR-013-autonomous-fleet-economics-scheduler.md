---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-11"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
  - "docs/07-architecture/ADR-009-multi-tier-standby-pools.md"
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Formulate architectural decisions for autonomous fleet-level economics, host RAM pressure feedback control, and dynamic Hot/Warm/Cold sizing"
outputs:
  - "docs/07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md"
status: "Approved"
---

# ADR 013: Autonomous Fleet Economics & Dynamic Sizing Scheduler

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-11` Fleet Economics & Scheduling. Also touches `TP-07` (Multi-Tier Pools) and `TP-09` (Host Memory Deduplication).  
> **Inputs:** [PILLARS-Phase-2.md](PILLARS-Phase-2.md), [ADR-009](ADR-009-multi-tier-standby-pools.md), [ADR-011](ADR-011-hyperv-memory-combining-deduplication.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md) (`IMP-MXC-004`, `IMP-MXC-011`, `IMP-MXC-020`)  
> **Outputs:** ADR-013-autonomous-fleet-economics-scheduler.md

---

## 1. Executive Summary

Epics 007–009 delivered static multi-tier standby pools (`HotRunning`, `WarmPaused`, `ColdSaved`), predictive wake forecasting, and Hyper-V host memory combining. However, static tier ratios (e.g. fixed 10% Hot / 30% Warm / 60% Cold) cannot adapt automatically to shifting tenant traffic economics or sudden host RAM commit pressure across heterogeneous workloads (e.g., 4 GB Desktop GUI guests vs. 2 GB lean headless agent guests).

`ADR-013` introduces an **Autonomous Fleet Economics & Dynamic Sizing Scheduler**: a closed-loop controller that continuously optimizes **cost-per-session**, **SLA wake latency compliance**, and **host physical RAM headroom**—dynamically adjusting Hot/Warm/Cold tier watermarks, enforcing archetype RAM floors, and shedding idle Warm RAM to Cold NVMe checkpoints before host commit saturation occurs.

---

## 2. Decision & Architectural Mechanics

1. **Closed-Loop Host RAM Pressure Autotuner (`IMP-MXC-004`):**
   - Continuously samples host committed physical RAM ratio (`host_ram_used_pct`) and Hyper-V Memory Combining effective RAM (`ADR-011`).
   - Enforces three pressure bands:
     - **Normal (`< 75%` host RAM):** Optimize for SLA speed and predictive pre-warming (`ADR-010`).
     - **Elevated (`75%–85%` host RAM):** Halt non-critical Cold→Warm promotions and tighten Warm→Cold idle demotion cooldowns by 50%.
     - **Critical (`> 85%` host RAM):** Shed lowest-priority idle `WarmPaused` guests to `ColdSaved` (0.0 MB RAM) while strictly protecting `K_min` Platinum Hot slots and active sessions.
2. **Economic Cost-vs-SLA Objective Function (`IMP-MXC-011`):**
   - Computes per-pool effective cost-per-session using RAM-GB-hours, active vCPU-seconds, and SLA breach penalty weights.
   - Rebalances tier target ratios (`hot_target`, `warm_target`, `cold_target`) within operator-configured min/max guardrails.
3. **Archetype-Aware Sizing Floor Enforcement (`IMP-MXC-020`):**
   - Respects per-image minimum sizing profiles (`desktop_gui`: 4 GB static RAM / 4 vCPU floor; `lean_agent`: 2 GB RAM / 2 vCPU; `server_core`: 1–2 GB RAM) so the scheduler never starves a guest into `MemoryStatus: Low` display/execution stalls.
4. **Deterministic Hysteresis & Anti-Thrash Bounds:**
   - Every promotion/demotion decision enforces a minimum dwell window (`min_dwell_seconds >= 60s`) so the fleet never oscillates rapidly between Warm and Cold under noisy telemetry.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Static operator-configured tier percentages | Over-provisions RAM during overnight/weekend troughs and risks host swapping during concurrent multi-tenant bursts. |
| Rely exclusively on Hyper-V Dynamic Memory ballooning | Aggressive guest ballooning below OS floor causes silent VMConnect stalls (`MemoryStatus: Low`) and page-file thrashing on wake, breaking `< 250 ms` warm SLAs. |
| Black-box reinforcement learning controller | Unpredictable behavior in regulated EU environments; deterministic closed-loop economics with auditable cost weights and hard guardrails is explainable and certifiable. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Prevents host OOM/swapping at 120+ micro-VM density, maximizes FinOps cost-per-session efficiency, and guarantees Platinum SLA protection under pressure (`BEN-01`, `BEN-10`, `BEN-15`).
- **Negative:** Under sustained `> 85%` host pressure, Silver/Batch tenants experience Cold-tier wake latency (2–4s) instead of Warm (~215ms).
- **Mitigation:** Pressure shedding strictly follows SLA priority order (Silver → Gold → never active or `K_min` Platinum Hot) and emits structured capacity-exhaustion alerts for cluster scale-out.
