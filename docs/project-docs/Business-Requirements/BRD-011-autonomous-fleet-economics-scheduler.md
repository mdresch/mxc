---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/user-stories/epic-011-autonomous-fleet-economics-scheduler.md"
process: "Define business requirements and FinOps guardrails for autonomous fleet economics, RAM pressure autotuning, and dynamic tier sizing"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md"
status: "Proposed"
---

# BRD-011: Autonomous Fleet Economics & Dynamic Sizing Scheduler

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 2)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-013](../../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md), [Project-Charter-Phase-2.md](../Project-Charter-Phase-2.md), [Benefits-Statement-Phase-2.md](../Benefits-Statement-Phase-2.md)  
> **Outputs:** BRD-011-autonomous-fleet-economics-scheduler.md

**Source ADR:** [ADR-013](../../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md) — Autonomous Fleet Economics & Dynamic Sizing Scheduler  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Proposed  
**Stakeholders:** Menno Drescher (Product Owner / Architect), FinOps Team, Platform Engineering, Enterprise Operations

---

## 1. Business Need

Operating multi-tenant Hyper-V standby fleets at scale requires balancing two competing pressures: **sub-second SLA responsiveness** for high-value tenants and **strict FinOps cost-per-session / RAM headroom control** across 64–256 GB hosts. Manual watermark tuning fails under real-world diurnal bursts and mixed Windows Server / Windows 11 workloads. An autonomous, auditable economics scheduler eliminates manual tuning while preventing host memory exhaustion and silent guest starvation.

---

## 2. Business Rules (BRU)

- **BRU-011-01 (Host RAM Pressure Protection):** When host physical RAM utilization exceeds **85%**, the scheduler MUST proactively demote idle lower-priority `WarmPaused` instances to `ColdSaved` (0.0 MB RAM) until utilization returns below **80%**, preventing host swapping.
- **BRU-011-02 (Priority SLA Preservation):** Pressure shedding MUST strictly preserve all active sessions and `K_min` Platinum `HotRunning` capacity, shedding Silver/Batch Warm buffers first and Gold second.
- **BRU-011-03 (Archetype Minimum Sizing Floor):** The scheduler MUST never shrink or provision any VM below its declared image-archetype RAM/vCPU floor (e.g., `4 GB` static RAM / `4` vCPU for Windows Desktop GUI; `2 GB` for lean headless agents).
- **BRU-011-04 (Anti-Thrash Hysteresis):** No instance may be promoted and demoted more than once within its configured minimum dwell window (`>= 60s`), preventing NVMe checkpoint thrashing.
- **BRU-011-05 (Auditable Cost-per-Session Telemetry):** Every scheduling cycle MUST emit structured FinOps metrics (`cost_per_session`, `ram_gb_hours`, `sla_hit_rate`, `shed_count`, `pressure_band`) for executive reporting.

---

## 3. Stakeholder Success Metrics

| Metric | Business Target | Baseline Reference |
|---|---|---|
| **Host OOM / Swap Incidents** | `0` under 120-VM burst load | `BEN-01` / `HYP-mxc-018` |
| **Platinum Hot SLA Hit Rate** | `>= 99.5%` (`<= 5 ms` dispatch) | `BEN-02` / `BEN-17` |
| **Idle RAM Waste Reduction** | `>= 30%` vs. static tier allocations | `BEN-01` / `BEN-10` |
| **Tier Thrash Rate** | `0` oscillations within 60s dwell window | `BEN-15` |

---

## 4. Traceability

- **Topic Pillar:** `TP-11` Fleet Economics & Scheduling
- **Architectural Decision:** [ADR-013](../../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md)
- **Functional Design:** [FDD-011](../Functional-Design/FDD-011-autonomous-fleet-economics-scheduler.md)
- **User Story Epic:** [epic-011-autonomous-fleet-economics-scheduler.md](../../user-stories/epic-011-autonomous-fleet-economics-scheduler.md) (WBS 12.0)
- **Harvested Improvements:** `IMP-MXC-004`, `IMP-MXC-011`, `IMP-MXC-020`

---

## 5. Out of Scope

- Cross-datacenter live VM migration across multiple Hyper-V clusters (single-host and local-cluster scope first).
- Cloud spot-instance bidding or external public-cloud autoscaling APIs.
