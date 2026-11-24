---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md"
  - "docs/project-docs/Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md"
  - "docs/project-docs/Functional-Design/FDD-011-autonomous-fleet-economics-scheduler.md"
process: "Decompose autonomous fleet economics, host RAM pressure autotuning, and archetype sizing enforcement into testable user stories"
outputs:
  - "docs/user-stories/epic-011-autonomous-fleet-economics-scheduler.md"
status: "Closed / Implemented & Validated"
---

# Epic 011: Autonomous Fleet Economics & Dynamic Sizing Scheduler

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 2)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-013](../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md)  
> **Target Baseline:** `PMP-BL-v2.0.0` | **WBS Index:** 12.0 | **Topic Pillar:** `TP-11`  
> **Status:** Closed / Implemented & Validated (2026-11-24)

---

## Story 11.1 — Host RAM Pressure Autotuner & Anti-Thrash Hysteresis Controller
- **WBS:** 12.1
- **Status:** Implemented & Validated
- **As a** Platform Operations Engineer,  
  **I want** a closed-loop pressure autotuner that monitors host physical RAM utilization and sheds idle lower-priority `WarmPaused` guests to `ColdSaved` above 85% commit while enforcing a 60-second anti-thrash dwell window,  
  **so that** high-density Hyper-V hosts never swap or starve Platinum tenants during burst traffic.
- **Acceptance Criteria:**
  - **AC-11.1.1:** `evaluate_fleet_rebalance()` classifies `<75%` as `NORMAL`, `75%–85%` as `ELEVATED`, and `>85%` as `CRITICAL`, shedding idle Warm guests to Cold under `CRITICAL` pressure while strictly preserving `target_hot >= platinum_k_min`.
  - **AC-11.1.2:** Non-critical tier oscillations within `min_dwell_seconds` (default `60s`) are suppressed to prevent NVMe checkpoint thrashing.

---

## Story 11.2 — Archetype Sizing Floor Guard & FinOps Cost-per-Session Estimator
- **WBS:** 12.2
- **Status:** Implemented & Validated
- **As a** FinOps & Capacity Lead,  
  **I want** image-archetype RAM/vCPU minimums enforced at provisioning time alongside deterministic cost-per-session telemetry per scheduling cycle,  
  **so that** desktop/agent VMs never stall from under-allocation and leadership can track exact unit economics across Hot, Warm, and Cold tiers.
- **Acceptance Criteria:**
  - **AC-11.2.1:** `validate_archetype_sizing()` rejects `desktop_gui` requests below `4096 MB` static RAM / `4` vCPUs (`ERR_ARCHETYPE_FLOOR_VIOLATION`) and accepts compliant `lean_agent` (`>= 2048 MB` / `>= 2` vCPUs) profiles.
  - **AC-11.2.2:** Each `RebalanceDecision` emits a deterministic `estimated_cost_per_session_eur` reflecting effective deduplicated RAM (`ADR-011`) and active tier ratios.
