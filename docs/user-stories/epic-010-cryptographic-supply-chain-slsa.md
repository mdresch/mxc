---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
  - "docs/project-docs/Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md"
  - "docs/project-docs/Functional-Design/FDD-010-cryptographic-supply-chain-slsa.md"
process: "Decompose cryptographic image supply chain, signed SBOM generation, and PoolRegistrationGuard admission gate into testable user stories"
outputs:
  - "docs/user-stories/epic-010-cryptographic-supply-chain-slsa.md"
status: "Approved — Ready for Implementation"
---

# Epic 010: Cryptographic Image Supply Chain & Signed SBOM Attestation

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 2)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-012](../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md)  
> **Target Baseline:** `PMP-BL-v2.0.0` | **WBS Index:** 11.0 | **Topic Pillar:** `TP-10`  
> **Status:** Approved — Ready for Implementation (2026-11-24)

---

## Story 10.1 — Deterministic SLSA Provenance Envelope & CycloneDX SBOM Generator
- **WBS:** 11.1
- **Status:** Planned
- **As a** Platform Security Engineer,  
  **I want** golden image builds to emit a CycloneDX SBOM and a cryptographically signed in-toto/SLSA provenance envelope binding the VHDX SHA-256 digest to the source Git commit,  
  **so that** every production image carries verifiable, tamper-evident build lineage.
- **Acceptance Criteria:**
  - **AC-10.1.1:** `generate_sbom_and_provenance()` produces a valid CycloneDX JSON SBOM and a signed `AttestationBundle` containing `image_id`, `vhdx_sha256`, `sbom_sha256`, `git_commit`, `issued_at_utc`, and `expires_at_utc`.
  - **AC-10.1.2:** Modifying a single byte of the SBOM or provenance payload invalidates the cryptographic signature deterministically.

---

## Story 10.2 — Fail-Closed `PoolRegistrationGuard` Offline Attestation Gate
- **WBS:** 11.2
- **Status:** Planned
- **As a** CISO / Compliance Auditor,  
  **I want** `PoolRegistrationGuard` to verify signature validity, VHDX SHA-256 digest, SBOM policy compliance, key revocation, and expiry completely offline before admitting any image into a standby pool,  
  **so that** tampered, unsigned, or revoked images can never boot in production.
- **Acceptance Criteria:**
  - **AC-10.2.1:** Valid signed bundles pass `verify_pool_admission()` with `admitted=True` and `reason_code="ADMITTED"` with zero network calls.
  - **AC-10.2.2:** Tampered VHDX digest (`ERR_DIGEST_MISMATCH`), invalid signature (`ERR_SIGNATURE_INVALID`), revoked signing key (`ERR_KEY_REVOKED`), expired bundle (`ERR_EXPIRED`), and forbidden SBOM packages (`ERR_SBOM_INVALID`) are all rejected fail-closed (`admitted=False`).
  - **AC-10.2.3:** Runtime dispatch path (`HotRunning` / `WarmPaused`) incurs `0 ms` additional latency because verification occurs exclusively at registration and background integrity sweeps.
