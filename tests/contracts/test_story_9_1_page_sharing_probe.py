"""Contract Test: Story 9.1 — Hyper-V Page Sharing Configuration & Diagnostic Probe (WBS 10.1).

Governing Artifacts:
- ADR: ADR-011 (Hyper-V Host-Level Memory Combining & Fleet Page Deduplication)
- BRD: BRD-009 (BRU-009-01, BRU-009-03)
- FDD: FDD-009 (§1.1 Hyper-V Memory Combining Subsystem, §1.2 Telemetry & Diagnostic Interface)
- Epic: Epic 009 (User Story 9.1, WBS 10.1)

Acceptance Criteria:
- AC-9.1.1: Memory combining scan is configured and verified via WMI/PowerShell hypervisor settings.
- AC-9.1.2: Diagnostic probe reads `\\Hyper-V Dynamic Memory\\Memory Combining Shared Pages`
  and verifies non-zero page sharing across paused instances.
"""

import pytest

from scripts.lib.memory_combining_probe import (
    MemoryCombiningConfig,
    MemoryCombiningProbe,
    MemoryDeduplicationReport,
)


def test_hypervisor_memory_combining_configuration():
    """AC-9.1.1: Memory combining scan is configured and verified via hypervisor settings."""
    probe = MemoryCombiningProbe()
    config = MemoryCombiningConfig(
        enabled=True,
        scan_interval_seconds=45.0,
        low_priority_io=True,
        cpu_throttle_percent=0.5,
    )

    success = probe.configure_hypervisor(config)
    assert success is True

    current_cfg = probe.get_hypervisor_config()
    assert current_cfg.enabled is True
    assert current_cfg.scan_interval_seconds == 45.0
    assert current_cfg.low_priority_io is True
    assert current_cfg.cpu_throttle_percent == 0.5


def test_diagnostic_probe_reads_perf_counters():
    """AC-9.1.2: Diagnostic probe reads performance counters including shared pages and saved memory."""
    probe = MemoryCombiningProbe()
    counters = probe.read_perf_counters()

    assert "\\Hyper-V Dynamic Memory\\Memory Combining Shared Pages" in counters
    assert "\\Hyper-V Dynamic Memory\\Memory Combining Saved Memory (MB)" in counters
    assert "\\Hyper-V Dynamic Memory\\Memory Combining CPU Usage" in counters

    # Values must be numeric and non-negative
    shared_pages = counters["\\Hyper-V Dynamic Memory\\Memory Combining Shared Pages"]
    saved_mb = counters["\\Hyper-V Dynamic Memory\\Memory Combining Saved Memory (MB)"]
    cpu_usage = counters["\\Hyper-V Dynamic Memory\\Memory Combining CPU Usage"]

    assert isinstance(shared_pages, int) and shared_pages >= 0
    assert isinstance(saved_mb, (int, float)) and saved_mb >= 0.0
    assert isinstance(cpu_usage, (int, float)) and 0.0 <= cpu_usage <= 100.0


def test_fleet_deduplication_metrics_across_paused_cohort():
    """AC-9.1.2: Verifies non-zero page sharing and calculated report across paused instances."""
    probe = MemoryCombiningProbe()
    # Simulate a cohort of 40 identical Windows Server 2025 micro-VMs
    cohort = [f"mxc-paused-vm-{i:02d}" for i in range(1, 41)]

    report = probe.get_fleet_deduplication_metrics(
        vm_cohort=cohort,
        logical_ram_per_vm_mb=640.0,
    )

    assert isinstance(report, MemoryDeduplicationReport)
    assert report.is_enabled is True
    assert report.total_vms == 40
    assert report.logical_allocated_mb == 40 * 640.0  # 25,600 MB (25.6 GB)

    # Must verify non-zero page sharing across the cohort
    assert report.shared_pages_count > 0
    assert report.saved_memory_mb > 0.0

    # Effective host RAM must be strictly less than logical allocated RAM
    assert report.effective_host_ram_mb < report.logical_allocated_mb
    assert report.deduplication_ratio > 0.0

    # Scanner CPU overhead must be within BRU-009-03 limit (< 0.5%)
    assert report.scanner_cpu_percent <= 0.5


def test_disabled_memory_combining_behavior():
    """AC-9.1.1: When memory combining is disabled, saved memory is 0 MB and ratio is 0.0."""
    probe = MemoryCombiningProbe()
    probe.configure_hypervisor(MemoryCombiningConfig(enabled=False))

    report = probe.get_fleet_deduplication_metrics(
        vm_cohort=["vm-1", "vm-2"],
        logical_ram_per_vm_mb=640.0,
    )

    assert report.is_enabled is False
    assert report.shared_pages_count == 0
    assert report.saved_memory_mb == 0.0
    assert report.effective_host_ram_mb == report.logical_allocated_mb
    assert report.deduplication_ratio == 0.0
