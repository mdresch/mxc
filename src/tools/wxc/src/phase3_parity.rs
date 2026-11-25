// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Native Rust Phase 3 runtime parity primitives for `wxc-exec` (`ADR-019` / `FDD-018` / `Epic 018`).
//!
//! Ports the Python Phase 3 reference invariants into compiled Rust with exact error-code parity:
//! - Story 18.1: UTF-8 BOM-tolerant manifest parsing with CLI flag precedence (`parse_manifest_bom_safe`)
//!   and SHA-256 verified chunked binary VMBus framing (`chunk_payload_frames`, `reassemble_chunk_frames`).
//! - Story 18.2: Bounded parallel `.avhdx` snapshot forking (`create_parallel_forks`, `discard_losing_branches`)
//!   and token-boundary static secret scanning for zero-secret git sync (`scan_git_sync_secrets`).

#![allow(dead_code)]

use std::collections::HashSet;

use sha2::{Digest, Sha256};

const UTF8_BOM: &[u8] = &[0xEF, 0xBB, 0xBF];

const SENSITIVE_ENV_TOKENS: &[&str] = &["PAT", "TOKEN", "SECRET", "PASSWORD", "PASSWD"];
const SENSITIVE_ENV_SUBSTRINGS: &[&str] = &["SSH_AUTH_SOCK", "PRIVATE_KEY", "API_KEY"];
const SECRET_VALUE_PREFIXES: &[&str] = &["ghp_", "github_pat_", "glpat-", "AKIA"];

/// Sequenced binary VMBus payload frame with per-chunk and whole-stream SHA-256 integrity digests.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VmbusChunkFrame {
    pub seq: usize,
    pub total_frames: usize,
    pub data: Vec<u8>,
    pub chunk_sha256: String,
    pub stream_sha256: String,
}

/// Bounded parallel `.avhdx` snapshot branch anchored at an immutable parent checkpoint.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SnapshotBranch {
    pub branch_id: String,
    pub parent_checkpoint_id: String,
    pub depth: usize,
    pub diff_disk_path: String,
    pub status: String,
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut out, "{byte:02x}");
    }
    out
}

fn constant_time_eq(a: &str, b: &str) -> bool {
    let ab = a.as_bytes();
    let bb = b.as_bytes();
    if ab.len() != bb.len() {
        return false;
    }
    let mut diff = 0u8;
    for (&x, &y) in ab.iter().zip(bb.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}

fn resolve_manifest_field(
    cli_value: Option<&str>,
    obj: &serde_json::Map<String, serde_json::Value>,
    primary_key: &str,
    legacy_key: &str,
) -> Option<String> {
    if let Some(val) = cli_value {
        if !val.trim().is_empty() {
            return Some(val.to_string());
        }
    }
    for key in [primary_key, legacy_key] {
        if let Some(serde_json::Value::String(val)) = obj.get(key) {
            if !val.trim().is_empty() {
                return Some(val.clone());
            }
        }
    }
    None
}

/// Strip leading UTF-8 BOM bytes (`\xEF\xBB\xBF`), parse a JSON object manifest, preserve
/// legacy `phase`/`sandboxId` keys, and apply non-empty CLI overrides for `operation` and `container_id`.
pub fn parse_manifest_bom_safe(
    raw_bytes: &[u8],
    cli_operation: Option<&str>,
    cli_container_id: Option<&str>,
) -> Result<serde_json::Value, String> {
    let mut stripped = raw_bytes;
    while let Some(rest) = stripped.strip_prefix(UTF8_BOM) {
        stripped = rest;
    }

    if stripped.iter().all(|b| b.is_ascii_whitespace()) {
        return Err("ERR_MANIFEST_EMPTY".to_string());
    }

    let text = std::str::from_utf8(stripped)
        .map_err(|e| format!("ERR_MANIFEST_INVALID_UTF8: {e}"))?
        .trim_start_matches('\u{FEFF}');

    if text.trim().is_empty() {
        return Err("ERR_MANIFEST_EMPTY".to_string());
    }

    let parsed: serde_json::Value =
        serde_json::from_str(text).map_err(|e| format!("ERR_MANIFEST_INVALID_JSON: {e}"))?;

    let mut obj = match parsed {
        serde_json::Value::Object(map) => map,
        _ => return Err("ERR_MANIFEST_NOT_OBJECT".to_string()),
    };

    let resolved_operation = resolve_manifest_field(cli_operation, &obj, "operation", "phase");
    let resolved_container_id =
        resolve_manifest_field(cli_container_id, &obj, "container_id", "sandboxId");

    if let Some(op) = resolved_operation {
        obj.insert("operation".to_string(), serde_json::Value::String(op));
    }
    if let Some(cid) = resolved_container_id {
        obj.insert("container_id".to_string(), serde_json::Value::String(cid));
    }

    Ok(serde_json::Value::Object(obj))
}

/// Split an arbitrary binary payload into sequenced, SHA-256 verified VMBus frames.
pub fn chunk_payload_frames(
    payload: &[u8],
    chunk_size_bytes: usize,
) -> Result<Vec<VmbusChunkFrame>, String> {
    if chunk_size_bytes == 0 {
        return Err("ERR_CHUNK_SIZE_INVALID".to_string());
    }
    if payload.is_empty() {
        return Ok(Vec::new());
    }

    let stream_sha256 = sha256_hex(payload);
    let total_frames = payload.len().div_ceil(chunk_size_bytes);
    let mut frames = Vec::with_capacity(total_frames);

    for (seq, chunk) in payload.chunks(chunk_size_bytes).enumerate() {
        frames.push(VmbusChunkFrame {
            seq,
            total_frames,
            data: chunk.to_vec(),
            chunk_sha256: sha256_hex(chunk),
            stream_sha256: stream_sha256.clone(),
        });
    }

    Ok(frames)
}

/// Reassemble sequenced VMBus frames, failing closed with `ERR_CHUNK_CHECKSUM_MISMATCH` on any
/// missing frame, out-of-order sequence number, tampered payload bytes, or mismatched digest.
pub fn reassemble_chunk_frames(frames: &[VmbusChunkFrame]) -> Result<Vec<u8>, String> {
    if frames.is_empty() {
        return Ok(Vec::new());
    }

    let expected_total = frames.len();
    let expected_stream_sha = frames[0].stream_sha256.as_str();
    if expected_stream_sha.is_empty() {
        return Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string());
    }

    let total_bytes: usize = frames.iter().map(|f| f.data.len()).sum();
    let mut assembled = Vec::with_capacity(total_bytes);

    for (expected_seq, frame) in frames.iter().enumerate() {
        if frame.seq != expected_seq || frame.total_frames != expected_total {
            return Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string());
        }
        let actual_chunk_sha = sha256_hex(&frame.data);
        if !constant_time_eq(&actual_chunk_sha, &frame.chunk_sha256)
            || !constant_time_eq(&frame.stream_sha256, expected_stream_sha)
        {
            return Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string());
        }
        assembled.extend_from_slice(&frame.data);
    }

    let actual_stream_sha = sha256_hex(&assembled);
    if !constant_time_eq(&actual_stream_sha, expected_stream_sha) {
        return Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string());
    }

    Ok(assembled)
}

/// Allocate bounded parallel `SnapshotBranch` records anchored at an immutable parent checkpoint.
pub fn create_parallel_forks(
    parent_checkpoint_id: &str,
    branch_names: &[&str],
    current_depth: usize,
    max_depth: usize,
    max_parallel: usize,
) -> Result<Vec<SnapshotBranch>, String> {
    let next_depth = match current_depth.checked_add(1) {
        Some(d) if max_depth > 0 && d <= max_depth => d,
        _ => return Err("ERR_FORK_DEPTH_EXCEEDED".to_string()),
    };

    if parent_checkpoint_id.trim().is_empty()
        || max_parallel == 0
        || branch_names.is_empty()
        || branch_names.len() > max_parallel
    {
        return Err("ERR_FORK_BOUNDS_INVALID".to_string());
    }

    let mut seen = HashSet::with_capacity(branch_names.len());
    let mut validated_names = Vec::with_capacity(branch_names.len());
    for &raw_name in branch_names {
        let clean = raw_name.trim();
        if clean.is_empty() || !seen.insert(clean.to_string()) {
            return Err("ERR_FORK_BOUNDS_INVALID".to_string());
        }
        validated_names.push(raw_name);
    }

    let branches = validated_names
        .into_iter()
        .enumerate()
        .map(|(idx, name)| {
            let tag = &sha256_hex(
                format!("{parent_checkpoint_id}:{name}:{next_depth}:{idx}").as_bytes(),
            )[..8];
            SnapshotBranch {
                branch_id: format!("{parent_checkpoint_id}:{name}:{tag}"),
                parent_checkpoint_id: parent_checkpoint_id.to_string(),
                depth: next_depth,
                diff_disk_path: format!("{parent_checkpoint_id}/{name}.avhdx"),
                status: "ACTIVE".to_string(),
            }
        })
        .collect();

    Ok(branches)
}

/// Mark non-winning branches `DISCARDED`, keep the winning branch `ACTIVE`, and preserve
/// `parent_hash` bit-for-bit without drift.
pub fn discard_losing_branches(
    branches: &[SnapshotBranch],
    winning_branch_id: Option<&str>,
    parent_hash: &str,
) -> (Vec<SnapshotBranch>, String) {
    if branches.is_empty() {
        return (Vec::new(), parent_hash.to_string());
    }

    let reconciled = branches
        .iter()
        .map(|branch| {
            let mut updated = branch.clone();
            updated.status = if winning_branch_id == Some(branch.branch_id.as_str()) {
                "ACTIVE".to_string()
            } else {
                "DISCARDED".to_string()
            };
            updated
        })
        .collect();

    (reconciled, parent_hash.to_string())
}

fn has_embedded_url_credentials(value: &str) -> bool {
    let lower = value.to_ascii_lowercase();
    let bytes = lower.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let rest = &lower[i..];
        let scheme_len = if rest.starts_with("https://") {
            Some(8)
        } else if rest.starts_with("http://") {
            Some(7)
        } else {
            None
        };
        if let Some(len) = scheme_len {
            let after_scheme = &rest[len..];
            let authority_end = after_scheme
                .find(|c: char| c == '/' || c.is_whitespace())
                .unwrap_or(after_scheme.len());
            let authority = &after_scheme[..authority_end];
            if let Some(at_pos) = authority.find('@') {
                if at_pos > 0 {
                    return true;
                }
            }
            i += len;
        } else {
            i += 1;
        }
    }
    false
}

fn has_pem_private_key_header(value: &str) -> bool {
    for line in value.lines() {
        let upper = line.to_ascii_uppercase();
        if let Some(begin_pos) = upper.find("BEGIN") {
            let after_begin = &upper[begin_pos + 5..];
            if !after_begin.starts_with(char::is_whitespace) {
                continue;
            }
            let tokens: Vec<&str> = after_begin.split_whitespace().collect();
            if tokens
                .windows(2)
                .any(|w| w[0] == "PRIVATE" && (w[1] == "KEY" || w[1].starts_with("KEY-")))
            {
                return true;
            }
        }
    }
    false
}

fn has_secret_material(value: &str) -> bool {
    if value.is_empty() {
        return false;
    }
    if SECRET_VALUE_PREFIXES.iter().any(|p| value.contains(p)) {
        return true;
    }
    if has_embedded_url_credentials(value) {
        return true;
    }
    has_pem_private_key_header(value)
}

fn is_sensitive_env_key(key: &str) -> bool {
    let upper = key.to_ascii_uppercase();
    if SENSITIVE_ENV_SUBSTRINGS.iter().any(|m| upper.contains(m)) {
        return true;
    }
    let tokens: Vec<&str> = upper
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|t| !t.is_empty())
        .collect();
    if tokens.iter().any(|t| SENSITIVE_ENV_TOKENS.contains(t)) {
        return true;
    }
    tokens.contains(&"PRIVATE") && tokens.contains(&"KEY")
}

/// Scan a git sync remote URL and guest environment slice for static secrets using token-boundary
/// env key matching (explicitly allowing benign keys such as `PATH`).
pub fn scan_git_sync_secrets(
    remote_url: Option<&str>,
    guest_env: &[(&str, &str)],
) -> Result<(), String> {
    if let Some(url) = remote_url {
        if has_secret_material(url) {
            return Err("ERR_STATIC_SECRET_DETECTED".to_string());
        }
    }

    for &(key, value) in guest_env {
        if is_sensitive_env_key(key) || has_secret_material(key) || has_secret_material(value) {
            return Err("ERR_STATIC_SECRET_DETECTED".to_string());
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // ── Story 18.1 / AC-18.1.1: BOM-tolerant manifest parsing & CLI override precedence ──

    #[test]
    fn phase3_parity_manifest_strips_utf8_bom_and_preserves_legacy_fields() {
        let mut raw = Vec::from(UTF8_BOM);
        raw.extend_from_slice(br#"{"phase":"run","sandboxId":"sb-42","extra":true}"#);

        let parsed = parse_manifest_bom_safe(&raw, None, None).expect("BOM manifest should parse");
        assert_eq!(parsed["phase"], "run");
        assert_eq!(parsed["sandboxId"], "sb-42");
        assert_eq!(parsed["operation"], "run");
        assert_eq!(parsed["container_id"], "sb-42");
        assert_eq!(parsed["extra"], true);
    }

    #[test]
    fn phase3_parity_manifest_cli_overrides_take_precedence_and_empty_falls_back() {
        let raw = br#"{"operation":"create","container_id":"cid-1","phase":"init","sandboxId":"sb-1"}"#;

        let overridden = parse_manifest_bom_safe(raw, Some("exec"), Some("cid-override"))
            .expect("CLI overrides should succeed");
        assert_eq!(overridden["operation"], "exec");
        assert_eq!(overridden["container_id"], "cid-override");
        assert_eq!(overridden["phase"], "init");
        assert_eq!(overridden["sandboxId"], "sb-1");

        let fallback = parse_manifest_bom_safe(raw, Some("   "), Some(""))
            .expect("blank CLI overrides should fall back to manifest keys");
        assert_eq!(fallback["operation"], "create");
        assert_eq!(fallback["container_id"], "cid-1");
    }

    #[test]
    fn phase3_parity_manifest_rejects_empty_invalid_utf8_json_and_non_object() {
        assert!(parse_manifest_bom_safe(b"", None, None).is_err());
        assert!(parse_manifest_bom_safe(UTF8_BOM, None, None).is_err());
        assert!(parse_manifest_bom_safe(b"   \r\n  ", None, None).is_err());
        assert!(parse_manifest_bom_safe(&[0xFF, 0xFE, 0xFD], None, None).is_err());
        assert!(parse_manifest_bom_safe(b"{not-json", None, None).is_err());
        assert!(parse_manifest_bom_safe(b"[1, 2, 3]", None, None).is_err());
        assert!(parse_manifest_bom_safe(b"\"scalar\"", None, None).is_err());
    }

    // ── Story 18.1 / AC-18.1.2: Chunked binary VMBus framing & SHA-256 integrity ──

    #[test]
    fn phase3_parity_vmbus_empty_payload_roundtrip_and_zero_chunk_size_rejected() {
        assert!(chunk_payload_frames(b"hello", 0).is_err());

        let frames = chunk_payload_frames(&[], 65_536).expect("empty slice should return empty vec");
        assert!(frames.is_empty());

        let reassembled = reassemble_chunk_frames(&frames).expect("empty frames should return empty vec");
        assert!(reassembled.is_empty());
    }

    #[test]
    fn phase3_parity_vmbus_multi_mb_roundtrip_bit_exact() {
        let payload: Vec<u8> = (0..(1_500_000usize))
            .map(|i| ((i.wrapping_mul(31) ^ (i >> 7)) & 0xFF) as u8)
            .collect();

        let frames = chunk_payload_frames(&payload, 65_536).expect("chunking 1.5 MB should succeed");
        assert_eq!(frames.len(), 23);
        assert_eq!(frames[0].seq, 0);
        assert_eq!(frames[0].total_frames, 23);
        assert_eq!(frames[22].seq, 22);

        let reassembled = reassemble_chunk_frames(&frames).expect("reassembly should succeed");
        assert_eq!(reassembled, payload);
    }

    #[test]
    fn phase3_parity_vmbus_fails_closed_on_tamper_missing_or_out_of_order() {
        let payload = vec![0xA5u8; 200_000];
        let base_frames = chunk_payload_frames(&payload, 65_536).expect("chunking should succeed");
        assert_eq!(base_frames.len(), 4);

        // Tampered payload byte
        let mut tampered_bytes = base_frames.clone();
        tampered_bytes[1].data[10] ^= 0xFF;
        assert_eq!(
            reassemble_chunk_frames(&tampered_bytes),
            Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string())
        );

        // Tampered chunk digest
        let mut tampered_digest = base_frames.clone();
        tampered_digest[2].chunk_sha256 = "0".repeat(64);
        assert_eq!(
            reassemble_chunk_frames(&tampered_digest),
            Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string())
        );

        // Missing frame (truncation)
        let missing_frame = base_frames[..3].to_vec();
        assert_eq!(
            reassemble_chunk_frames(&missing_frame),
            Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string())
        );

        // Out-of-order seq
        let mut out_of_order = base_frames.clone();
        out_of_order.swap(1, 2);
        assert_eq!(
            reassemble_chunk_frames(&out_of_order),
            Err("ERR_CHUNK_CHECKSUM_MISMATCH".to_string())
        );
    }

    // ── Story 18.2 / AC-18.2.1: Bounded parallel snapshot forking & immutable parent hash ──

    #[test]
    fn phase3_parity_snapshot_fork_allocates_bounded_siblings_and_preserves_parent_hash() {
        let branches = create_parallel_forks(
            "chk-base-01",
            &["plan-a", "plan-b", "plan-c", "plan-d"],
            0,
            4,
            5,
        )
        .expect("4 parallel forks at depth 0/4 should succeed");

        assert_eq!(branches.len(), 4);
        for branch in &branches {
            assert_eq!(branch.parent_checkpoint_id, "chk-base-01");
            assert_eq!(branch.depth, 1);
            assert_eq!(branch.status, "ACTIVE");
            assert!(branch.diff_disk_path.ends_with(".avhdx"));
        }

        let parent_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
        let winner_id = branches[1].branch_id.clone();
        let (reconciled, post_hash) =
            discard_losing_branches(&branches, Some(&winner_id), parent_hash);

        assert_eq!(post_hash, parent_hash);
        assert_eq!(reconciled.len(), 4);
        assert_eq!(reconciled[0].status, "DISCARDED");
        assert_eq!(reconciled[1].status, "ACTIVE");
        assert_eq!(reconciled[2].status, "DISCARDED");
        assert_eq!(reconciled[3].status, "DISCARDED");

        let (empty_reconciled, empty_hash) = discard_losing_branches(&[], None, parent_hash);
        assert!(empty_reconciled.is_empty());
        assert_eq!(empty_hash, parent_hash);
    }

    #[test]
    fn phase3_parity_snapshot_fork_enforces_depth_and_bounds() {
        assert_eq!(
            create_parallel_forks("chk-1", &["a"], 4, 4, 5),
            Err("ERR_FORK_DEPTH_EXCEEDED".to_string())
        );
        assert_eq!(
            create_parallel_forks("chk-1", &["a"], 0, 0, 5),
            Err("ERR_FORK_DEPTH_EXCEEDED".to_string())
        );
        assert_eq!(
            create_parallel_forks("", &["a"], 0, 4, 5),
            Err("ERR_FORK_BOUNDS_INVALID".to_string())
        );
        assert_eq!(
            create_parallel_forks("chk-1", &[], 0, 4, 5),
            Err("ERR_FORK_BOUNDS_INVALID".to_string())
        );
        assert_eq!(
            create_parallel_forks("chk-1", &["a", "b", "c", "d", "e", "f"], 0, 4, 5),
            Err("ERR_FORK_BOUNDS_INVALID".to_string())
        );
        assert_eq!(
            create_parallel_forks("chk-1", &["a", "a"], 0, 4, 5),
            Err("ERR_FORK_BOUNDS_INVALID".to_string())
        );
        assert_eq!(
            create_parallel_forks("chk-1", &["a", "   "], 0, 4, 5),
            Err("ERR_FORK_BOUNDS_INVALID".to_string())
        );
    }

    // ── Story 18.2 / AC-18.2.2: Token-boundary zero-secret git sync scanner ──

    #[test]
    fn phase3_parity_git_sync_scanner_allows_clean_url_path_env_and_empty_inputs() {
        assert_eq!(scan_git_sync_secrets(None, &[]), Ok(()));
        assert_eq!(
            scan_git_sync_secrets(
                Some("https://github.com/microsoft/mxc.git"),
                &[
                    ("PATH", "/usr/local/bin:/usr/bin"),
                    ("GOPATH", "/workspace/go"),
                    ("PATTERNS", "*.rs"),
                    ("RUST_LOG", "info"),
                ],
            ),
            Ok(())
        );
    }

    #[test]
    fn phase3_parity_git_sync_scanner_rejects_url_creds_sensitive_keys_and_secret_values() {
        assert_eq!(
            scan_git_sync_secrets(Some("https://user:supersecret@github.com/org/repo.git"), &[]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("GITHUB_PAT", "placeholder")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("API_TOKEN", "abc")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("SSH_AUTH_SOCK", "/tmp/agent.sock")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("MY_API_KEY", "12345")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("SAFE_VAR", "ghp_1234567890abcdef")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("SAFE_VAR", "github_pat_abcdef")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("SAFE_VAR", "glpat-abcdef")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(None, &[("SAFE_VAR", "AKIAIOSFODNN7EXAMPLE")]),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
        assert_eq!(
            scan_git_sync_secrets(
                None,
                &[("SAFE_VAR", "-----BEGIN OPENSSH PRIVATE KEY-----\nabc")]
            ),
            Err("ERR_STATIC_SECRET_DETECTED".to_string())
        );
    }
}
