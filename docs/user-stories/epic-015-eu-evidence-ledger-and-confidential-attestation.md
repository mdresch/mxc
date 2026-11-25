---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/project-docs/Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/project-docs/Functional-Design/FDD-015-eu-evidence-ledger-and-confidential-attestation.md"
process: "Decompose unified EU evidence ledger, Entra Conditional Access hook, Hit-L freeze-and-rollback kill switch, and vTPM/TEE attestation into testable user stories"
outputs:
  - "docs/user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md"
status: "Approved — Ready for Implementation"
---

# Epic 015: Unified EU Regulatory Evidence Ledger, Kill Switch & Confidential Enclave Attestation

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 3)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-016](../07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | **WBS:** `16.0` | **Topic Pillar:** `TP-14`  
> **Status:** Approved — Ready for Implementation (2026-11-24) (`IMP-MXC-025`, `028`, `030`)

---

## Story 15.1 — Tamper-Evident EU Evidence Ledger, Entra Conditional Access & Hit-L Kill Switch
- **WBS:** 16.1
- **Status:** Planned
- **As a** EU AI Act / DORA / NIS2 Compliance Lead,  
  **I want** an append-only SHA-256 hash-chained `EvidenceLedger` (`>= 180` days retention), Entra Agent ID Conditional Access posture evaluation, and a `<= 250 ms` `freeze-and-rollback` Hit-L circuit breaker,  
  **so that** every autonomous agent session is audit-traceable and immediately haltable upon anomaly.
- **Acceptance Criteria:**
  - **AC-15.1.1:** `EvidenceLedger` enforces `retention_days >= 180` (raising `ValueError` below 180), handles empty `verify_chain()` safely as `(True, "OK")`, and detects any single-field historical mutation as `(False, "ERR_LEDGER_CHAIN_BROKEN")`.
  - **AC-15.1.2:** `evaluate_entra_conditional_access()` passes compliant low-risk postures (`(True, "OK")`) and rejects `None`, empty dicts, `device_compliant=False`, or high-risk postures with `(False, "ERR_CONDITIONAL_ACCESS_DENIED")`.
  - **AC-15.1.3:** `FreezeRollbackCircuitBreaker.freeze_and_rollback()` returns state `"FROZEN_ROLLED_BACK"` within `<= 250 ms` and appends a verified audit event to the ledger.

---

## Story 15.2 — vTPM 2.0 & Confidential VM (AMD SEV-SNP / Intel TDX) Remote Attestation Gate
- **WBS:** 16.2
- **Status:** Planned
- **As a** Confidential Infrastructure Architect,  
  **I want** `PoolRegistrationGuard` to verify signed vTPM 2.0 PCR and SEV-SNP / TDX boot quotes fail-closed before releasing secrets,  
  **so that** compromised enclaves never unlock private repositories or credentials and unsupported hosts fail honestly.
- **Acceptance Criteria:**
  - **AC-15.2.1:** Supported enclaves with matching `measured_pcr_hex == expected_pcr_hex` return `(True, "ATTESTED")` with `0 ms` post-admission dispatch overhead on cached quotes.
  - **AC-15.2.2:** Mismatched, empty, or `None` quotes fail closed with `(False, "ERR_PCR_ATTESTATION_FAILED")`.
  - **AC-15.2.3:** Hosts with `hardware_supported=False` explicitly return `(False, "ERR_TEE_UNSUPPORTED")` rather than faking compliance.
