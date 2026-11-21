"""Contract tests for Story 5.3 — Discard and reproduce (WBS 6.3).

Acceptance Criteria:
- AC1: Given Path A whole-guest removal, when next guest is provisioned,
       then parent is approved production image (BEN-12).
- AC2: Given Path B .avhdx only, when next session starts,
       then parent is still approved production image and guest may remain.
- Invariants: Neither path inherits disk changes from the previous session;
  attempting to anchor on developer image (winserv2025-mxc-dev.vhdx) is strictly rejected (BRU-003-01 / BRU-005-02).
"""

import pytest
from scripts.lib.session_sterility import (
    SessionDiskManager,
    DiscardPath,
    DiscardResult,
    SessionLifecycleState,
    UnapprovedParentImageError,
    APPROVED_PRODUCTION_PARENT,
)


class TestStory53DiscardAndReproduce:
    """Validate Path A (whole guest) and Path B (.avhdx only) discard and reproduction."""

    @pytest.fixture
    def manager(self):
        return SessionDiskManager(parent_vhdx_name=APPROVED_PRODUCTION_PARENT)

    # -------------------------------------------------------------------------
    # AC1: Path A Whole-Guest Removal
    # -------------------------------------------------------------------------
    def test_path_a_whole_guest_removal(self, manager):
        """AC1 (BEN-12): Path A removes the whole guest and reproduces from approved production parent."""
        session_1 = manager.create_session("sess-100", "mxc-guest-alpha")
        manager.record_session_file("sess-100", "C:\\temp\\session_data.txt")
        manager.record_session_file("sess-100", "C:\\temp\\scratch_cache.bin")
        assert len(session_1.files) == 2

        # Execute Path A discard
        result: DiscardResult = manager.execute_discard_path(
            session_id="sess-100",
            path=DiscardPath.PATH_A_WHOLE_GUEST,
            next_session_id="sess-101",
        )

        assert result.discard_path == DiscardPath.PATH_A_WHOLE_GUEST
        assert not result.guest_persisted, "Path A must not persist the existing guest"
        assert result.is_residue_eliminated
        assert result.next_parent_image == APPROVED_PRODUCTION_PARENT
        assert result.next_parent_image != "winserv2025-mxc-dev.vhdx"

        # Verify old session wiped
        assert len(session_1.files) == 0
        assert session_1.state == SessionLifecycleState.DISCARDED

        # Verify new session clean
        session_2 = manager.get_session("sess-101")
        assert len(session_2.files) == 0
        assert session_2.state == SessionLifecycleState.ACTIVE
        assert session_2.vm_name != session_1.vm_name  # new guest instance

    # -------------------------------------------------------------------------
    # AC2: Path B Differencing Disk (.avhdx) Only Discard
    # -------------------------------------------------------------------------
    def test_path_b_differencing_disk_only(self, manager):
        """AC2 (BEN-12): Path B discards only .avhdx, retains guest, next session parent is approved image."""
        session_1 = manager.create_session("sess-200", "mxc-guest-bravo")
        manager.record_session_file("sess-200", "C:\\Users\\Default\\AppData\\payload.dll")
        assert len(session_1.files) == 1

        # Execute Path B discard
        result: DiscardResult = manager.execute_discard_path(
            session_id="sess-200",
            path=DiscardPath.PATH_B_DIFFERENCING_ONLY,
            next_session_id="sess-201",
        )

        assert result.discard_path == DiscardPath.PATH_B_DIFFERENCING_ONLY
        assert result.guest_persisted, "Path B retains the guest VM shell"
        assert result.is_residue_eliminated
        assert result.next_parent_image == APPROVED_PRODUCTION_PARENT
        assert result.next_parent_image != "winserv2025-mxc-dev.vhdx"

        # Verify old session wiped
        assert len(session_1.files) == 0
        assert session_1.state == SessionLifecycleState.DISCARDED

        # Verify new session clean and retains same guest VM
        session_2 = manager.get_session("sess-201")
        assert len(session_2.files) == 0
        assert session_2.state == SessionLifecycleState.ACTIVE
        assert session_2.vm_name == session_1.vm_name  # same guest shell reused

    # -------------------------------------------------------------------------
    # Invariant: Developer and unapproved images strictly rejected
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("invalid_parent", [
        "winserv2025-mxc-dev.vhdx",
        "custom-dev-golden.vhdx",
        "unapproved-base.vhdx",
        "",
    ])
    def test_unapproved_or_developer_parent_rejected(self, invalid_parent):
        """Reject instantiation with dev image or unapproved parent per BRU-003-01 and BRU-005-02."""
        with pytest.raises(UnapprovedParentImageError) as exc_info:
            SessionDiskManager(parent_vhdx_name=invalid_parent)
        assert "BRU-003-01" in str(exc_info.value) or "BRU-005-02" in str(exc_info.value)

    # -------------------------------------------------------------------------
    # Invariant: Dual discard path equivalence
    # -------------------------------------------------------------------------
    def test_dual_discard_path_equivalence(self, manager):
        """BEN-12: Both discard paths guarantee zero residue carryover and identical approved parent."""
        # Run Path A
        s_a = manager.create_session("sess-a1", "vm-equiv-a")
        manager.record_session_file("sess-a1", "C:\\temp\\file_a.txt")
        res_a = manager.execute_discard_path("sess-a1", DiscardPath.PATH_A_WHOLE_GUEST, "sess-a2")

        # Run Path B
        s_b = manager.create_session("sess-b1", "vm-equiv-b")
        manager.record_session_file("sess-b1", "C:\\temp\\file_b.txt")
        res_b = manager.execute_discard_path("sess-b1", DiscardPath.PATH_B_DIFFERENCING_ONLY, "sess-b2")

        # Equivalence checks
        assert res_a.is_residue_eliminated == res_b.is_residue_eliminated is True
        assert res_a.next_parent_image == res_b.next_parent_image == APPROVED_PRODUCTION_PARENT
        assert len(manager.get_session("sess-a2").files) == len(manager.get_session("sess-b2").files) == 0
