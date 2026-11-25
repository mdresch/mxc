"""Contract tests for Story 17.2 — Pure In-Memory RAM-Disk/DAX Differencing, Kernel TLS Probes & Neural Forecaster (ADR-018).

Spec Gate Episode: spec-17_2-65c5c5ea (Robust Utility Margin: +0.2104)
Contract Interpretations:
  I1 (Defensive None-Safety): Optional fields must be safely accessed (e.g. using
      getattr or .get() with defaults) to avoid AttributeError when None; packet_bytes=None
      or empty bytes returns a safe non-TLS pass-through without raising.
  I2 (Fail-Closed RAM-Disk Allocation): allocate_ramdisk_overlay() rejects invalid,
      None, bool, non-finite, zero/negative requested_mb, negative available/latency,
      quota overflow (ERR_RAMDISK_QUOTA_EXCEEDED), and >50.0 ms mounts
      (ERR_RAMDISK_MOUNT_LATENCY_EXCEEDED) without unhandled exceptions.
  I3 (Neural Pre-Warm Bounds): inspect_kernel_tls_promotion() validates
      neural_prewarm_confidence and false_positive_rate in [0.0, 1.0] (non-None,
      non-bool, finite) with ValueError, and triggers promote_fast=True
      (perceived_wake_ms=0.0) when confidence >= 0.90 and false_positive_rate <= 0.05.
"""

from __future__ import annotations

import struct
import pytest

from scripts.lib.frontier_density_and_gpu import (
    allocate_ramdisk_overlay,
    inspect_kernel_tls_promotion,
)


def _build_client_hello(sni_hostname: str | None = None) -> bytes:
    """Build a synthetic TLS 1.2/1.3 ClientHello packet with optional SNI extension."""
    if sni_hostname is not None:
        host_bytes = sni_hostname.encode("ascii")
        sni_list = b"\x00" + struct.pack("!H", len(host_bytes)) + host_bytes
        sni_ext_data = struct.pack("!H", len(sni_list)) + sni_list
        sni_ext = struct.pack("!HH", 0x0000, len(sni_ext_data)) + sni_ext_data
        extensions_block = struct.pack("!H", len(sni_ext)) + sni_ext
    else:
        extensions_block = struct.pack("!H", 0)

    body = (
        b"\x03\x03"
        + (b"\x11" * 32)
        + b"\x00"
        + struct.pack("!H", 2)
        + b"\xc0\x2f"
        + b"\x01\x00"
        + extensions_block
    )
    handshake = b"\x01" + struct.pack("!I", len(body))[1:] + body
    record = b"\x16\x03\x01" + struct.pack("!H", len(handshake)) + handshake
    return record


# Story 17.2 — AC-17.2.1 (ADR-018)
def test_ac_17_2_1_ramdisk_overlay_admission_and_boundaries():
    assert allocate_ramdisk_overlay(
        requested_mb=256,
        available_ramdisk_mb=1024,
        mount_latency_ms=12.5,
    ) == (True, "OK")

    # Exact quota and latency ceiling boundaries
    assert allocate_ramdisk_overlay(
        requested_mb=512,
        available_ramdisk_mb=512,
        mount_latency_ms=50.0,
    ) == (True, "OK")


# Story 17.2 — AC-17.2.1 (ADR-018)
@pytest.mark.parametrize(
    "kwargs,expected",
    [
        (
            {"requested_mb": 0, "available_ramdisk_mb": 512, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": -64, "available_ramdisk_mb": 512, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": 64, "available_ramdisk_mb": -1, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": 64, "available_ramdisk_mb": 512, "mount_latency_ms": -0.1},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": None, "available_ramdisk_mb": 512, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": True, "available_ramdisk_mb": 512, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": 64, "available_ramdisk_mb": 512, "mount_latency_ms": float("nan")},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": 64, "available_ramdisk_mb": 512, "mount_latency_ms": float("inf")},
            (False, "ERR_RAMDISK_INVALID_REQUEST"),
        ),
        (
            {"requested_mb": 1025, "available_ramdisk_mb": 1024, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_QUOTA_EXCEEDED"),
        ),
        (
            {"requested_mb": 10, "available_ramdisk_mb": 0, "mount_latency_ms": 10.0},
            (False, "ERR_RAMDISK_QUOTA_EXCEEDED"),
        ),
        (
            {"requested_mb": 128, "available_ramdisk_mb": 1024, "mount_latency_ms": 50.1},
            (False, "ERR_RAMDISK_MOUNT_LATENCY_EXCEEDED"),
        ),
    ],
)
def test_ac_17_2_1_ramdisk_overlay_fails_closed_on_invalid_quota_and_latency(kwargs, expected):
    assert allocate_ramdisk_overlay(**kwargs) == expected


# Story 17.2 — AC-17.2.2 (ADR-018)
def test_ac_17_2_2_kernel_tls_client_hello_sni_and_neural_fast_promotion():
    pkt = _build_client_hello("agent-prod.mxc.internal")
    res = inspect_kernel_tls_promotion(
        packet_bytes=pkt,
        neural_prewarm_confidence=0.90,
        false_positive_rate=0.05,
    )

    assert res["is_tls_client_hello"] is True
    assert res["sni_hint"] == "agent-prod.mxc.internal"
    assert res["promote_fast"] is True
    assert res["perceived_wake_ms"] == 0.0

    # Minimal ClientHello frame without SNI extension
    minimal_hello = b"\x16\x03\x01\x00\x05\x01"
    res_no_sni = inspect_kernel_tls_promotion(
        packet_bytes=minimal_hello,
        neural_prewarm_confidence=0.89,
        false_positive_rate=0.02,
    )
    assert res_no_sni["is_tls_client_hello"] is True
    assert res_no_sni["sni_hint"] is None
    assert res_no_sni["promote_fast"] is False
    assert res_no_sni["perceived_wake_ms"] is None


# Story 17.2 — AC-17.2.2 (ADR-018)
def test_ac_17_2_2_non_tls_empty_and_none_payloads_pass_through_safely():
    for payload in (None, b"", b"\x16\x03\x01\x00", b"GET /health HTTP/1.1\r\n"):
        res = inspect_kernel_tls_promotion(
            packet_bytes=payload,
            neural_prewarm_confidence=0.95,
            false_positive_rate=0.06,
        )
        assert res["is_tls_client_hello"] is False
        assert res["sni_hint"] is None
        assert res["promote_fast"] is False
        assert res["perceived_wake_ms"] is None


# Story 17.2 — AC-17.2.2 (ADR-018)
@pytest.mark.parametrize(
    "conf,fpr",
    [
        (None, 0.01),
        (0.95, None),
        (True, 0.01),
        (0.95, False),
        (float("nan"), 0.01),
        (0.95, float("inf")),
        (-0.01, 0.01),
        (1.01, 0.01),
        (0.95, -0.01),
        (0.95, 1.01),
    ],
)
def test_ac_17_2_2_invalid_forecaster_probabilities_raise_value_error(conf, fpr):
    with pytest.raises(ValueError):
        inspect_kernel_tls_promotion(
            packet_bytes=b"",
            neural_prewarm_confidence=conf,
            false_positive_rate=fpr,
        )
