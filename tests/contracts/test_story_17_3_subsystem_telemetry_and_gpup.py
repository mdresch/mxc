"""Contract tests for Story 17.3 — Automated Subsystem Differential Telemetry Matrix & GPU-P/DDA Agent Sandbox Tier (ADR-018).

Spec Gate Episode: spec-17_3-3cb1f339 (Robust Utility Margin: +0.2129)
Contract Interpretations:
  I1 (Pre-Dispatch Subsystem Matrix): evaluate_subsystem_differential_matrix() verifies
      that all four mandatory Windows subsystems (wmi, com_plus, services, gpo) — with
      case-insensitive normalization of "com+" to "com_plus" — report True or
      {"healthy": True}; None, non-dicts, empty {}, missing entries, or degraded
      entries fail closed with (False, "ERR_SUBSYSTEM_DEGRADED").
  I2 (Fail-Closed GPU-P Precedence): provision_gpup_sandbox() enforces deterministic
      check order: gpu_supported is not True -> ERR_GPUP_UNSUPPORTED; invalid/non-finite
      partition_ratio or throughput_ratio or partition_ratio not in (0, 1] ->
      ERR_GPUP_PARTITION_INVALID; throughput_ratio < 0.85 -> ERR_GPUP_SLA_BELOW_FLOOR;
      otherwise (True, "OK").
"""

from __future__ import annotations

import pytest

from scripts.lib.frontier_density_and_gpu import (
    evaluate_subsystem_differential_matrix,
    provision_gpup_sandbox,
)


# Story 17.3 — AC-17.3.1 (ADR-018)
def test_ac_17_3_1_subsystem_matrix_admits_all_healthy_and_normalizes_com_plus_alias():
    ok_bool, code_bool = evaluate_subsystem_differential_matrix(
        {
            "wmi": True,
            "com_plus": True,
            "services": True,
            "gpo": True,
        }
    )
    assert (ok_bool, code_bool) == (True, "OK")

    ok_mixed, code_mixed = evaluate_subsystem_differential_matrix(
        {
            "WMI": {"healthy": True, "latency_ms": 1.2},
            "COM+": {"healthy": True},
            "Services": True,
            "GPO": {"healthy": True},
        }
    )
    assert (ok_mixed, code_mixed) == (True, "OK")


# Story 17.3 — AC-17.3.1 (ADR-018)
@pytest.mark.parametrize(
    "telemetry",
    [
        None,
        {},
        ["wmi", "com_plus", "services", "gpo"],
        "healthy",
        {"wmi": True, "com_plus": True, "services": True},
        {"wmi": True, "com_plus": False, "services": True, "gpo": True},
        {"wmi": True, "com+": {"healthy": False}, "services": True, "gpo": True},
        {"wmi": True, "com_plus": True, "services": {}, "gpo": True},
        {"wmi": True, "com_plus": True, "services": None, "gpo": True},
        {"wmi": True, "com_plus": "yes", "services": True, "gpo": True},
        {"wmi": True, "com+": False, "com_plus": True, "services": True, "gpo": True},
    ],
)
def test_ac_17_3_1_subsystem_matrix_fails_closed_on_missing_or_degraded(telemetry):
    assert evaluate_subsystem_differential_matrix(telemetry) == (
        False,
        "ERR_SUBSYSTEM_DEGRADED",
    )


# Story 17.3 — AC-17.3.2 (ADR-018)
def test_ac_17_3_2_gpup_sandbox_admits_valid_partition_and_sla():
    assert provision_gpup_sandbox(
        gpu_supported=True,
        partition_ratio=0.25,
        throughput_ratio=0.92,
    ) == (True, "OK")

    # Boundary: full partition and exact 85% SLA floor
    assert provision_gpup_sandbox(
        gpu_supported=True,
        partition_ratio=1.0,
        throughput_ratio=0.85,
    ) == (True, "OK")


# Story 17.3 — AC-17.3.2 (ADR-018)
@pytest.mark.parametrize(
    "kwargs,expected",
    [
        # Precedence 1: hardware capability first, even with bad partition/SLA
        (
            {"gpu_supported": False, "partition_ratio": 0.0, "throughput_ratio": 0.10},
            (False, "ERR_GPUP_UNSUPPORTED"),
        ),
        (
            {"gpu_supported": None, "partition_ratio": 0.5, "throughput_ratio": 0.95},
            (False, "ERR_GPUP_UNSUPPORTED"),
        ),
        (
            {"gpu_supported": 1, "partition_ratio": 0.5, "throughput_ratio": 0.95},
            (False, "ERR_GPUP_UNSUPPORTED"),
        ),
        # Precedence 2: partition/numeric validity before SLA floor
        (
            {"gpu_supported": True, "partition_ratio": 0.0, "throughput_ratio": 0.50},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": -0.25, "throughput_ratio": 0.90},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": 1.01, "throughput_ratio": 0.95},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": None, "throughput_ratio": 0.95},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": True, "throughput_ratio": 0.95},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": float("nan"), "throughput_ratio": 0.95},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": 0.5, "throughput_ratio": float("inf")},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": 0.5, "throughput_ratio": None},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        (
            {"gpu_supported": True, "partition_ratio": 0.5, "throughput_ratio": False},
            (False, "ERR_GPUP_PARTITION_INVALID"),
        ),
        # Precedence 3: SLA throughput floor (< 0.85)
        (
            {"gpu_supported": True, "partition_ratio": 0.5, "throughput_ratio": 0.849},
            (False, "ERR_GPUP_SLA_BELOW_FLOOR"),
        ),
    ],
)
def test_ac_17_3_2_gpup_sandbox_deterministic_fail_closed_precedence(kwargs, expected):
    assert provision_gpup_sandbox(**kwargs) == expected
