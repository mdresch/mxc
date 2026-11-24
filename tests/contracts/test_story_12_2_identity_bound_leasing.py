"""Contract tests for Story 12.2 — Opt-In Identity-Bound VM Leasing & Mandatory TTL Expiry Reclamation (ADR-008).

Spec Gate Episode: spec-12_2-06896982 (Robust Utility Margin: +0.2080)
Contract Interpretations:
  I1 (Defensive None-Safety): Optional fields (assertion, default_pool_target, binding_ttl_seconds)
      are safely accessed with defaults to avoid AttributeError when None.
  I2: Opt-in identity_bound leasing stores (subject_id, pool_target) -> vm_id so returning verified
      callers reattach to the same warm VM within TTL, while other identities are strictly isolated.
  I3: binding_ttl_seconds is clamped to [300, 86400] (default 14400s), resolving ADR-008 §4.5, and
      sweep_expired_bindings() evicts expired mappings and returns vm_ids for ADR-005 sterile discard.
"""

from __future__ import annotations

from scripts.lib.auth_gated_leasing import (
    MAX_BINDING_TTL_SECONDS,
    MIN_BINDING_TTL_SECONDS,
    AuthGatedLeaseController,
    VerifiedAssertion,
)


def _make_controller():
    allocated = []

    def _allocator(pool_target: str) -> str:
        vm_id = f"vm-{pool_target}-{len(allocated) + 1:03d}"
        allocated.append(vm_id)
        return vm_id

    claims_map = {
        ("tenant-cba", "desktop-user"): "pool-win11-desktop",
    }
    return AuthGatedLeaseController(claims_map=claims_map, pool_allocator=_allocator), allocated


# Story 12.2 — AC-12.2.1 (ADR-008)
def test_ac_12_2_1_identity_bound_reattachment_and_cross_identity_isolation():
    ctrl, allocated = _make_controller()

    alice = VerifiedAssertion(
        subject_id="alice@cba.eu",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("desktop-user",),
        issued_at_epoch=1000.0,
        expires_at_epoch=5000.0,
    )
    bob = VerifiedAssertion(
        subject_id="bob@cba.eu",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("desktop-user",),
        issued_at_epoch=1000.0,
        expires_at_epoch=5000.0,
    )

    first_alice = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=alice,
        now_epoch=1000.0,
    )
    assert first_alice["admitted"] is True
    assert first_alice["reattached"] is False
    alice_vm = first_alice["vm_id"]

    # Returning Alice within TTL reattaches to same VM without allocating a new one
    second_alice = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=alice,
        now_epoch=2000.0,
    )
    assert second_alice["admitted"] is True
    assert second_alice["reattached"] is True
    assert second_alice["vm_id"] == alice_vm
    assert len(allocated) == 1

    # Bob must receive a completely separate VM (zero cross-identity collision)
    first_bob = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=bob,
        now_epoch=2000.0,
    )
    assert first_bob["admitted"] is True
    assert first_bob["vm_id"] != alice_vm
    assert len(allocated) == 2


# Story 12.2 — AC-12.2.2 & AC-12.2.3 (ADR-008 §4.5)
def test_ac_12_2_2_and_3_ttl_clamping_and_expired_binding_sterile_reclamation():
    ctrl, allocated = _make_controller()

    alice = VerifiedAssertion(
        subject_id="alice@cba.eu",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("desktop-user",),
        issued_at_epoch=1000.0,
        expires_at_epoch=200000.0,
    )
    bob = VerifiedAssertion(
        subject_id="bob@cba.eu",
        subject_type="human",
        tenant_id="tenant-cba",
        roles=("desktop-user",),
        issued_at_epoch=1000.0,
        expires_at_epoch=200000.0,
    )

    # Request below min TTL (10s) -> clamped to MIN_BINDING_TTL_SECONDS (300s)
    res_low = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=alice,
        binding_ttl_seconds=10,
        now_epoch=1000.0,
    )
    assert res_low["binding_expires_at_epoch"] == 1000.0 + MIN_BINDING_TTL_SECONDS

    # Request above max TTL (999999s) -> clamped to MAX_BINDING_TTL_SECONDS (86400s)
    res_high = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=bob,
        binding_ttl_seconds=999999,
        now_epoch=1000.0,
    )
    assert res_high["binding_expires_at_epoch"] == 1000.0 + MAX_BINDING_TTL_SECONDS

    # Sweep at t=1350 -> Alice's 300s binding expires and is queued for ADR-005 sterile discard; Bob remains active
    reclaimed = ctrl.sweep_expired_bindings(now_epoch=1350.0)
    assert reclaimed == [res_low["vm_id"]]

    # Subsequent Alice login allocates a fresh VM (no stale binding reuse)
    fresh_alice = ctrl.acquire_lease(
        route_mode="auth_gated",
        leasing_strategy="identity_bound",
        assertion=alice,
        now_epoch=1400.0,
    )
    assert fresh_alice["admitted"] is True
    assert fresh_alice["reattached"] is False
    assert fresh_alice["vm_id"] != res_low["vm_id"]
    assert len(allocated) == 3
