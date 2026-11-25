"""Contract tests for Story 20.2 — Non-Destructive Bare-Metal HIL Benchmark Validator & Protected-VM Isolation Guard (ADR-021).

Spec Gate Episode: spec-20_2-e26e3c99 (Robust Utility Margin: +0.2184)
Contract Interpretations:
  I1 (Compliant HIL Benchmark Report): verify_hil_benchmark_report() returns (True, "OK")
      when touched_vms excludes all protected_vm_names (case-insensitive), parent_sha_before
      equals parent_sha_after via constant-time hmac.compare_digest, and finite non-bool
      metrics satisfy paused_ram_mb <= 640.0, effective_ram_mb < 350.0,
      remote_numa_pages == 0, and ramdisk_mount_ms <= 50.0.
  I2 (Fail-Closed Precedence): None, non-dict, or empty {} -> ERR_BENCHMARK_REPORT_INVALID;
      protected VM in touched_vms -> ERR_PROTECTED_VM_TOUCHED; parent hash drift ->
      ERR_PARENT_HASH_DRIFT; out-of-bounds/bool/NaN/inf/negative metrics ->
      ERR_BENCHMARK_SLA_FAILED.
  I3 (Offline Airgap Invariance): Validation runs 100% offline with zero network calls
      (socket.create_connection blocked).
"""

from __future__ import annotations

import math
import socket

import pytest

from scripts.lib.silicon_hil_harness import verify_hil_benchmark_report

_VALID_SHA = "a" * 64
_DRIFTED_SHA = "b" * 64


def _compliant_report(**overrides) -> dict:
    base = {
        "touched_vms": ["mxc-hil-ephemeral-01"],
        "parent_sha_before": _VALID_SHA,
        "parent_sha_after": _VALID_SHA,
        "paused_ram_mb": 612.5,
        "effective_ram_mb": 328.0,
        "remote_numa_pages": 0,
        "ramdisk_mount_ms": 24.5,
    }
    base.update(overrides)
    return base


# Story 20.2 — AC-20.2.1 (ADR-021)
def test_ac_20_2_1_compliant_hil_benchmark_report_returns_ok():
    assert verify_hil_benchmark_report(_compliant_report()) == (True, "OK")
    # Boundary values: paused_ram_mb == 640.0, ramdisk_mount_ms == 50.0, empty touched_vms
    boundary = _compliant_report(
        touched_vms=[],
        paused_ram_mb=640.0,
        effective_ram_mb=349.9,
        remote_numa_pages=0,
        ramdisk_mount_ms=50.0,
    )
    assert verify_hil_benchmark_report(boundary) == (True, "OK")


# Story 20.2 — AC-20.2.2 (ADR-021)
@pytest.mark.parametrize("bad_report", [None, {}, [], "report", 123])
def test_ac_20_2_2_none_empty_or_non_dict_fails_closed(bad_report):
    assert verify_hil_benchmark_report(bad_report) == (
        False,
        "ERR_BENCHMARK_REPORT_INVALID",
    )


# Story 20.2 — AC-20.2.2 (ADR-021)
@pytest.mark.parametrize(
    "touched_vms",
    [
        ["Windows 11 Pro Dev"],
        ["windows 11 pro dev"],
        ["mxc-hil-01", "WINDOWS 11 PRO DEV"],
    ],
)
def test_ac_20_2_2_protected_vm_touched_fails_closed_case_insensitive(touched_vms):
    report = _compliant_report(touched_vms=touched_vms)
    assert verify_hil_benchmark_report(report) == (False, "ERR_PROTECTED_VM_TOUCHED")


# Story 20.2 — AC-20.2.2 (ADR-021)
def test_ac_20_2_2_custom_protected_vm_names_enforced():
    report = _compliant_report(touched_vms=["mxc-hv-930733af"])
    assert verify_hil_benchmark_report(
        report,
        protected_vm_names=("Windows 11 Pro Dev", "mxc-hv-930733af"),
    ) == (False, "ERR_PROTECTED_VM_TOUCHED")


# Story 20.2 — AC-20.2.2 (ADR-021)
def test_ac_20_2_2_parent_hash_drift_fails_closed():
    report = _compliant_report(
        parent_sha_before=_VALID_SHA,
        parent_sha_after=_DRIFTED_SHA,
    )
    assert verify_hil_benchmark_report(report) == (False, "ERR_PARENT_HASH_DRIFT")


# Story 20.2 — AC-20.2.2 (ADR-021)
@pytest.mark.parametrize(
    "metric_override",
    [
        {"paused_ram_mb": 640.1},
        {"paused_ram_mb": -1.0},
        {"paused_ram_mb": True},
        {"paused_ram_mb": math.nan},
        {"paused_ram_mb": math.inf},
        {"effective_ram_mb": 350.0},
        {"effective_ram_mb": 410.0},
        {"effective_ram_mb": -5.0},
        {"effective_ram_mb": False},
        {"effective_ram_mb": math.nan},
        {"remote_numa_pages": 1},
        {"remote_numa_pages": -1},
        {"remote_numa_pages": False},
        {"remote_numa_pages": 0.5},
        {"ramdisk_mount_ms": 50.1},
        {"ramdisk_mount_ms": -0.1},
        {"ramdisk_mount_ms": True},
        {"ramdisk_mount_ms": math.inf},
    ],
)
def test_ac_20_2_2_invalid_or_out_of_bounds_metrics_fail_closed(metric_override):
    report = _compliant_report(**metric_override)
    assert verify_hil_benchmark_report(report) == (False, "ERR_BENCHMARK_SLA_FAILED")


# Story 20.2 — AC-20.2.1 (ADR-021)
def test_ac_20_2_1_hil_benchmark_validator_runs_offline_airgapped(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise AssertionError("Network access is forbidden in HIL benchmark validator")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    assert verify_hil_benchmark_report(_compliant_report()) == (True, "OK")
