---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/user-stories/epic-010-cryptographic-supply-chain-slsa.md"
process: "Define business requirements and compliance rules for cryptographic golden-image supply chain, SBOM attestation, and fail-closed pool admission"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md"
status: "Proposed"
---

# BRD-010: Cryptographic Image Supply Chain & Signed SBOM Attestation

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 2)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-012](../../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md), [Project-Charter-Phase-2.md](../Project-Charter-Phase-2.md), [Benefits-Statement-Phase-2.md](../Benefits-Statement-Phase-2.md)  
> **Outputs:** BRD-010-cryptographic-supply-chain-slsa.md

**Source ADR:** [ADR-012](../../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md) — Cryptographic Image Supply Chain, Signed SBOM & SLSA Level 3 Attestation  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Proposed  
**Stakeholders:** Menno Drescher (Product Owner / Architect), CISO / SecOps, Enterprise Compliance (EU AI Act / DORA / NIS2)

---

## 1. Business Need

Regulated financial, healthcare, and public-sector buyers deploying autonomous AI agents on MXC must prove to auditors that every micro-VM boots from an untampered, cryptographically signed golden image with a complete Software Bill of Materials (SBOM). Without an enforced build-to-runtime attestation gate, a tampered `.vhdx` or unauthorized developer image could silently enter a production standby pool, violating NIS2 supply-chain security, DORA ICT resilience, and EU AI Act Annex III technical documentation mandates.

---

## 2. Business Rules (BRU)

- **BRU-010-01 (Mandatory Signed Provenance):** Every production golden image registered into MXC (`winserv2025-prod-adpa.vhdx`, `win11-agent-lean.vhdx`) MUST carry a cryptographically signed in-toto / SLSA provenance envelope binding its SHA-256 digest to its source commit and build inputs.
- **BRU-010-02 (Mandatory SBOM Attachment):** Every production golden image MUST include a machine-readable CycloneDX or SPDX SBOM enumerating OS build, patches, and pre-baked agent toolchains, referenced by digest inside the signed provenance envelope.
- **BRU-010-03 (Fail-Closed Pool Admission):** `PoolRegistrationGuard` MUST reject any unsigned, expired, revoked, or digest-mismatched VHDX with zero fallback to unverified admission (`ERR_ATTESTATION_FAILED`).
- **BRU-010-04 (Airgapped Offline Verification):** All cryptographic signature and SBOM verification MUST succeed without outbound internet connectivity, using a locally pinned trust-root bundle.
- **BRU-010-05 (Zero Dispatch Latency Penalty):** Cryptographic verification executes at registration/admission and scheduled integrity sweeps, adding **0 ms** to Hot (`<= 5 ms`) and Warm (`<= 250 ms`) tenant dispatch SLAs.

---

## 3. Stakeholder Success Metrics

| Metric | Business Target | Baseline Reference |
|---|---|---|
| **Unsigned / Tampered Admission Rate** | `0%` (100% fail-closed rejection) | `BEN-08` / `HYP-mxc-017` |
| **Dispatch Path Latency Overhead** | `0 ms` on Hot/Warm lease | `BEN-02` / `BEN-13` |
| **Offline Verification Success** | `100%` with zero network adapters | `TP-01` / `TP-10` |
| **Audit Evidence Completeness** | 100% of active pool images traceable to Git commit + SBOM + signature | `BEN-08` |

---

## 4. Traceability

- **Topic Pillar:** `TP-10` Cryptographic Supply Chain
- **Architectural Decision:** [ADR-012](../../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md)
- **Functional Design:** [FDD-010](../Functional-Design/FDD-010-cryptographic-supply-chain-slsa.md)
- **User Story Epic:** [epic-010-cryptographic-supply-chain-slsa.md](../../user-stories/epic-010-cryptographic-supply-chain-slsa.md) (WBS 11.0)
- **Harvested Improvements:** `IMP-MXC-003`, `IMP-MXC-010`, `IMP-MXC-018`

---

## 5. Out of Scope

- Hardware vTPM 2.0 / AMD SEV-SNP / Intel TDX runtime enclave attestation (tracked as `IMP-MXC-028` for Phase Next).
- Public Sigstore Rekor online transparency log submission (optional CI extension; offline bundles are mandatory baseline).
