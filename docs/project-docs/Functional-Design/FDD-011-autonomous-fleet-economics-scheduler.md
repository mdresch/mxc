---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md"
  - "docs/project-docs/Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md"
process: "Specify the closed-loop fleet economics scheduler, host pressure bands, archetype sizing guards, and anti-thrash hysteresis state machine"
outputs:
  - "docs/project-docs/Functional-Design/FDD-011-autonomous-fleet-economics-scheduler.md"
status: "Approved"
---

# FDD-011: Autonomous Fleet Economics & Dynamic Sizing Scheduler

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-013](../../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md), [BRD-011](../Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md)  
> **Outputs:** FDD-011-autonomous-fleet-economics-scheduler.md

**Source ADR:** [ADR-013](../../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md)  
**Source BRD:** [BRD-011](../Business-Requirements/BRD-011-autonomous-fleet-economics-scheduler.md)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved (2026-11-24)

---

## 1. Technical Architecture & Interfaces

### 1.1 Closed-Loop Economics & Pressure Control Loop
```
 [Host RAM Telemetry] + [Memory Combining Ratio] + [Tenant Request Velocity]
                                   │
                                   ▼
            [FleetEconomicsScheduler (scripts/lib/fleet_economics.py)]
              ├── Classify Pressure Band: NORMAL (<75%) | ELEVATED (75-85%) | CRITICAL (>85%)
              ├── Enforce Archetype Sizing Floor (Desktop >= 4096 MB | LeanAgent >= 2048 MB)
              ├── Evaluate Cost-per-Session & SLA Hit Rate Objective
              ├── Apply Hysteresis Filter (min_dwell_seconds >= 60s)
              └── Emit TierRebalancePlan (promote / demote / shed / hold)
                                   │
                                   ▼
            [Multi-Tier WatermarkPool (scripts/lib/watermark_pool.py)]
```

### 1.2 Core Interfaces (`scripts/lib/fleet_economics.py`)
```python
@dataclass(frozen=True)
class ArchetypeProfile:
    archetype: str          # "desktop_gui" | "lean_agent" | "server_core"
    min_ram_mb: int         # e.g., 4096 for desktop_gui, 2048 for lean_agent
    min_vcpus: int          # e.g., 4 for desktop_gui, 2 for lean_agent
    static_ram_required: bool

@dataclass(frozen=True)
class FleetTelemetrySnapshot:
    host_total_ram_mb: int
    host_used_ram_mb: int
    effective_warm_ram_mb: float
    hot_count: int
    warm_count: int
    cold_count: int
    platinum_k_min: int
    recent_rps: float
    sla_hit_rate: float

@dataclass(frozen=True)
class RebalanceDecision:
    pressure_band: str      # "NORMAL" | "ELEVATED" | "CRITICAL"
    target_hot: int
    target_warm: int
    shed_warm_to_cold: int
    estimated_cost_per_session_eur: float
    rationale: str

def evaluate_fleet_rebalance(
    snapshot: FleetTelemetrySnapshot,
    seconds_since_last_transition: float,
    min_dwell_seconds: float = 60.0,
) -> RebalanceDecision: ...

def validate_archetype_sizing(
    profile: ArchetypeProfile,
    requested_ram_mb: int,
    requested_vcpus: int,
    dynamic_memory_enabled: bool,
) -> tuple[bool, str]: ...
```

---

## 2. Invariant Contracts & Error Handling

| Check | Contract Invariant | Verification Method |
|---|---|---|
| **Critical Pressure Shedding** | `host_used_ram_mb / host_total_ram_mb > 0.85` MUST emit `shed_warm_to_cold > 0` while `warm_count > 0` and keep `target_hot >= platinum_k_min`. | Contract test simulating 88% host RAM commit. |
| **Hysteresis Lock** | If `seconds_since_last_transition < min_dwell_seconds` and band is not `CRITICAL`, scheduler returns hold (`shed_warm_to_cold == 0`, no oscillation). | Contract test asserting dwell guard. |
| **Archetype Floor** | Requesting `2048 MB` or Dynamic Memory for `desktop_gui` returns `(False, "ERR_ARCHETYPE_FLOOR_VIOLATION")`. | Unit test for `validate_archetype_sizing()`. |
| **FinOps Cost Calculation** | `estimated_cost_per_session_eur >= 0.0` is deterministic and monotonically decreases as `effective_warm_ram_mb` drops via `ADR-011` deduplication. | Deterministic math contract test. |
