"""Contract test for Story 4.2: Trimmed paused footprint bounds.

Governed by ADR-004, BRD-004 (BRU-004-03, BRU-004-04), FDD-004, and WBS 5.2.
Enforces AC-03.2 & BEN-10:
- Given release restores `baseline-hot-ready` then suspends, when RAM is measured,
  then footprint is about 1.0–1.2 GB (1024–1228.8 MB) and configured target is recorded.
- Guest memory stays resident; 0 MB reading means Saved/Stopped, not Paused (BRU-004-03).
- Trim must execute before Suspend-VM while vCPUs run (FDD-004).
"""

from __future__ import annotations

import pytest

from scripts.lib.paused_ram import (
    FleetAuditError,
    MemoryFootprintReading,
    PausedRamFleetManager,
    StandbyVMDescriptor,
    StandbyVMState,
    TrimExecutionError,
)


class TestStory42TrimmedPausedFootprint:
    """Acceptance contract suite for AC-03.2 / Story 4.2."""

    def test_paused_vm_memory_within_target_bounds(self) -> None:
        """AC-03.2 / BEN-10: Paused RAM footprint measures ~1.0–1.2 GB and records configured target."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-prod-01",
            state=StandbyVMState.RUNNING,
            assigned_ram_mb=2048.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
            session_avhdx="mxc-hv-prod-01.avhdx",
        )
        manager.register_vm(descriptor)

        # Release, restore baseline-hot-ready, trim working set, and suspend
        reading: MemoryFootprintReading = manager.release_restore_and_suspend(
            vm_name="mxc-hv-prod-01",
            checkpoint_name="baseline-hot-ready",
        )

        assert reading.vm_name == "mxc-hv-prod-01"
        assert reading.state == StandbyVMState.PAUSED
        assert reading.is_resident is True
        assert 1024.0 <= reading.resident_ram_mb <= 1228.8
        assert reading.configured_target_min_mb == 1024.0
        assert reading.configured_target_max_mb == 1228.8
        assert reading.is_within_target_bounds is True

    def test_resident_memory_cannot_be_zero(self) -> None:
        """BRU-004-03: Guest memory must stay resident; 0 MB reading violates Paused invariant."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-saved-invalid",
            state=StandbyVMState.SAVED,
            assigned_ram_mb=0.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
        )
        manager.register_vm(descriptor)

        with pytest.raises(FleetAuditError) as exc_info:
            manager.measure_paused_ram_footprint("mxc-hv-saved-invalid")

        assert "BRU-004-03" in str(exc_info.value)
        assert "0 mb" in str(exc_info.value).lower() or "resident" in str(exc_info.value).lower()

    def test_trim_must_occur_before_suspend(self) -> None:
        """FDD-004: Balloon/WorkingSet trim cannot execute after Suspend-VM (vCPUs frozen)."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-already-paused",
            state=StandbyVMState.PAUSED,
            assigned_ram_mb=1800.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
            is_trimmed=False,
        )
        manager.register_vm(descriptor)

        with pytest.raises(TrimExecutionError) as exc_info:
            manager.trim_working_set("mxc-hv-already-paused")

        assert "frozen" in str(exc_info.value).lower() or "paused" in str(exc_info.value).lower()
        assert "before" in str(exc_info.value).lower()

    def test_configured_target_recorded_in_telemetry(self) -> None:
        """AC-03.2 / BEN-10: Configured target footprint range is explicitly recorded."""
        manager = PausedRamFleetManager()
        manager.register_vm(
            StandbyVMDescriptor(
                vm_name="mxc-hv-prod-02",
                state=StandbyVMState.RUNNING,
                assigned_ram_mb=2048.0,
                backing_vhdx="winserv2025-prod-adpa.vhdx",
            )
        )

        reading = manager.release_restore_and_suspend("mxc-hv-prod-02")
        manifest = reading.to_telemetry_dict()

        assert "configured_target" in manifest
        assert manifest["configured_target"]["min_mb"] == 1024.0
        assert manifest["configured_target"]["max_mb"] == 1228.8
        assert manifest["benefit_anchor"] == "BEN-10"
