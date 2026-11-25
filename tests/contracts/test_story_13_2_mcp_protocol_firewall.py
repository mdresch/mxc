"""Contract tests for Story 13.2 — Protocol-Aware MCP JSON-RPC Firewall over VMBus (ADR-014).

Spec Gate Episode: spec-13_2-0807f165 (Robust Utility Margin: +0.2184)
Contract Interpretations:
  I1 (Allowlisted MCP Execution & Latency): evaluate_mcp_call() admits allowlisted
      (server_id, schema_sha256, tool_name) calls with clean arguments returning
      McpCallVerdict(allowed=True, reason_code="ALLOWED", ...) within <= 2 ms and
      100% offline with zero network calls.
  I2 (Deterministic Fail-Closed Precedence): Unapproved or missing server_id fails with
      ERR_MCP_SERVER_UNAPPROVED; missing or drifted schema_sha256 (checked via
      hmac.compare_digest) fails with ERR_MCP_SCHEMA_DRIFT; unlisted tool_name fails with
      ERR_MCP_TOOL_BLOCKED; recursive key/value matches against blocked_arg_patterns or
      non-dict/None arguments fail with ERR_MCP_ARG_VIOLATION.
  I3 (Defensive None & Malformed Envelope Safety): None policy, None/empty request dicts,
      malformed JSON-RPC payloads, or None/non-dict arguments fail closed cleanly without
      AttributeError or TypeError.
"""

from __future__ import annotations

import socket
import time

import pytest

from scripts.lib.zero_secret_mcp_gateway import (
    McpCallVerdict,
    McpFirewallPolicy,
    evaluate_mcp_call,
)

GITHUB_SCHEMA_SHA = "deadbeef" * 8
DOCS_SCHEMA_SHA = "cafebabe" * 8


def _sample_policy() -> McpFirewallPolicy:
    return McpFirewallPolicy(
        allowed_servers={
            "github-mcp": GITHUB_SCHEMA_SHA,
            "docs-mcp": DOCS_SCHEMA_SHA,
        },
        allowed_tools={
            "github-mcp": {"get_issue", "list_commits"},
            "docs-mcp": {"search_docs"},
        },
        blocked_arg_patterns=(
            r"\.\.[\\/]",
            r"file://",
            r"169\.254\.169\.254",
            r"ghp_",
        ),
    )


# Story 13.2 — AC-13.2.1 (ADR-014)
def test_ac_13_2_1_allowlisted_mcp_call_passes_offline_within_2ms(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("MCP firewall inspection must remain 100% offline over VMBus")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    policy = _sample_policy()
    request = {
        "server_id": "github-mcp",
        "schema_sha256": GITHUB_SCHEMA_SHA.upper(),
        "tool_name": "get_issue",
        "arguments": {
            "owner": "contoso",
            "repo": "mxc",
            "issue_number": 42,
            "filters": ["open", "tp-12"],
        },
    }

    t0 = time.perf_counter()
    verdict = evaluate_mcp_call(policy, request)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert verdict == McpCallVerdict(
        allowed=True,
        reason_code="ALLOWED",
        server_id="github-mcp",
        tool_name="get_issue",
    )
    assert elapsed_ms <= 2.0

    # Also validate JSON-RPC 2.0 params envelope with empty arguments dict
    jsonrpc_req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "server_id": "docs-mcp",
            "schema_sha256": DOCS_SCHEMA_SHA,
            "name": "search_docs",
            "arguments": {},
        },
    }
    verdict_rpc = evaluate_mcp_call(policy, jsonrpc_req)
    assert verdict_rpc == McpCallVerdict(
        allowed=True,
        reason_code="ALLOWED",
        server_id="docs-mcp",
        tool_name="search_docs",
    )


# Story 13.2 — AC-13.2.2 (ADR-014)
def test_ac_13_2_2_blocks_unapproved_server_schema_drift_tool_and_recursive_args():
    policy = _sample_policy()

    # 1. Unlisted server_id
    v_server = evaluate_mcp_call(
        policy,
        {
            "server_id": "rogue-mcp",
            "schema_sha256": GITHUB_SCHEMA_SHA,
            "tool_name": "get_issue",
            "arguments": {"owner": "contoso"},
        },
    )
    assert v_server.allowed is False
    assert v_server.reason_code == "ERR_MCP_SERVER_UNAPPROVED"

    # 2. Rug-pull schema drift
    v_drift = evaluate_mcp_call(
        policy,
        {
            "server_id": "github-mcp",
            "schema_sha256": "0" * 64,
            "tool_name": "get_issue",
            "arguments": {"owner": "contoso"},
        },
    )
    assert v_drift.allowed is False
    assert v_drift.reason_code == "ERR_MCP_SCHEMA_DRIFT"

    # 3. Disallowed tool_name on approved server
    v_tool = evaluate_mcp_call(
        policy,
        {
            "server_id": "github-mcp",
            "schema_sha256": GITHUB_SCHEMA_SHA,
            "tool_name": "delete_repository",
            "arguments": {"owner": "contoso"},
        },
    )
    assert v_tool.allowed is False
    assert v_tool.reason_code == "ERR_MCP_TOOL_BLOCKED"

    # 4. Blocked argument patterns (nested dict value, list item, and malicious dict key)
    bad_arg_payloads = [
        {"path": "../../etc/passwd"},
        {"nested": {"uri": "file:///C:/Windows/System32/config/SAM"}},
        {"targets": ["https://safe.example", "http://169.254.169.254/latest/meta-data"]},
        {"../escape_key": "harmless_value"},
        {"meta": {"auth": "Bearer ghp_exfiltratedToken"}},
    ]
    for args in bad_arg_payloads:
        v_arg = evaluate_mcp_call(
            policy,
            {
                "server_id": "github-mcp",
                "schema_sha256": GITHUB_SCHEMA_SHA,
                "tool_name": "get_issue",
                "arguments": args,
            },
        )
        assert v_arg.allowed is False
        assert v_arg.reason_code == "ERR_MCP_ARG_VIOLATION"


# Story 13.2 — AC-13.2.2 (ADR-014)
def test_ac_13_2_2_deterministic_precedence_order():
    policy = _sample_policy()

    # Unapproved server wins over schema drift, blocked tool, and bad args
    v1 = evaluate_mcp_call(
        policy,
        {
            "server_id": "unknown-mcp",
            "schema_sha256": "0" * 64,
            "tool_name": "drop_db",
            "arguments": {"path": "../../etc/passwd"},
        },
    )
    assert v1.reason_code == "ERR_MCP_SERVER_UNAPPROVED"

    # Schema drift wins over blocked tool and bad args
    v2 = evaluate_mcp_call(
        policy,
        {
            "server_id": "github-mcp",
            "schema_sha256": "0" * 64,
            "tool_name": "drop_db",
            "arguments": {"path": "../../etc/passwd"},
        },
    )
    assert v2.reason_code == "ERR_MCP_SCHEMA_DRIFT"

    # Blocked tool wins over bad args
    v3 = evaluate_mcp_call(
        policy,
        {
            "server_id": "github-mcp",
            "schema_sha256": GITHUB_SCHEMA_SHA,
            "tool_name": "drop_db",
            "arguments": {"path": "../../etc/passwd"},
        },
    )
    assert v3.reason_code == "ERR_MCP_TOOL_BLOCKED"


# Story 13.2 — AC-13.2.3 (ADR-014)
@pytest.mark.parametrize(
    ("use_none_policy", "request_payload", "expected_reason"),
    [
        (True, None, "ERR_MCP_SERVER_UNAPPROVED"),
        (
            True,
            {
                "server_id": "github-mcp",
                "schema_sha256": GITHUB_SCHEMA_SHA,
                "tool_name": "get_issue",
                "arguments": {},
            },
            "ERR_MCP_SERVER_UNAPPROVED",
        ),
        (False, None, "ERR_MCP_SERVER_UNAPPROVED"),
        (False, {}, "ERR_MCP_SERVER_UNAPPROVED"),
        (False, "malformed-envelope", "ERR_MCP_SERVER_UNAPPROVED"),  # type: ignore[arg-type]
        (
            False,
            {
                "server_id": "github-mcp",
                "schema_sha256": None,
                "tool_name": "get_issue",
                "arguments": {},
            },
            "ERR_MCP_SCHEMA_DRIFT",
        ),
        (
            False,
            {
                "server_id": "github-mcp",
                "schema_sha256": GITHUB_SCHEMA_SHA,
                "tool_name": None,
                "arguments": {},
            },
            "ERR_MCP_TOOL_BLOCKED",
        ),
        (
            False,
            {
                "server_id": "github-mcp",
                "schema_sha256": GITHUB_SCHEMA_SHA,
                "tool_name": "get_issue",
                "arguments": None,
            },
            "ERR_MCP_ARG_VIOLATION",
        ),
        (
            False,
            {
                "server_id": "github-mcp",
                "schema_sha256": GITHUB_SCHEMA_SHA,
                "tool_name": "get_issue",
                "arguments": ["non-dict-arguments"],
            },
            "ERR_MCP_ARG_VIOLATION",
        ),
    ],
)
def test_ac_13_2_3_malformed_empty_and_none_inputs_fail_closed_safely(
    use_none_policy, request_payload, expected_reason
):
    policy = None if use_none_policy else _sample_policy()
    verdict = evaluate_mcp_call(policy, request_payload)
    assert isinstance(verdict, McpCallVerdict)
    assert verdict.allowed is False
    assert verdict.reason_code == expected_reason
    assert isinstance(verdict.server_id, str)
    assert isinstance(verdict.tool_name, str)
