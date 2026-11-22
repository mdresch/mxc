"""Contract Test: Story 9.2 — Deduplication Floor & Host Saturation Verification (WBS 10.2).

Governing Artifacts:
- ADR: ADR-011 (Hyper-V Host-Level Memory Combining & Fleet Page Deduplication)
- BRD: BRD-009 (BRU-009-01, BRU-009-02, BRU-009-04)
- FDD: FDD-009 (§1.1 Memory Combining Subsystem, §2 Invariant Contracts)
- Epic: Epic 009 (User Story 9.2, WBS 10.2)

Acceptance Criteria:
- AC-9.2.1: Net host physical memory consumption across 40 identical standby VMs does not exceed 18 GB
  (<= 450 MB effective host RAM each).
- AC-9.2.2: Copy-On-Write (COW) memory isolation is verified: page modifications in one tenant VM
  never corrupt or leak into peer VM memory.
"""

import pytest

from scripts.lib.memory_combining_probe import (
    COWIsolationVerificationResult,
    MemoryCombiningConfig,
    MemoryCombiningProbe,
    verify_copy_on_write_isolation,
    verify_host_saturation_floor,
)


def test_host_saturation_and_effective_ram_floor():
    """AC-9.2.1: 40 identical standby VMs consume <= 18 GB net physical host RAM (<= 450 MB each)."""
    probe = MemoryCombiningProbe()
    probe.configure_hypervisor(MemoryCombiningConfig(enabled=True))

    is_compliant, report = verify_host_saturation_floor(
        probe=probe,
        total_vms=40,
        logical_ram_per_vm_mb=640.0,
        max_net_host_ram_gb=18.0,
    )

    assert is_compliant is True
    assert report.total_vms == 40
    # Net physical memory consumption in GB <= 18.0 GB
    host_ram_gb = report.effective_host_ram_mb / 1024.0
    assert host_ram_gb <= 18.0

    # Effective RAM per guest <= 450 MB
    assert report.effective_ram_per_vm_mb <= 450.0

    # Fleet deduplication ratio >= 40% (BEN-14, BRD-009 §3)
    assert report.deduplication_ratio >= 0.40


def test_host_saturation_fails_when_memory_combining_disabled():
    """AC-9.2.1: Disabling memory combining causes host saturation to exceed 18 GB floor."""
    probe = MemoryCombiningProbe()
    probe.configure_hypervisor(MemoryCombiningConfig(enabled=False))

    is_compliant, report = verify_host_saturation_floor(
        probe=probe,
        total_vms=40,
        logical_ram_per_vm_mb=640.0,
        max_net_host_ram_gb=18.0,
    )

    assert is_compliant is False
    # Without combining, 40 * 640 MB = 25.0 GB > 18.0 GB
    host_ram_gb = report.effective_host_ram_mb / 1024.0
    assert host_ram_gb == 25.0
    assert report.effective_ram_per_vm_mb == 640.0


def test_copy_on_write_memory_isolation_invariant():
    """AC-9.2.2: COW isolation: modifying shared page in VM A never corrupts VM B."""
    probe = MemoryCombiningProbe()
    canary = b"TENANT_A_CONFIDENTIAL_PAYLOAD_XYZ_99"

    result = verify_copy_on_write_isolation(
        probe=probe,
        vm_source="mxc-tenant-vm-01",
        vm_target="mxc-tenant-vm-02",
        page_offset=0x1000,
        write_payload=canary,
    )

    assert isinstance(result, COWIsolationVerificationResult)
    assert result.is_isolated is True
    assert result.source_vm == "mxc-tenant-vm-01"
    assert result.target_vm == "mxc-tenant-vm-02"
    assert result.source_page_modified is True
    assert result.target_page_corrupted is False
    assert result.bytes_leaked == 0
    assert result.details == "Hardware COW fault cloned page into private frame; target VM memory intact."
