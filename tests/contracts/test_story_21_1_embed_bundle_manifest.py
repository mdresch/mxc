"""Contract tests for Story 21.1 — Deterministic Offline Pilot Bundle Manifest Builder (ADR-022).

Spec Gate Episode: spec-21_1-6cf42f62 (Robust Utility Margin: +0.2152)
Contract Interpretations:
  I1: build_embed_bundle_manifest() emits an immutable EmbedBundleManifest with offline_only=True,
      trimmed bundle_version, lowercase 64-hex SHA-256 digests for all vendored payload artifacts
      (wxc-exec.exe, golden_image_registry.json, HIL scripts), and lowercase 64-hex golden_vhdx_sha256.
  I2 (Defensive None-Safety & Input Validation): None, blank, or non-string bundle_version; None,
      non-dict, or empty file_hashes; blank, non-string, absolute, or traversal artifact paths; or
      malformed non-64-hex SHA-256 digests all fail closed by raising ValueError.
  I3: Manifest generation executes 100% deterministically and offline with zero outbound network calls
      (LL-011, LL-022).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import socket

import pytest

from scripts.lib.mxc_embed_packager import (
    EmbedBundleManifest,
    build_embed_bundle_manifest,
)

SAMPLE_EXE_SHA256 = "A1B2C3D4" * 8
SAMPLE_REG_SHA256 = "11223344" * 8
SAMPLE_HIL_SHA256 = "DEADBEEF" * 8
SAMPLE_VHDX_SHA256 = "F0E1D2C3" * 8


# Story 21.1 — AC-21.1.1 (ADR-022)
def test_ac_21_1_1_build_embed_bundle_manifest_emits_frozen_offline_manifest(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Network egress is strictly prohibited during offline bundle packaging")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    input_hashes = {
        "bin/wxc-exec.exe": SAMPLE_EXE_SHA256,
        "registry/golden_image_registry.json": SAMPLE_REG_SHA256,
        "scripts/hyperv/demo_win11_agent_sandbox.ps1": SAMPLE_HIL_SHA256,
    }

    manifest = build_embed_bundle_manifest(
        bundle_version="  2026.11.25-eu-pilot  ",
        file_hashes=input_hashes,
        golden_vhdx_sha256=SAMPLE_VHDX_SHA256,
    )

    assert isinstance(manifest, EmbedBundleManifest)
    assert manifest.bundle_version == "2026.11.25-eu-pilot"
    assert manifest.offline_only is True
    assert manifest.golden_vhdx_sha256 == SAMPLE_VHDX_SHA256.lower()
    assert manifest.artifacts == {
        "bin/wxc-exec.exe": SAMPLE_EXE_SHA256.lower(),
        "registry/golden_image_registry.json": SAMPLE_REG_SHA256.lower(),
        "scripts/hyperv/demo_win11_agent_sandbox.ps1": SAMPLE_HIL_SHA256.lower(),
    }

    # Mutating caller dict must not affect the manifest
    input_hashes["bin/wxc-exec.exe"] = "0" * 64
    assert manifest.artifacts["bin/wxc-exec.exe"] == SAMPLE_EXE_SHA256.lower()

    # Manifest dataclass must be frozen
    with pytest.raises(FrozenInstanceError):
        manifest.offline_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        manifest.bundle_version = "mutated"  # type: ignore[misc]


# Story 21.1 — AC-21.1.2 (ADR-022)
@pytest.mark.parametrize(
    ("bundle_version", "file_hashes", "golden_vhdx_sha256"),
    [
        # Invalid bundle_version
        (None, {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("   ", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        (123, {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        # Invalid file_hashes container
        ("1.0.0", None, SAMPLE_VHDX_SHA256),
        ("1.0.0", {}, SAMPLE_VHDX_SHA256),
        ("1.0.0", [("bin/wxc-exec.exe", SAMPLE_EXE_SHA256)], SAMPLE_VHDX_SHA256),
        ("1.0.0", "bin/wxc-exec.exe", SAMPLE_VHDX_SHA256),
        # Invalid artifact relative path keys
        ("1.0.0", {"": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"   ": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {None: SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {123: SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"/etc/passwd": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"\\windows\\system32\\cmd.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"C:\\HyperV\\wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"../escape/wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/../../wxc-exec.exe": SAMPLE_EXE_SHA256}, SAMPLE_VHDX_SHA256),
        # Invalid artifact SHA-256 digests
        ("1.0.0", {"bin/wxc-exec.exe": None}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/wxc-exec.exe": ""}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/wxc-exec.exe": "deadbeef"}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/wxc-exec.exe": "g" * 64}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/wxc-exec.exe": ("a" * 64) + "\n"}, SAMPLE_VHDX_SHA256),
        ("1.0.0", {"bin/wxc-exec.exe": 999}, SAMPLE_VHDX_SHA256),
        # Invalid golden_vhdx_sha256
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, None),
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, ""),
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, "abc123"),
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, "z" * 64),
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, ("b" * 64) + "\n"),
        ("1.0.0", {"bin/wxc-exec.exe": SAMPLE_EXE_SHA256}, 42),
    ],
)
def test_ac_21_1_2_rejects_invalid_bundle_version_hashes_or_golden_sha(
    bundle_version,
    file_hashes,
    golden_vhdx_sha256,
):
    with pytest.raises(ValueError):
        build_embed_bundle_manifest(
            bundle_version=bundle_version,
            file_hashes=file_hashes,
            golden_vhdx_sha256=golden_vhdx_sha256,
        )
