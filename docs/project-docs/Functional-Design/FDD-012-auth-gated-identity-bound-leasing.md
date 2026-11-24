---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-008-authentication-gated-session-provisioning.md"
  - "docs/project-docs/Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md"
process: "Specify the auth_gated ingress state machine, claims-to-pool-target resolver, identity-bound lease table, and mandatory binding expiry sweeper"
outputs:
  - "docs/project-docs/Functional-Design/FDD-012-auth-gated-identity-bound-leasing.md"
status: "Proposed"
---

# FDD-012: Authentication-Gated Session Provisioning & Identity-Bound VM Leasing

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-008](../../07-architecture/ADR-008-authentication-gated-session-provisioning.md), [BRD-012](../Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md)  
> **Outputs:** FDD-012-auth-gated-identity-bound-leasing.md

**Source ADR:** [ADR-008](../../07-architecture/ADR-008-authentication-gated-session-provisioning.md)  
**Source BRD:** [BRD-012](../Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Proposed *(Resolves the mandatory binding-expiry follow-up named in `ADR-008 §4.5`)*

---

## 1. Technical Architecture & Interfaces

### 1.1 `auth_gated` Ingress & Identity-Bound Lease Flow
```
[Client / Agent] ──TLS──▶ [MXC Ingress Gateway (leasing_mode="auth_gated")]
                                │ (Connection buffered; 0 VMs woken yet)
                                ▼
                     [Enterprise IdP: OIDC / SAML / Entra Agent ID]
                                │
                  ┌─────────────┴──────────────┐
           (Auth Failed)                (Verified Assertion)
                  │                            │
                  ▼                            ▼
        [HTTP 401 / 403]          [Claims-to-Pool Resolver]
        (0 VMs Woken)             (Deny-by-default map: role/tenant/agent_id)
                                               │
                                  ┌────────────┴────────────┐
                         (pool_generic)              (identity_bound)
                                  │                         │
                                  ▼                         ▼
                       [Standard ADR-002/005]    [IdentityBindingStore]
                       [Lease + Sterile Reset]   (identity, pool_target) -> vm_id
                                                 + binding_ttl_seconds (default 4h)
                                                            │
                                                            ▼
                                                 [Resume-VM <= 300ms + /health]
```

### 1.2 Core Interfaces (`scripts/lib/auth_gated_leasing.py`)
```python
@dataclass(frozen=True)
class VerifiedAssertion:
    subject_id: str             # OIDC sub, SAML NameID, or Entra Agent ID
    subject_type: str           # "human" | "entra_agent_id"
    tenant_id: str
    roles: tuple[str, ...]
    issued_at_epoch: float
    expires_at_epoch: float

@dataclass(frozen=True)
class IdentityBinding:
    identity_key: tuple[str, str]   # (subject_id, pool_target)
    vm_id: str
    created_at_epoch: float
    expires_at_epoch: float         # Mandatory TTL per ADR-008 §4.5

class AuthGatedLeaseController:
    def resolve_pool_target(
        self,
        assertion: VerifiedAssertion,
        claims_map: dict[tuple[str, str], str],  # (tenant_id, role) -> pool_target
    ) -> str: ...

    def acquire_lease(
        self,
        route_mode: str,            # "path_only" | "auth_gated"
        leasing_strategy: str,      # "pool_generic" | "identity_bound"
        assertion: VerifiedAssertion | None,
        binding_ttl_seconds: int = 14400,
    ) -> dict[str, object]: ...

    def sweep_expired_bindings(
        self,
        now_epoch: float,
    ) -> list[str]:
        """Evicts expired bindings and returns vm_ids queued for ADR-005 sterile discard."""
```

---

## 2. Invariant Contracts & Binding Expiry Policy (Resolving `ADR-008 §4.5`)

| Invariant | Specification | Error / Enforcement |
|---|---|---|
| **Auth-Before-Wake** | `route_mode == "auth_gated"` with `assertion is None` or `now > assertion.expires_at_epoch` | Return `ERR_AUTH_REQUIRED` / `ERR_ASSERTION_EXPIRED`; `pool_lease` call count MUST be `0`. |
| **Deny-by-Default Claims Map** | No matching `(tenant_id, role)` entry in `claims_map` | Reject with `ERR_CLAIM_UNMAPPED`; never fall back to a privileged pool. |
| **Mandatory Binding Expiry** | `binding_ttl_seconds` clamped to `[300, 86400]` (default `14400s` = 4h). | `sweep_expired_bindings()` deletes expired keys and triggers `ADR-005` `.avhdx` discard before pool return. |
| **Strict Identity Affinity** | Lookup key is strictly `(subject_id, pool_target)`; a different `subject_id` can never attach to another caller's bound `vm_id`. | Enforced by composite key lookup + `ERR_IDENTITY_MISMATCH` guard. |
| **Unchanged Default Mode** | `route_mode == "path_only"` bypasses assertion checks and preserves `ADR-002` + `ADR-005` verbatim. | Regression test verifying zero impact on existing path-routed contracts. |
