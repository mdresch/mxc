"""MXC Authentication-Gated Session Provisioning & Identity-Bound VM Leasing (ADR-008 / Epic 012).

Implements:
  - Story 12.1: auth_gated ingress gate (zero unauthenticated wake) + deny-by-default claims-to-pool
                resolver supporting human OIDC/SAML and Microsoft Entra Agent ID assertions, while
                keeping ADR-002 path_only routing unchanged as the default.
  - Story 12.2: Opt-in identity_bound VM leasing with mandatory TTL clamping [300s, 86400s] (resolving
                ADR-008 §4.5) and sweep_expired_bindings() for mandatory ADR-005 sterile reclamation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

MIN_BINDING_TTL_SECONDS = 300
DEFAULT_BINDING_TTL_SECONDS = 14400
MAX_BINDING_TTL_SECONDS = 86400


@dataclass(frozen=True)
class VerifiedAssertion:
    subject_id: str
    subject_type: str  # "human" | "entra_agent_id"
    tenant_id: str
    roles: tuple[str, ...]
    issued_at_epoch: float
    expires_at_epoch: float


@dataclass(frozen=True)
class IdentityBinding:
    identity_key: tuple[str, str]  # (subject_id, pool_target)
    vm_id: str
    created_at_epoch: float
    expires_at_epoch: float


def clamp_binding_ttl(ttl_seconds: int | None) -> int:
    """Clamp binding TTL to [300, 86400] seconds (default 14400s), safely handling None."""
    if ttl_seconds is None:
        return DEFAULT_BINDING_TTL_SECONDS
    return max(MIN_BINDING_TTL_SECONDS, min(MAX_BINDING_TTL_SECONDS, int(ttl_seconds)))


class AuthGatedLeaseController:
    """Controls auth_gated ingress admission, claims-to-pool resolution, and TTL-bounded VM bindings."""

    def __init__(
        self,
        *,
        claims_map: dict[tuple[str, str], str],
        pool_allocator: Callable[[str], str],
    ) -> None:
        self._claims_map = dict(claims_map)
        self._pool_allocator = pool_allocator
        self._bindings: dict[tuple[str, str], IdentityBinding] = {}

    def resolve_pool_target(
        self,
        assertion: VerifiedAssertion | None,
        claims_map: dict[tuple[str, str], str] | None = None,
    ) -> str | None:
        """Deny-by-default claims-to-pool resolver; returns None if assertion or claims are unmapped."""
        if assertion is None:
            return None
        active_map = claims_map if claims_map is not None else self._claims_map
        roles = getattr(assertion, "roles", ()) or ()
        tenant_id = getattr(assertion, "tenant_id", "") or ""
        for role in roles:
            target = active_map.get((tenant_id, role))
            if target:
                return target
        return None

    def acquire_lease(
        self,
        *,
        route_mode: str = "path_only",
        leasing_strategy: str = "pool_generic",
        assertion: VerifiedAssertion | None = None,
        default_pool_target: str | None = None,
        binding_ttl_seconds: int | None = DEFAULT_BINDING_TTL_SECONDS,
        now_epoch: float | None = None,
    ) -> dict[str, object]:
        now = time.time() if now_epoch is None else float(now_epoch)

        # ADR-002 default: path_only bypasses authentication and stays pool-generic
        if route_mode == "path_only":
            pool_target = default_pool_target or "default-pool"
            vm_id = self._pool_allocator(pool_target)
            return {
                "admitted": True,
                "reason_code": "ADMITTED",
                "pool_target": pool_target,
                "vm_id": vm_id,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        if route_mode != "auth_gated":
            return {
                "admitted": False,
                "reason_code": "ERR_INVALID_ROUTE_MODE",
                "pool_target": None,
                "vm_id": None,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        # ADR-008: auth_gated requires a valid, non-expired assertion before waking any VM
        if assertion is None:
            return {
                "admitted": False,
                "reason_code": "ERR_AUTH_REQUIRED",
                "pool_target": None,
                "vm_id": None,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        if now > assertion.expires_at_epoch:
            return {
                "admitted": False,
                "reason_code": "ERR_ASSERTION_EXPIRED",
                "pool_target": None,
                "vm_id": None,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        pool_target = self.resolve_pool_target(assertion)
        if pool_target is None:
            return {
                "admitted": False,
                "reason_code": "ERR_CLAIM_UNMAPPED",
                "pool_target": None,
                "vm_id": None,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        if leasing_strategy == "pool_generic":
            vm_id = self._pool_allocator(pool_target)
            return {
                "admitted": True,
                "reason_code": "ADMITTED",
                "pool_target": pool_target,
                "vm_id": vm_id,
                "reattached": False,
                "binding_expires_at_epoch": None,
            }

        if leasing_strategy == "identity_bound":
            key = (assertion.subject_id, pool_target)
            existing = self._bindings.get(key)
            if existing is not None and now <= existing.expires_at_epoch:
                return {
                    "admitted": True,
                    "reason_code": "ADMITTED",
                    "pool_target": pool_target,
                    "vm_id": existing.vm_id,
                    "reattached": True,
                    "binding_expires_at_epoch": existing.expires_at_epoch,
                }

            clamped_ttl = clamp_binding_ttl(binding_ttl_seconds)
            vm_id = self._pool_allocator(pool_target)
            binding = IdentityBinding(
                identity_key=key,
                vm_id=vm_id,
                created_at_epoch=now,
                expires_at_epoch=now + clamped_ttl,
            )
            self._bindings[key] = binding
            return {
                "admitted": True,
                "reason_code": "ADMITTED",
                "pool_target": pool_target,
                "vm_id": vm_id,
                "reattached": False,
                "binding_expires_at_epoch": binding.expires_at_epoch,
            }

        return {
            "admitted": False,
            "reason_code": "ERR_INVALID_STRATEGY",
            "pool_target": None,
            "vm_id": None,
            "reattached": False,
            "binding_expires_at_epoch": None,
        }

    def sweep_expired_bindings(self, now_epoch: float | None = None) -> list[str]:
        """Evict expired identity bindings and return vm_ids queued for ADR-005 sterile discard."""
        now = time.time() if now_epoch is None else float(now_epoch)
        expired_keys = [
            key for key, binding in self._bindings.items() if now > binding.expires_at_epoch
        ]
        reclaimed_vm_ids: list[str] = []
        for key in expired_keys:
            reclaimed_vm_ids.append(self._bindings.pop(key).vm_id)
        return reclaimed_vm_ids
