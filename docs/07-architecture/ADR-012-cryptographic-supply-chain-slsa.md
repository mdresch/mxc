---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-10"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
  - "docs/07-architecture/ADR-003-production-base-image.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Formulate architectural decisions for end-to-end cryptographic golden-image supply chain, SBOM generation, SLSA Level 3 provenance, and pre-dispatch signature verification"
outputs:
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
status: "Proposed"
---

# ADR 012: Cryptographic Image Supply Chain, Signed SBOM & SLSA Level 3 Attestation

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-10` Cryptographic Supply Chain. Also touches `TP-03` (Image Supply) and `TP-05` (Session Sterility).  
> **Inputs:** [PILLARS-Phase-2.md](PILLARS-Phase-2.md), [ADR-003](ADR-003-production-base-image.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md) (`IMP-MXC-003`, `IMP-MXC-010`, `IMP-MXC-018`)  
> **Outputs:** ADR-012-cryptographic-supply-chain-slsa.md

---

## 1. Executive Summary

Phase 1 (`ADR-003`) separated production golden images (`winserv2025-prod-adpa.vhdx`, `win11-agent-lean.vhdx`) from developer images and introduced static SHA-256 hash verification in `golden_image_registry.json`. However, hash comparison alone cannot prove *who* built the VHDX, *which* source commit and ISO produced it, or *which* OS packages and agent toolchains are embedded inside it.

`ADR-012` establishes an unbroken, **SLSA Level 3-aligned cryptographic chain of custody** from build scripts (`bake_golden_image.ps1`, `build_win11_agent_from_iso.ps1`) through **SPDX/CycloneDX SBOM generation**, **Sigstore/Cosign (or offline PKI) detached signing**, **in-toto provenance attestation**, and a fail-closed runtime verification gate inside **`PoolRegistrationGuard`** prior to any VHDX entering a standby pool.

---

## 2. Decision & Architectural Mechanics

1. **Deterministic Build Provenance (in-toto / SLSA Level 3 Envelope):**
   - Every golden-image build emits a signed DSSE / in-toto provenance statement binding:
     - Git repository URI + exact commit SHA of the baker script,
     - Input ISO / parent VHDX SHA-256 digest,
     - Output golden VHDX SHA-256 digest and byte length,
     - Build timestamp, builder identity, and immutable `image_id`.
2. **Embedded Package & Toolchain SBOM (CycloneDX / SPDX JSON):**
   - During the bake finalize phase (before `Optimize-VHD`), the builder exports a structured SBOM listing Windows OS build/KB patches, remaining AppX/features, and all pre-installed agent tools (e.g., `git`, `pwsh`, `python`, `node`, `ruff`, `pytest`).
   - The SBOM digest is included inside the signed provenance envelope.
3. **Fail-Closed `PoolRegistrationGuard` Runtime Gate:**
   - Before registering or admitting any VHDX into `HotRunning`, `WarmPaused`, or `ColdSaved` standby pools, `PoolRegistrationGuard` MUST verify:
     1. Cryptographic signature validity against the pinned trust root (offline root key or Sigstore Fulcio/Rekor bundle for airgapped hosts),
     2. Live SHA-256 digest match between the on-disk `.vhdx` and the signed provenance subject,
     3. SBOM presence and policy compliance (zero forbidden packages, zero expired certificates, non-revoked image ID).
   - Any verification failure immediately quarantines the image (`ERR_ATTESTATION_FAILED`) and emits an immutable audit event.
4. **Airgapped / Sovereign Host Compatibility:**
   - Verification MUST operate 100% offline using local trust-root bundles (no runtime internet calls to Rekor or public CAs required on airgapped Hyper-V hosts).

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Rely solely on `golden_image_registry.json` SHA-256 hashes | A local registry file can be edited by a compromised host process without cryptographic signature verification; provides no SBOM or build provenance for EU AI Act / DORA / ISO 42001 audits. |
| Require online Rekor / Sigstore transparency-log lookup at VM dispatch | Violates MXC's airgapped-by-default sovereign deployment invariant (`TP-01`, `IMP-MXC-031`). Offline verification bundles preserve both SLSA rigor and airgap compatibility. |
| Sign only the `.avhdx` checkpoint, not the golden `.vhdx` parent | Does not prove provenance of the immutable parent disk; signing the parent + provenance envelope establishes the root of trust for all derived `.avhdx` disks. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Guarantees verifiable supply-chain provenance, tamper-evident golden images, and audit-ready SBOMs aligned with **EU AI Act Annex III (Dec 2, 2027)**, **DORA**, **NIS2**, and **SLSA Level 3** (`BEN-08`).
- **Negative:** Adds ~2–5 seconds to golden-image registration (SHA-256 streaming of multi-GB VHDX + signature verification) and requires key-rotation hygiene for offline signing roots.
- **Mitigation:** Signature and digest verification executes once at `PoolRegistrationGuard` admission (and periodically on background integrity sweeps), adding **0 ms** to the hot/warm VM dispatch path.
