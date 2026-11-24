"""Contract tests for Story 12.1 — auth_gated Ingress Gate & Deny-by-Default Claims-to-Pool Resolver (ADR-008).

Spec Gate Episode: spec-12_1-0a227e26 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1: On routes with route_mode="auth_gated", missing or expired VerifiedAssertion rejects
      with ERR_AUTH_REQUIRED / ERR_ASSERTION_EXPIRED and issues 0 pool_lease calls.
  I2: Verified OIDC/SAML human and Microsoft Entra Agent ID assertions resolve (tenant_id, role)
      deterministically via a deny-by-default claims_map; unmapped claims fail closed with ERR_CLAIM_UNMAPPED.
  I3: route_mode="path_only" preserves ADR-002 path-routed leasing unchanged with zero auth requirement.
"""

from __future__ import annotations

from scripts.lib.auth_gated_leasing import (
    AuthGatedLeaseController,
    VerifiedAssertion,
)


def _make_controller():
    leased_calls = []

    def _allocator(pool_target: str) -> str:
        vm_id = f"vm-{pool_target}-{len(leased_calls) + 1:03d}"
        leased_calls.append((pool_target, vm_id))
        return vm_id

    claims_map = {
        ("tenant-cba", "finance-analyst"): "pool-prod-adpa",
        ("tenant-cba", "agent-coder"): "pool-win11-agent-lean",
    }
    ctrl = AuthGatedLeaseController(claims_map=claims_map, pool_allocator=_allocator)
    return ctrl, leased_calls


# Story 12.1 — AC-12.1.1 (ADR-008)
def test_ac_12_1_1_missing_or_expired_assertion_wakes_zero_vms():
    ctrl, leased_calls = _make_controller()

    # Missing assertion
    res_none = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="pool_generic",
        assertion=None,
        now_epoch=1000.0,
    )
    assert res_none["admitted"] is False
    assert res_none["reason_code"] == "ERR_AUTH_REQUIRED"
    assert len(leased_calls) == 0

    # Expired assertion
    expired = VerifiedAssertion(
        subject_id="user-alice",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("finance-analyst",),
        issued_at_epoch=500.0,
        expires_at_epoch=900.0,
    )
    res_exp = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="pool_generic",
        assertion=expired,
        now_epoch=1000.0,
    )
    assert res_exp["admitted"] is False
    assert res_exp["reason_code"] == "ERR_ASSERTION_EXPIRED"
    assert len(leased_calls) == 0


# Story 12.1 — AC-12.1.2 (ADR-008)
def test_ac_12_1_2_claims_to_pool_resolver_is_deny_by_default_and_supports_entra_agent_id():
    ctrl, leased_calls = _make_controller()

    # Valid Entra Agent ID assertion
    agent_assertion = VerifiedAssertion(
        subject_id="entra-agent-007",
        subject_type="entra_agent_id",
        tenant_id="tenant-cba",
        roles=("agent-coder",),
        issued_at_epoch=950.0,
        expires_at_epoch=1500.0,
    )
    res_ok = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="pool_generic",
        assertion=agent_assertion,
        now_epoch=1000.0,
    )
    assert res_ok["admitted"] is True
    assert res_ok["pool_target"] == "pool-win11-agent-lean"
    assert res_ok["vm_id"] == "vm-pool-win11-agent-lean-001"
    assert len(leased_calls) == 1

    # Unmapped / over-broad claim -> fail closed, 0 VMs woken
    unmapped = VerifiedAssertion(
        subject_id="user-mallory",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("guest-unmapped",),
        issued_at_epoch=950.0,
        expires_at_epoch=1500.0,
    )
    res_deny = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="pool_generic",
        assertion=unmapped,
        now_epoch=1000.0,
    )
    assert res_deny["admitted"] is False
    assert res_deny["reason_code"] == "ERR_CLAIM_UNMAPPED"
    assert len(leased_calls) == 1


# Story 12.1 — AC-12.1.3 (ADR-008)
def test_ac_12_1_3_path_only_default_mode_remains_unchanged():
    ctrl, leased_calls = _make_controller()

    res_path = ctrl.acquire_lease(
        route_mode="path_only",
        leasing_strategy="pool_generic",
        assertion=None,
        default_pool_target="pool-prod-adpa",
        now_epoch=1000.0,
    )
    assert res_path["admitted"] is True
    assert res_path["pool_target"] == "pool-prod-adpa"
    assert res_path["vm_id"] == "vm-pool-prod-adpa-001"
    assert len(leased_calls) == 1
