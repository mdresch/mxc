"""MXC Parallel Snapshot Branching, Chunked VMBus Streaming, BOM-Tolerant CLI & IDE Workers (ADR-015 / Epic 014).

Implements:
  - Story 14.1: Bounded parallel .avhdx snapshot branching (create_parallel_forks) and clean
                loser teardown (discard_losing_branches) preserving parent_hash invariance.
  - Story 14.2: Chunked binary VMBus payload framing/reassembly with per-chunk and stream SHA-256
                verification, plus UTF-8 BOM-tolerant wxc-exec manifest parsing with CLI flag precedence.
  - Story 14.3: Declarative ephemeral IDE worker profile validation for Cursor, Antigravity, and
                Claude Code with zero-secret mxc-sync enforcement.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
import hashlib
import hmac
import json
import math
import uuid

ALLOWED_IDE_CLIENTS = frozenset({"cursor", "antigravity", "claude-code"})
DEFAULT_CHUNK_SIZE_BYTES = 65536
MIN_IDE_WORKER_RAM_MB = 2048
_UTF8_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class SnapshotBranch:
    branch_id: str
    parent_checkpoint_id: str
    depth: int
    diff_disk_path: str
    status: str  # "ACTIVE" | "DISCARDED"


def _is_valid_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def create_parallel_forks(
    parent_checkpoint_id: str,
    branch_names: list[str],
    *,
    current_depth: int = 0,
    max_depth: int = 4,
    max_parallel: int = 5,
) -> list[SnapshotBranch]:
    """Allocate bounded active SnapshotBranch records anchored at an immutable parent checkpoint."""
    if not _is_valid_int(current_depth) or not _is_valid_int(max_depth):
        raise ValueError("ERR_FORK_DEPTH_EXCEEDED")
    if current_depth < 0 or max_depth <= 0 or current_depth + 1 > max_depth:
        raise ValueError("ERR_FORK_DEPTH_EXCEEDED")

    if not isinstance(parent_checkpoint_id, str) or not parent_checkpoint_id.strip():
        raise ValueError("ERR_FORK_BOUNDS_INVALID")
    if not _is_valid_int(max_parallel) or max_parallel <= 0:
        raise ValueError("ERR_FORK_BOUNDS_INVALID")
    if (
        branch_names is None
        or isinstance(branch_names, (str, bytes, bytearray, dict))
        or not isinstance(branch_names, Sequence)
    ):
        raise ValueError("ERR_FORK_BOUNDS_INVALID")
    if len(branch_names) == 0 or len(branch_names) > max_parallel:
        raise ValueError("ERR_FORK_BOUNDS_INVALID")

    seen: set[str] = set()
    validated_names: list[str] = []
    for raw_name in branch_names:
        if not isinstance(raw_name, str):
            raise ValueError("ERR_FORK_BOUNDS_INVALID")
        clean_name = raw_name.strip()
        if not clean_name or clean_name in seen:
            raise ValueError("ERR_FORK_BOUNDS_INVALID")
        seen.add(clean_name)
        validated_names.append(raw_name)

    next_depth = current_depth + 1
    return [
        SnapshotBranch(
            branch_id=f"{parent_checkpoint_id}:{name}:{uuid.uuid4().hex[:8]}",
            parent_checkpoint_id=parent_checkpoint_id,
            depth=next_depth,
            diff_disk_path=f"{parent_checkpoint_id}/{name}.avhdx",
            status="ACTIVE",
        )
        for name in validated_names
    ]


def discard_losing_branches(
    branches: list[SnapshotBranch] | None,
    winning_branch_id: str | None,
    *,
    parent_hash: str,
) -> tuple[list[SnapshotBranch], str]:
    """Mark non-winning branches DISCARDED, preserve winner ACTIVE, and keep parent_hash unchanged."""
    if not branches:
        return ([], parent_hash)

    reconciled: list[SnapshotBranch] = []
    for branch in branches:
        new_status = (
            "ACTIVE"
            if winning_branch_id is not None and branch.branch_id == winning_branch_id
            else "DISCARDED"
        )
        reconciled.append(replace(branch, status=new_status))
    return (reconciled, parent_hash)


def chunk_payload_frames(
    payload: bytes,
    *,
    chunk_size_bytes: int = DEFAULT_CHUNK_SIZE_BYTES,
) -> list[dict]:
    """Split binary payload into sequenced, SHA-256 verified VMBus transfer frames."""
    if not isinstance(payload, (bytes, bytearray)):
        raise ValueError("ERR_CHUNK_PAYLOAD_INVALID")
    if not _is_valid_int(chunk_size_bytes) or chunk_size_bytes <= 0:
        raise ValueError("ERR_CHUNK_SIZE_INVALID")

    raw = bytes(payload)
    if not raw:
        return []

    stream_sha256 = hashlib.sha256(raw).hexdigest()
    chunks = [
        raw[offset : offset + chunk_size_bytes]
        for offset in range(0, len(raw), chunk_size_bytes)
    ]
    total_frames = len(chunks)
    return [
        {
            "seq": seq,
            "total_frames": total_frames,
            "data": chunk,
            "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
            "stream_sha256": stream_sha256,
        }
        for seq, chunk in enumerate(chunks)
    ]


def reassemble_chunk_frames(frames: list[dict]) -> bytes:
    """Reassemble sequenced VMBus frames after verifying order, count, and SHA-256 integrity."""
    if (
        frames is None
        or isinstance(frames, (str, bytes, bytearray, dict))
        or not isinstance(frames, Sequence)
    ):
        raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")
    if len(frames) == 0:
        return b""

    expected_total = len(frames)
    first_frame = frames[0]
    if not isinstance(first_frame, dict):
        raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")
    expected_stream_sha = first_frame.get("stream_sha256")
    if not isinstance(expected_stream_sha, str) or not expected_stream_sha:
        raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")

    parts: list[bytes] = []
    for expected_seq, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")

        seq = frame.get("seq")
        total_frames = frame.get("total_frames")
        data = frame.get("data")
        chunk_sha = frame.get("chunk_sha256")
        stream_sha = frame.get("stream_sha256")

        if (
            not _is_valid_int(seq)
            or seq != expected_seq
            or not _is_valid_int(total_frames)
            or total_frames != expected_total
            or not isinstance(data, (bytes, bytearray))
            or not isinstance(chunk_sha, str)
            or not isinstance(stream_sha, str)
        ):
            raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")

        chunk_bytes = bytes(data)
        actual_chunk_sha = hashlib.sha256(chunk_bytes).hexdigest()
        if not hmac.compare_digest(actual_chunk_sha, chunk_sha):
            raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")
        if not hmac.compare_digest(stream_sha, expected_stream_sha):
            raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")
        parts.append(chunk_bytes)

    assembled = b"".join(parts)
    actual_stream_sha = hashlib.sha256(assembled).hexdigest()
    if not hmac.compare_digest(actual_stream_sha, expected_stream_sha):
        raise ValueError("ERR_CHUNK_CHECKSUM_MISMATCH")
    return assembled


def _resolve_manifest_field(
    cli_value: str | None,
    manifest: dict,
    primary_key: str,
    legacy_key: str,
) -> str | None:
    """Resolve an effective manifest field giving non-empty CLI flags precedence over manifest keys."""
    if isinstance(cli_value, str) and cli_value.strip():
        return cli_value
    for key in (primary_key, legacy_key):
        val = manifest.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return None


def parse_wxc_manifest_bom_safe(
    raw_bytes: bytes,
    *,
    cli_operation: str | None = None,
    cli_container_id: str | None = None,
) -> dict:
    """Strip leading UTF-8 BOM bytes, parse JSON cleanly, and apply CLI flag precedence."""
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise ValueError("ERR_MANIFEST_INVALID")

    stripped = bytes(raw_bytes)
    while stripped.startswith(_UTF8_BOM):
        stripped = stripped[len(_UTF8_BOM) :]

    if not stripped.strip():
        raise ValueError("ERR_MANIFEST_EMPTY")

    try:
        text = stripped.decode("utf-8").lstrip("\ufeff")
        if not text.strip():
            raise ValueError("ERR_MANIFEST_EMPTY")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"ERR_MANIFEST_INVALID_JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("ERR_MANIFEST_NOT_OBJECT")

    result = dict(parsed)
    resolved_operation = _resolve_manifest_field(cli_operation, parsed, "operation", "phase")
    resolved_container_id = _resolve_manifest_field(
        cli_container_id, parsed, "container_id", "sandboxId"
    )

    if resolved_operation is not None:
        result["operation"] = resolved_operation
    if resolved_container_id is not None:
        result["container_id"] = resolved_container_id
    return result


def _is_valid_toolchain(value: object) -> bool:
    if isinstance(value, (str, bytes, bytearray, dict)) or not isinstance(value, Sequence):
        return False
    if len(value) == 0:
        return False
    return all(isinstance(pkg, str) and bool(pkg.strip()) for pkg in value)


def validate_ide_worker_profile(profile: dict | None) -> tuple[bool, str]:
    """Validate an ephemeral IDE worker profile enforcing zero-secret and sizing floors."""
    if not isinstance(profile, dict) or len(profile) == 0:
        return (False, "ERR_WORKER_PROFILE_INVALID")

    ide_client = profile.get("ide_client")
    if not isinstance(ide_client, str) or ide_client not in ALLOWED_IDE_CLIENTS:
        return (False, "ERR_WORKER_PROFILE_INVALID")

    if profile.get("zero_secret") is not True:
        return (False, "ERR_WORKER_PROFILE_INVALID")

    if profile.get("sync_mode", "mxc-sync") != "mxc-sync":
        return (False, "ERR_WORKER_PROFILE_INVALID")

    if "toolchain" not in profile and "toolchain_packages" not in profile:
        return (False, "ERR_WORKER_PROFILE_INVALID")
    for key in ("toolchain", "toolchain_packages"):
        if key in profile and not _is_valid_toolchain(profile[key]):
            return (False, "ERR_WORKER_PROFILE_INVALID")

    if "guest_secrets_count" in profile and profile["guest_secrets_count"] is not None:
        secrets_count = profile["guest_secrets_count"]
        if not _is_valid_int(secrets_count) or secrets_count != 0:
            return (False, "ERR_WORKER_PROFILE_INVALID")

    if "ram_mb" in profile and profile["ram_mb"] is not None:
        ram_mb = profile["ram_mb"]
        if (
            isinstance(ram_mb, bool)
            or not isinstance(ram_mb, (int, float))
            or not math.isfinite(ram_mb)
            or ram_mb < MIN_IDE_WORKER_RAM_MB
        ):
            return (False, "ERR_WORKER_PROFILE_INVALID")

    return (True, "OK")
