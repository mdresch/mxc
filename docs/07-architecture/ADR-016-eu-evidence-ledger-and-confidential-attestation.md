---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-14"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-008-authentication-gated-session-provisioning.md"
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
process: "Formulate architectural decisions for append-only EU AI Act/DORA/NIS2 evidence ledger, Entra Conditional Access lease hooks, Hit-L freeze-and-rollback circuit breaker, and vTPM/SEV-SNP/TDX attestation"
outputs:
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
status: "Proposed"
---

# ADR 016: Unified EU Regulatory Evidence Ledger, Hit-L Kill Switch, Entra Conditional Access & Confidential Enclave Attestation

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-14` Unified EU Regulatory Evidence Ledger & Hardware Enclave Trust. Also touches `TP-02` (`ADR-008`) and `TP-10` (`ADR-012`).  
> **Inputs:** [PILLARS-Phase-3.md](PILLARS-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md) (`HYP-mxc-026`, `027`), [ADR-008](ADR-008-authentication-gated-session-provisioning.md), [ADR-012](ADR-012-cryptographic-supply-chain-slsa.md)  
> **Outputs:** ADR-016-eu-evidence-ledger-and-confidential-attestation.md

---

## 1. Executive Summary

Ahead of the **EU AI Act Annex III** compliance deadline (**December 2, 2027**, per Regulation (EU) 2026/1744), alongside **DORA** and **NIS2**, regulated enterprises must maintain tamper-evident execution logs retained for at least 6 months (`>= 180 days`), enforce real-time Conditional Access on agent identities (`Entra Agent ID`), provide immediate operator kill switches (`freeze-and-rollback`), and verify confidential VM hardware integrity prior to unlocking private secrets.

`ADR-016` introduces MXC's **Unified Evidence & Enclave Trust Layer**, pairing a SHA-256 hash-chained ledger and sub-250ms circuit breaker with optional vTPM 2.0 / AMD SEV-SNP / Intel TDX remote attestation inside `PoolRegistrationGuard`.

---

## 2. Decision & Architectural Mechanics

1. **Append-Only SHA-256 Hash-Chained Evidence Ledger (`IMP-MXC-030`):**
   - Every dispatch, Entra Conditional Access claim, VMBus command digest, file diff hash, and rollback action appends an immutable event linking `prev_hash -> entry_hash`.
   - Default retention policy enforces `retention_days >= 180` (`ERR_RETENTION_BELOW_EU_FLOOR` if lower) satisfying EU AI Act Art. 19, DORA, and NIS2 from one unified audit store.
2. **Microsoft Entra Agent ID Conditional Access Hook (`IMP-MXC-025`):**
   - Extends `ADR-008` assertions with Conditional Access posture fields (`device_compliant`, `risk_level`, `approved_network`), failing closed with `ERR_CONDITIONAL_ACCESS_DENIED` on elevated risk or non-compliant sessions.
3. **Hit-L / Hot-L `freeze-and-rollback` Circuit Breaker (`IMP-MXC-030`):**
   - Operators or anomaly detectors trigger `freeze_and_rollback()` to suspend guest vCPUs, sever egress/VMBus pipes, and revert to the clean checkpoint in `<= 250 ms` while appending an immutable kill-switch record.
4. **vTPM 2.0 & Confidential VM (SEV-SNP / TDX) Attestation Gate (`IMP-MXC-028`):**
   - `PoolRegistrationGuard` verifies signed hardware PCR/TDX measurement quotes against pinned golden measurements (`ERR_PCR_ATTESTATION_FAILED`), explicitly reporting `ERR_TEE_UNSUPPORTED` on hardware lacking confidential silicon rather than faking attestation.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Emit separate flat text logs per subsystem (gateway, hypervisor, IAM) | Creates unlinked, mutable log silos that fail DORA/NIS2 tamper-evidence checks and force manual audit stitching for EU AI Act Art. 19. |
| Silently downgrade missing SEV-SNP / TDX support to "attested" | False green attestation violates zero-trust compliance; hosts lacking confidential silicon must surface `ERR_TEE_UNSUPPORTED` when confidential mode is requested. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Turns MXC telemetry into unified EU AI Act / DORA / NIS2 evidence (`BEN-21`) and protects proprietary IP/keys with hardware enclave attestation (`BEN-22`).
- **Negative:** Confidential SEV-SNP / TDX profiles require modern server CPUs and Windows Server 2025 Hyper-V host support.
- **Mitigation:** Capability probe cleanly separates standard vTPM 2.0 Gen2 isolation from Confidential VM (`SEV-SNP` / `TDX`) hardware tiers.
