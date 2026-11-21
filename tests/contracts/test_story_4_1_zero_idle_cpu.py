"""Contract test for Story 4.1: Zero idle CPU for Paused standby fleet.

Governed by ADR-004, BRD-004 (BRU-004-01, BRU-004-02, BRU-004-06), FDD-004, and WBS 5.1.
Enforces AC-03.1:
- Given 10 standby VMs Paused, when host CPU is read, total CPU for those guests is 0.0%.
- Host GPU for paused guests is 0.0% (absent partition counts as 0.0% with note).
"""

from __future__ import annotations

import pytest

from scripts.lib.paused_ram import (
    FleetAuditError,
    HostResourceMetrics,
    PausedRamFleetManager,
    StandbyVMDescriptor,
    StandbyVMState,
)


class TestStory41ZeroIdleCpu:
    """Acceptance contract suite for AC-03.1 / Story 4.1."""

    def test_ten_standby_vms_paused_measure_zero_cpu(self) -> None:
        """AC-03.1 / BRU-004-01: Given 10 standby VMs Paused, host CPU is strictly 0.0%."""
        manager = PausedRamFleetManager()

        # Provision 10 standby VMs and place them in Paused state
        for i in range(1, 11):
            manager.register_vm(
                StandbyVMDescriptor(
                    vm_name=f"mxc-hv-prod-{i:02d}",
                    state=StandbyVMState.PAUSED,
                    assigned_ram_mb=1150.0,
                    backing_vhdx="winserv2025-prod-adpa.vhdx",
                    session_avhdx=f"mxc-hv-prod-{i:02d}.avhdx",
                    has_gpu_partition=False,
                )
            )

        assert manager.standby_count == 10

        metrics: HostResourceMetrics = manager.read_host_resource_metrics()
        assert metrics.total_cpu_pct == 0.0
        assert metrics.max_single_vm_cpu_pct == 0.0
        assert metrics.all_guests_paused is True
        for vm_metric in metrics.vm_metrics:
            assert vm_metric.cpu_pct == 0.0
            assert vm_metric.state == StandbyVMState.PAUSED

    def test_paused_standby_vms_measure_zero_gpu(self) -> None:
        """BRU-004-02: Paused guests measure 0.0% GPU; absent partition noted."""
        manager = PausedRamFleetManager()
        manager.register_vm(
            StandbyVMDescriptor(
                vm_name="mxc-hv-prod-01",
                state=StandbyVMState.PAUSED,
                assigned_ram_mb=1100.0,
                backing_vhdx="winserv2025-prod-adpa.vhdx",
                session_avhdx="mxc-hv-prod-01.avhdx",
                has_gpu_partition=False,
            )
        )

        metrics = manager.read_host_resource_metrics()
        assert metrics.total_gpu_pct == 0.0
        vm_m = metrics.vm_metrics[0]
        assert vm_m.gpu_pct == 0.0
        assert "absent" in vm_m.gpu_note.lower() or "0.0%" in vm_m.gpu_note

    def test_running_idle_vm_violates_zero_cpu_invariant(self) -> None:
        """BRU-004-01 / ADR-004 §4.1: A guest left Running has non-zero CPU and is rejected."""
        manager = PausedRamFleetManager()
        manager.register_vm(
            StandbyVMDescriptor(
                vm_name="mxc-hv-prod-erroneous-running",
                state=StandbyVMState.RUNNING,
                assigned_ram_mb=2048.0,
                backing_vhdx="winserv2025-prod-adpa.vhdx",
                session_avhdx="mxc-hv-prod-erroneous.avhdx",
                has_gpu_partition=False,
            )
        )

        with pytest.raises(FleetAuditError) as exc_info:
            manager.verify_zero_idle_cpu_invariant()

        assert "BRU-004-01" in str(exc_info.value)
        assert "running" in str(exc_info.value).lower()
        assert "0.0%" in str(exc_info.value)

    def test_fleet_with_mixed_states_rejects_standby_pool_certification(self) -> None:
        """ADR-004: All members of standby pool must be strictly Paused."""
        manager = PausedRamFleetManager()
        # 9 Paused, 1 Saved (not Paused)
        for i in range(1, 10):
            manager.register_vm(
                StandbyVMDescriptor(
                    vm_name=f"mxc-hv-prod-{i:02d}",
                    state=StandbyVMState.PAUSED,
                    assigned_ram_mb=1150.0,
                    backing_vhdx="winserv2025-prod-adpa.vhdx",
                    session_avhdx=f"mxc-hv-prod-{i:02d}.avhdx",
                )
            )
        manager.register_vm(
            StandbyVMDescriptor(
                vm_name="mxc-hv-prod-10",
                state=StandbyVMState.SAVED,
                assigned_ram_mb=0.0,  # Saved VM drops host RAM to 0
                backing_vhdx="winserv2025-prod-adpa.vhdx",
                session_avhdx="mxc-hv-prod-10.avhdx",
            )
        )

        with pytest.raises(FleetAuditError) as exc_info:
            manager.verify_zero_idle_cpu_invariant()

        assert "Saved" in str(exc_info.value) or "Paused" in str(exc_info.value)

    def test_paused_guest_retains_allocated_disks(self) -> None:
        """BRU-004-06: Paused guest keeps parent VHDX and session .avhdx allocated."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-prod-01",
            state=StandbyVMState.PAUSED,
            assigned_ram_mb=1120.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
            session_avhdx="mxc-hv-prod-01.avhdx",
        )
        manager.register_vm(descriptor)

        disk_status = manager.verify_disk_allocations("mxc-hv-prod-01")
        assert disk_status.parent_vhdx_allocated is True
        assert disk_status.session_avhdx_allocated is True
        assert disk_status.parent_vhdx_path == "winserv2025-prod-adpa.vhdx"
