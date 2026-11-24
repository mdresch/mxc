"""Contract tests for Story 10.2 — Fail-Closed PoolRegistrationGuard Offline Attestation Gate (ADR-012).

Spec Gate Episode: spec-10_2-0c4ffc6d (Robust Utility Margin: +0.2129)
Contract Interpretations:
  I1: verify_pool_admission() operates 100% offline using locally pinned trust roots and returns
      AttestationDecision(admitted=True, reason_code="ADMITTED") only when signature, VHDX SHA-256,
      SBOM SHA-256, key revocation, expiry, and forbidden-package checks all succeed.
  I2: Any single check failure fails closed (admitted=False) with an explicit deterministic
      reason_code: ERR_KEY_REVOKED, ERR_SIGNATURE_INVALID, ERR_EXPIRED, ERR_DIGEST_MISMATCH,
      or ERR_SBOM_INVALID.
  I3: Verification executes strictly at registration/admission time; cached admission tokens incur
      0 ms cryptographic overhead on the hot/warm dispatch path.
"""

from __future__ import annotations

import hashlib
import socket
import time

import pytest

from scripts.lib.supply_chain_attestation import (
    AttestationBundle,
    PoolRegistrationGuard,
    generate_sbom_and_provenance,
    verify_pool_admission,
)

TRUSTED_KEY = b"mxc-prod-signing-key-2026-airgap!!"
TRUSTED_KEYS = {"mxc-root-2026-01": TRUSTED_KEY}
BASE_PACKAGES = [
    {"name": "windows-server-2025", "version": "26100.1"},
    {"name": "python", "version": "3.15.2"},
    {"name": "git", "version": "2.56.1"},
]


def _make_valid_bundle(tmp_path, packages=None, ttl_days=90):
    vhdx = tmp_path / "winserv2025-prod-adpa.vhdx"
    vhdx.write_bytes(b"immutable-golden-parent-bytes")
    bundle, sbom_doc = generate_sbom_and_provenance(
        image_id="img-prod-adpa",
        vhdx_path=str(vhdx),
        packages=packages if packages is not None else BASE_PACKAGES,
        git_commit="0248fcb5abcdef0123456789",
        signing_key_bytes=TRUSTED_KEY,
        key_id="mxc-root-2026-01",
        ttl_days=ttl_days,
        output_dir=str(tmp_path),
    )
    return bundle, sbom_doc, vhdx


# Story 10.2 — AC-10.2.1 (ADR-012)
def test_ac_10_2_1_valid_bundle_admitted_offline_with_zero_network(tmp_path, monkeypatch):
    bundle, sbom_doc, vhdx = _make_valid_bundle(tmp_path)
    actual_vhdx_sha = hashlib.sha256(vhdx.read_bytes()).hexdigest()

    def _forbid_network(*args, **kwargs):
        raise AssertionError("Network access is strictly forbidden during offline attestation")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    decision = verify_pool_admission(
        bundle=bundle,
        actual_vhdx_sha256=actual_vhdx_sha,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=[c["name"] for c in sbom_doc["components"]],
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages={"dev-debugger", "unapproved-tool"},
        now_utc=bundle.issued_at_utc,
    )
    assert decision.admitted is True
    assert decision.reason_code == "ADMITTED"
    assert decision.image_id == "img-prod-adpa"


# Story 10.2 — AC-10.2.2 (ADR-012)
def test_ac_10_2_2_fail_closed_on_tamper_revocation_expiry_and_forbidden_sbom(tmp_path):
    bundle, sbom_doc, vhdx = _make_valid_bundle(tmp_path)
    actual_vhdx_sha = hashlib.sha256(vhdx.read_bytes()).hexdigest()
    pkg_names = [c["name"] for c in sbom_doc["components"]]

    # 1. Tampered VHDX digest
    d_tamper = verify_pool_admission(
        bundle=bundle,
        actual_vhdx_sha256="0" * 64,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=pkg_names,
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages=set(),
        now_utc=bundle.issued_at_utc,
    )
    assert d_tamper.admitted is False
    assert d_tamper.reason_code == "ERR_DIGEST_MISMATCH"

    # 2. Invalid signature
    bad_sig_bundle = AttestationBundle(**{**bundle.__dict__, "signature_b64": "AAAAinvalid=="})
    d_sig = verify_pool_admission(
        bundle=bad_sig_bundle,
        actual_vhdx_sha256=actual_vhdx_sha,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=pkg_names,
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages=set(),
        now_utc=bundle.issued_at_utc,
    )
    assert d_sig.admitted is False
    assert d_sig.reason_code == "ERR_SIGNATURE_INVALID"

    # 3. Revoked signing key
    d_revoked = verify_pool_admission(
        bundle=bundle,
        actual_vhdx_sha256=actual_vhdx_sha,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=pkg_names,
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids={"mxc-root-2026-01"},
        forbidden_packages=set(),
        now_utc=bundle.issued_at_utc,
    )
    assert d_revoked.admitted is False
    assert d_revoked.reason_code == "ERR_KEY_REVOKED"

    # 4. Expired bundle
    d_expired = verify_pool_admission(
        bundle=bundle,
        actual_vhdx_sha256=actual_vhdx_sha,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=pkg_names,
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages=set(),
        now_utc="2099-01-01T00:00:00Z",
    )
    assert d_expired.admitted is False
    assert d_expired.reason_code == "ERR_EXPIRED"

    # 5. Forbidden package in SBOM
    d_sbom = verify_pool_admission(
        bundle=bundle,
        actual_vhdx_sha256=actual_vhdx_sha,
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=pkg_names + ["dev-debugger"],
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages={"dev-debugger"},
        now_utc=bundle.issued_at_utc,
    )
    assert d_sbom.admitted is False
    assert d_sbom.reason_code == "ERR_SBOM_INVALID"


# Story 10.2 — AC-10.2.3 (ADR-012)
def test_ac_10_2_3_guard_admits_once_with_zero_hot_dispatch_overhead(tmp_path):
    bundle, sbom_doc, vhdx = _make_valid_bundle(tmp_path)
    guard = PoolRegistrationGuard(
        trusted_public_keys=TRUSTED_KEYS,
        revoked_key_ids=set(),
        forbidden_packages={"dev-debugger"},
    )
    decision = guard.admit(
        bundle=bundle,
        actual_vhdx_sha256=hashlib.sha256(vhdx.read_bytes()).hexdigest(),
        actual_sbom_sha256=bundle.sbom_sha256,
        sbom_packages=[c["name"] for c in sbom_doc["components"]],
        now_utc=bundle.issued_at_utc,
    )
    assert decision.admitted is True

    # Hot-path check is O(1) in-memory lookup (sub-millisecond, zero crypto hashing)
    t0 = time.perf_counter()
    for _ in range(1000):
        assert guard.is_admitted("img-prod-adpa") is True
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 5.0
    assert guard.is_admitted("img-unregistered") is False
