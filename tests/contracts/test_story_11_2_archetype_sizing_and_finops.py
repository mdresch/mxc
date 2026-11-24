"""Contract tests for Story 11.2 — Archetype Sizing Floor Guard & FinOps Cost-per-Session Estimator (ADR-013).

Spec Gate Episode: spec-11_2-98b76e43 (Robust Utility Margin: +0.2129)
Contract Interpretations:
  I1: validate_archetype_sizing() enforces minimum RAM, vCPU, and static-RAM requirements per image
      archetype (desktop_gui: >=4096 MB static RAM & >=4 vCPUs; lean_agent: >=2048 MB & >=2 vCPUs;
      server_core: >=1024 MB & >=2 vCPUs), returning (False, "ERR_ARCHETYPE_FLOOR_VIOLATION") on breach.
  I2: evaluate_fleet_rebalance() computes deterministic estimated_cost_per_session_eur >= 0.0 that
      strictly decreases when effective_warm_ram_mb is lowered via ADR-011 host memory combining.
"""

from __future__ import annotations

from scripts.lib.fleet_economics import (
    DEFAULT_ARCHETYPE_PROFILES,
    FleetTelemetrySnapshot,
    evaluate_fleet_rebalance,
    validate_archetype_sizing,
)


# Story 11.2 — AC-11.2.1 (ADR-013)
def test_ac_11_2_1_archetype_sizing_floor_guard_prevents_desktop_starvation():
    desktop = DEFAULT_ARCHETYPE_PROFILES["desktop_gui"]
    lean = DEFAULT_ARCHETYPE_PROFILES["lean_agent"]

    # Desktop GUI with 2048 MB RAM -> rejected
    ok_low_ram, code_low_ram = validate_archetype_sizing(
        desktop, requested_ram_mb=2048, requested_vcpus=4, dynamic_memory_enabled=False
    )
    assert ok_low_ram is False
    assert code_low_ram == "ERR_ARCHETYPE_FLOOR_VIOLATION"

    # Desktop GUI with Dynamic Memory enabled -> rejected (prevents MemoryStatus: Low display stall)
    ok_dyn, code_dyn = validate_archetype_sizing(
        desktop, requested_ram_mb=4096, requested_vcpus=4, dynamic_memory_enabled=True
    )
    assert ok_dyn is False
    assert code_dyn == "ERR_ARCHETYPE_FLOOR_VIOLATION"

    # Desktop GUI with 4096 MB static RAM & 4 vCPUs -> accepted
    ok_desktop, code_desktop = validate_archetype_sizing(
        desktop, requested_ram_mb=4096, requested_vcpus=4, dynamic_memory_enabled=False
    )
    assert ok_desktop is True
    assert code_desktop == "OK"

    # Lean headless agent with 2048 MB RAM & 2 vCPUs -> accepted
    ok_lean, code_lean = validate_archetype_sizing(
        lean, requested_ram_mb=2048, requested_vcpus=2, dynamic_memory_enabled=False
    )
    assert ok_lean is True
    assert code_lean == "OK"

    # Lean headless agent with 1 vCPU -> rejected
    ok_lean_bad, code_lean_bad = validate_archetype_sizing(
        lean, requested_ram_mb=2048, requested_vcpus=1, dynamic_memory_enabled=False
    )
    assert ok_lean_bad is False
    assert code_lean_bad == "ERR_ARCHETYPE_FLOOR_VIOLATION"


# Story 11.2 — AC-11.2.2 (ADR-013)
def test_ac_11_2_2_finops_cost_per_session_decreases_with_memory_deduplication():
    snap_undeduplicated = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=40000,
        effective_warm_ram_mb=1100.0,  # Phase 1 baseline
        hot_count=4,
        warm_count=20,
        cold_count=30,
        platinum_k_min=3,
        recent_rps=10.0,
        sla_hit_rate=0.997,
    )
    snap_deduplicated = FleetTelemetrySnapshot(
        host_total_ram_mb=65536,
        host_used_ram_mb=24000,
        effective_warm_ram_mb=400.0,  # Phase 2 ADR-011 deduplicated baseline
        hot_count=4,
        warm_count=20,
        cold_count=30,
        platinum_k_min=3,
        recent_rps=10.0,
        sla_hit_rate=0.997,
    )

    dec_before = evaluate_fleet_rebalance(snap_undeduplicated, seconds_since_last_transition=120.0)
    dec_after = evaluate_fleet_rebalance(snap_deduplicated, seconds_since_last_transition=120.0)

    assert dec_before.estimated_cost_per_session_eur > 0.0
    assert dec_after.estimated_cost_per_session_eur > 0.0
    assert dec_after.estimated_cost_per_session_eur < dec_before.estimated_cost_per_session_eur
