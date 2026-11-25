"""Contract tests for Story 16.2 — Turnkey Zero-Cloud "MXC Embed" Sovereign Appliance & Gated 5-Act HIL Suite (ADR-017).

Spec Gate Episode: spec-16_2-6327b6f2 (Robust Utility Margin: +0.2160)
Contract Interpretations:
  I1: run_mxc_embed_preflight() executes 100% offline with zero network egress (LL-011), returning
      (True, "OK") iff outbound_internet_required is False, hyperv_enabled and base_image_present are
      True, and install_minutes_estimate is a finite non-boolean number in (0.0, 15.0].
  I2: Fail-closed preflight precedence checks outbound_internet_required (ERR_NETWORK_EGRESS_ATTEMPTED)
      before host prerequisites (ERR_PREFLIGHT_PREREQ_MISSING) and install budget (ERR_INSTALL_BUDGET_EXCEEDED).
  I3: evaluate_five_act_hil_gate() verifies immutable parent SHA-256 invariance via constant-time
      hmac.compare_digest (ERR_PARENT_HASH_DRIFT on None/empty/mismatch) before verifying that
      act_results is a list of exactly 5 dict entries each with passed=True (ERR_HIL_ACT_FAILED).
"""

from __future__ import annotations

import socket

import pytest

from scripts.lib.mxc_embed_appliance import (
    evaluate_five_act_hil_gate,
    run_mxc_embed_preflight,
)

PARENT_SHA = "0123456789abcdef" * 4


def _passing_five_acts() -> list[dict]:
    return [
        {"act": 1, "name": "airgapped_9s_boot", "passed": True},
        {"act": 2, "name": "vmbus_copy_file", "passed": True},
        {"act": 3, "name": "polyglot_toolchain_exec", "passed": True},
        {"act": 4, "name": "rogue_mutation_and_rollback", "passed": True},
        {"act": 5, "name": "parent_sha256_invariance", "passed": True},
    ]


# Story 16.2 — AC-16.2.1 (ADR-017)
def test_ac_16_2_1_mxc_embed_preflight_admits_offline_host_with_zero_network_calls(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise RuntimeError("Network egress is strictly prohibited during MXC Embed install")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    ok_fast, code_fast = run_mxc_embed_preflight(
        hyperv_enabled=True,
        base_image_present=True,
        outbound_internet_required=False,
        install_minutes_estimate=9.5,
    )
    assert (ok_fast, code_fast) == (True, "OK")

    # Exact 15.0-minute ceiling is admitted
    ok_boundary, code_boundary = run_mxc_embed_preflight(
        hyperv_enabled=True,
        base_image_present=True,
        outbound_internet_required=False,
        install_minutes_estimate=15.0,
    )
    assert (ok_boundary, code_boundary) == (True, "OK")

    # 5-Act HIL gate also operates 100% offline with zero outbound network calls
    hil_ok, hil_code = evaluate_five_act_hil_gate(
        act_results=_passing_five_acts(),
        parent_sha_before=PARENT_SHA,
        parent_sha_after=PARENT_SHA,
    )
    assert (hil_ok, hil_code) == (True, "OK")


# Story 16.2 — AC-16.2.1 (ADR-017)
@pytest.mark.parametrize(
    ("hyperv_enabled", "base_image_present", "outbound_internet_required", "install_minutes_estimate", "expected_code"),
    [
        # Precedence 1: Network egress rejected first even if prerequisites/budget also invalid
        (False, False, True, 99.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (True, True, True, 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (True, True, None, 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        (True, True, "no", 10.0, "ERR_NETWORK_EGRESS_ATTEMPTED"),
        # Precedence 2: Missing Hyper-V or base image rejected before duration check
        (False, True, False, 99.0, "ERR_PREFLIGHT_PREREQ_MISSING"),
        (True, False, False, 10.0, "ERR_PREFLIGHT_PREREQ_MISSING"),
        (None, True, False, 10.0, "ERR_PREFLIGHT_PREREQ_MISSING"),
        (True, None, False, 10.0, "ERR_PREFLIGHT_PREREQ_MISSING"),
        # Precedence 3: Install budget validation (non-positive, >15.0, non-finite, bool, None)
        (True, True, False, 15.01, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, 0.0, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, -5.0, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, float("nan"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, float("inf"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, float("-inf"), "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, None, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, True, "ERR_INSTALL_BUDGET_EXCEEDED"),
        (True, True, False, "10.0", "ERR_INSTALL_BUDGET_EXCEEDED"),
    ],
)
def test_ac_16_2_1_mxc_embed_preflight_fails_closed_with_deterministic_precedence(
    hyperv_enabled,
    base_image_present,
    outbound_internet_required,
    install_minutes_estimate,
    expected_code,
):
    ok, code = run_mxc_embed_preflight(
        hyperv_enabled=hyperv_enabled,
        base_image_present=base_image_present,
        outbound_internet_required=outbound_internet_required,
        install_minutes_estimate=install_minutes_estimate,
    )
    assert ok is False
    assert code == expected_code


# Story 16.2 — AC-16.2.2 (ADR-017)
def test_ac_16_2_2_five_act_hil_gate_passes_and_rejects_drift_or_act_failures():
    # Case-insensitive hex match passes
    ok_case, code_case = evaluate_five_act_hil_gate(
        act_results=_passing_five_acts(),
        parent_sha_before=PARENT_SHA.upper(),
        parent_sha_after=PARENT_SHA.lower(),
    )
    assert (ok_case, code_case) == (True, "OK")

    # Parent SHA drift takes precedence even when act_results is empty
    flipped = ("f" if PARENT_SHA[0] != "f" else "0") + PARENT_SHA[1:]
    drift_ok, drift_code = evaluate_five_act_hil_gate(
        act_results=[],
        parent_sha_before=PARENT_SHA,
        parent_sha_after=flipped,
    )
    assert (drift_ok, drift_code) == (False, "ERR_PARENT_HASH_DRIFT")

    # None or empty parent SHA fails closed with ERR_PARENT_HASH_DRIFT
    for bad_before, bad_after in [
        (None, PARENT_SHA),
        (PARENT_SHA, None),
        ("", PARENT_SHA),
        (PARENT_SHA, "   "),
        (12345, PARENT_SHA),
    ]:
        ok_bad_sha, code_bad_sha = evaluate_five_act_hil_gate(
            act_results=_passing_five_acts(),
            parent_sha_before=bad_before,  # type: ignore[arg-type]
            parent_sha_after=bad_after,  # type: ignore[arg-type]
        )
        assert (ok_bad_sha, code_bad_sha) == (False, "ERR_PARENT_HASH_DRIFT")

    # Empty, short, extra, None, non-list, or failed Act results fail closed with ERR_HIL_ACT_FAILED
    acts_act4_failed = _passing_five_acts()
    acts_act4_failed[3] = {"act": 4, "name": "rogue_mutation_and_rollback", "passed": False}

    acts_non_bool_passed = _passing_five_acts()
    acts_non_bool_passed[2] = {"act": 3, "name": "polyglot_toolchain_exec", "passed": 1}

    acts_non_dict = _passing_five_acts()
    acts_non_dict[1] = None  # type: ignore[call-overload]

    for bad_acts in [
        None,
        [],
        _passing_five_acts()[:4],
        _passing_five_acts() + [{"act": 6, "passed": True}],
        tuple(_passing_five_acts()),
        acts_act4_failed,
        acts_non_bool_passed,
        acts_non_dict,
    ]:
        ok_bad_acts, code_bad_acts = evaluate_five_act_hil_gate(
            act_results=bad_acts,  # type: ignore[arg-type]
            parent_sha_before=PARENT_SHA,
            parent_sha_after=PARENT_SHA,
        )
        assert (ok_bad_acts, code_bad_acts) == (False, "ERR_HIL_ACT_FAILED")
