---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-008-authentication-gated-session-provisioning.md"
  - "docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md"
  - "docs/07-architecture/ADR-005-transient-differencing-disk.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
  - "docs/user-stories/epic-012-auth-gated-identity-bound-leasing.md"
process: "Define business requirements, claims-mapping guardrails, and binding-expiry rules for ADR-008 authentication-gated provisioning and identity-bound VM leasing"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md"
status: "Approved"
---

# BRD-012: Authentication-Gated Session Provisioning & Identity-Bound VM Leasing

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 2)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-008](../../07-architecture/ADR-008-authentication-gated-session-provisioning.md), [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md), [PILLARS-Phase-2.md](../../07-architecture/PILLARS-Phase-2.md)  
> **Outputs:** BRD-012-auth-gated-identity-bound-leasing.md

**Source ADR:** [ADR-008](../../07-architecture/ADR-008-authentication-gated-session-provisioning.md) — Authentication-Gated Session Provisioning & Identity-Bound VM Leasing (Accepted 2026-11-04)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved (2026-11-24)  
**Stakeholders:** Menno Drescher (Product Owner / Architect), Enterprise IAM / Identity Team, CISO / SecOps

---

## 1. Business Need

`ADR-002`'s default path-routed wake is optimal for stateless APIs, but for personalized interactive desktops and privileged enterprise AI agents (human OIDC/SAML users or Microsoft Entra Agent IDs), waking a guest VM *before* caller authentication wastes standby capacity on unauthenticated scans/abandoned logins and prevents routing callers to role-specific golden images. `ADR-008` adds opt-in `auth_gated` ingress and opt-in identity-bound VM leasing while preserving `ADR-002` path-only wake and `ADR-005` sterile rollback as unchanged defaults.

---

## 2. Business Rules (BRU)

- **BRU-012-01 (Opt-In `auth_gated` Default Preservation):** `ADR-002` path-only leasing MUST remain the default for all routes unless a route explicitly configures `leasing_mode: "auth_gated"`.
- **BRU-012-02 (Zero Unauthenticated Wake):** On an `auth_gated` route, failed, expired, or abandoned OIDC/SAML/Entra assertions MUST wake **0** VMs and issue **0** `pool_lease` calls.
- **BRU-012-03 (Least-Privilege Claims-to-Pool Mapping):** Verified IdP claims (`group`, `role`, `tenant`, or `agent_id`) MUST resolve through an explicit, deny-by-default claims-to-pool-target map (`ERR_CLAIM_UNMAPPED` on unknown or over-broad claims).
- **BRU-012-04 (Explicit Opt-In Identity Binding & Mandatory Expiry):** Identity-bound persistence `(authenticated_identity, pool_target) -> vm_id` is strictly opt-in per route and MUST enforce a finite binding TTL (`binding_ttl_seconds`, default `14400s` / 4 hours; max `86400s` / 24 hours). Upon expiry, the binding is deleted and the VM undergoes mandatory `ADR-005` `.avhdx` sterile discard before returning to the shared pool.
- **BRU-012-05 (Cross-Identity Isolation Guarantee):** An identity-bound VM MUST never be leased to a different `authenticated_identity` prior to expiry + sterile `ADR-005` rollback.

---

## 3. Stakeholder Success Metrics

| Metric | Business Target | Baseline Reference |
|---|---|---|
| **Unauthenticated Wake Rate (`auth_gated` routes)** | `0%` (zero VMs woken on failed/abandoned login) | `ADR-008` / `TP-02` |
| **Post-Assertion Resume Overhead** | `<= 350 ms` (`<= 300 ms` Resume-VM + `~50 ms` health probe) | `ADR-004` / `ADR-008` |
| **Cross-User Identity Leakage** | `0` cross-identity lease collisions | `ADR-005` / `TP-05` |
| **Expired Binding Reclamation** | `100%` of expired bindings sterile-reclaimed within cooldown | `ADR-008 §4.5` |

---

## 4. Traceability

- **Topic Pillars:** `TP-02` (Ingress) and `TP-05` (Session Sterility)
- **Architectural Decision:** [ADR-008](../../07-architecture/ADR-008-authentication-gated-session-provisioning.md)
- **Functional Design:** [FDD-012](../Functional-Design/FDD-012-auth-gated-identity-bound-leasing.md)
- **User Story Epic:** [epic-012-auth-gated-identity-bound-leasing.md](../../user-stories/epic-012-auth-gated-identity-bound-leasing.md) (WBS 3.4 / Epic 012)
- **Related Improvement:** `IMP-MXC-025` (Microsoft Entra Agent ID & Conditional Access Lease Binding)
- **Note on Phase 1 Lineage:** `HYP-mxc-008` and `BEN-06` remain exclusively with `ADR-002` per `ADR-008 §2–§3`.

---

## 5. Out of Scope

- Implementing an IdP or MFA engine inside MXC (authentication remains delegated to the organization's OIDC/SAML/Entra IdP).
- "Disconnect, don't release" interactive grace windows (deferred to future horizon per `ADR-008 §4.5`).
