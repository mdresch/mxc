"""Contract tests for Story 16.1 — Reproducible ISO-to-Lean Agent Image CI Factory & Auto-Registry Hasher (ADR-017).

Spec Gate Episode: spec-16_1-2b2d6d3d (Robust Utility Margin: +0.2176)
Contract Interpretations:
  I1: build_auto_registry_entry() transforms a valid ImageFactoryBuildSpec (with explorer_stripped=True
      and compact_os_lzx=True), output vhdx_sha256, and positive int size_bytes into a normalized
      golden_image_registry.json-compatible dict marked slsa_ready=True for ADR-012 handoff.
  I2 (Defensive None-Safety & Input Validation): None, blank, non-sequence/empty toolchain_packages,
      non-64-hex SHA-256 digests, non-positive or boolean size_bytes, and unstripped/uncompacted specs
      all fail closed by raising ValueError.
  I3: Registry entry fabrication operates 100% deterministically and offline with zero manual hash edits
      and zero outbound network connections (LL-011).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import socket

import pytest

from scripts.lib.mxc_embed_appliance import (
    ImageFactoryBuildSpec,
    build_auto_registry_entry,
)

SAMPLE_ISO_SHA256 = "A1B2C3D4" * 8
SAMPLE_VHDX_SHA256 = "F0E1D2C3" * 8
SAMPLE_PACKAGES = ("git", "gh", "python", "uv", "node", "pnpm", "pwsh")


# Story 16.1 — AC-16.1.1 (ADR-017)
def test_ac_16_1_1_build_auto_registry_entry_emits_slsa_ready_record(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Network egress is strictly prohibited during CI registry generation")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    spec = ImageFactoryBuildSpec(
        image_id="img-win11-agent-lean",
        iso_sha256=SAMPLE_ISO_SHA256,
        toolchain_packages=SAMPLE_PACKAGES,
    )
    assert spec.explorer_stripped is True
    assert spec.compact_os_lzx is True

    with pytest.raises(FrozenInstanceError):
        spec.image_id = "mutated"  # type: ignore[misc]

    entry = build_auto_registry_entry(
        spec=spec,
        vhdx_sha256=SAMPLE_VHDX_SHA256,
        size_bytes=24_599_429_120,
    )

    assert entry == {
        "image_id": "img-win11-agent-lean",
        "iso_sha256": SAMPLE_ISO_SHA256.lower(),
        "vhdx_sha256": SAMPLE_VHDX_SHA256.lower(),
        "size_bytes": 24_599_429_120,
        "toolchain_packages": list(SAMPLE_PACKAGES),
        "explorer_stripped": True,
        "compact_os_lzx": True,
        "slsa_ready": True,
    }


# Story 16.1 — AC-16.1.2 (ADR-017)
@pytest.mark.parametrize(
    ("spec", "vhdx_sha256", "size_bytes"),
    [
        # Invalid or missing spec
        (None, SAMPLE_VHDX_SHA256, 1024),
        ({"image_id": "img-1"}, SAMPLE_VHDX_SHA256, 1024),
        # Invalid image_id
        (ImageFactoryBuildSpec(None, SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("   ", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec(123, SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        # Invalid toolchain_packages
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, None), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, ()), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, []), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, "git"), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, ("git", "")), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, ("git", "   ")), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, ("git", None)), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        # Invalid iso_sha256
        (ImageFactoryBuildSpec("img-1", None, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", "abc", SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("img-1", "g" * 64, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),
        (ImageFactoryBuildSpec("img-1", ("a" * 64) + "\n", SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024),
        # Invalid vhdx_sha256
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), None, 1024),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), "deadbeef", 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), "z" * 64, 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), ("b" * 64) + "\n", 1024),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), 999, 1024),  # type: ignore[arg-type]
        # Invalid size_bytes
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, None),  # type: ignore[arg-type]
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 0),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, -512),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, True),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, False),
        (ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES), SAMPLE_VHDX_SHA256, 1024.5),  # type: ignore[arg-type]
        # Unstripped or uncompacted images
        (
            ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES, explorer_stripped=False),
            SAMPLE_VHDX_SHA256,
            1024,
        ),
        (
            ImageFactoryBuildSpec("img-1", SAMPLE_ISO_SHA256, SAMPLE_PACKAGES, compact_os_lzx=False),
            SAMPLE_VHDX_SHA256,
            1024,
        ),
    ],
)
def test_ac_16_1_2_rejects_invalid_or_incomplete_factory_specs(spec, vhdx_sha256, size_bytes):
    with pytest.raises(ValueError):
        build_auto_registry_entry(spec=spec, vhdx_sha256=vhdx_sha256, size_bytes=size_bytes)
