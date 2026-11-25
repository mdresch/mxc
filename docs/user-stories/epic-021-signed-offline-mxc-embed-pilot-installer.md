---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md"
  - "docs/project-docs/Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md"
  - "docs/project-docs/Functional-Design/FDD-021-signed-offline-mxc-embed-pilot-installer.md"
process: "Decompose offline MXC Embed pilot bundle packager, integrity verifier, and unattended 5-Act installer gate into testable user stories"
outputs:
  - "docs/user-stories/epic-021-signed-offline-mxc-embed-pilot-installer.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# Epic 021: Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 4)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-022](../07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md) | **WBS:** `22.0` | **Topic Pillar:** `TP-20`  
> **Status:** Draft — Ready for Stage 5/6 Approval (`HYP-mxc-034`, `BEN-28`)

---

## Story 21.1 — Deterministic Offline Pilot Bundle Manifest Builder (`mxc-embed-manifest.json`)
- **WBS:** 22.1
- **Status:** Planned
- **As a** Sovereign Release Engineer,  
  **I want** `build_embed_bundle_manifest()` to emit a strict SHA-256 manifest for compiled `wxc-exec.exe`, `golden_image_registry.json`, and HIL scripts with `offline_only=True`,  
  **so that** customer pilot bundles are reproducible and tamper-evident prior to airgapped delivery.
- **Acceptance Criteria:**
  - **AC-21.1.1:** Valid inputs emit an `EmbedBundleManifest` with `offline_only=True`, lowercase 64-hex SHA-256 digests for all artifacts and `golden_vhdx_sha256`.
  - **AC-21.1.2:** Empty/`None` `bundle_version`, empty/`None` `file_hashes`, or malformed non-64-hex SHA-256 digests raise `ValueError`.

---

## Story 21.2 — Zero-Cloud Offline Bundle Verifier & Unattended `<= 15 min` 5-Act Installer Gate
- **WBS:** 22.2
- **Status:** Planned
- **As a** Sovereign Enterprise Solutions Architect,  
  **I want** `verify_embed_bundle_offline()` and `scripts/hyperv/install_mxc_embed.ps1` to verify bundle hashes, block outbound internet attempts, and gate completion on the `<= 15 min` 5-Act HIL self-test,  
  **so that** airgapped EU hosts deploy and self-verify MXC with zero cloud dependencies.
- **Acceptance Criteria:**
  - **AC-21.2.1:** Matching offline manifests within `0.0 < install_minutes_estimate <= 15.0` and `outbound_internet_attempted=False` return `(True, "OK")` with zero network calls.
  - **AC-21.2.2:** `outbound_internet_attempted=True` (`ERR_NETWORK_EGRESS_ATTEMPTED`), `None`/empty/mismatched/missing/extra file hashes (`ERR_BUNDLE_INTEGRITY_FAILED`), or non-finite/`<= 0`/`> 15.0` install durations (`ERR_INSTALL_BUDGET_EXCEEDED`) fail closed deterministically.
