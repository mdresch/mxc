"""Contract test for Story 4.3: Sub-300 ms resume latency.

Governed by ADR-004, BRD-004 (BRU-004-05), FDD-004, and WBS 5.3.
Enforces AC-03.3:
- Given ingress dispatches wake, when `Resume-VM` completes, elapsed time <= 300 ms.
- Resume occurs from host RAM resident pages without disk page-in.
- Resumes that wait on disk page-in (e.g. from Saved state) fail the 300 ms ceiling (FDD-004).
"""

from __future__ import annotations

import pytest

from scripts.lib.paused_ram import (
    FleetAuditError,
    PausedRamFleetManager,
    ResumeResult,
    StandbyVMDescriptor,
    StandbyVMState,
)


class TestStory43Sub300msResume:
    """Acceptance contract suite for AC-03.3 / Story 4.3."""

    def test_resume_vm_from_paused_state_completes_under_300ms(self) -> None:
        """AC-03.3 / BRU-004-05: Resume-VM unpauses resident RAM in <= 300 ms."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-prod-01",
            state=StandbyVMState.PAUSED,
            assigned_ram_mb=1150.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
            session_avhdx="mxc-hv-prod-01.avhdx",
            is_trimmed=True,
        )
        manager.register_vm(descriptor)

        res: ResumeResult = manager.resume_vm("mxc-hv-prod-01")

        assert res.vm_name == "mxc-hv-prod-01"
        assert res.elapsed_ms <= 300.0
        assert res.is_sub_300ms is True
        assert res.waited_on_disk_pagein is False
        assert res.prior_state == StandbyVMState.PAUSED
        assert res.current_state == StandbyVMState.RUNNING

    def test_resume_from_saved_state_violates_300ms_ceiling(self) -> None:
        """ADR-004 §5: Saved state pays disk page-in penalty and fails 300 ms ceiling."""
        manager = PausedRamFleetManager()
        descriptor = StandbyVMDescriptor(
            vm_name="mxc-hv-saved-slow",
            state=StandbyVMState.SAVED,
            assigned_ram_mb=0.0,
            backing_vhdx="winserv2025-prod-adpa.vhdx",
        )
        manager.register_vm(descriptor)

        res = manager.resume_vm("mxc-hv-saved-slow")

        assert res.waited_on_disk_pagein is True
        assert res.is_sub_300ms is False
        assert res.elapsed_ms > 300.0

    def test_batch_fleet_resume_all_meet_sub_300ms_ceiling(self) -> None:
        """AC-03.3: All standby fleet members satisfy <= 300 ms resume ceiling."""
        manager = PausedRamFleetManager()
        for i in range(1, 6):
            manager.register_vm(
                StandbyVMDescriptor(
                    vm_name=f"mxc-hv-prod-{i:02d}",
                    state=StandbyVMState.PAUSED,
                    assigned_ram_mb=1120.0,
                    backing_vhdx="winserv2025-prod-adpa.vhdx",
                    session_avhdx=f"mxc-hv-prod-{i:02d}.avhdx",
                    is_trimmed=True,
                )
            )

        for i in range(1, 6):
            res = manager.resume_vm(f"mxc-hv-prod-{i:02d}")
            assert res.elapsed_ms <= 300.0
            assert res.is_sub_300ms is True
            assert res.waited_on_disk_pagein is False

    def test_resume_unknown_vm_raises_error(self) -> None:
        """Error handling: Non-existent VM raises FleetAuditError."""
        manager = PausedRamFleetManager()

        with pytest.raises(FleetAuditError) as exc_info:
            manager.resume_vm("mxc-hv-nonexistent")

        assert "not found" in str(exc_info.value).lower()
