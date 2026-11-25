"""MXC Embed Sovereign On-Premises Appliance, ISO-to-Lean CI Factory & 5-Act HIL Gate (ADR-017 / Epic 016).

Implements:
  - Story 16.1: Parameterized ISO-to-Lean CI factory manifest builder and automated
                golden_image_registry.json record generator ready for ADR-012 SLSA attestation
                (IMP-MXC-018).
  - Story 16.2: Zero-cloud single-host "MXC Embed" preflight validator (<= 15.0 min, 0 outbound
                internet calls) and gated 5-Act Hardware-in-the-Loop (HIL) release verifier with
                immutable parent SHA-256 invariance (IMP-MXC-023, IMP-MXC-031).

Python 3 standard library only; zero external dependencies and zero network I/O.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hmac
import math
import re
from typing import Any

_SHA256_HEX_RE = re.compile(r"[0-9a-fA-F]{64}")
MAX_INSTALL_MINUTES = 15.0
EXPECTED_HIL_ACT_COUNT = 5


@dataclass(frozen=True)
class ImageFactoryBuildSpec:
    """Declarative specification for a reproducible ISO-to-Lean Windows 11 Agent image build."""

    image_id: str
    iso_sha256: str
    toolchain_packages: tuple[str, ...]
    explorer_stripped: bool = True
    compact_os_lzx: bool = True


def _is_valid_sha256(value: Any) -> bool:
    """Return True iff value is a strict 64-character hexadecimal SHA-256 digest."""
    return isinstance(value, str) and _SHA256_HEX_RE.fullmatch(value) is not None


def build_auto_registry_entry(
    spec: ImageFactoryBuildSpec,
    vhdx_sha256: str,
    size_bytes: int,
) -> dict[str, Any]:
    """Validate an ISO-to-Lean build spec and emit an ADR-012 SLSA-ready registry record."""
    if spec is None or not isinstance(spec, ImageFactoryBuildSpec):
        raise ValueError("spec must be a valid ImageFactoryBuildSpec instance")

    if not isinstance(spec.image_id, str) or not spec.image_id.strip():
        raise ValueError("spec.image_id must be a non-empty string")

    packages = spec.toolchain_packages
    if (
        packages is None
        or isinstance(packages, (str, bytes, bytearray))
        or not isinstance(packages, Sequence)
        or len(packages) == 0
    ):
        raise ValueError("spec.toolchain_packages must be a non-empty sequence of package names")
    if any(not isinstance(pkg, str) or not pkg.strip() for pkg in packages):
        raise ValueError("spec.toolchain_packages must not contain blank or non-string entries")

    if not _is_valid_sha256(spec.iso_sha256):
        raise ValueError("spec.iso_sha256 must be a valid 64-character hex SHA-256 string")

    if not _is_valid_sha256(vhdx_sha256):
        raise ValueError("vhdx_sha256 must be a valid 64-character hex SHA-256 string")

    if size_bytes is None or isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes <= 0:
        raise ValueError("size_bytes must be a positive integer")

    if spec.explorer_stripped is not True or spec.compact_os_lzx is not True:
        raise ValueError("ISO-to-Lean images must have explorer_stripped=True and compact_os_lzx=True")

    return {
        "image_id": spec.image_id,
        "iso_sha256": spec.iso_sha256.lower(),
        "vhdx_sha256": vhdx_sha256.lower(),
        "size_bytes": size_bytes,
        "toolchain_packages": list(packages),
        "explorer_stripped": True,
        "compact_os_lzx": True,
        "slsa_ready": True,
    }


def run_mxc_embed_preflight(
    *,
    hyperv_enabled: bool,
    base_image_present: bool,
    outbound_internet_required: bool,
    install_minutes_estimate: float,
) -> tuple[bool, str]:
    """Run deterministic fail-closed zero-cloud preflight checks for single-host MXC Embed."""
    if outbound_internet_required is True or not isinstance(outbound_internet_required, bool):
        return (False, "ERR_NETWORK_EGRESS_ATTEMPTED")

    if hyperv_enabled is not True or base_image_present is not True:
        return (False, "ERR_PREFLIGHT_PREREQ_MISSING")

    if (
        install_minutes_estimate is None
        or isinstance(install_minutes_estimate, bool)
        or not isinstance(install_minutes_estimate, (int, float))
    ):
        return (False, "ERR_INSTALL_BUDGET_EXCEEDED")

    try:
        estimate = float(install_minutes_estimate)
    except (TypeError, ValueError, OverflowError):
        return (False, "ERR_INSTALL_BUDGET_EXCEEDED")

    if not math.isfinite(estimate) or estimate <= 0.0 or estimate > MAX_INSTALL_MINUTES:
        return (False, "ERR_INSTALL_BUDGET_EXCEEDED")

    return (True, "OK")


def evaluate_five_act_hil_gate(
    *,
    act_results: list[dict],
    parent_sha_before: str,
    parent_sha_after: str,
) -> tuple[bool, str]:
    """Evaluate the gated 5-Act HIL proof suite and enforce parent VHDX SHA-256 invariance."""
    if (
        not isinstance(parent_sha_before, str)
        or not isinstance(parent_sha_after, str)
        or not parent_sha_before.strip()
        or not parent_sha_after.strip()
    ):
        return (False, "ERR_PARENT_HASH_DRIFT")

    if not hmac.compare_digest(
        parent_sha_before.lower().encode("utf-8"),
        parent_sha_after.lower().encode("utf-8"),
    ):
        return (False, "ERR_PARENT_HASH_DRIFT")

    if (
        act_results is None
        or not isinstance(act_results, list)
        or len(act_results) != EXPECTED_HIL_ACT_COUNT
        or any(not isinstance(item, dict) or item.get("passed") is not True for item in act_results)
    ):
        return (False, "ERR_HIL_ACT_FAILED")

    return (True, "OK")
