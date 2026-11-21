"""Contract test for Story 5.1: Ephemeral session disk and parent immutability.

Governed by ADR-005, BRD-005 (BRU-005-01, BRU-005-04), FDD-005, and WBS 6.1.
Enforces AC-02.1 & AC-02.2:
- Given files written on `.avhdx`, when session ends or 300 s idle with no open requests,
  then `.avhdx` is deleted (`AC-02.1`).
- Given parent `winserv2025-prod-adpa.vhdx`, when SHA-256 compared before and after,
  then hash is strictly unchanged (`AC-02.2`).
- Hung requests past 900 s terminate with HTTP 504 and trigger instance reap (`BRU-005-04`).
"""

from __future__ import annotations

import hashlib
import pytest

from scripts.lib.session_sterility import (
    DifferencingDiskStatus,
    HungRequestError,
    ParentIntegrityStatus,
    SessionDiskManager,
    SessionLifecycleState,
    SessionRecord,
)


class TestStory51EphemeralSessionDisk:
    """Acceptance contract suite for AC-02.1, AC-02.2 / Story 5.1."""

    def test_differencing_disk_deleted_on_session_release(self) -> None:
        """AC-02.1: Given files written on .avhdx, when session ends, .avhdx is deleted."""
        manager = SessionDiskManager(parent_vhdx_name="winserv2025-prod-adpa.vhdx")

        # 1. Lease session and attach child differencing disk
        session = manager.create_session(
            session_id="sess-prod-01",
            vm_name="mxc-hv-prod-01",
        )
        assert session.differencing_disk_path.endswith(".avhdx")
        assert session.state == SessionLifecycleState.ACTIVE

        # 2. Write session files (simulating guest state mutation)
        manager.write_session_file(session.session_id, "C:\\workspace\\temp_calc.dat", b"payload-12345")
        assert manager.has_session_file(session.session_id, "C:\\workspace\\temp_calc.dat") is True

        # 3. Release session
        release_res = manager.release_session(session.session_id)
        assert release_res.is_disk_deleted is True
        assert release_res.state == SessionLifecycleState.DISCARDED
        assert manager.has_session_file(session.session_id, "C:\\workspace\\temp_calc.dat") is False

    def test_differencing_disk_deleted_after_300s_idle_with_zero_requests(self) -> None:
        """AC-02.1: After 300 s idle with 0 open requests, .avhdx is deleted."""
        manager = SessionDiskManager(parent_vhdx_name="winserv2025-prod-adpa.vhdx")
        session = manager.create_session("sess-prod-02", "mxc-hv-prod-02")
        manager.write_session_file(session.session_id, "C:\\workspace\\cache.bin", b"binary-data")

        # 301 seconds elapsed with 0 active requests
        reap_res = manager.check_idle_timeout(
            session_id=session.session_id,
            idle_seconds=301.0,
            active_open_requests=0,
        )
        assert reap_res.is_reaped is True
        assert reap_res.is_disk_deleted is True
        assert manager.has_session_file(session.session_id, "C:\\workspace\\cache.bin") is False

    def test_differencing_disk_not_deleted_if_active_requests_remain(self) -> None:
        """AC-02.1: Idle timeout does NOT delete .avhdx if active_open_requests > 0."""
        manager = SessionDiskManager(parent_vhdx_name="winserv2025-prod-adpa.vhdx")
        session = manager.create_session("sess-prod-03", "mxc-hv-prod-03")

        reap_res = manager.check_idle_timeout(
            session_id=session.session_id,
            idle_seconds=400.0,
            active_open_requests=1,
        )
        assert reap_res.is_reaped is False
        assert reap_res.is_disk_deleted is False
        assert reap_res.reason == "active_requests_present"

    def test_parent_vhdx_sha256_strictly_unchanged(self) -> None:
        """AC-02.2: Parent winserv2025-prod-adpa.vhdx SHA-256 stays identical before and after."""
        fake_parent_content = b"PRISTINE_WINSERV_2025_PRODUCTION_IMAGE_VHDX_DATA"
        initial_hash = hashlib.sha256(fake_parent_content).hexdigest()

        manager = SessionDiskManager(
            parent_vhdx_name="winserv2025-prod-adpa.vhdx",
            parent_initial_hash=initial_hash,
        )

        session = manager.create_session("sess-prod-04", "mxc-hv-prod-04")
        # Mutate child session disk
        manager.write_session_file(session.session_id, "C:\\temp\\exploit.exe", b"malware-payload")
        manager.release_session(session.session_id)

        # Integrity audit
        audit: ParentIntegrityStatus = manager.verify_parent_integrity(current_parent_content=fake_parent_content)
        assert audit.is_intact is True
        assert audit.before_hash == initial_hash
        assert audit.after_hash == initial_hash
        assert audit.parent_name == "winserv2025-prod-adpa.vhdx"

    def test_hung_request_aborts_at_900s_with_504(self) -> None:
        """BRU-005-04 / ADR-005 §4.6: Request hanging past 900s returns HTTP 504 and reaps instance."""
        manager = SessionDiskManager(parent_vhdx_name="winserv2025-prod-adpa.vhdx")
        session = manager.create_session("sess-prod-05", "mxc-hv-prod-05")

        with pytest.raises(HungRequestError) as exc_info:
            manager.monitor_request_duration(
                session_id=session.session_id,
                request_elapsed_seconds=905.0,
            )

        assert exc_info.value.status_code == 504
        assert "900" in str(exc_info.value)
        # Verify instance was reaped
        sess_record = manager.get_session(session.session_id)
        assert sess_record.state == SessionLifecycleState.REAPED
