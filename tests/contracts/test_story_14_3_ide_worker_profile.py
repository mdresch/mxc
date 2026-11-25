"""Contract tests for Story 14.3 — Standardized Ephemeral IDE Worker Profile (ADR-015).

Spec Gate Episode: spec-14_3-34aecf5b (Robust Utility Margin: +0.2129)
Contract Interpretations:
  Spec gate emitted zero warnings (all adversarial checks [OK]: completeness, defensive
  None-handling, storage boundary).
  I1: validate_ide_worker_profile() admits Cursor, Antigravity, and Claude Code worker
      profiles configured with zero_secret=True, mxc-sync mode, non-empty toolchains,
      zero guest secrets, and ram_mb >= 2048, returning (True, "OK").
  I2: None, empty dicts, unsupported IDEs, missing/empty toolchains, ram_mb < 2048, or
      non-zero-secret configurations fail closed with (False, "ERR_WORKER_PROFILE_INVALID").
"""

from __future__ import annotations

from scripts.lib.snapshot_fork_and_vmbus import validate_ide_worker_profile


# Story 14.3 — AC-14.3.1 (ADR-015)
def test_ac_14_3_1_valid_ide_worker_profiles_return_ok():
    for client in ("cursor", "antigravity", "claude-code"):
        profile = {
            "ide_client": client,
            "zero_secret": True,
            "sync_mode": "mxc-sync",
            "toolchain": ["git", "python3", "pytest"],
            "guest_secrets_count": 0,
            "ram_mb": 4096,
        }
        assert validate_ide_worker_profile(profile) == (True, "OK")

    # Minimal valid profile using default sync_mode and toolchain_packages alias at 2048 MB floor
    minimal_profile = {
        "ide_client": "cursor",
        "zero_secret": True,
        "toolchain_packages": ["git", "uv"],
        "ram_mb": 2048,
    }
    assert validate_ide_worker_profile(minimal_profile) == (True, "OK")


# Story 14.3 — AC-14.3.2 (ADR-015)
def test_ac_14_3_2_invalid_or_insecure_ide_worker_profiles_fail_closed():
    invalid_profiles = [
        None,
        {},
        ["cursor"],  # non-dict
        {
            "ide_client": "unknown-ide",
            "zero_secret": True,
            "toolchain": ["git"],
        },
        {
            "ide_client": "cursor",
            "zero_secret": False,
            "toolchain": ["git"],
        },
        {
            "ide_client": "antigravity",
            "toolchain": ["git"],  # missing zero_secret
        },
        {
            "ide_client": "claude-code",
            "zero_secret": True,
            "sync_mode": "ssh-agent",
            "toolchain": ["git"],
        },
        {
            "ide_client": "cursor",
            "zero_secret": True,
            "sync_mode": None,
            "toolchain": ["git"],
        },
        {
            "ide_client": "cursor",
            "zero_secret": True,
            # missing toolchain / toolchain_packages
        },
        {
            "ide_client": "cursor",
            "zero_secret": True,
            "toolchain": [],
        },
        {
            "ide_client": "cursor",
            "zero_secret": True,
            "toolchain": "git",  # string instead of sequence
        },
        {
            "ide_client": "cursor",
            "zero_secret": True,
            "toolchain": ["git", "  "],  # blank item
        },
        {
            "ide_client": "antigravity",
            "zero_secret": True,
            "toolchain": ["git"],
            "guest_secrets_count": 1,
        },
        {
            "ide_client": "claude-code",
            "zero_secret": True,
            "toolchain": ["git"],
            "ram_mb": 1024,
        },
    ]

    for bad_profile in invalid_profiles:
        assert validate_ide_worker_profile(bad_profile) == (  # type: ignore[arg-type]
            False,
            "ERR_WORKER_PROFILE_INVALID",
        )
