"""Contract tests for Story 13.1 — Host-Side Zero-Secret Git Bundle Sync (mxc-sync) & Credential Sidecar Proxy (ADR-014).

Spec Gate Episode: spec-13_1-a1cf178e (Robust Utility Margin: +0.2184)
Contract Interpretations:
  I1 (Zero Static Secrets & Airgap Sync): plan_zero_secret_git_sync() scans remote_url and
      guest_env keys/values for embedded credentials (PATs, private keys, authenticated URLs,
      sensitive env tokens) and fails closed with ERR_STATIC_SECRET_DETECTED; clean bundles
      execute 100% offline with nic_count == 0 and secrets_present == False.
  I2 (Host-Side Credential Sidecar & Redaction): CredentialSidecarProxy substitutes declared
      placeholders only for allowlisted (target_host, secret_scope) pairs within <= 5 ms,
      strictly redacting real secret values ([REDACTED]) from audit_log and failing closed
      with ERR_SECRET_SCOPE_DENIED for unapproved/mismatched scopes or missing placeholders.
  I3 (Defensive None & Empty Safety): Passing None, empty strings, invalid 64-char SHA-256
      digests, or empty/None vault and header maps fails closed cleanly without AttributeError.
"""

from __future__ import annotations

import json
import socket
import time

import pytest

from scripts.lib.zero_secret_mcp_gateway import (
    CredentialSidecarProxy,
    GitBundleSyncPlan,
    plan_zero_secret_git_sync,
)

VALID_SHA256 = "A1B2C3D4" * 8
REAL_GITHUB_SECRET = "ghp_HostOnlyRealSecretTokenValue987654"
PLACEHOLDER_GH = "__MXC_SECRET_GITHUB__"


# Story 13.1 — AC-13.1.1 (ADR-014)
def test_ac_13_1_1_clean_bundle_sync_succeeds_offline_with_zero_nics_and_zero_secrets(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Network calls are strictly forbidden during airgapped mxc-sync")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    ok, reason, plan = plan_zero_secret_git_sync(
        repo_slug="contoso/mxc-agent-repo",
        remote_url="https://github.com/contoso/mxc-agent-repo.git",
        bundle_sha256=VALID_SHA256,
        guest_target_dir="/workspace/repo",
        guest_env={"PATH": "/usr/local/bin:/usr/bin", "GIT_TERMINAL_PROMPT": "0"},
    )
    assert ok is True
    assert reason == "OK"
    assert isinstance(plan, GitBundleSyncPlan)
    assert plan.repo_slug == "contoso/mxc-agent-repo"
    assert plan.bundle_sha256 == VALID_SHA256.lower()
    assert plan.guest_target_dir == "/workspace/repo"
    assert plan.nic_count == 0
    assert plan.secrets_present is False

    # Pure offline bundle with remote_url=None also succeeds cleanly
    ok_no_url, reason_no_url, plan_no_url = plan_zero_secret_git_sync(
        repo_slug="contoso/mxc-agent-repo",
        remote_url=None,
        bundle_sha256=VALID_SHA256.lower(),
        guest_target_dir="/workspace/repo",
        guest_env=None,
    )
    assert ok_no_url is True
    assert reason_no_url == "OK"
    assert plan_no_url is not None
    assert plan_no_url.nic_count == 0
    assert plan_no_url.secrets_present is False


# Story 13.1 — AC-13.1.1 (ADR-014)
@pytest.mark.parametrize(
    ("remote_url", "guest_env"),
    [
        ("https://x-access-token:ghp_test123456@github.com/org/repo.git", {}),
        ("https://deploy-user:s3cr3t@git.internal.local/org/repo.git", None),
        ("https://github.com/org/repo.git", {"GIT_AUTH": "ghp_LeakedToken123456"}),
        ("https://github.com/org/repo.git", {"CI_CREDS": "github_pat_11ABCDEF_secret"}),
        ("https://github.com/org/repo.git", {"GITLAB_CREDS": "glpat-SecretToken123"}),
        ("https://github.com/org/repo.git", {"CLOUD_ID": "AKIAIOSFODNN7EXAMPLE"}),
        (
            "https://github.com/org/repo.git",
            {"DEPLOY_KEY": "-----BEGIN OPENSSH PRIVATE KEY-----\nAAAA"},
        ),
        ("https://github.com/org/repo.git", {"GITHUB_PAT": "secret-pat"}),
        ("https://github.com/org/repo.git", {"GITHUB_TOKEN": "secret-tok"}),
        ("https://github.com/org/repo.git", {"API_SECRET": "secret-val"}),
        ("https://github.com/org/repo.git", {"SSH_AUTH_SOCK": "/tmp/ssh-agent.sock"}),
    ],
)
def test_ac_13_1_1_static_secrets_in_remote_url_or_guest_env_fail_closed(remote_url, guest_env):
    ok, reason, plan = plan_zero_secret_git_sync(
        repo_slug="contoso/mxc-agent-repo",
        remote_url=remote_url,
        bundle_sha256=VALID_SHA256,
        guest_target_dir="/workspace/repo",
        guest_env=guest_env,
    )
    assert ok is False
    assert reason == "ERR_STATIC_SECRET_DETECTED"
    assert plan is None


# Story 13.1 — AC-13.1.2 (ADR-014)
def test_ac_13_1_2_sidecar_proxy_injects_allowlisted_scope_within_5ms_and_redacts_audit_log(
    monkeypatch,
):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Sidecar policy resolution must stay offline in contract test")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    proxy = CredentialSidecarProxy(
        vault_secrets={
            ("api.github.com", "repo:read"): (PLACEHOLDER_GH, REAL_GITHUB_SECRET),
        }
    )
    guest_headers = {
        "Authorization": f"Bearer {PLACEHOLDER_GH}",
        "Accept": "application/vnd.github+json",
    }

    t0 = time.perf_counter()
    result = proxy.inject_credentials(
        target_host="api.github.com",
        secret_scope="repo:read",
        headers=guest_headers,
    )
    wall_ms = (time.perf_counter() - t0) * 1000.0

    assert result["allowed"] is True
    assert result["reason_code"] == "OK"
    assert result["outbound_headers"] == {
        "Authorization": f"Bearer {REAL_GITHUB_SECRET}",
        "Accept": "application/vnd.github+json",
    }
    # Caller's original headers dictionary must remain untouched
    assert guest_headers["Authorization"] == f"Bearer {PLACEHOLDER_GH}"

    audit_serialized = json.dumps(result["audit_log"])
    assert REAL_GITHUB_SECRET not in audit_serialized
    assert "[REDACTED]" in audit_serialized
    assert result["elapsed_ms"] <= 5.0
    assert wall_ms <= 5.0


# Story 13.1 — AC-13.1.2 (ADR-014)
def test_ac_13_1_2_sidecar_proxy_denies_unknown_scope_or_missing_placeholder_and_redacts():
    proxy = CredentialSidecarProxy(
        vault_secrets={
            ("api.github.com", "repo:read"): (PLACEHOLDER_GH, REAL_GITHUB_SECRET),
        }
    )

    # Disallowed target host
    bad_host = proxy.inject_credentials(
        target_host="evil.exfil.example",
        secret_scope="repo:read",
        headers={"Authorization": f"Bearer {PLACEHOLDER_GH}"},
    )
    assert bad_host["allowed"] is False
    assert bad_host["reason_code"] == "ERR_SECRET_SCOPE_DENIED"
    assert bad_host["outbound_headers"] == {}
    assert bad_host["elapsed_ms"] <= 5.0

    # Disallowed scope on known host
    bad_scope = proxy.inject_credentials(
        target_host="api.github.com",
        secret_scope="admin:org",
        headers={"Authorization": f"Bearer {PLACEHOLDER_GH}"},
    )
    assert bad_scope["allowed"] is False
    assert bad_scope["reason_code"] == "ERR_SECRET_SCOPE_DENIED"
    assert bad_scope["outbound_headers"] == {}

    # Known host/scope but placeholder absent or mismatched
    missing_placeholder = proxy.inject_credentials(
        target_host="api.github.com",
        secret_scope="repo:read",
        headers={"Authorization": "Bearer __WRONG_PLACEHOLDER__"},
    )
    assert missing_placeholder["allowed"] is False
    assert missing_placeholder["reason_code"] == "ERR_SECRET_SCOPE_DENIED"
    assert missing_placeholder["outbound_headers"] == {}

    # Even if an adversarial caller echoes the real secret in headers, audit_log must redact it
    leaked_probe = proxy.inject_credentials(
        target_host="evil.exfil.example",
        secret_scope="repo:read",
        headers={"Authorization": f"Bearer {REAL_GITHUB_SECRET}"},
    )
    assert leaked_probe["allowed"] is False
    assert REAL_GITHUB_SECRET not in json.dumps(leaked_probe["audit_log"])


# Story 13.1 — AC-13.1.3 (ADR-014)
def test_ac_13_1_3_none_empty_and_invalid_inputs_fail_closed_without_attribute_error():
    # Invalid / None sync inputs
    for slug, sha, target_dir in [
        (None, VALID_SHA256, "/workspace/repo"),
        ("", VALID_SHA256, "/workspace/repo"),
        ("contoso/repo", None, "/workspace/repo"),
        ("contoso/repo", "", "/workspace/repo"),
        ("contoso/repo", "short-sha", "/workspace/repo"),
        ("contoso/repo", "z" * 64, "/workspace/repo"),
        ("contoso/repo", VALID_SHA256, None),
        ("contoso/repo", VALID_SHA256, ""),
    ]:
        ok, reason, plan = plan_zero_secret_git_sync(
            repo_slug=slug,
            remote_url="https://github.com/contoso/repo.git",
            bundle_sha256=sha,
            guest_target_dir=target_dir,
            guest_env={},
        )
        assert ok is False
        assert reason == "ERR_INVALID_SYNC_INPUT"
        assert plan is None

    # Empty / None sidecar vaults and inputs
    for vault in (None, {}):
        proxy = CredentialSidecarProxy(vault_secrets=vault)
        for host, scope, hdrs in [
            (None, None, None),
            ("", "", {}),
            ("api.github.com", "repo:read", None),
            ("api.github.com", "repo:read", {}),
            ("api.github.com", None, {"Authorization": f"Bearer {PLACEHOLDER_GH}"}),
        ]:
            res = proxy.inject_credentials(target_host=host, secret_scope=scope, headers=hdrs)
            assert res["allowed"] is False
            assert res["reason_code"] == "ERR_SECRET_SCOPE_DENIED"
            assert res["outbound_headers"] == {}
            assert res["elapsed_ms"] <= 5.0
