"""MXC Zero-Secret Git Sync, Credential Sidecar Proxy & MCP Firewall (ADR-014 / Epic 013).

Implements:
  - Story 13.1: Host-side zero-secret bare git bundle sync planning (`mxc-sync`, IMP-MXC-017)
                and outbound CredentialSidecarProxy with constant-time placeholder validation and
                strict audit-log secret redaction (IMP-MXC-024).
  - Story 13.2: Protocol-aware MCP JSON-RPC Firewall (`McpFirewallPolicy`, `evaluate_mcp_call`)
                with deterministic fail-closed precedence and rug-pull schema digest checks
                (IMP-MXC-026).

All operations execute 100% offline using the Python 3 standard library only.
"""

from __future__ import annotations

import hmac
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")

# Patterns indicating static secret material inside remote URLs or environment values.
_SECRET_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"https?://[^/\s@]+@", re.IGNORECASE),
    re.compile(r"ghp_"),
    re.compile(r"github_pat_"),
    re.compile(r"glpat-"),
    re.compile(r"AKIA"),
    re.compile(r"BEGIN\s+[^\r\n]*PRIVATE\s+KEY", re.IGNORECASE),
)

_SENSITIVE_ENV_TOKENS: frozenset[str] = frozenset({"PAT", "TOKEN", "SECRET", "PASSWORD", "PASSWD"})
_SENSITIVE_ENV_SUBSTRINGS: tuple[str, ...] = ("SSH_AUTH_SOCK", "PRIVATE_KEY", "API_KEY")

_MAX_CREDENTIAL_HEADER_LEN = 16384
_MAX_MCP_ARG_DEPTH = 32


@dataclass(frozen=True)
class GitBundleSyncPlan:
    """Airgapped host-to-guest VMBus git bundle transfer plan with zero static secrets."""

    repo_slug: str
    bundle_sha256: str
    guest_target_dir: str
    nic_count: int = 0
    secrets_present: bool = False


@dataclass(frozen=True)
class McpFirewallPolicy:
    """Deny-by-default protocol-aware MCP JSON-RPC inspection policy."""

    allowed_servers: dict[str, str]
    allowed_tools: dict[str, set[str]]
    blocked_arg_patterns: tuple[str, ...]


@dataclass(frozen=True)
class McpCallVerdict:
    """Deterministic fail-closed verdict emitted by the MCP Firewall PEP."""

    allowed: bool
    reason_code: str
    server_id: str
    tool_name: str


def _has_secret_material(value: str) -> bool:
    return any(pattern.search(value) is not None for pattern in _SECRET_VALUE_PATTERNS)


def _is_sensitive_env_key(key: str) -> bool:
    upper = key.upper()
    if any(marker in upper for marker in _SENSITIVE_ENV_SUBSTRINGS):
        return True
    tokens = [tok for tok in re.split(r"[^A-Z0-9]+", upper) if tok]
    if any(tok in _SENSITIVE_ENV_TOKENS for tok in tokens):
        return True
    return "PRIVATE" in tokens and "KEY" in tokens


def _scan_sync_secrets(remote_url: str | None, guest_env: dict[str, str] | None) -> bool:
    if isinstance(remote_url, str) and remote_url and _has_secret_material(remote_url):
        return True
    if isinstance(guest_env, dict):
        for key, value in guest_env.items():
            if isinstance(key, str):
                if _is_sensitive_env_key(key) or _has_secret_material(key):
                    return True
            if isinstance(value, str) and value and _has_secret_material(value):
                return True
    return False


def plan_zero_secret_git_sync(
    *,
    repo_slug: str | None,
    remote_url: str | None,
    bundle_sha256: str | None,
    guest_target_dir: str | None,
    guest_env: dict[str, str] | None = None,
) -> tuple[bool, str, GitBundleSyncPlan | None]:
    """Validate an airgapped git bundle transfer plan and enforce zero static guest secrets."""
    if _scan_sync_secrets(remote_url, guest_env):
        return False, "ERR_STATIC_SECRET_DETECTED", None

    if remote_url is not None and not isinstance(remote_url, str):
        return False, "ERR_INVALID_SYNC_INPUT", None
    if guest_env is not None and not isinstance(guest_env, dict):
        return False, "ERR_INVALID_SYNC_INPUT", None
    if not isinstance(repo_slug, str) or not repo_slug.strip():
        return False, "ERR_INVALID_SYNC_INPUT", None
    if not isinstance(guest_target_dir, str) or not guest_target_dir.strip():
        return False, "ERR_INVALID_SYNC_INPUT", None
    if not isinstance(bundle_sha256, str) or _SHA256_HEX_RE.fullmatch(bundle_sha256) is None:
        return False, "ERR_INVALID_SYNC_INPUT", None

    return (
        True,
        "OK",
        GitBundleSyncPlan(
            repo_slug=repo_slug,
            bundle_sha256=bundle_sha256.lower(),
            guest_target_dir=guest_target_dir,
            nic_count=0,
            secrets_present=False,
        ),
    )


def _contains_constant_time(haystack: str, needle: str) -> bool:
    """Scan haystack for exact needle substring using constant-time digest checks."""
    nlen = len(needle)
    hlen = len(haystack)
    if nlen == 0 or hlen < nlen or hlen > _MAX_CREDENTIAL_HEADER_LEN:
        return False
    matched = False
    for idx in range(hlen - nlen + 1):
        if hmac.compare_digest(haystack[idx : idx + nlen], needle):
            matched = True
    return matched


class CredentialSidecarProxy:
    """Host-resident outbound proxy that substitutes allowlisted placeholders without guest exposure."""

    def __init__(self, vault_secrets: dict[tuple[str, str], tuple[str, str]] | None = None) -> None:
        cleaned: dict[tuple[str, str], tuple[str, str]] = {}
        if isinstance(vault_secrets, dict):
            for key, value in vault_secrets.items():
                if (
                    isinstance(key, tuple)
                    and len(key) == 2
                    and isinstance(key[0], str)
                    and isinstance(key[1], str)
                    and key[0]
                    and key[1]
                    and isinstance(value, tuple)
                    and len(value) == 2
                    and isinstance(value[0], str)
                    and isinstance(value[1], str)
                    and value[0]
                    and value[1]
                ):
                    cleaned[key] = value
        self._vault_secrets = cleaned
        # Longest-first ordering prevents partial-prefix leakage when redacting overlapping secrets.
        self._all_real_secrets: tuple[str, ...] = tuple(
            sorted({pair[1] for pair in cleaned.values()}, key=len, reverse=True)
        )

    def _redact_text(self, text: str, placeholder: str | None = None) -> str:
        redacted = text
        for secret in self._all_real_secrets:
            if secret in redacted:
                redacted = redacted.replace(secret, "[REDACTED]")
        if placeholder and placeholder in redacted:
            redacted = redacted.replace(placeholder, "[REDACTED]")
        return redacted

    def _build_audit_log(
        self,
        *,
        target_host: str | None,
        secret_scope: str | None,
        headers: dict[str, str] | None,
        allowed: bool,
        reason_code: str,
        placeholder: str | None = None,
    ) -> dict[str, Any]:
        safe_host = self._redact_text(target_host, placeholder) if isinstance(target_host, str) else ""
        safe_scope = self._redact_text(secret_scope, placeholder) if isinstance(secret_scope, str) else ""
        redacted_headers: dict[str, str] = {}
        if isinstance(headers, dict):
            for hk, hv in headers.items():
                key_str = self._redact_text(hk if isinstance(hk, str) else str(hk), placeholder)
                val_str = self._redact_text(hv if isinstance(hv, str) else str(hv), placeholder)
                redacted_headers[key_str] = val_str
        return {
            "target_host": safe_host,
            "secret_scope": safe_scope,
            "allowed": allowed,
            "reason_code": reason_code,
            "redacted_headers": redacted_headers,
        }

    def inject_credentials(
        self,
        *,
        target_host: str | None,
        secret_scope: str | None,
        headers: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Inject host-resident credentials only for allowlisted (host, scope) and valid placeholders."""
        t0 = time.perf_counter()

        def _deny() -> dict[str, Any]:
            return {
                "allowed": False,
                "reason_code": "ERR_SECRET_SCOPE_DENIED",
                "outbound_headers": {},
                "audit_log": self._build_audit_log(
                    target_host=target_host,
                    secret_scope=secret_scope,
                    headers=headers,
                    allowed=False,
                    reason_code="ERR_SECRET_SCOPE_DENIED",
                ),
                "elapsed_ms": (time.perf_counter() - t0) * 1000.0,
            }

        if (
            not isinstance(target_host, str)
            or not target_host
            or not isinstance(secret_scope, str)
            or not secret_scope
            or not isinstance(headers, dict)
            or not headers
        ):
            return _deny()

        vault_entry = self._vault_secrets.get((target_host, secret_scope))
        if vault_entry is None:
            return _deny()

        placeholder_token, real_secret_value = vault_entry
        outbound_headers: dict[str, str] = {}
        matched_placeholder = False

        for hk, hv in headers.items():
            if not isinstance(hk, str) or not isinstance(hv, str):
                return _deny()
            if _contains_constant_time(hv, placeholder_token):
                matched_placeholder = True
                outbound_headers[hk] = hv.replace(placeholder_token, real_secret_value)
            else:
                outbound_headers[hk] = hv

        if not matched_placeholder:
            return _deny()

        return {
            "allowed": True,
            "reason_code": "OK",
            "outbound_headers": outbound_headers,
            "audit_log": self._build_audit_log(
                target_host=target_host,
                secret_scope=secret_scope,
                headers=headers,
                allowed=True,
                reason_code="OK",
                placeholder=placeholder_token,
            ),
            "elapsed_ms": (time.perf_counter() - t0) * 1000.0,
        }


@lru_cache(maxsize=256)
def _compile_blocked_patterns(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    compiled: list[re.Pattern[str]] = []
    for raw in patterns:
        try:
            compiled.append(re.compile(raw, re.IGNORECASE))
        except re.error:
            compiled.append(re.compile(re.escape(raw), re.IGNORECASE))
    return tuple(compiled)


def _matches_any_pattern(text: str, compiled_patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) is not None for pattern in compiled_patterns)


def _walk_arguments_violate(
    node: Any,
    compiled_patterns: tuple[re.Pattern[str], ...],
    depth: int = 0,
) -> bool:
    """Recursively inspect argument keys and values for blocked patterns (fail-closed on excess depth)."""
    if depth > _MAX_MCP_ARG_DEPTH:
        return True
    if node is None:
        return False
    if isinstance(node, dict):
        for key, value in node.items():
            key_text = key if isinstance(key, str) else str(key)
            if _matches_any_pattern(key_text, compiled_patterns):
                return True
            if _walk_arguments_violate(value, compiled_patterns, depth + 1):
                return True
        return False
    if isinstance(node, (list, tuple, set, frozenset)):
        return any(_walk_arguments_violate(item, compiled_patterns, depth + 1) for item in node)
    text = node if isinstance(node, str) else str(node)
    return _matches_any_pattern(text, compiled_patterns)


def _extract_mcp_fields(request: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    params = request.get("params")
    params_dict = params if isinstance(params, dict) else {}

    server_id = request.get("server_id") if "server_id" in request else params_dict.get("server_id")
    schema_sha256 = (
        request.get("schema_sha256") if "schema_sha256" in request else params_dict.get("schema_sha256")
    )
    if "tool_name" in request:
        tool_name = request.get("tool_name")
    elif "tool_name" in params_dict:
        tool_name = params_dict.get("tool_name")
    else:
        tool_name = params_dict.get("name")

    if "arguments" in request:
        arguments = request.get("arguments")
    elif "arguments" in params_dict:
        arguments = params_dict.get("arguments")
    else:
        arguments = None

    return server_id, schema_sha256, tool_name, arguments


def evaluate_mcp_call(policy: McpFirewallPolicy | None, request: dict[str, Any] | None) -> McpCallVerdict:
    """Inspect an MCP JSON-RPC tool call in deterministic fail-closed precedence."""
    if not isinstance(request, dict):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_SERVER_UNAPPROVED",
            server_id="",
            tool_name="",
        )

    server_id, schema_sha256, tool_name, arguments = _extract_mcp_fields(request)
    safe_server_id = server_id if isinstance(server_id, str) else ""
    safe_tool_name = tool_name if isinstance(tool_name, str) else ""

    if policy is None:
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_SERVER_UNAPPROVED",
            server_id=safe_server_id,
            tool_name=safe_tool_name,
        )

    allowed_servers = getattr(policy, "allowed_servers", None)
    if (
        not isinstance(allowed_servers, dict)
        or not isinstance(server_id, str)
        or not server_id
        or server_id not in allowed_servers
    ):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_SERVER_UNAPPROVED",
            server_id=safe_server_id,
            tool_name=safe_tool_name,
        )

    expected_sha = allowed_servers.get(server_id)
    if (
        not isinstance(expected_sha, str)
        or not expected_sha
        or not isinstance(schema_sha256, str)
        or not schema_sha256
        or not hmac.compare_digest(schema_sha256.lower(), expected_sha.lower())
    ):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_SCHEMA_DRIFT",
            server_id=server_id,
            tool_name=safe_tool_name,
        )

    allowed_tools = getattr(policy, "allowed_tools", None)
    server_tools = allowed_tools.get(server_id) if isinstance(allowed_tools, dict) else None
    if (
        not isinstance(tool_name, str)
        or not tool_name
        or not isinstance(server_tools, (set, frozenset, list, tuple))
        or tool_name not in server_tools
    ):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_TOOL_BLOCKED",
            server_id=server_id,
            tool_name=safe_tool_name,
        )

    if not isinstance(arguments, dict):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_ARG_VIOLATION",
            server_id=server_id,
            tool_name=tool_name,
        )

    raw_patterns = getattr(policy, "blocked_arg_patterns", None) or ()
    pattern_tuple = tuple(p for p in raw_patterns if isinstance(p, str) and p)
    compiled_patterns = _compile_blocked_patterns(pattern_tuple)
    if compiled_patterns and _walk_arguments_violate(arguments, compiled_patterns):
        return McpCallVerdict(
            allowed=False,
            reason_code="ERR_MCP_ARG_VIOLATION",
            server_id=server_id,
            tool_name=tool_name,
        )

    return McpCallVerdict(
        allowed=True,
        reason_code="ALLOWED",
        server_id=server_id,
        tool_name=tool_name,
    )
