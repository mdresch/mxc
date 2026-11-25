"""Contract tests for Story 20.1 — Honest Fail-Closed Host Hardware Capability Probe (ADR-021).

Spec Gate Episode: spec-20_1-b0350d62 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1 (Honest Fail-Closed Capability Verdicts): evaluate_silicon_capabilities() probes
      HostHardwareCapabilities without fabricating passing hardware scores on unsupported
      workstations. Required missing capabilities yield explicit verdicts:
      tee_verdict == "ERR_TEE_UNSUPPORTED", gpup_verdict == "ERR_GPUP_UNSUPPORTED",
      numa_verdict == "SKIPPED_NO_MULTISOCKET_NUMA", and ready is False.
  I2 (Defensive None & Invalid-Type Guard): None, non-dataclass values, bool-as-int
      counts, negative counts, or non-bool flags fail closed with
      ready=False and reason_code="ERR_CAPABILITY_PROBE_INVALID" without raising
      AttributeError.
  I3 (Offline Airgap Invariance): Capability evaluation runs 100% offline with zero
      network calls (socket.create_connection blocked).
"""

from __future__ import annotations

import socket

import pytest

from scripts.lib.silicon_hil_harness import (
    HostHardwareCapabilities,
    evaluate_silicon_capabilities,
)


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_workstation_without_optional_requirements_passes_honestly():
    caps = HostHardwareCapabilities(
        hyperv_enabled=True,
        numa_node_count=1,
        vtpm_supported=True,
        sev_snp_or_tdx_supported=False,
        gpup_supported=False,
        ramdisk_available_mb=2048,
    )
    verdict = evaluate_silicon_capabilities(caps)
    assert verdict["ready"] is True
    assert verdict["reason_code"] == "OK"
    assert verdict["tee_verdict"] == "NOT_REQUIRED"
    assert verdict["gpup_verdict"] == "NOT_REQUIRED"
    assert verdict["numa_verdict"] == "NOT_REQUIRED"


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_server_with_all_capabilities_passes_when_all_required():
    caps = HostHardwareCapabilities(
        hyperv_enabled=True,
        numa_node_count=2,
        vtpm_supported=True,
        sev_snp_or_tdx_supported=True,
        gpup_supported=True,
        ramdisk_available_mb=16384,
    )
    verdict = evaluate_silicon_capabilities(
        caps,
        require_tee=True,
        require_gpup=True,
        require_multisocket_numa=True,
    )
    assert verdict["ready"] is True
    assert verdict["reason_code"] == "OK"
    assert verdict["tee_verdict"] == "OK"
    assert verdict["gpup_verdict"] == "OK"
    assert verdict["numa_verdict"] == "OK"


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_unsupported_workstation_fails_closed_for_tee_gpup_and_numa():
    caps = HostHardwareCapabilities(
        hyperv_enabled=True,
        numa_node_count=1,
        vtpm_supported=True,
        sev_snp_or_tdx_supported=False,
        gpup_supported=False,
        ramdisk_available_mb=1024,
    )
    verdict = evaluate_silicon_capabilities(
        caps,
        require_tee=True,
        require_gpup=True,
        require_multisocket_numa=True,
    )
    assert verdict["ready"] is False
    assert verdict["tee_verdict"] == "ERR_TEE_UNSUPPORTED"
    assert verdict["gpup_verdict"] == "ERR_GPUP_UNSUPPORTED"
    assert verdict["numa_verdict"] == "SKIPPED_NO_MULTISOCKET_NUMA"


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_tee_requires_both_vtpm_and_sev_snp_or_tdx():
    caps_no_vtpm = HostHardwareCapabilities(
        hyperv_enabled=True,
        numa_node_count=2,
        vtpm_supported=False,
        sev_snp_or_tdx_supported=True,
        gpup_supported=True,
        ramdisk_available_mb=4096,
    )
    verdict = evaluate_silicon_capabilities(caps_no_vtpm, require_tee=True)
    assert verdict["ready"] is False
    assert verdict["tee_verdict"] == "ERR_TEE_UNSUPPORTED"
    assert verdict["reason_code"] == "ERR_TEE_UNSUPPORTED"


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_hyperv_disabled_fails_closed():
    caps = HostHardwareCapabilities(
        hyperv_enabled=False,
        numa_node_count=2,
        vtpm_supported=True,
        sev_snp_or_tdx_supported=True,
        gpup_supported=True,
        ramdisk_available_mb=4096,
    )
    verdict = evaluate_silicon_capabilities(caps)
    assert verdict["ready"] is False
    assert verdict["reason_code"] == "ERR_HYPERV_DISABLED"


# Story 20.1 — AC-20.1.2 (ADR-021)
@pytest.mark.parametrize(
    "bad_caps",
    [
        None,
        {},
        {"hyperv_enabled": True},
        "HostHardwareCapabilities",
        42,
        HostHardwareCapabilities(
            hyperv_enabled=True,
            numa_node_count=True,  # type: ignore[arg-type]
            vtpm_supported=True,
            sev_snp_or_tdx_supported=True,
            gpup_supported=True,
            ramdisk_available_mb=1024,
        ),
        HostHardwareCapabilities(
            hyperv_enabled=True,
            numa_node_count=-1,
            vtpm_supported=True,
            sev_snp_or_tdx_supported=True,
            gpup_supported=True,
            ramdisk_available_mb=1024,
        ),
        HostHardwareCapabilities(
            hyperv_enabled=True,
            numa_node_count=1,
            vtpm_supported=True,
            sev_snp_or_tdx_supported=True,
            gpup_supported=True,
            ramdisk_available_mb=-64,
        ),
        HostHardwareCapabilities(
            hyperv_enabled=True,
            numa_node_count=1,
            vtpm_supported=True,
            sev_snp_or_tdx_supported=True,
            gpup_supported=True,
            ramdisk_available_mb=False,  # type: ignore[arg-type]
        ),
    ],
)
def test_ac_20_1_2_none_or_invalid_capabilities_fail_closed_without_attribute_error(
    bad_caps,
):
    verdict = evaluate_silicon_capabilities(bad_caps)
    assert verdict["ready"] is False
    assert verdict["reason_code"] == "ERR_CAPABILITY_PROBE_INVALID"


# Story 20.1 — AC-20.1.1 (ADR-021)
def test_ac_20_1_1_capability_probe_runs_offline_airgapped(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise AssertionError("Network access is forbidden in silicon capability probe")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    caps = HostHardwareCapabilities(
        hyperv_enabled=True,
        numa_node_count=2,
        vtpm_supported=True,
        sev_snp_or_tdx_supported=True,
        gpup_supported=False,
        ramdisk_available_mb=4096,
    )
    verdict = evaluate_silicon_capabilities(
        caps,
        require_tee=True,
        require_gpup=True,
        require_multisocket_numa=True,
    )
    assert verdict["ready"] is False
    assert verdict["tee_verdict"] == "OK"
    assert verdict["gpup_verdict"] == "ERR_GPUP_UNSUPPORTED"
    assert verdict["numa_verdict"] == "OK"
