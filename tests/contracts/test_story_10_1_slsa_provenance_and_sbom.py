"""Contract tests for Story 10.1 — Deterministic SLSA Provenance Envelope & CycloneDX SBOM Generator (ADR-012).

Spec Gate Episode: spec-10_1-33cdce90 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1: generate_sbom_and_provenance() emits a CycloneDX 1.5 JSON SBOM containing all declared
      packages and an AttestationBundle binding image_id, vhdx_sha256, sbom_sha256, git_commit,
      builder_id, issued_at_utc, expires_at_utc, key_id, and a detached cryptographic signature.
  I2: Canonical serialization is deterministic; mutating a single byte of the SBOM or any
      provenance field invalidates signature verification deterministically.
  I3: Empty or malformed inputs (empty image_id, non-hex digest, empty signing key) raise ValueError.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.lib.supply_chain_attestation import (
    AttestationBundle,
    generate_sbom_and_provenance,
    verify_bundle_signature,
)

SAMPLE_KEY = b"mxc-offline-signing-root-key-v1-32b!"
SAMPLE_VHDX_SHA256 = hashlib.sha256(b"golden-win11-agent-lean-vhdx-payload").hexdigest()
SAMPLE_PACKAGES = [
    {"name": "windows-11-pro", "version": "26300.9457"},
    {"name": "git", "version": "2.56.1"},
    {"name": "python", "version": "3.15.2"},
    {"name": "ruff", "version": "0.17.6"},
]


# Story 10.1 — AC-10.1.1 (ADR-012)
def test_ac_10_1_1_generates_cyclonedx_sbom_and_signed_provenance(tmp_path):
    vhdx_file = tmp_path / "win11-agent-lean.vhdx"
    vhdx_file.write_bytes(b"golden-win11-agent-lean-vhdx-payload")

    bundle, sbom_doc = generate_sbom_and_provenance(
        image_id="img-win11-agent-lean",
        vhdx_path=str(vhdx_file),
        packages=SAMPLE_PACKAGES,
        git_commit="a90fefab1234567890abcdef1234567890abcdef",
        signing_key_bytes=SAMPLE_KEY,
        key_id="mxc-root-2026-01",
        ttl_days=90,
        output_dir=str(tmp_path),
    )

    assert isinstance(bundle, AttestationBundle)
    assert bundle.image_id == "img-win11-agent-lean"
    assert bundle.vhdx_sha256 == SAMPLE_VHDX_SHA256
    assert bundle.git_commit == "a90fefab1234567890abcdef1234567890abcdef"
    assert bundle.key_id == "mxc-root-2026-01"
    assert bundle.issued_at_utc < bundle.expires_at_utc
    assert bundle.signature_b64

    # CycloneDX 1.5 structure check
    assert sbom_doc["bomFormat"] == "CycloneDX"
    assert sbom_doc["specVersion"] == "1.5"
    names = {c["name"] for c in sbom_doc["components"]}
    assert {"windows-11-pro", "git", "python", "ruff"} <= names

    # SBOM file persisted and digest matches
    sbom_bytes = (tmp_path / "img-win11-agent-lean.sbom.cdx.json").read_bytes()
    assert hashlib.sha256(sbom_bytes).hexdigest() == bundle.sbom_sha256
    assert json.loads(sbom_bytes.decode("utf-8"))["bomFormat"] == "CycloneDX"
    assert verify_bundle_signature(bundle, SAMPLE_KEY) is True


# Story 10.1 — AC-10.1.2 (ADR-012)
def test_ac_10_1_2_single_byte_tamper_invalidates_signature(tmp_path):
    vhdx_file = tmp_path / "winserv2025-prod-adpa.vhdx"
    vhdx_file.write_bytes(b"prod-adpa-vhdx-bytes")

    bundle, _ = generate_sbom_and_provenance(
        image_id="img-prod-adpa",
        vhdx_path=str(vhdx_file),
        packages=SAMPLE_PACKAGES,
        git_commit="deadbeef0123456789",
        signing_key_bytes=SAMPLE_KEY,
        key_id="mxc-root-2026-01",
        output_dir=str(tmp_path),
    )

    assert verify_bundle_signature(bundle, SAMPLE_KEY) is True

    # Mutate single character of sbom_sha256
    flipped_char = "0" if bundle.sbom_sha256[0] != "0" else "1"
    tampered_sbom_bundle = AttestationBundle(
        **{**bundle.__dict__, "sbom_sha256": flipped_char + bundle.sbom_sha256[1:]}
    )
    assert verify_bundle_signature(tampered_sbom_bundle, SAMPLE_KEY) is False

    # Mutate git_commit
    tampered_commit_bundle = AttestationBundle(
        **{**bundle.__dict__, "git_commit": "000000000000000000"}
    )
    assert verify_bundle_signature(tampered_commit_bundle, SAMPLE_KEY) is False

    # Wrong verification key
    assert verify_bundle_signature(bundle, b"wrong-key-bytes") is False


def test_story_10_1_rejects_empty_or_invalid_inputs(tmp_path):
    vhdx_file = tmp_path / "sample.vhdx"
    vhdx_file.write_bytes(b"data")

    with pytest.raises(ValueError):
        generate_sbom_and_provenance(
            image_id="",
            vhdx_path=str(vhdx_file),
            packages=SAMPLE_PACKAGES,
            git_commit="abc123",
            signing_key_bytes=SAMPLE_KEY,
            key_id="k1",
            output_dir=str(tmp_path),
        )

    with pytest.raises(ValueError):
        generate_sbom_and_provenance(
            image_id="img-1",
            vhdx_path=str(vhdx_file),
            packages=SAMPLE_PACKAGES,
            git_commit="abc123",
            signing_key_bytes=b"",
            key_id="k1",
            output_dir=str(tmp_path),
        )
