"""Contract tests for Story 14.2 — Chunked VMBus Payload Streaming & UTF-8 BOM-Tolerant CLI (ADR-015).

Spec Gate Episode: spec-14_2-36f75f09 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  Spec gate emitted zero warnings (all adversarial checks [OK]: completeness, defensive
  None-handling, architectural boundaries).
  I1: chunk_payload_frames() and reassemble_chunk_frames() round-trip b"" cleanly and stream
      multi-MB payloads above the 8 KB cmd.exe ceiling with per-chunk and overall SHA-256
      verification, raising ValueError("ERR_CHUNK_CHECKSUM_MISMATCH") on None, missing,
      out-of-order, or tampered frames.
  I2: parse_wxc_manifest_bom_safe() strips leading UTF-8 BOM bytes (\xef\xbb\xbf) without
      JSONDecodeError, preserves manifest fields including phase/sandboxId, and enforces
      cli_operation / cli_container_id precedence cleanly when supplied or None.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.lib.snapshot_fork_and_vmbus import (
    chunk_payload_frames,
    parse_wxc_manifest_bom_safe,
    reassemble_chunk_frames,
)


# Story 14.2 — AC-14.2.1 (ADR-015)
def test_ac_14_2_1_chunk_and_reassemble_empty_and_multi_mb_payloads():
    # Empty 0-byte payload round-trips cleanly
    empty_frames = chunk_payload_frames(b"")
    assert empty_frames == []
    assert reassemble_chunk_frames(empty_frames) == b""

    # Multi-MB payload well beyond 8 KB cmd.exe limit
    payload = (b"MXC-VMBUS-CHUNK-STREAM-0123456789ABCDEF" * 60000) + b"TAIL"
    assert len(payload) > 2 * 1024 * 1024

    frames = chunk_payload_frames(payload, chunk_size_bytes=65536)
    expected_stream_sha = hashlib.sha256(payload).hexdigest()
    assert len(frames) > 30
    for idx, frame in enumerate(frames):
        assert frame["seq"] == idx
        assert frame["total_frames"] == len(frames)
        assert isinstance(frame["data"], bytes)
        assert len(frame["data"]) <= 65536
        assert frame["chunk_sha256"] == hashlib.sha256(frame["data"]).hexdigest()
        assert frame["stream_sha256"] == expected_stream_sha

    assert reassemble_chunk_frames(frames) == payload

    # Corrupted chunk data -> ERR_CHUNK_CHECKSUM_MISMATCH
    corrupt_data_frames = [dict(f) for f in frames]
    corrupt_data_frames[3]["data"] = b"X" * len(corrupt_data_frames[3]["data"])
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(corrupt_data_frames)

    # Corrupted chunk digest -> ERR_CHUNK_CHECKSUM_MISMATCH
    corrupt_hash_frames = [dict(f) for f in frames]
    corrupt_hash_frames[0]["chunk_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(corrupt_hash_frames)

    # Corrupted stream digest -> ERR_CHUNK_CHECKSUM_MISMATCH
    corrupt_stream_frames = [dict(f, stream_sha256="f" * 64) for f in frames]
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(corrupt_stream_frames)

    # Missing frame -> ERR_CHUNK_CHECKSUM_MISMATCH
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(frames[:-1])

    # Out-of-order frames -> ERR_CHUNK_CHECKSUM_MISMATCH
    reordered = [frames[1], frames[0], *frames[2:]]
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(reordered)

    # None frames -> ERR_CHUNK_CHECKSUM_MISMATCH
    with pytest.raises(ValueError, match="ERR_CHUNK_CHECKSUM_MISMATCH"):
        reassemble_chunk_frames(None)  # type: ignore[arg-type]

    # Invalid chunk_payload_frames inputs raise ValueError
    with pytest.raises(ValueError):
        chunk_payload_frames(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        chunk_payload_frames(b"abc", chunk_size_bytes=0)
    with pytest.raises(ValueError):
        chunk_payload_frames(b"abc", chunk_size_bytes=True)  # type: ignore[arg-type]


# Story 14.2 — AC-14.2.2 (ADR-015)
def test_ac_14_2_2_bom_tolerant_manifest_parsing_and_cli_override_precedence():
    manifest_obj = {
        "phase": "exec",
        "sandboxId": "hv:legacy-sandbox-01",
        "command": "pytest -q",
        "timeoutSeconds": 60,
    }
    winps_bom_bytes = b"\xef\xbb\xbf" + json.dumps(manifest_obj).encode("utf-8")

    # Without CLI overrides: strips UTF-8 BOM cleanly and maps phase/sandboxId
    parsed_default = parse_wxc_manifest_bom_safe(winps_bom_bytes)
    assert parsed_default["operation"] == "exec"
    assert parsed_default["container_id"] == "hv:legacy-sandbox-01"
    assert parsed_default["phase"] == "exec"
    assert parsed_default["sandboxId"] == "hv:legacy-sandbox-01"
    assert parsed_default["command"] == "pytest -q"

    # With explicit CLI overrides: preserves phase/sandboxId and overrides cleanly
    parsed_override = parse_wxc_manifest_bom_safe(
        winps_bom_bytes,
        cli_operation="fork",
        cli_container_id="hv:new-fork-02",
    )
    assert parsed_override["operation"] == "fork"
    assert parsed_override["container_id"] == "hv:new-fork-02"
    assert parsed_override["phase"] == "exec"
    assert parsed_override["sandboxId"] == "hv:legacy-sandbox-01"

    # Empty / None CLI overrides fall back to operation/container_id before phase/sandboxId
    dual_obj = {
        "operation": "copy-file",
        "phase": "legacy-phase",
        "container_id": "hv:primary-01",
        "sandboxId": "hv:fallback-02",
    }
    parsed_fallback = parse_wxc_manifest_bom_safe(
        json.dumps(dual_obj).encode("utf-8"),
        cli_operation="",
        cli_container_id=None,
    )
    assert parsed_fallback["operation"] == "copy-file"
    assert parsed_fallback["container_id"] == "hv:primary-01"

    # None, empty, BOM-only, or malformed JSON raise ValueError
    for bad_raw in (None, b"", b"\xef\xbb\xbf", b"\xef\xbb\xbf   \n", b"\xef\xbb\xbf{invalid-json"):
        with pytest.raises(ValueError):
            parse_wxc_manifest_bom_safe(bad_raw)  # type: ignore[arg-type]
