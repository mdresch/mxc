"""Bare-metal Hyper-V silicon HIL capability probe and benchmark validator (ADR-021, Epic 020).

Standard-library only, 100% offline, fail-closed implementation covering:
- Story 20.1: HostHardwareCapabilities & evaluate_silicon_capabilities()
- Story 20.2: verify_hil_benchmark_report()
"""

from __future__ import annotations

from dataclasses import dataclass
import hmac
import math
from typing import Any


@dataclass(frozen=True)
class HostHardwareCapabilities:
    hyperv_enabled: bool
    numa_node_count: int
    vtpm_supported: bool
    sev_snp_or_tdx_supported: bool
    gpup_supported: bool
    ramdisk_available_mb: int


def _is_nonneg_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_finite_nonneg_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )


def evaluate_silicon_capabilities(
    caps: HostHardwareCapabilities | None,
    *,
    require_tee: bool = False,
    require_gpup: bool = False,
    require_multisocket_numa: bool = False,
) -> dict[str, Any]:
    """Evaluate probed host hardware capabilities fail-closed without faking compliance."""
    if (
        caps is None
        or not isinstance(caps, HostHardwareCapabilities)
        or not isinstance(require_tee, bool)
        or not isinstance(require_gpup, bool)
        or not isinstance(require_multisocket_numa, bool)
        or not isinstance(caps.hyperv_enabled, bool)
        or not isinstance(caps.vtpm_supported, bool)
        or not isinstance(caps.sev_snp_or_tdx_supported, bool)
        or not isinstance(caps.gpup_supported, bool)
        or not _is_nonneg_int(caps.numa_node_count)
        or not _is_nonneg_int(caps.ramdisk_available_mb)
    ):
        return {
            "ready": False,
            "reason_code": "ERR_CAPABILITY_PROBE_INVALID",
            "tee_verdict": "ERR_CAPABILITY_PROBE_INVALID",
            "gpup_verdict": "ERR_CAPABILITY_PROBE_INVALID",
            "numa_verdict": "ERR_CAPABILITY_PROBE_INVALID",
        }

    if require_tee:
        tee_verdict = (
            "OK"
            if (caps.vtpm_supported and caps.sev_snp_or_tdx_supported)
            else "ERR_TEE_UNSUPPORTED"
        )
    else:
        tee_verdict = "NOT_REQUIRED"

    if require_gpup:
        gpup_verdict = "OK" if caps.gpup_supported else "ERR_GPUP_UNSUPPORTED"
    else:
        gpup_verdict = "NOT_REQUIRED"

    if require_multisocket_numa:
        numa_verdict = (
            "OK" if caps.numa_node_count >= 2 else "SKIPPED_NO_MULTISOCKET_NUMA"
        )
    else:
        numa_verdict = "NOT_REQUIRED"

    if not caps.hyperv_enabled:
        ready = False
        reason_code = "ERR_HYPERV_DISABLED"
    elif tee_verdict == "ERR_TEE_UNSUPPORTED":
        ready = False
        reason_code = "ERR_TEE_UNSUPPORTED"
    elif gpup_verdict == "ERR_GPUP_UNSUPPORTED":
        ready = False
        reason_code = "ERR_GPUP_UNSUPPORTED"
    elif numa_verdict == "SKIPPED_NO_MULTISOCKET_NUMA":
        ready = False
        reason_code = "SKIPPED_NO_MULTISOCKET_NUMA"
    else:
        ready = True
        reason_code = "OK"

    return {
        "ready": ready,
        "reason_code": reason_code,
        "hyperv_enabled": caps.hyperv_enabled,
        "numa_node_count": caps.numa_node_count,
        "ramdisk_available_mb": caps.ramdisk_available_mb,
        "tee_verdict": tee_verdict,
        "gpup_verdict": gpup_verdict,
        "numa_verdict": numa_verdict,
    }


def verify_hil_benchmark_report(
    report: dict[str, Any] | None,
    *,
    protected_vm_names: tuple[str, ...] = ("Windows 11 Pro Dev",),
) -> tuple[bool, str]:
    """Validate a bare-metal HIL benchmark report fail-closed."""
    if report is None or not isinstance(report, dict) or len(report) == 0:
        return (False, "ERR_BENCHMARK_REPORT_INVALID")

    if (
        protected_vm_names is None
        or isinstance(protected_vm_names, (str, bytes))
        or not isinstance(protected_vm_names, (tuple, list, set, frozenset))
    ):
        return (False, "ERR_BENCHMARK_REPORT_INVALID")

    protected_normalized = {
        name.strip().lower()
        for name in protected_vm_names
        if isinstance(name, str) and name.strip()
    }

    touched_vms = report.get("touched_vms")
    if not isinstance(touched_vms, (list, tuple)):
        return (False, "ERR_BENCHMARK_REPORT_INVALID")

    for vm_name in touched_vms:
        if not isinstance(vm_name, str):
            return (False, "ERR_BENCHMARK_REPORT_INVALID")
        if vm_name.strip().lower() in protected_normalized:
            return (False, "ERR_PROTECTED_VM_TOUCHED")

    parent_sha_before = report.get("parent_sha_before")
    parent_sha_after = report.get("parent_sha_after")
    if (
        not isinstance(parent_sha_before, str)
        or not isinstance(parent_sha_after, str)
        or not parent_sha_before.strip()
        or not parent_sha_after.strip()
    ):
        return (False, "ERR_BENCHMARK_REPORT_INVALID")

    if not hmac.compare_digest(
        parent_sha_before.strip().lower(),
        parent_sha_after.strip().lower(),
    ):
        return (False, "ERR_PARENT_HASH_DRIFT")

    paused_ram_mb = report.get("paused_ram_mb")
    effective_ram_mb = report.get("effective_ram_mb")
    remote_numa_pages = report.get("remote_numa_pages")
    ramdisk_mount_ms = report.get("ramdisk_mount_ms")

    if (
        not _is_finite_nonneg_number(paused_ram_mb)
        or paused_ram_mb > 640.0
        or not _is_finite_nonneg_number(effective_ram_mb)
        or effective_ram_mb >= 350.0
        or not _is_nonneg_int(remote_numa_pages)
        or remote_numa_pages != 0
        or not _is_finite_nonneg_number(ramdisk_mount_ms)
        or ramdisk_mount_ms > 50.0
    ):
        return (False, "ERR_BENCHMARK_SLA_FAILED")

    return (True, "OK")
