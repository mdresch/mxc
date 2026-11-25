"""Signed offline MXC Embed sovereign enterprise pilot bundle packager and verifier (ADR-022, Epic 021).

Implements:
  - Story 21.1: Deterministic offline pilot bundle manifest builder (`build_embed_bundle_manifest`).
  - Story 21.2: Zero-cloud offline bundle verifier (`verify_embed_bundle_offline`) enforcing
    fail-closed precedence across network egress, constant-time SHA-256 bundle integrity, and
    the <= 15.0 minute sovereign deployment SLA budget.

Standard library only (IMP-024); zero network calls (LL-011, LL-022).
"""

from __future__ import annotations

from dataclasses import dataclass
import hmac
import math
import re

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}\Z")
_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_MAX_INSTALL_MINUTES = 15.0


@dataclass(frozen=True)
class EmbedBundleManifest:
    """Immutable offline pilot bundle manifest (`mxc-embed-manifest.json`)."""

    bundle_version: str
    offline_only: bool
    artifacts: dict[str, str]
    golden_vhdx_sha256: str


def _is_valid_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


def _is_valid_relative_path(path: object) -> bool:
    if not isinstance(path, str):
        return False
    if not path or not path.strip():
        return False
    if path.startswith("/") or path.startswith("\\") or _DRIVE_PREFIX_RE.match(path):
        return False
    segments = re.split(r"[/\\]", path)
    if any(seg == ".." for seg in segments):
        return False
    return True


def build_embed_bundle_manifest(
    bundle_version: str,
    file_hashes: dict[str, str] | None,
    golden_vhdx_sha256: str,
) -> EmbedBundleManifest:
    """Build a deterministic, offline-only EmbedBundleManifest with normalized lowercase SHA-256 digests."""
    if not isinstance(bundle_version, str) or not bundle_version.strip():
        raise ValueError("bundle_version must be a non-blank string")

    if not isinstance(file_hashes, dict) or not file_hashes:
        raise ValueError("file_hashes must be a non-empty dict of relative path -> 64-hex SHA-256")

    if not _is_valid_sha256(golden_vhdx_sha256):
        raise ValueError("golden_vhdx_sha256 must be a strict 64-hex SHA-256 digest")

    normalized_artifacts: dict[str, str] = {}
    for rel_path, digest in file_hashes.items():
        if not _is_valid_relative_path(rel_path):
            raise ValueError(f"Invalid artifact relative path: {rel_path!r}")
        if not _is_valid_sha256(digest):
            raise ValueError(f"Invalid SHA-256 digest for artifact {rel_path!r}")
        normalized_artifacts[rel_path] = digest.lower()

    return EmbedBundleManifest(
        bundle_version=bundle_version.strip(),
        offline_only=True,
        artifacts=normalized_artifacts,
        golden_vhdx_sha256=golden_vhdx_sha256.lower(),
    )


def verify_embed_bundle_offline(
    manifest: EmbedBundleManifest | None,
    actual_file_hashes: dict[str, str] | None,
    *,
    outbound_internet_attempted: bool = False,
    install_minutes_estimate: float = 10.0,
) -> tuple[bool, str]:
    """Verify an offline MXC Embed pilot bundle with deterministic fail-closed precedence.

    Precedence:
      1. Outbound network egress attempted or invalid bool -> (False, "ERR_NETWORK_EGRESS_ATTEMPTED")
      2. Manifest/artifact integrity failure (constant-time hmac.compare_digest) ->
         (False, "ERR_BUNDLE_INTEGRITY_FAILED")
      3. Non-finite, non-positive, boolean, or > 15.0 min install budget ->
         (False, "ERR_INSTALL_BUDGET_EXCEEDED")
      4. Otherwise -> (True, "OK")
    """
    # Precedence 1: Strict zero-cloud offline guarantee
    if not isinstance(outbound_internet_attempted, bool) or outbound_internet_attempted is True:
        return (False, "ERR_NETWORK_EGRESS_ATTEMPTED")

    # Precedence 2: Cryptographic bundle manifest & artifact integrity
    if (
        manifest is None
        or not isinstance(manifest, EmbedBundleManifest)
        or manifest.offline_only is not True
        or actual_file_hashes is None
        or not isinstance(actual_file_hashes, dict)
        or not isinstance(manifest.artifacts, dict)
        or not manifest.artifacts
        or set(manifest.artifacts.keys()) != set(actual_file_hashes.keys())
    ):
        return (False, "ERR_BUNDLE_INTEGRITY_FAILED")

    for rel_path, expected_digest in manifest.artifacts.items():
        actual_digest = actual_file_hashes.get(rel_path)
        if not _is_valid_sha256(expected_digest) or not _is_valid_sha256(actual_digest):
            return (False, "ERR_BUNDLE_INTEGRITY_FAILED")
        if not hmac.compare_digest(expected_digest.lower(), actual_digest.lower()):
            return (False, "ERR_BUNDLE_INTEGRITY_FAILED")

    # Precedence 3: <= 15.0 minute sovereign deployment SLA budget
    if (
        install_minutes_estimate is None
        or isinstance(install_minutes_estimate, bool)
        or not isinstance(install_minutes_estimate, (int, float))
    ):
        return (False, "ERR_INSTALL_BUDGET_EXCEEDED")

    minutes = float(install_minutes_estimate)
    if not math.isfinite(minutes) or minutes <= 0.0 or minutes > _MAX_INSTALL_MINUTES:
        return (False, "ERR_INSTALL_BUDGET_EXCEEDED")

    return (True, "OK")
