"""Contract tests for Story 11.1 — Host RAM Pressure Autotuner & Anti-Thrash Hysteresis Controller (ADR-013).

Spec Gate Episode: spec-11_1-25e32156 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1: evaluate_fleet_rebalance() classifies host RAM pressure into NORMAL (<75%), ELEVATED (75%-85%),
      and CRITICAL (>85%). Under CRITICAL pressure, idle WarmPaused instances are shed to ColdSaved
      until projected host RAM drops to <=80%, while strictly preserving target_hot >= platinum_k_min.
  I2: Anti-thrash hysteresis suppresses non-CRITICAL tier changes when seconds_since_last_transition
      is below min_dwell_seconds (default 60s), while CRITICAL pressure always overrides dwell to
      prevent host OOM/swapping.
  I3: Invalid telemetry (non-positive host_total_ram_mb, negative counts) raises ValueError.
"""

from __future__ import annotations

import pytest

from scripts.lib.fleet_economics import (
    FleetTelemetrySnapshot,
    RebalanceDecision,
    evaluate_fleet_rebalance,
)


# Story 11.1 — AC-11.1.1 (ADR-013)
def test_ac_11_1_1_pressure_band_classification_and_critical_shedding_preserves_platinum():
    # NORMAL (<75%)
    snap_normal = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=32768,  # 50%
        effective_warm_ram_mb=420.0,
        hot_count=4,
        warm_count=20,
        cold_count=30,
        platinum_k_min=3,
        recent_rps=12.0,
        sla_hit_rate=0.998,
    )
    dec_normal = evaluate_fleet_rebalance(snap_normal, seconds_since_last_transition=120.0)
    assert isinstance(dec_normal, RebalanceDecision)
    assert dec_normal.pressure_band == "NORMAL"
    assert dec_normal.shed_warm_to_cold == 0
    assert dec_normal.target_hot >= snap_normal.platinum_k_min

    # ELEVATED (75%-85%)
    snap_elevated = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=52428,  # 80%
        effective_warm_ram_mb=420.0,
        hot_count=4,
        warm_count=20,
        cold_count=30,
        platinum_k_min=3,
        recent_rps=10.0,
        sla_hit_rate=0.996,
    )
    dec_elevated = evaluate_fleet_rebalance(snap_elevated, seconds_since_last_transition=120.0)
    assert dec_elevated.pressure_band == "ELEVATED"
    assert dec_elevated.shed_warm_to_cold == 0
    assert dec_elevated.target_hot >= snap_elevated.platinum_k_min

    # CRITICAL (>85%) — must shed WarmPaused to ColdSaved while protecting platinum_k_min
    snap_critical = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=58982,  # 90%
        effective_warm_ram_mb=450.0,
        hot_count=3,
        warm_count=25,
        cold_count=20,
        platinum_k_min=3,
        recent_rps=15.0,
        sla_hit_rate=0.995,
    )
    dec_critical = evaluate_fleet_rebalance(snap_critical, seconds_since_last_transition=10.0)
    assert dec_critical.pressure_band == "CRITICAL"
    assert dec_critical.shed_warm_to_cold > 0
    assert dec_critical.shed_warm_to_cold <= snap_critical.warm_count
    assert dec_critical.target_hot >= snap_critical.platinum_k_min
    assert dec_critical.target_warm == snap_critical.warm_count - dec_critical.shed_warm_to_cold


# Story 11.1 — AC-11.1.2 (ADR-013)
def test_ac_11_1_2_hysteresis_suppresses_non_critical_oscillation_within_dwell_window():
    snap_surge = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=30000,  # ~45.8% NORMAL
        effective_warm_ram_mb=400.0,
        hot_count=2,
        warm_count=10,
        cold_count=20,
        platinum_k_min=2,
        recent_rps=25.0,
        sla_hit_rate=0.98,  # below 0.995 target -> would normally scale hot up
    )
    # Within 60s dwell window: must hold steady
    dec_hold = evaluate_fleet_rebalance(snap_surge, seconds_since_last_transition=30.0, min_dwell_seconds=60.0)
    assert dec_hold.pressure_band == "NORMAL"
    assert dec_hold.target_hot == snap_surge.hot_count
    assert dec_hold.target_warm == snap_surge.warm_count
    assert dec_hold.shed_warm_to_cold == 0
    assert "dwell" in dec_hold.rationale.lower()

    # After 60s dwell window expires: allowed to scale hot up to restore SLA
    dec_scale = evaluate_fleet_rebalance(snap_surge, seconds_since_last_transition=90.0, min_dwell_seconds=60.0)
    assert dec_scale.target_hot > snap_surge.hot_count


def test_story_11_1_rejects_invalid_telemetry():
    bad_snap = FleetTelemetrySnapshot(
        host_total_ram_mb=0,
        host_used_ram_mb=100,
        effective_warm_ram_mb=400.0,
        hot_count=1,
        warm_count=1,
        cold_count=1,
        platinum_k_min=1,
        recent_rps=1.0,
        sla_hit_rate=1.0,
    )
    with pytest.raises(ValueError):
        evaluate_fleet_rebalance(bad_snap, seconds_since_last_transition=120.0)
