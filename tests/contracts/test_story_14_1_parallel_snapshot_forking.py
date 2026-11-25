"""Contract tests for Story 14.1 — Sub-500ms Parallel .avhdx Snapshot Branching (ADR-015).

Spec Gate Episode: spec-14_1-f72b6317 (Robust Utility Margin: +0.2207)
Contract Interpretations:
  Spec gate emitted zero warnings (all 4 adversarial checks [OK]: completeness, empty
  collection base case, explicit ValueError classes, architectural boundaries).
  I1: create_parallel_forks() allocates 1..max_parallel (default 5) active SnapshotBranch
      records anchored to an immutable parent_checkpoint_id within <= 500 ms, while
      discard_losing_branches() marks losers DISCARDED, handles None/empty safely, and
      preserves parent_hash bit-for-bit.
  I2: Nesting depth exceeding max_depth=4 raises ValueError("ERR_FORK_DEPTH_EXCEEDED"), and
      empty/None/duplicate/oversized branch requests raise ValueError("ERR_FORK_BOUNDS_INVALID").
"""

from __future__ import annotations

import hashlib
import time

import pytest

from scripts.lib.snapshot_fork_and_vmbus import (
    SnapshotBranch,
    create_parallel_forks,
    discard_losing_branches,
)


# Story 14.1 — AC-14.1.1 (ADR-015)
def test_ac_14_1_1_parallel_snapshot_forks_and_clean_discard_preserve_parent_hash():
    parent_checkpoint = "chk-win11-warm-001"
    parent_hash = hashlib.sha256(b"immutable-golden-parent-vhdx").hexdigest()
    branch_names = ["fix-auth", "fix-cache", "fix-retry", "fix-parser"]

    t0 = time.perf_counter()
    branches = create_parallel_forks(parent_checkpoint, branch_names)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms <= 500.0
    assert len(branches) == 4
    assert all(isinstance(b, SnapshotBranch) for b in branches)
    assert len({b.branch_id for b in branches}) == 4
    for name, branch in zip(branch_names, branches):
        assert branch.branch_id
        assert branch.parent_checkpoint_id == parent_checkpoint
        assert branch.depth == 1
        assert branch.diff_disk_path == f"{parent_checkpoint}/{name}.avhdx"
        assert branch.status == "ACTIVE"

    winner_id = branches[1].branch_id
    reconciled, returned_hash = discard_losing_branches(
        branches, winner_id, parent_hash=parent_hash
    )
    assert returned_hash == parent_hash
    assert len(reconciled) == 4
    for branch in reconciled:
        if branch.branch_id == winner_id:
            assert branch.status == "ACTIVE"
        else:
            assert branch.status == "DISCARDED"

    # Empty / None branch lists safely return ([], parent_hash) without mutation
    assert discard_losing_branches(None, winner_id, parent_hash=parent_hash) == ([], parent_hash)
    assert discard_losing_branches([], winner_id, parent_hash=parent_hash) == ([], parent_hash)

    # No winner (winning_branch_id=None) discards all branches cleanly
    all_discarded, hash_after = discard_losing_branches(branches, None, parent_hash=parent_hash)
    assert hash_after == parent_hash
    assert all(b.status == "DISCARDED" for b in all_discarded)


# Story 14.1 — AC-14.1.2 (ADR-015)
def test_ac_14_1_2_fork_depth_and_parallel_bounds_fail_closed():
    # Depth 3 -> child depth 4 is still within max_depth=4
    level4 = create_parallel_forks("chk-level-3", ["cand-a", "cand-b", "cand-c"], current_depth=3)
    assert all(b.depth == 4 for b in level4)

    # Depth 4 -> child depth 5 exceeds max_depth=4
    with pytest.raises(ValueError, match="ERR_FORK_DEPTH_EXCEEDED"):
        create_parallel_forks("chk-level-4", ["cand-a"], current_depth=4)

    for bad_depth in (-1, None, True):
        with pytest.raises(ValueError, match="ERR_FORK_DEPTH_EXCEEDED"):
            create_parallel_forks("chk-0", ["cand-a"], current_depth=bad_depth)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="ERR_FORK_DEPTH_EXCEEDED"):
        create_parallel_forks("chk-0", ["cand-a"], current_depth=0, max_depth=0)

    # Exceeding max_parallel=5 raises ERR_FORK_BOUNDS_INVALID
    with pytest.raises(ValueError, match="ERR_FORK_BOUNDS_INVALID"):
        create_parallel_forks("chk-0", ["b1", "b2", "b3", "b4", "b5", "b6"])

    # Empty / None / blank / duplicate branch names and invalid parent checkpoint fail closed
    for bad_branches in (None, [], ["  "], ["dup", "dup"], ["ok", ""]):
        with pytest.raises(ValueError, match="ERR_FORK_BOUNDS_INVALID"):
            create_parallel_forks("chk-0", bad_branches)  # type: ignore[arg-type]

    for bad_parent in (None, "", "   "):
        with pytest.raises(ValueError, match="ERR_FORK_BOUNDS_INVALID"):
            create_parallel_forks(bad_parent, ["b1"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="ERR_FORK_BOUNDS_INVALID"):
        create_parallel_forks("chk-0", ["b1"], max_parallel=0)
