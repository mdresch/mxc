---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-20"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/07-architecture/PILLARS-Phase-4.md"
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
process: "Specify turnkey zero-cloud MXC Embed single-host installer bundle, offline manifest verification, and gated 5-Act self-test architecture"
outputs:
  - "docs/07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md"
status: "Approved"
---

# ADR 022: Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 4)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-20` Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer. Also touches `TP-10`, `TP-15`.  
> **Inputs:** [PILLARS-Phase-4.md](PILLARS-Phase-4.md), [Ideation-Document-Phase-4.md](../project-docs/Ideation-Document-Phase-4.md) (`HYP-mxc-034`), [ADR-012](ADR-012-cryptographic-supply-chain-slsa.md), [ADR-017](ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md)  
> **Outputs:** ADR-022-signed-offline-mxc-embed-pilot-installer.md

---

## 1. Executive Summary

`ADR-022` operationalizes `ADR-017` into a self-contained, zero-cloud single-host pilot installer bundle (`mxc-embed-bundle`) for Windows 11 Pro and Windows Server 2025. The bundle packages compiled `wxc-exec.exe`, signed `golden_image_registry.json` (`ADR-012` SLSA provenance + CycloneDX SBOM), ISO-to-Lean image factory scripts, and an unattended 5-Act Hardware-in-the-Loop self-test completing in `<= 15 minutes` with `0` outbound internet calls.

---

## 2. Decision & Architectural Mechanics

1. **Zero-Cloud Offline Bundle Manifest (`scripts/lib/mxc_embed_packager.py` + `scripts/hyperv/install_mxc_embed.ps1`):**
   - Every payload file in the pilot bundle carries a verified lowercase SHA-256 digest in `mxc-embed-manifest.json`; missing, extra, or tampered files fail closed (`ERR_BUNDLE_INTEGRITY_FAILED`) before touching Hyper-V configuration.
   - Preflight enforces `outbound_internet_required == False` (`ERR_NETWORK_EGRESS_ATTEMPTED`), Hyper-V role presence, base image presence, and `<= 15.0 min` install budget (`ADR-017`).
2. **Integrated `ADR-012` Supply Chain Verification:**
   - Installer validates `golden_image_registry.json` provenance and SBOM offline prior to registering the golden parent VHDX.
3. **Unattended 5-Act HIL Self-Test Gate:**
   - Post-install verification executes all 5 Acts (airgapped boot, VMBus transfer, polyglot execution, rogue mutation, instant checkpoint rollback) and asserts bit-for-bit parent VHDX SHA-256 invariance (`ERR_PARENT_HASH_DRIFT` on any drift).

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Fetch PowerShell Gallery modules or GitHub Release binaries during install | Violates airgapped sovereign deployment mandate (`RISK-P4-04`). |
| Ship installer without automated post-install HIL verification | Leaves customer PoCs vulnerable to silent Hyper-V misconfiguration or unverified parent drift. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Repeatable `<= 15 min` sovereign EU enterprise PoC deployment with built-in cryptographic and 5-Act proof (`BEN-28`).
- **Negative:** Offline bundles are larger because all binaries and scripts are vendored upfront.
- **Mitigation:** Separate the lightweight control-plane installer bundle from the large golden `.vhdx` image referenced by SHA-256 digest.
