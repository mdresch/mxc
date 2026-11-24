"""MXC Cryptographic Image Supply Chain, CycloneDX SBOM & Offline Attestation Gate (ADR-012 / Epic 010).

Implements:
  - Story 10.1: Deterministic SLSA v1.0 provenance envelope & CycloneDX 1.5 SBOM generator.
  - Story 10.2: Fail-closed offline PoolRegistrationGuard attestation gate with zero hot-path overhead.

All cryptographic operations use Python stdlib (hashlib, hmac, base64) so verification runs
100% offline on airgapped Hyper-V hosts with zero external dependencies or network I/O.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AttestationBundle:
    image_id: str
    vhdx_path: str
    vhdx_sha256: str
    sbom_path: str
    sbom_sha256: str
    git_commit: str
    builder_id: str
    issued_at_utc: str
    expires_at_utc: str
    signature_b64: str
    key_id: str


@dataclass(frozen=True)
class AttestationDecision:
    admitted: bool
    image_id: str
    reason_code: str
    verified_at_utc: str


def _canonical_payload_bytes(
    *,
    image_id: str,
    vhdx_sha256: str,
    sbom_sha256: str,
    git_commit: str,
    builder_id: str,
    issued_at_utc: str,
    expires_at_utc: str,
    key_id: str,
) -> bytes:
    payload = {
        "slsa_version": "1.0",
        "image_id": image_id,
        "vhdx_sha256": vhdx_sha256.lower(),
        "sbom_sha256": sbom_sha256.lower(),
        "git_commit": git_commit,
        "builder_id": builder_id,
        "issued_at_utc": issued_at_utc,
        "expires_at_utc": expires_at_utc,
        "key_id": key_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign_bytes(payload: bytes, key_bytes: bytes) -> str:
    mac = hmac.new(key_bytes, payload, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("ascii")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc(ts: str) -> datetime:
    normalized = ts.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def generate_sbom_and_provenance(
    image_id: str,
    vhdx_path: str,
    packages: list[dict[str, str]],
    git_commit: str,
    signing_key_bytes: bytes,
    key_id: str,
    *,
    builder_id: str = "mxc-golden-image-factory/v1",
    ttl_days: int = 90,
    output_dir: str | None = None,
    issued_at: datetime | None = None,
) -> tuple[AttestationBundle, dict]:
    """Generate a CycloneDX 1.5 SBOM and signed SLSA provenance AttestationBundle."""
    if not image_id or not image_id.strip():
        raise ValueError("image_id must be a non-empty string")
    if not git_commit or not git_commit.strip():
        raise ValueError("git_commit must be a non-empty string")
    if not key_id or not key_id.strip():
        raise ValueError("key_id must be a non-empty string")
    if not signing_key_bytes:
        raise ValueError("signing_key_bytes must be non-empty")
    if ttl_days <= 0:
        raise ValueError("ttl_days must be positive")

    vhdx_file = Path(vhdx_path)
    if not vhdx_file.is_file():
        raise FileNotFoundError(f"Golden image VHDX not found: {vhdx_path}")

    now_dt = (issued_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    exp_dt = now_dt + timedelta(days=ttl_days)
    issued_str = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_str = exp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    vhdx_sha256 = _sha256_file(vhdx_file)

    components = [
        {
            "type": "application",
            "name": str(pkg["name"]),
            "version": str(pkg.get("version", "unknown")),
        }
        for pkg in packages
    ]
    sbom_doc = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": issued_str,
            "component": {
                "type": "operating-system",
                "name": image_id,
                "hashes": [{"alg": "SHA-256", "content": vhdx_sha256}],
            },
        },
        "components": components,
    }
    sbom_bytes = json.dumps(sbom_doc, sort_keys=True, indent=2).encode("utf-8")
    sbom_sha256 = hashlib.sha256(sbom_bytes).hexdigest()

    out_base = Path(output_dir) if output_dir else vhdx_file.parent
    out_base.mkdir(parents=True, exist_ok=True)
    sbom_file = out_base / f"{image_id}.sbom.cdx.json"
    sbom_file.write_bytes(sbom_bytes)

    canonical = _canonical_payload_bytes(
        image_id=image_id,
        vhdx_sha256=vhdx_sha256,
        sbom_sha256=sbom_sha256,
        git_commit=git_commit,
        builder_id=builder_id,
        issued_at_utc=issued_str,
        expires_at_utc=expires_str,
        key_id=key_id,
    )
    signature_b64 = _sign_bytes(canonical, signing_key_bytes)

    bundle = AttestationBundle(
        image_id=image_id,
        vhdx_path=str(vhdx_file),
        vhdx_sha256=vhdx_sha256,
        sbom_path=str(sbom_file),
        sbom_sha256=sbom_sha256,
        git_commit=git_commit,
        builder_id=builder_id,
        issued_at_utc=issued_str,
        expires_at_utc=expires_str,
        signature_b64=signature_b64,
        key_id=key_id,
    )
    return bundle, sbom_doc


def verify_bundle_signature(bundle: AttestationBundle, verification_key_bytes: bytes) -> bool:
    """Verify the detached cryptographic signature over an AttestationBundle."""
    if not verification_key_bytes or not bundle.signature_b64:
        return False
    canonical = _canonical_payload_bytes(
        image_id=bundle.image_id,
        vhdx_sha256=bundle.vhdx_sha256,
        sbom_sha256=bundle.sbom_sha256,
        git_commit=bundle.git_commit,
        builder_id=bundle.builder_id,
        issued_at_utc=bundle.issued_at_utc,
        expires_at_utc=bundle.expires_at_utc,
        key_id=bundle.key_id,
    )
    expected_sig = _sign_bytes(canonical, verification_key_bytes)
    return hmac.compare_digest(expected_sig, bundle.signature_b64)


def verify_pool_admission(
    *,
    bundle: AttestationBundle,
    actual_vhdx_sha256: str,
    actual_sbom_sha256: str,
    sbom_packages: Iterable[str],
    trusted_public_keys: dict[str, bytes],
    revoked_key_ids: set[str],
    forbidden_packages: set[str],
    now_utc: str,
) -> AttestationDecision:
    """Fail-closed offline attestation gate for standby pool image registration."""
    if bundle.key_id in revoked_key_ids:
        return AttestationDecision(False, bundle.image_id, "ERR_KEY_REVOKED", now_utc)

    verify_key = trusted_public_keys.get(bundle.key_id)
    if verify_key is None or not verify_bundle_signature(bundle, verify_key):
        return AttestationDecision(False, bundle.image_id, "ERR_SIGNATURE_INVALID", now_utc)

    if _parse_utc(now_utc) > _parse_utc(bundle.expires_at_utc):
        return AttestationDecision(False, bundle.image_id, "ERR_EXPIRED", now_utc)

    if not hmac.compare_digest(actual_vhdx_sha256.lower(), bundle.vhdx_sha256.lower()):
        return AttestationDecision(False, bundle.image_id, "ERR_DIGEST_MISMATCH", now_utc)

    if not hmac.compare_digest(actual_sbom_sha256.lower(), bundle.sbom_sha256.lower()):
        return AttestationDecision(False, bundle.image_id, "ERR_SBOM_INVALID", now_utc)

    normalized_forbidden = {p.lower() for p in forbidden_packages}
    for pkg in sbom_packages:
        if pkg.lower() in normalized_forbidden:
            return AttestationDecision(False, bundle.image_id, "ERR_SBOM_INVALID", now_utc)

    return AttestationDecision(True, bundle.image_id, "ADMITTED", now_utc)


class PoolRegistrationGuard:
    """In-memory admission cache enforcing fail-closed registration with 0 ms hot-path checks."""

    def __init__(
        self,
        *,
        trusted_public_keys: dict[str, bytes],
        revoked_key_ids: set[str] | None = None,
        forbidden_packages: set[str] | None = None,
    ) -> None:
        self._trusted_keys = dict(trusted_public_keys)
        self._revoked_keys = set(revoked_key_ids or set())
        self._forbidden_packages = set(forbidden_packages or set())
        self._admitted_images: dict[str, AttestationDecision] = {}

    def admit(
        self,
        *,
        bundle: AttestationBundle,
        actual_vhdx_sha256: str,
        actual_sbom_sha256: str,
        sbom_packages: Iterable[str],
        now_utc: str,
    ) -> AttestationDecision:
        decision = verify_pool_admission(
            bundle=bundle,
            actual_vhdx_sha256=actual_vhdx_sha256,
            actual_sbom_sha256=actual_sbom_sha256,
            sbom_packages=sbom_packages,
            trusted_public_keys=self._trusted_keys,
            revoked_key_ids=self._revoked_keys,
            forbidden_packages=self._forbidden_packages,
            now_utc=now_utc,
        )
        if decision.admitted:
            self._admitted_images[bundle.image_id] = decision
        else:
            self._admitted_images.pop(bundle.image_id, None)
        return decision

    def is_admitted(self, image_id: str) -> bool:
        return image_id in self._admitted_images
