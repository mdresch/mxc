---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md"
process: "Define business rules for unified EU AI Act/DORA/NIS2 evidence ledger, Entra Conditional Access gate, Hit-L kill switch, and vTPM/TEE attestation"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md"
status: "Approved"
---

# BRD-015: Unified EU Regulatory Evidence Ledger, Kill Switch & Confidential Enclave Attestation

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 3)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-016](../../07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | **Topic Pillar:** `TP-14` | **Status:** Approved (2026-11-24)

---

## 1. Business Need

Directly supporting CBa Consult's **EU AI Act Annex III (`Dec 2, 2027`) / ISO 42001 / DORA / NIS2** offerings (`OP-RSK-004` & `OP-ITG-017`), enterprise risk officers require verifiable immutable audit logs (`>= 180` days), real-time Entra Agent ID Conditional Access checks, instant incident kill switches, and hardware enclave attestation before allowing autonomous agents near sensitive records.

---

## 2. Business Rules (BRU)

- **BRU-015-01 (Hash-Chained Integrity & 180-Day Retention):** Every ledger event MUST cryptographically chain `prev_hash -> entry_hash`; altering any historical entry MUST fail chain verification (`100%` detection, `ERR_LEDGER_CHAIN_BROKEN`), and retention policies below `180` days MUST be rejected (`ERR_RETENTION_BELOW_EU_FLOOR`).
- **BRU-015-02 (Entra Agent ID Conditional Access Gate):** Requests carrying `risk_level` above configured ceiling or `device_compliant == False` MUST fail closed (`ERR_CONDITIONAL_ACCESS_DENIED`).
- **BRU-015-03 (Sub-250ms Hit-L Circuit Breaker):** Invoking `freeze_and_rollback()` MUST transition the session to `FROZEN_ROLLED_BACK` within **$\le 250\text{ ms}$** and append an immutable audit event.
- **BRU-015-04 (Fail-Closed Hardware Quote Verification):** Mismatched PCR/TEE quotes MUST fail closed (`ERR_PCR_ATTESTATION_FAILED`) with **0 ms** hot-dispatch overhead post-admission, while hardware lacking TEE capability MUST honestly report `ERR_TEE_UNSUPPORTED` rather than fabricating compliance.

---

## 3. Traceability

- **Topic Pillar:** `TP-14` | **ADR:** [ADR-016](../../07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | **FDD:** [FDD-015](../Functional-Design/FDD-015-eu-evidence-ledger-and-confidential-attestation.md) | **Epic:** [epic-015](../../user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md) (`WBS 16.0`)
- **Hypotheses & Benefits:** `HYP-mxc-026`, `027`, `BEN-21`, `BEN-22` | **Improvements:** `IMP-MXC-025`, `028`, `030`
