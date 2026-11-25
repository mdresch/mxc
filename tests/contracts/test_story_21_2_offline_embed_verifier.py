"""Contract tests for Story 21.2 — Zero-Cloud Offline Bundle Verifier & <= 15 min 5-Act Gate (ADR-022).

Spec Gate Episode: spec-21_2-e0a22b0e (Robust Utility Margin: +0.2129)
Contract Interpretations:
  I1: verify_embed_bundle_offline() executes 100% offline with zero outbound network calls (LL-011,
      LL-022), returning (True, "OK") iff outbound_internet_attempted is False, manifest is a valid
      offline_only=True EmbedBundleManifest with exact key-set and constant-time SHA-256 digest match
      against actual_file_hashes, and install_minutes_estimate is a finite non-boolean number in
      (0.0, 15.0].
  I2: Fail-closed precedence evaluates network egress (ERR_NETWORK_EGRESS_ATTEMPTED) first, then
      bundle/manifest integrity (ERR_BUNDLE_INTEGRITY_FAILED) via constant-time hmac.compare_digest,
      then install duration SLA budget (ERR_INSTALL_BUDGET_EXCEEDED).
  I3: Non-finite (NaN/Inf), non-positive (<= 0.0), over-budget (> 15.0), boolean, or None install
      estimates fail closed deterministically without using math.isclose (IMP-024).
"""

from __future__ import annotations

import hmac
import socket

import pytest

from scripts.lib.mxc_embed_packager import (
    EmbedBundleManifest,
    build_embed_bundle_manifest,
    verify_embed_bundle_offline,
)

EXE_SHA = "a1b2c3d4" * 8
REG_SHA = "11223344" * 8
HIL_SHA = "deadbeef" * 8
VHDX_SHA = "f0e1d2c3" * 8


def _valid_manifest() -> EmbedBundleManifest:
    return build_embed_bundle_manifest(
        bundle_version="2026.11.25-eu-pilot",
        file_hashes={
            "bin/wxc-exec.exe": EXE_SHA,
            "registry/golden_image_registry.json": REG_SHA,
            "scripts/hyperv/demo_win11_agent_sandbox.ps1": HIL_SHA,
        },
        golden_vhdx_sha256=VHDX_SHA,
    )


def _matching_hashes() -> dict[str, str]:
    return {
        "bin/wxc-exec.exe": EXE_SHA,
        "registry/golden_image_registry.json": REG_SHA,
        "scripts/hyperv/demo_win11_agent_sandbox.ps1": HIL_SHA,
    }


# Story 21.2 — AC-21.2.1 (ADR-022)
def test_ac_21_2_1_verify_embed_bundle_offline_admits_matching_bundle_with_zero_network_calls(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Network egress is strictly prohibited during MXC Embed offline verification")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    manifest = _valid_manifest()

    # Standard 10.0-minute default install budget
    assert verify_embed_bundle_offline(manifest, _matching_hashes()) == (True, "OK")

    # Case-insensitive uppercase hex hashes from Get-FileHash -Algorithm SHA256
    upper_hashes = {k: v.upper() for k, v in _matching_hashes().items()}
    assert verify_embed_bundle_offline(
        manifest,
        upper_hashes,
        outbound_internet_attempted=False,
        install_minutes_estimate=12.5,
    ) == (True, "OK")

    # Exact 15.0-minute ceiling and small positive duration admitted
    assert verify_embed_bundle_offline(
        manifest,
        _matching_hashes(),
        outbound_internet_attempted=False,
        install_minutes_estimate=15.0,
    ) == (True, "OK")
    assert verify_embed_bundle_offline(
        manifest,
        _matching_hashes(),
        outbound_internet_attempted=False,
        install_minutes_estimate=0.5,
    ) == (True, "OK")


# Story 21.2 — AC-21.2.2 (ADR-022)
def test_ac_21_2_2_verify_embed_bundle_offline_uses_constant_time_hmac_compare_digest(monkeypatch):
    manifest = _valid_manifest()
    calls: list[tuple[str, str]] = []
    real_compare = hmac.compare_digest

    def _spy_compare(a, b):
        calls.append((a, b))
        return real_compare(a, b)

    monkeypatch.setattr(hmac, "compare_digest", _spy_compare)

    ok, code = verify_embed_bundle_offline(manifest, _matching_hashes())
    assert (ok, code) == (True, "OK")
    assert len(calls) == len(manifest.artifacts)


# Story 21.2 — AC-21.2.2 (ADR-022)
@pytest.mark.parametrize(
    ("manifest", "actual_file_hashes", "outbound_internet_attempted", "install_minutes_estimate", "expected_code"),
    [
        # Precedence 1: Network egress rejected first even if manifest & budget are also invalid
        (None, None, True, 99.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (_valid_manifest(), _matching_hashes(), True, 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (_valid_manifest(), _matching_hashes(), None, 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (_valid_manifest(), _matching_hashes(), "false", 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        # Precedence 2: Bundle / manifest integrity rejected before install duration budget
        (None, _matching_hashes(), False, 99.0, "ERR_BUNDLE_INTEGRITY_FAILED"),
        ({"offline_only": True}, _matching_hashes(), False, 99.0, "ERR_BUNDLE_INTEGRITY_FAILED"),
        (
            EmbedBundleManifest("1.0.0", False, _matching_hashes(), VHDX_SHA),
            _matching_hashes(),
            False,
            99.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        (
            EmbedBundleManifest("1.0.0", True, {}, VHDX_SHA),
            {},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        (_valid_manifest(), None, False, 10.0, "ERR_BUNDLE_INTEGRITY_FAILED"),
        (_valid_manifest(), [], False, 10.0, "ERR_BUNDLE_INTEGRITY_FAILED"),
        # Missing file in actual hashes
        (
            _valid_manifest(),
            {"bin/wxc-exec.exe": EXE_SHA, "registry/golden_image_registry.json": REG_SHA},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        # Extra unexpected file in actual hashes
        (
            _valid_manifest(),
            {**_matching_hashes(), "bin/rogue.dll": "0" * 64},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        # Tampered file digest
        (
            _valid_manifest(),
            {**_matching_hashes(), "bin/wxc-exec.exe": "0" * 64},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        # Non-string / None actual digest
        (
            _valid_manifest(),
            {**_matching_hashes(), "bin/wxc-exec.exe": None},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        (
            _valid_manifest(),
            {**_matching_hashes(), "bin/wxc-exec.exe": 12345},
            False,
            10.0,
            "ERR_BUNDLE_INTEGRITY_FAILED",
        ),
        # Precedence 3: Install duration budget validation (<=0, >15.0, non-finite, bool, None, str)
        (_valid_manifest(), _matching_hashes(), False, 15.01, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, 0.0, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, -2.5, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, float("nan"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, float("inf"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, float("-inf"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, None, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, True, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, False, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (_valid_manifest(), _matching_hashes(), False, "10.0", "ERR_INSTALL_BUDGET_EXCEEDED"),
    ],
)
def test_ac_21_2_2_verify_embed_bundle_offline_fails_closed_with_deterministic_precedence(
    manifest,
    actual_file_hashes,
    outbound_internet_attempted,
    install_minutes_estimate,
    expected_code,
):
    ok, code = verify_embed_bundle_offline(
        manifest=manifest,
        actual_file_hashes=actual_file_hashes,
        outbound_internet_attempted=outbound_internet_attempted,
        install_minutes_estimate=install_minutes_estimate,
    )
    assert ok is False
    assert code == expected_code
