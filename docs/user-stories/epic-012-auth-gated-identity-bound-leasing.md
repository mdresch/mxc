---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-008-authentication-gated-session-provisioning.md"
  - "docs/project-docs/Business-Requirements/BRD-012-auth-gated-identity-bound-leasing.md"
  - "docs/project-docs/Functional-Design/FDD-012-auth-gated-identity-bound-leasing.md"
process: "Decompose ADR-008 authentication-gated provisioning, deny-by-default claims routing, and TTL-bounded identity-bound VM leasing into testable user stories"
outputs:
  - "docs/user-stories/epic-012-auth-gated-identity-bound-leasing.md"
status: "Proposed — Ready for Gate Approval"
---

# Epic 012: Authentication-Gated Session Provisioning & Identity-Bound VM Leasing (`ADR-008`)

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 2)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-008](../07-architecture/ADR-008-authentication-gated-session-provisioning.md) (Accepted 2026-11-04)  
> **Target Baseline:** `PMP-BL-v2.0.0` | **WBS Index:** 3.4 / 13.0 | **Topic Pillars:** `TP-02` & `TP-05`  
> **Status:** Proposed — Ready for Gate Approval

---

## Story 12.1 — `auth_gated` Ingress Gate & Deny-by-Default Claims-to-Pool Resolver
- **WBS:** 3.4.1
- **Status:** Planned
- **As an** Enterprise IAM Architect,  
  **I want** routes configured with `leasing_mode: "auth_gated"` to require a verified OIDC/SAML/Entra Agent ID assertion before calling `pool_lease` and to select the target golden-image pool via a deny-by-default claims map,  
  **so that** unauthenticated traffic wakes zero VMs and callers only access pools authorized by their verified claims.
- **Acceptance Criteria:**
  - **AC-12.1.1:** Missing or expired assertions on an `auth_gated` route return `ERR_AUTH_REQUIRED` / `ERR_ASSERTION_EXPIRED` with `0` VMs woken.
  - **AC-12.1.2:** Verified assertions resolve `(tenant_id, role)` deterministically to the configured `pool_target`; unmapped claims fail closed with `ERR_CLAIM_UNMAPPED`.
  - **AC-12.1.3:** Existing `path_only` routes remain 100% unchanged (`ADR-002` regression invariance).

---

## Story 12.2 — Opt-In Identity-Bound VM Leasing & Mandatory TTL Expiry Reclamation
- **WBS:** 3.4.2
- **Status:** Planned
- **As a** Security & Platform Operations Lead,  
  **I want** opt-in identity-bound leases `(subject_id, pool_target) -> vm_id` to reconnect returning users/agents to their warm VM within a bounded TTL and automatically reclaim expired bindings via `ADR-005` sterile `.avhdx` discard,  
  **so that** personalized desktops/agents persist safely without cross-user leakage or indefinite pool starvation.
- **Acceptance Criteria:**
  - **AC-12.2.1:** A returning verified caller with matching `(subject_id, pool_target)` before `expires_at_epoch` reattaches to the same `vm_id`; any other `subject_id` is strictly isolated from that `vm_id`.
  - **AC-12.2.2:** `binding_ttl_seconds` is clamped to `[300, 86400]` (default `14400s`), resolving `ADR-008 §4.5`.
  - **AC-12.2.3:** `sweep_expired_bindings()` evicts expired mappings and returns their `vm_id`s for mandatory `ADR-005` `.avhdx` sterile discard prior to re-entering the shared standby pool.
