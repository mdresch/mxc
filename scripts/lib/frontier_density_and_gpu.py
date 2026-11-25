"""Next-frontier fleet density, RAM-disk/DAX differencing, kernel TLS probes & GPU-P sandboxes.

Governed by ADR-018 (TP-16), BRD-017 (BRU-017-01..05), FDD-017 (§1..§2),
and Epic 017 Stories 17.1..17.3 (WBS 18.0).
"""

from __future__ import annotations

import math
import re
import struct
from typing import Any

_PAUSED_FLOOR_MAX_MB = 640.0
_CROSSGEN2_MIN_SHARED_RATIO = 0.65
_DISPOSABLE_TRIM_BYPASS_MS = 50.0
_RAMDISK_MOUNT_SLA_MS = 50.0
_NEURAL_CONFIDENCE_FLOOR = 0.90
_NEURAL_MAX_FPR = 0.05
_GPUP_MIN_THROUGHPUT_RATIO = 0.85

_REQUIRED_SUBSYSTEMS = ("wmi", "com_plus", "services", "gpo")
_ASCII_HOSTNAME_RE = re.compile(rb"^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")


def _is_finite_number(value: object) -> bool:
    """Return True for non-bool int/float values that are finite."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _decode_ascii_sni(candidate: bytes) -> str | None:
    """Decode a valid ASCII hostname candidate from SNI bytes, or return None."""
    if not candidate or not _ASCII_HOSTNAME_RE.fullmatch(candidate):
        return None
    return candidate.decode("ascii")


def _extract_sni_from_rfc_client_hello(raw: bytes) -> str | None:
    """Parse a standard TLS ClientHello record and return the ASCII SNI hostname if present."""
    if len(raw) < 9:
        return None
    if raw[0] != 0x16 or raw[1] != 0x03 or raw[2] not in (0x01, 0x02, 0x03, 0x04):
        return None

    record_len = struct.unpack("!H", raw[3:5])[0]
    if len(raw) < 5 + record_len or raw[5] != 0x01:
        return None

    handshake_len = struct.unpack("!I", b"\x00" + raw[6:9])[0]
    if len(raw) < 9 + handshake_len:
        return None

    offset = 9 + 34  # ClientHello version (2) + random (32)
    if offset >= len(raw):
        return None

    session_id_len = raw[offset]
    offset += 1 + session_id_len
    if offset + 2 > len(raw):
        return None

    cipher_suites_len = struct.unpack("!H", raw[offset : offset + 2])[0]
    offset += 2 + cipher_suites_len
    if offset + 1 > len(raw):
        return None

    compression_len = raw[offset]
    offset += 1 + compression_len
    if offset + 2 > len(raw):
        return None

    extensions_len = struct.unpack("!H", raw[offset : offset + 2])[0]
    offset += 2
    ext_end = min(len(raw), offset + extensions_len)

    while offset + 4 <= ext_end:
        ext_type, ext_len = struct.unpack("!HH", raw[offset : offset + 4])
        offset += 4
        if offset + ext_len > ext_end:
            return None
        if ext_type == 0x0000:
            ext_data = raw[offset : offset + ext_len]
            if len(ext_data) < 5:
                return None
            if ext_data[2] == 0x00:
                name_len = struct.unpack("!H", ext_data[3:5])[0]
                if len(ext_data) >= 5 + name_len:
                    return _decode_ascii_sni(ext_data[5 : 5 + name_len])
            return None
        offset += ext_len
    return None


def _extract_sni_from_tlv_scan(raw: bytes) -> str | None:
    """Fallback scan for an SNI extension TLV inside compact synthetic ClientHello payloads."""
    limit = len(raw) - 9
    for idx in range(6, max(6, limit + 1)):
        if raw[idx] != 0x00 or raw[idx + 1] != 0x00:
            continue
        ext_len = struct.unpack("!H", raw[idx + 2 : idx + 4])[0]
        list_len = struct.unpack("!H", raw[idx + 4 : idx + 6])[0]
        name_type = raw[idx + 6]
        name_len = struct.unpack("!H", raw[idx + 7 : idx + 9])[0]
        if (
            name_type == 0x00
            and name_len > 0
            and ext_len == list_len + 2
            and list_len == name_len + 3
            and idx + 9 + name_len <= len(raw)
        ):
            decoded = _decode_ascii_sni(raw[idx + 9 : idx + 9 + name_len])
            if decoded is not None:
                return decoded
    return None


def _extract_client_hello_sni(raw: bytes) -> str | None:
    """Safely extract an ASCII SNI hint from a ClientHello payload without raising."""
    try:
        sni = _extract_sni_from_rfc_client_hello(raw)
        if sni is not None:
            return sni
        return _extract_sni_from_tlv_scan(raw)
    except Exception:
        return None


def _is_subsystem_healthy(entry: Any) -> bool:
    """Return True strictly for boolean True or {'healthy': True}."""
    if entry is True:
        return True
    if isinstance(entry, dict) and entry.get("healthy") is True:
        return True
    return False


def evaluate_density_and_numa(
    *,
    paused_ram_mb: float,
    shared_page_ratio: float,
    remote_numa_pages: int,
    disposable_discard: bool,
) -> dict[str, Any]:
    """Evaluate 640 MB paused RAM floor, CrossGen2 sharing ratio, trim bypass, and NUMA pinning."""
    if not _is_finite_number(paused_ram_mb):
        raise ValueError("paused_ram_mb must be a finite number")
    if paused_ram_mb <= 0.0:
        raise ValueError("paused_ram_mb must be > 0.0")
    if paused_ram_mb > _PAUSED_FLOOR_MAX_MB:
        raise ValueError(
            f"ERR_PAUSED_FLOOR_EXCEEDED: paused_ram_mb ({paused_ram_mb}) exceeds {_PAUSED_FLOOR_MAX_MB} MB floor"
        )

    if not _is_finite_number(shared_page_ratio):
        raise ValueError("shared_page_ratio must be a finite number")
    if shared_page_ratio < 0.0 or shared_page_ratio > 1.0:
        raise ValueError("shared_page_ratio must be within [0.0, 1.0]")

    if not _is_finite_number(remote_numa_pages):
        raise ValueError("remote_numa_pages must be a finite integer")
    if isinstance(remote_numa_pages, float) and not remote_numa_pages.is_integer():
        raise ValueError("remote_numa_pages must be an integer")
    if remote_numa_pages < 0:
        raise ValueError("remote_numa_pages must be >= 0")
    if remote_numa_pages > 0:
        raise ValueError(
            f"ERR_NUMA_REMOTE_PAGES: expected 0 remote NUMA pages, got {remote_numa_pages}"
        )

    if not isinstance(disposable_discard, bool):
        raise ValueError("disposable_discard must be a bool")

    paused_val = float(paused_ram_mb)
    ratio_val = float(shared_page_ratio)
    effective_ram_mb = round(paused_val * (1.0 - ratio_val), 2)

    return {
        "paused_ram_mb": paused_val,
        "shared_page_ratio": ratio_val,
        "effective_ram_mb": effective_ram_mb,
        "trim_bypass_ms_saved": _DISPOSABLE_TRIM_BYPASS_MS if disposable_discard else 0.0,
        "crossgen2_compliant": ratio_val >= _CROSSGEN2_MIN_SHARED_RATIO,
        "numa_local_pinned": True,
        "remote_numa_pages": 0,
    }


def allocate_ramdisk_overlay(
    *,
    requested_mb: int,
    available_ramdisk_mb: int,
    mount_latency_ms: float,
) -> tuple[bool, str]:
    """Fail-closed admission for quota-bounded host RAM-disk/DAX differencing overlays."""
    if (
        not _is_finite_number(requested_mb)
        or not _is_finite_number(available_ramdisk_mb)
        or not _is_finite_number(mount_latency_ms)
        or requested_mb <= 0
        or available_ramdisk_mb < 0
        or mount_latency_ms < 0.0
    ):
        return False, "ERR_RAMDISK_INVALID_REQUEST"

    if requested_mb > available_ramdisk_mb:
        return False, "ERR_RAMDISK_QUOTA_EXCEEDED"

    if mount_latency_ms > _RAMDISK_MOUNT_SLA_MS:
        return False, "ERR_RAMDISK_MOUNT_LATENCY_EXCEEDED"

    return True, "OK"


def inspect_kernel_tls_promotion(
    *,
    packet_bytes: bytes | None,
    neural_prewarm_confidence: float,
    false_positive_rate: float,
) -> dict[str, Any]:
    """Inspect packet bytes for TLS ClientHello SNI and evaluate neural fast-promotion bounds."""
    if (
        not _is_finite_number(neural_prewarm_confidence)
        or neural_prewarm_confidence < 0.0
        or neural_prewarm_confidence > 1.0
    ):
        raise ValueError("neural_prewarm_confidence must be a finite float in [0.0, 1.0]")

    if (
        not _is_finite_number(false_positive_rate)
        or false_positive_rate < 0.0
        or false_positive_rate > 1.0
    ):
        raise ValueError("false_positive_rate must be a finite float in [0.0, 1.0]")

    if isinstance(packet_bytes, (bytes, bytearray, memoryview)):
        raw = bytes(packet_bytes)
    else:
        raw = b""

    is_tls_client_hello = len(raw) >= 6 and raw[0] == 0x16 and raw[5] == 0x01
    sni_hint = _extract_client_hello_sni(raw) if is_tls_client_hello else None

    promote_fast = (
        float(neural_prewarm_confidence) >= _NEURAL_CONFIDENCE_FLOOR
        and float(false_positive_rate) <= _NEURAL_MAX_FPR
    )

    return {
        "is_tls_client_hello": is_tls_client_hello,
        "sni_hint": sni_hint,
        "promote_fast": promote_fast,
        "perceived_wake_ms": 0.0 if promote_fast else None,
    }


def evaluate_subsystem_differential_matrix(telemetry: dict | None) -> tuple[bool, str]:
    """Verify WMI, COM+, Services, and GPO telemetry matrix pre-dispatch."""
    if not isinstance(telemetry, dict) or len(telemetry) == 0:
        return False, "ERR_SUBSYSTEM_DEGRADED"

    normalized_health: dict[str, bool] = {}
    for raw_key, raw_value in telemetry.items():
        if not isinstance(raw_key, str):
            continue
        key = raw_key.strip().lower()
        if key == "com+":
            key = "com_plus"
        healthy = _is_subsystem_healthy(raw_value)
        if key in normalized_health:
            normalized_health[key] = normalized_health[key] and healthy
        else:
            normalized_health[key] = healthy

    for required in _REQUIRED_SUBSYSTEMS:
        if not normalized_health.get(required, False):
            return False, "ERR_SUBSYSTEM_DEGRADED"

    return True, "OK"


def provision_gpup_sandbox(
    *,
    gpu_supported: bool,
    partition_ratio: float,
    throughput_ratio: float,
) -> tuple[bool, str]:
    """Admit GPU-P/DDA sandbox tiers with deterministic hardware, partition, and SLA precedence."""
    if gpu_supported is not True:
        return False, "ERR_GPUP_UNSUPPORTED"

    if (
        not _is_finite_number(partition_ratio)
        or not _is_finite_number(throughput_ratio)
        or partition_ratio <= 0.0
        or partition_ratio > 1.0
    ):
        return False, "ERR_GPUP_PARTITION_INVALID"

    if throughput_ratio < _GPUP_MIN_THROUGHPUT_RATIO:
        return False, "ERR_GPUP_SLA_BELOW_FLOOR"

    return True, "OK"
