"""MXC Autonomous Fleet Economics & Dynamic Sizing Scheduler (ADR-013 / Epic 011).

Implements:
  - Story 11.1: Closed-loop host RAM pressure autotuner (<75% NORMAL, 75-85% ELEVATED, >85% CRITICAL)
                with Platinum Hot SLA protection and anti-thrash dwell hysteresis (>= 60s).
  - Story 11.2: Image-archetype minimum RAM/vCPU sizing guard and deterministic FinOps cost-per-session estimator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ArchetypeProfile:
    archetype: str
    min_ram_mb: int
    min_vcpus: int
    static_ram_required: bool


DEFAULT_ARCHETYPE_PROFILES: dict[str, ArchetypeProfile] = {
    "desktop_gui": ArchetypeProfile(
        archetype="desktop_gui",
        min_ram_mb=4096,
        min_vcpus=4,
        static_ram_required=True,
    ),
    "lean_agent": ArchetypeProfile(
        archetype="lean_agent",
        min_ram_mb=2048,
        min_vcpus=2,
        static_ram_required=False,
    ),
    "server_core": ArchetypeProfile(
        archetype="server_core",
        min_ram_mb=1024,
        min_vcpus=2,
        static_ram_required=False,
    ),
}


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
    pressure_band: str
    target_hot: int
    target_warm: int
    shed_warm_to_cold: int
    estimated_cost_per_session_eur: float
    rationale: str


# Unit economics constants (EUR per GB-hour RAM + active hot vCPU baseline)
_EUR_PER_GB_HOUR_RAM = 0.0045
_EUR_PER_HOT_VM_HOUR = 0.018
_HOT_VM_RAM_GB = 1.2
_COLD_NVME_EUR_PER_VM_HOUR = 0.0002
_TARGET_SLA_HIT_RATE = 0.995


def _validate_snapshot(snapshot: FleetTelemetrySnapshot) -> None:
    if snapshot.host_total_ram_mb <= 0:
        raise ValueError("host_total_ram_mb must be positive")
    if snapshot.host_used_ram_mb < 0:
        raise ValueError("host_used_ram_mb must be non-negative")
    if snapshot.effective_warm_ram_mb <= 0 or not math.isfinite(snapshot.effective_warm_ram_mb):
        raise ValueError("effective_warm_ram_mb must be a finite positive number")
    if snapshot.hot_count < 0 or snapshot.warm_count < 0 or snapshot.cold_count < 0:
        raise ValueError("tier counts must be non-negative")
    if snapshot.platinum_k_min < 0:
        raise ValueError("platinum_k_min must be non-negative")
    if snapshot.recent_rps < 0 or not math.isfinite(snapshot.recent_rps):
        raise ValueError("recent_rps must be a finite non-negative number")


def _estimate_cost_per_session_eur(
    *,
    target_hot: int,
    target_warm: int,
    cold_count: int,
    effective_warm_ram_mb: float,
    recent_rps: float,
) -> float:
    warm_ram_gb = (target_warm * effective_warm_ram_mb) / 1024.0
    hot_hourly = target_hot * (_EUR_PER_HOT_VM_HOUR + _HOT_VM_RAM_GB * _EUR_PER_GB_HOUR_RAM)
    warm_hourly = warm_ram_gb * _EUR_PER_GB_HOUR_RAM
    cold_hourly = cold_count * _COLD_NVME_EUR_PER_VM_HOUR
    total_hourly = hot_hourly + warm_hourly + cold_hourly
    sessions_per_hour = max(recent_rps * 3600.0, 1.0)
    return round(total_hourly / sessions_per_hour, 8)


def evaluate_fleet_rebalance(
    snapshot: FleetTelemetrySnapshot,
    seconds_since_last_transition: float,
    min_dwell_seconds: float = 60.0,
) -> RebalanceDecision:
    """Evaluate host RAM pressure, enforce anti-thrash hysteresis, and return a tier rebalance plan."""
    _validate_snapshot(snapshot)
    if seconds_since_last_transition < 0 or min_dwell_seconds < 0:
        raise ValueError("dwell durations must be non-negative")

    ram_ratio = snapshot.host_used_ram_mb / snapshot.host_total_ram_mb
    if ram_ratio > 0.85:
        band = "CRITICAL"
    elif ram_ratio >= 0.75:
        band = "ELEVATED"
    else:
        band = "NORMAL"

    # CRITICAL overrides dwell hysteresis immediately to prevent host swapping/OOM
    if band == "CRITICAL":
        target_ram_mb = snapshot.host_total_ram_mb * 0.80
        excess_ram_mb = max(0.0, snapshot.host_used_ram_mb - target_ram_mb)
        needed_shed = int(math.ceil(excess_ram_mb / snapshot.effective_warm_ram_mb)) if excess_ram_mb > 0 else 0
        shed = min(snapshot.warm_count, max(1, needed_shed) if snapshot.warm_count > 0 else 0)
        target_hot = max(snapshot.hot_count, snapshot.platinum_k_min)
        target_warm = snapshot.warm_count - shed
        cost = _estimate_cost_per_session_eur(
            target_hot=target_hot,
            target_warm=target_warm,
            cold_count=snapshot.cold_count + shed,
            effective_warm_ram_mb=snapshot.effective_warm_ram_mb,
            recent_rps=snapshot.recent_rps,
        )
        return RebalanceDecision(
            pressure_band=band,
            target_hot=target_hot,
            target_warm=target_warm,
            shed_warm_to_cold=shed,
            estimated_cost_per_session_eur=cost,
            rationale=f"CRITICAL RAM pressure ({ram_ratio:.1%}): shedding {shed} WarmPaused to ColdSaved while preserving Platinum K_min={snapshot.platinum_k_min}.",
        )

    # Non-critical anti-thrash dwell guard
    if seconds_since_last_transition < min_dwell_seconds:
        target_hot = max(snapshot.hot_count, snapshot.platinum_k_min)
        cost = _estimate_cost_per_session_eur(
            target_hot=target_hot,
            target_warm=snapshot.warm_count,
            cold_count=snapshot.cold_count,
            effective_warm_ram_mb=snapshot.effective_warm_ram_mb,
            recent_rps=snapshot.recent_rps,
        )
        return RebalanceDecision(
            pressure_band=band,
            target_hot=target_hot,
            target_warm=snapshot.warm_count,
            shed_warm_to_cold=0,
            estimated_cost_per_session_eur=cost,
            rationale=f"Hold within anti-thrash dwell window ({seconds_since_last_transition:.1f}s < {min_dwell_seconds:.1f}s).",
        )

    target_hot = max(snapshot.hot_count, snapshot.platinum_k_min)
    target_warm = snapshot.warm_count
    rationale = f"{band} RAM pressure ({ram_ratio:.1%}): tier watermarks balanced."

    if band == "NORMAL" and snapshot.sla_hit_rate < _TARGET_SLA_HIT_RATE:
        target_hot = max(target_hot + 1, snapshot.platinum_k_min)
        rationale = f"NORMAL pressure with SLA hit rate {snapshot.sla_hit_rate:.3f} < {_TARGET_SLA_HIT_RATE}: scaling HotRunning to {target_hot}."
    elif band == "ELEVATED":
        rationale = f"ELEVATED RAM pressure ({ram_ratio:.1%}): pausing Cold->Warm promotions and tightening idle cooldowns."

    cost = _estimate_cost_per_session_eur(
        target_hot=target_hot,
        target_warm=target_warm,
        cold_count=snapshot.cold_count,
        effective_warm_ram_mb=snapshot.effective_warm_ram_mb,
        recent_rps=snapshot.recent_rps,
    )
    return RebalanceDecision(
        pressure_band=band,
        target_hot=target_hot,
        target_warm=target_warm,
        shed_warm_to_cold=0,
        estimated_cost_per_session_eur=cost,
        rationale=rationale,
    )


def validate_archetype_sizing(
    profile: ArchetypeProfile,
    requested_ram_mb: int,
    requested_vcpus: int,
    dynamic_memory_enabled: bool,
) -> tuple[bool, str]:
    """Enforce image-archetype RAM, vCPU, and static-RAM floor invariants."""
    if requested_ram_mb < profile.min_ram_mb:
        return False, "ERR_ARCHETYPE_FLOOR_VIOLATION"
    if requested_vcpus < profile.min_vcpus:
        return False, "ERR_ARCHETYPE_FLOOR_VIOLATION"
    if profile.static_ram_required and dynamic_memory_enabled:
        return False, "ERR_ARCHETYPE_FLOOR_VIOLATION"
    return True, "OK"
