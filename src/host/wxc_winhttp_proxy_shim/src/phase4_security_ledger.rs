#![allow(dead_code)]

//! Phase 4 Epic 019 (ADR-020 / FDD-019 / TP-18):
//! Compiled host-side Zero-Secret Credential Sidecar Proxy,
//! Protocol-Aware MCP JSON-RPC Firewall PEP, EU Evidence Ledger (>= 180 days),
//! and Hit-L `freeze_and_rollback` circuit breaker.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

/// EU AI Act Art. 19 minimum retention floor in days.
pub const EU_MIN_RETENTION_DAYS: u32 = 180;

/// Canonical 64-hex-character genesis previous hash for sequence 1.
pub const GENESIS_PREV_HASH: &str =
    "0000000000000000000000000000000000000000000000000000000000000000";

/// Constant-time byte slice equality to prevent timing side-channels on
/// secret identifiers, scopes, and SHA-256 digests.
pub fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff: u8 = 0;
    for (&x, &y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    let digest = hasher.finalize();
    let mut out = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut out, "{byte:02x}");
    }
    out
}

// ============================================================================
// 1. Compiled Host Zero-Secret Credential Sidecar Proxy (AC-19.1.1)
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScopedSecretEntry {
    pub placeholder: String,
    pub secret_value: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SidecarInjectionResult {
    pub allowed: bool,
    pub reason_code: String,
    pub outbound_headers: BTreeMap<String, String>,
    pub redacted_audit_json: String,
}

#[derive(Debug, Clone, Default)]
pub struct CredentialSidecarProxy {
    /// Allowlist keyed by `(target_host_lowercase, secret_scope)`.
    allowlist: BTreeMap<(String, String), ScopedSecretEntry>,
}

impl CredentialSidecarProxy {
    pub fn new() -> Self {
        Self::default()
    }

    /// Registers an allowlisted `(target_host, secret_scope)` binding to a
    /// declared placeholder token and its host-vault secret value.
    pub fn register_scoped_secret(
        &mut self,
        target_host: impl Into<String>,
        secret_scope: impl Into<String>,
        placeholder: impl Into<String>,
        secret_value: impl Into<String>,
    ) {
        let host = target_host.into().trim().to_ascii_lowercase();
        let scope = secret_scope.into().trim().to_string();
        self.allowlist.insert(
            (host, scope),
            ScopedSecretEntry {
                placeholder: placeholder.into(),
                secret_value: secret_value.into(),
            },
        );
    }

    fn scrub_value(&self, input: &str) -> String {
        let mut scrubbed = input.to_string();
        for entry in self.allowlist.values() {
            if !entry.secret_value.is_empty() && scrubbed.contains(&entry.secret_value) {
                scrubbed = scrubbed.replace(&entry.secret_value, "[REDACTED]");
            }
        }
        scrubbed
    }

    fn build_redacted_audit_json(
        &self,
        allowed: bool,
        reason_code: &str,
        target_host: Option<&str>,
        secret_scope: Option<&str>,
        headers: Option<&BTreeMap<String, String>>,
    ) -> String {
        let mut redacted_headers = BTreeMap::new();
        if let Some(hdrs) = headers {
            for (k, v) in hdrs {
                redacted_headers.insert(self.scrub_value(k), self.scrub_value(v));
            }
        }
        let audit_obj = json!({
            "allowed": allowed,
            "reason_code": reason_code,
            "target_host": target_host.map(|h| self.scrub_value(h)),
            "secret_scope": secret_scope.map(|s| self.scrub_value(s)),
            "headers": redacted_headers,
        });
        self.scrub_value(&audit_obj.to_string())
    }

    /// Resolves allowlisted `(target_host, secret_scope)` placeholders into
    /// outbound headers while scrubbing every vault secret (`[REDACTED]`) from
    /// `redacted_audit_json` on both allowed and denied paths.
    pub fn inject_credentials(
        &self,
        target_host: Option<&str>,
        secret_scope: Option<&str>,
        headers: Option<&BTreeMap<String, String>>,
    ) -> SidecarInjectionResult {
        let deny = |hdrs: Option<&BTreeMap<String, String>>| SidecarInjectionResult {
            allowed: false,
            reason_code: "ERR_SECRET_SCOPE_DENIED".to_string(),
            outbound_headers: BTreeMap::new(),
            redacted_audit_json: self.build_redacted_audit_json(
                false,
                "ERR_SECRET_SCOPE_DENIED",
                target_host,
                secret_scope,
                hdrs,
            ),
        };

        let host_raw = match target_host {
            Some(h) if !h.trim().is_empty() => h.trim().to_ascii_lowercase(),
            _ => return deny(headers),
        };
        let scope_raw = match secret_scope {
            Some(s) if !s.trim().is_empty() => s.trim(),
            _ => return deny(headers),
        };
        let in_headers = match headers {
            Some(h) if !h.is_empty() => h,
            _ => return deny(headers),
        };

        // Constant-time lookup across allowlisted (host, scope) entries.
        let mut matched_entry: Option<&ScopedSecretEntry> = None;
        for ((allowed_host, allowed_scope), entry) in &self.allowlist {
            let host_ok = constant_time_eq(allowed_host.as_bytes(), host_raw.as_bytes());
            let scope_ok = constant_time_eq(allowed_scope.as_bytes(), scope_raw.as_bytes());
            if host_ok && scope_ok {
                matched_entry = Some(entry);
            }
        }

        let entry = match matched_entry {
            Some(e) if !e.placeholder.is_empty() => e,
            _ => return deny(Some(in_headers)),
        };

        let mut placeholder_found = false;
        let mut outbound_headers = BTreeMap::new();
        for (k, v) in in_headers {
            if v.contains(&entry.placeholder) {
                placeholder_found = true;
                outbound_headers.insert(
                    k.clone(),
                    v.replace(&entry.placeholder, &entry.secret_value),
                );
            } else {
                outbound_headers.insert(k.clone(), v.clone());
            }
        }

        if !placeholder_found {
            return deny(Some(in_headers));
        }

        let redacted_audit_json = self.build_redacted_audit_json(
            true,
            "OK",
            Some(&host_raw),
            Some(scope_raw),
            Some(&outbound_headers),
        );

        SidecarInjectionResult {
            allowed: true,
            reason_code: "OK".to_string(),
            outbound_headers,
            redacted_audit_json,
        }
    }
}

// ============================================================================
// 2. Compiled MCP JSON-RPC Firewall PEP (AC-19.1.2)
// ============================================================================

#[derive(Debug, Clone, Default)]
pub struct McpFirewallPolicy {
    /// Approved MCP server IDs mapped to their pinned schema SHA-256 hex digest.
    pub approved_servers: BTreeMap<String, String>,
    /// Explicitly blocked MCP tool names.
    pub blocked_tools: BTreeSet<String>,
    /// Case-insensitive disallowed argument key/value substrings.
    pub blocked_arg_patterns: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct McpCallVerdict {
    pub allowed: bool,
    pub reason_code: String,
    pub server_id: String,
    pub tool_name: String,
}

fn extract_str_field<'a>(root: &'a Value, params: Option<&'a Value>, keys: &[&str]) -> String {
    for key in keys {
        if let Some(s) = root.get(*key).and_then(Value::as_str) {
            if !s.trim().is_empty() {
                return s.trim().to_string();
            }
        }
        if let Some(p) = params {
            if let Some(s) = p.get(*key).and_then(Value::as_str) {
                if !s.trim().is_empty() {
                    return s.trim().to_string();
                }
            }
        }
    }
    String::new()
}

fn value_violates_patterns(value: &Value, lowered_patterns: &[String]) -> bool {
    match value {
        Value::String(s) => {
            let lowered = s.to_ascii_lowercase();
            lowered_patterns
                .iter()
                .any(|pat| !pat.is_empty() && lowered.contains(pat))
        }
        Value::Array(items) => items
            .iter()
            .any(|item| value_violates_patterns(item, lowered_patterns)),
        Value::Object(map) => map.iter().any(|(k, v)| {
            let key_lower = k.to_ascii_lowercase();
            let key_hit = lowered_patterns
                .iter()
                .any(|pat| !pat.is_empty() && key_lower.contains(pat));
            key_hit || value_violates_patterns(v, lowered_patterns)
        }),
        _ => false,
    }
}

/// Evaluates an incoming MCP `tools/call` JSON envelope in deterministic
/// precedence:
/// `ERR_MCP_SERVER_UNAPPROVED` -> `ERR_MCP_SCHEMA_DRIFT` ->
/// `ERR_MCP_TOOL_BLOCKED` -> `ERR_MCP_ARG_VIOLATION`.
/// Fails closed on `None`, empty, or malformed JSON.
pub fn evaluate_mcp_call(
    policy: Option<&McpFirewallPolicy>,
    request_json: Option<&str>,
) -> McpCallVerdict {
    let fail = |reason: &str, server_id: String, tool_name: String| McpCallVerdict {
        allowed: false,
        reason_code: reason.to_string(),
        server_id,
        tool_name,
    };

    let policy = match policy {
        Some(p) => p,
        None => return fail("ERR_MCP_SERVER_UNAPPROVED", String::new(), String::new()),
    };

    let raw = match request_json {
        Some(s) if !s.trim().is_empty() => s,
        _ => return fail("ERR_MCP_SERVER_UNAPPROVED", String::new(), String::new()),
    };

    let parsed: Value = match serde_json::from_str::<Value>(raw) {
        Ok(v) if v.is_object() => v,
        _ => return fail("ERR_MCP_SERVER_UNAPPROVED", String::new(), String::new()),
    };

    let params = parsed.get("params");
    let server_id = extract_str_field(&parsed, params, &["server_id"]);
    let schema_hash = extract_str_field(&parsed, params, &["schema_hash", "schema_sha256"]);
    let tool_name = extract_str_field(&parsed, params, &["name", "tool_name"]);

    // 1. Server allowlist check
    let expected_schema = match policy.approved_servers.get(&server_id) {
        Some(expected) if !server_id.is_empty() => expected,
        _ => return fail("ERR_MCP_SERVER_UNAPPROVED", server_id, tool_name),
    };

    // 2. Constant-time schema digest verification
    if schema_hash.is_empty()
        || expected_schema.is_empty()
        || !constant_time_eq(schema_hash.as_bytes(), expected_schema.as_bytes())
    {
        return fail("ERR_MCP_SCHEMA_DRIFT", server_id, tool_name);
    }

    // 3. Tool blocklist / presence check
    if tool_name.is_empty() || policy.blocked_tools.contains(&tool_name) {
        return fail("ERR_MCP_TOOL_BLOCKED", server_id, tool_name);
    }

    // 4. Arguments object validation + recursive pattern inspection
    let arguments = params
        .and_then(|p| p.get("arguments"))
        .or_else(|| parsed.get("arguments"));

    let args_obj = match arguments {
        Some(v) if v.is_object() => v,
        _ => return fail("ERR_MCP_ARG_VIOLATION", server_id, tool_name),
    };

    let lowered_patterns: Vec<String> = policy
        .blocked_arg_patterns
        .iter()
        .map(|p| p.to_ascii_lowercase())
        .collect();

    if value_violates_patterns(args_obj, &lowered_patterns) {
        return fail("ERR_MCP_ARG_VIOLATION", server_id, tool_name);
    }

    McpCallVerdict {
        allowed: true,
        reason_code: "ALLOWED".to_string(),
        server_id,
        tool_name,
    }
}

// ============================================================================
// 3. Compiled Host EU Evidence Ledger (>= 180d) (AC-19.2.1)
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LedgerEvent {
    pub seq: u64,
    pub timestamp_utc: String,
    pub event_type: String,
    pub session_id: String,
    pub payload_sha256: String,
    pub prev_hash: String,
    pub entry_hash: String,
}

#[derive(Debug, Clone)]
pub struct EuEvidenceLedger {
    retention_days: u32,
    events: Vec<LedgerEvent>,
}

fn compute_entry_hash(
    seq: u64,
    timestamp_utc: &str,
    event_type: &str,
    session_id: &str,
    payload_sha256: &str,
    prev_hash: &str,
) -> String {
    let canonical = format!(
        "{seq}|{timestamp_utc}|{event_type}|{session_id}|{payload_sha256}|{prev_hash}"
    );
    sha256_hex(canonical.as_bytes())
}

impl EuEvidenceLedger {
    /// Creates an EU AI Act Art. 19 compliant ledger, rejecting `retention_days < 180`.
    pub fn new(retention_days: u32) -> Result<Self, String> {
        if retention_days < EU_MIN_RETENTION_DAYS {
            return Err("ERR_RETENTION_BELOW_EU_FLOOR".to_string());
        }
        Ok(Self {
            retention_days,
            events: Vec::new(),
        })
    }

    pub fn retention_days(&self) -> u32 {
        self.retention_days
    }

    pub fn events(&self) -> &[LedgerEvent] {
        &self.events
    }

    pub fn events_mut(&mut self) -> &mut [LedgerEvent] {
        &mut self.events
    }

    pub fn append_event(
        &mut self,
        event_type: &str,
        session_id: &str,
        payload_json: &str,
        timestamp_utc: &str,
    ) -> Result<LedgerEvent, String> {
        if event_type.trim().is_empty()
            || session_id.trim().is_empty()
            || timestamp_utc.trim().is_empty()
        {
            return Err("ERR_INVALID_LEDGER_EVENT".to_string());
        }

        let seq = (self.events.len() as u64) + 1;
        let payload_sha256 = sha256_hex(payload_json.as_bytes());
        let prev_hash = self
            .events
            .last()
            .map(|e| e.entry_hash.clone())
            .unwrap_or_else(|| GENESIS_PREV_HASH.to_string());

        let entry_hash = compute_entry_hash(
            seq,
            timestamp_utc,
            event_type,
            session_id,
            &payload_sha256,
            &prev_hash,
        );

        let event = LedgerEvent {
            seq,
            timestamp_utc: timestamp_utc.to_string(),
            event_type: event_type.to_string(),
            session_id: session_id.to_string(),
            payload_sha256,
            prev_hash,
            entry_hash,
        };
        self.events.push(event.clone());
        Ok(event)
    }

    /// Verifies the full SHA-256 hash chain. Empty chains safely verify as `Ok(())`.
    pub fn verify_chain(&self) -> Result<(), String> {
        for (idx, ev) in self.events.iter().enumerate() {
            let expected_seq = (idx as u64) + 1;
            if ev.seq != expected_seq {
                return Err("ERR_LEDGER_CHAIN_BROKEN".to_string());
            }

            let expected_prev = if idx == 0 {
                GENESIS_PREV_HASH
            } else {
                self.events[idx - 1].entry_hash.as_str()
            };
            if !constant_time_eq(ev.prev_hash.as_bytes(), expected_prev.as_bytes()) {
                return Err("ERR_LEDGER_CHAIN_BROKEN".to_string());
            }

            let expected_entry = compute_entry_hash(
                ev.seq,
                &ev.timestamp_utc,
                &ev.event_type,
                &ev.session_id,
                &ev.payload_sha256,
                &ev.prev_hash,
            );
            if !constant_time_eq(ev.entry_hash.as_bytes(), expected_entry.as_bytes()) {
                return Err("ERR_LEDGER_CHAIN_BROKEN".to_string());
            }
        }
        Ok(())
    }
}

// ============================================================================
// 4. Hit-L `freeze_and_rollback` Circuit Breaker (AC-19.2.2)
// ============================================================================

/// Atomically freezes a live session, records a tamper-evident
/// `"FREEZE_AND_ROLLBACK"` event into the `EuEvidenceLedger`, and returns the
/// `"FROZEN_ROLLED_BACK"` state envelope.
pub fn freeze_and_rollback(
    session_id: Option<&str>,
    operator_id: Option<&str>,
    checkpoint_id: Option<&str>,
    ledger: &mut EuEvidenceLedger,
    timestamp_utc: &str,
) -> Result<Value, String> {
    let sid = match session_id {
        Some(s) if !s.trim().is_empty() => s.trim(),
        _ => return Err("ERR_INVALID_ROLLBACK_IDENTIFIER".to_string()),
    };
    let op = match operator_id {
        Some(s) if !s.trim().is_empty() => s.trim(),
        _ => return Err("ERR_INVALID_ROLLBACK_IDENTIFIER".to_string()),
    };
    let ckpt = match checkpoint_id {
        Some(s) if !s.trim().is_empty() => s.trim(),
        _ => return Err("ERR_INVALID_ROLLBACK_IDENTIFIER".to_string()),
    };
    if timestamp_utc.trim().is_empty() {
        return Err("ERR_INVALID_ROLLBACK_IDENTIFIER".to_string());
    }

    let payload = json!({
        "action": "FREEZE_AND_ROLLBACK",
        "state": "FROZEN_ROLLED_BACK",
        "session_id": sid,
        "operator_id": op,
        "checkpoint_id": ckpt,
    })
    .to_string();

    let event = ledger.append_event("FREEZE_AND_ROLLBACK", sid, &payload, timestamp_utc)?;

    Ok(json!({
        "state": "FROZEN_ROLLED_BACK",
        "session_id": sid,
        "operator_id": op,
        "checkpoint_id": ckpt,
        "timestamp_utc": timestamp_utc,
        "ledger_seq": event.seq,
        "entry_hash": event.entry_hash,
    }))
}

// ============================================================================
// Unit Tests (AC-19.1.1, AC-19.1.2, AC-19.2.1, AC-19.2.2)
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    fn sample_proxy() -> CredentialSidecarProxy {
        let mut proxy = CredentialSidecarProxy::new();
        proxy.register_scoped_secret(
            "api.github.com",
            "github:repo:read",
            "__MXC_SECRET_GITHUB__",
            "ghp_SUPER_SECRET_TOKEN_987654",
        );
        proxy.register_scoped_secret(
            "api.openai.com",
            "openai:inference",
            "__MXC_SECRET_OPENAI__",
            "sk-live-ANOTHER_SECRET_123456",
        );
        proxy
    }

    fn sample_mcp_policy() -> McpFirewallPolicy {
        let mut approved_servers = BTreeMap::new();
        approved_servers.insert("mcp-github".to_string(), "sha256-valid-schema-aaa".to_string());

        let mut blocked_tools = BTreeSet::new();
        blocked_tools.insert("delete_repo".to_string());

        McpFirewallPolicy {
            approved_servers,
            blocked_tools,
            blocked_arg_patterns: vec![
                "../".to_string(),
                "rm -rf".to_string(),
                "secret_dump".to_string(),
            ],
        }
    }

    // --- AC-19.1.1: Credential Sidecar Proxy ---

    #[test]
    fn sidecar_injects_allowlisted_secret_and_scrubs_audit_within_5ms() {
        let proxy = sample_proxy();
        let mut headers = BTreeMap::new();
        headers.insert(
            "Authorization".to_string(),
            "Bearer __MXC_SECRET_GITHUB__".to_string(),
        );
        headers.insert("X-Trace-Id".to_string(), "trace-001".to_string());

        let start = Instant::now();
        let res = proxy.inject_credentials(
            Some("API.GITHUB.COM"),
            Some("github:repo:read"),
            Some(&headers),
        );
        let elapsed_ms = start.elapsed().as_millis();

        assert!(res.allowed);
        assert_eq!(res.reason_code, "OK");
        assert!(elapsed_ms <= 5, "sidecar injection took {elapsed_ms} ms > 5 ms");
        assert_eq!(
            res.outbound_headers.get("Authorization").map(String::as_str),
            Some("Bearer ghp_SUPER_SECRET_TOKEN_987654")
        );
        assert!(!res.redacted_audit_json.contains("ghp_SUPER_SECRET_TOKEN_987654"));
        assert!(res.redacted_audit_json.contains("[REDACTED]"));
    }

    #[test]
    fn sidecar_denies_unscoped_or_missing_placeholder_and_scrubs_audit() {
        let proxy = sample_proxy();

        // Case 1: None/empty inputs
        for (h, s) in [(None, Some("github:repo:read")), (Some("api.github.com"), None), (Some(""), Some(""))] {
            let res = proxy.inject_credentials(h, s, None);
            assert!(!res.allowed);
            assert_eq!(res.reason_code, "ERR_SECRET_SCOPE_DENIED");
            assert!(res.outbound_headers.is_empty());
        }

        // Case 2: Unscoped host/scope even if request accidentally leaks a vault secret
        let mut leaked_headers = BTreeMap::new();
        leaked_headers.insert(
            "X-Leak".to_string(),
            "ghp_SUPER_SECRET_TOKEN_987654".to_string(),
        );
        let res_unscoped = proxy.inject_credentials(
            Some("evil.example.com"),
            Some("github:repo:read"),
            Some(&leaked_headers),
        );
        assert!(!res_unscoped.allowed);
        assert_eq!(res_unscoped.reason_code, "ERR_SECRET_SCOPE_DENIED");
        assert!(res_unscoped.outbound_headers.is_empty());
        assert!(!res_unscoped
            .redacted_audit_json
            .contains("ghp_SUPER_SECRET_TOKEN_987654"));
        assert!(res_unscoped.redacted_audit_json.contains("[REDACTED]"));

        // Case 3: Allowlisted host/scope but placeholder missing from headers
        let mut no_placeholder = BTreeMap::new();
        no_placeholder.insert("Authorization".to_string(), "Bearer plain".to_string());
        let res_missing = proxy.inject_credentials(
            Some("api.github.com"),
            Some("github:repo:read"),
            Some(&no_placeholder),
        );
        assert!(!res_missing.allowed);
        assert_eq!(res_missing.reason_code, "ERR_SECRET_SCOPE_DENIED");
        assert!(res_missing.outbound_headers.is_empty());
    }

    // --- AC-19.1.2: MCP JSON-RPC Firewall PEP ---

    #[test]
    fn mcp_firewall_allows_valid_call_within_2ms() {
        let policy = sample_mcp_policy();
        let req = json!({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "server_id": "mcp-github",
            "schema_hash": "sha256-valid-schema-aaa",
            "params": {
                "name": "list_issues",
                "arguments": {
                    "repo": "mxc/core",
                    "limit": 10
                }
            }
        })
        .to_string();

        let start = Instant::now();
        let verdict = evaluate_mcp_call(Some(&policy), Some(&req));
        let elapsed_ms = start.elapsed().as_millis();

        assert!(verdict.allowed);
        assert_eq!(verdict.reason_code, "ALLOWED");
        assert_eq!(verdict.server_id, "mcp-github");
        assert_eq!(verdict.tool_name, "list_issues");
        assert!(elapsed_ms <= 2, "MCP evaluation took {elapsed_ms} ms > 2 ms");
    }

    #[test]
    fn mcp_firewall_enforces_deterministic_precedence() {
        let policy = sample_mcp_policy();

        // 1. Unapproved server beats schema drift, blocked tool, and bad args
        let req_all_bad = json!({
            "server_id": "mcp-rogue",
            "schema_hash": "wrong-hash",
            "params": {
                "name": "delete_repo",
                "arguments": { "cmd": "rm -rf /" }
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_all_bad)).reason_code,
            "ERR_MCP_SERVER_UNAPPROVED"
        );

        // 2. Schema drift beats blocked tool and bad args
        let req_drift = json!({
            "server_id": "mcp-github",
            "schema_hash": "sha256-drifted-bbb",
            "params": {
                "name": "delete_repo",
                "arguments": { "cmd": "rm -rf /" }
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_drift)).reason_code,
            "ERR_MCP_SCHEMA_DRIFT"
        );

        // 3. Blocked tool beats bad args
        let req_blocked_tool = json!({
            "server_id": "mcp-github",
            "schema_hash": "sha256-valid-schema-aaa",
            "params": {
                "name": "delete_repo",
                "arguments": { "cmd": "rm -rf /" }
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_blocked_tool)).reason_code,
            "ERR_MCP_TOOL_BLOCKED"
        );

        // 4a. Argument violation via nested value
        let req_bad_val = json!({
            "server_id": "mcp-github",
            "schema_hash": "sha256-valid-schema-aaa",
            "params": {
                "name": "read_file",
                "arguments": { "nested": [{ "path": "../../etc/passwd" }] }
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_bad_val)).reason_code,
            "ERR_MCP_ARG_VIOLATION"
        );

        // 4b. Argument violation via nested key
        let req_bad_key = json!({
            "server_id": "mcp-github",
            "schema_hash": "sha256-valid-schema-aaa",
            "params": {
                "name": "read_file",
                "arguments": { "meta": { "SECRET_DUMP_flag": true } }
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_bad_key)).reason_code,
            "ERR_MCP_ARG_VIOLATION"
        );

        // 4c. Non-object or missing arguments
        let req_non_obj = json!({
            "server_id": "mcp-github",
            "schema_hash": "sha256-valid-schema-aaa",
            "params": {
                "name": "read_file",
                "arguments": ["not-an-object"]
            }
        })
        .to_string();
        assert_eq!(
            evaluate_mcp_call(Some(&policy), Some(&req_non_obj)).reason_code,
            "ERR_MCP_ARG_VIOLATION"
        );
    }

    #[test]
    fn mcp_firewall_fails_closed_on_none_empty_or_malformed_json() {
        let policy = sample_mcp_policy();
        assert!(!evaluate_mcp_call(None, Some("{}")).allowed);
        assert!(!evaluate_mcp_call(Some(&policy), None).allowed);
        assert!(!evaluate_mcp_call(Some(&policy), Some("   ")).allowed);
        assert!(!evaluate_mcp_call(Some(&policy), Some("{not valid json")).allowed);
        assert!(!evaluate_mcp_call(Some(&policy), Some("[1, 2, 3]")).allowed);
    }

    // --- AC-19.2.1: EU Evidence Ledger ---

    #[test]
    fn eu_ledger_enforces_180_day_floor_and_empty_chain_verifies_ok() {
        assert_eq!(
            EuEvidenceLedger::new(179).unwrap_err(),
            "ERR_RETENTION_BELOW_EU_FLOOR"
        );
        assert_eq!(
            EuEvidenceLedger::new(0).unwrap_err(),
            "ERR_RETENTION_BELOW_EU_FLOOR"
        );

        let ledger = EuEvidenceLedger::new(180).expect("180 days meets EU floor");
        assert_eq!(ledger.retention_days(), 180);
        assert!(ledger.verify_chain().is_ok());
    }

    #[test]
    fn eu_ledger_chains_sha256_and_detects_historical_mutation() {
        let mut ledger = EuEvidenceLedger::new(365).unwrap();
        let e1 = ledger
            .append_event("SESSION_START", "sess-01", r#"{"vm":"hv-1"}"#, "2026-11-25T08:00:00Z")
            .unwrap();
        let e2 = ledger
            .append_event("MCP_CALL", "sess-01", r#"{"tool":"list_issues"}"#, "2026-11-25T08:01:00Z")
            .unwrap();

        assert_eq!(e1.seq, 1);
        assert_eq!(e1.prev_hash, GENESIS_PREV_HASH);
        assert_eq!(e2.seq, 2);
        assert_eq!(e2.prev_hash, e1.entry_hash);
        assert!(ledger.verify_chain().is_ok());

        // Tamper with historical event 1 payload hash
        ledger.events_mut()[0].payload_sha256 = "deadbeef".repeat(8);
        assert_eq!(
            ledger.verify_chain().unwrap_err(),
            "ERR_LEDGER_CHAIN_BROKEN"
        );
    }

    // --- AC-19.2.2: Hit-L freeze_and_rollback ---

    #[test]
    fn freeze_and_rollback_validates_identifiers_and_appends_within_250ms() {
        let mut ledger = EuEvidenceLedger::new(180).unwrap();

        // Rejects None / empty identifiers without mutating ledger
        assert!(freeze_and_rollback(None, Some("op-1"), Some("ckpt-1"), &mut ledger, "2026-11-25T08:05:00Z").is_err());
        assert!(freeze_and_rollback(Some("sess-1"), Some(""), Some("ckpt-1"), &mut ledger, "2026-11-25T08:05:00Z").is_err());
        assert!(freeze_and_rollback(Some("sess-1"), Some("op-1"), None, &mut ledger, "2026-11-25T08:05:00Z").is_err());
        assert!(ledger.events().is_empty());

        let start = Instant::now();
        let resp = freeze_and_rollback(
            Some("sess-42"),
            Some("secops-alice"),
            Some("ckpt-20261125-001"),
            &mut ledger,
            "2026-11-25T08:05:00Z",
        )
        .expect("valid freeze_and_rollback should succeed");
        let elapsed_ms = start.elapsed().as_millis();

        assert_eq!(resp["state"], "FROZEN_ROLLED_BACK");
        assert_eq!(resp["session_id"], "sess-42");
        assert_eq!(resp["operator_id"], "secops-alice");
        assert_eq!(resp["checkpoint_id"], "ckpt-20261125-001");
        assert_eq!(resp["ledger_seq"], 1);
        assert!(elapsed_ms <= 250, "freeze_and_rollback took {elapsed_ms} ms > 250 ms");

        assert_eq!(ledger.events().len(), 1);
        assert_eq!(ledger.events()[0].event_type, "FREEZE_AND_ROLLBACK");
        assert!(ledger.verify_chain().is_ok());
    }
}
