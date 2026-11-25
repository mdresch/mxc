---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/project-docs/Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/project-docs/Functional-Design/FDD-016-mxc-embed-sovereign-appliance-and-image-factory.md"
process: "Decompose reproducible ISO-to-Lean CI factory, turnkey MXC Embed installer, and gated 5-Act HIL verification into testable user stories"
outputs:
  - "docs/user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md"
status: "Approved — Ready for Implementation"
---

# Epic 016: Turnkey "MXC Embed" Sovereign Appliance & Reproducible ISO-to-Lean Factory

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 3)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-017](../07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | **WBS:** `17.0` | **Topic Pillar:** `TP-15`  
> **Status:** Approved — Ready for Implementation (2026-11-24) (`IMP-MXC-018`, `023`, `031`)

---

## Story 16.1 — Reproducible ISO-to-Lean Agent Image CI Factory & Auto-Registry Hasher
- **WBS:** 17.1
- **Status:** Planned
- **As a** Release & Image Pipeline Engineer,  
  **I want** parameterized ISO-to-Lean factory builds that automatically hash the resulting VHDX and emit a complete `golden_image_registry.json` entry compatible with `ADR-012` SLSA attestation,  
  **so that** reproducible 9-second Windows 11 Agent images build cleanly without manual SHA-256 registry edits.
- **Acceptance Criteria:**
  - **AC-16.1.1:** `build_auto_registry_entry()` emits a valid registry dict with `image_id`, `vhdx_sha256`, `size_bytes`, `toolchain_packages`, `explorer_stripped=True`, and `compact_os_lzx=True`.
  - **AC-16.1.2:** Empty/`None` `image_id`, empty `toolchain_packages`, non-positive `size_bytes`, or invalid `vhdx_sha256` raise `ValueError`.

---

## Story 16.2 — Turnkey Zero-Cloud "MXC Embed" Sovereign Appliance & Gated 5-Act HIL Suite
- **WBS:** 17.2
- **Status:** Planned
- **As a** Sovereign Enterprise Buyer / Solutions Architect,  
  **I want** a zero-cloud single-host "MXC Embed" installer validator (`<= 15 minutes`, `0` outbound internet calls) and a gated 5-Act HIL release check verifying parent SHA-256 invariance,  
  **so that** airgapped EU organizations can deploy and continuously prove Hyper-V agent containment locally.
- **Acceptance Criteria:**
  - **AC-16.2.1:** `run_mxc_embed_preflight()` admits compliant offline hosts within `<= 15.0` minutes (`(True, "OK")`) and rejects `outbound_internet_required=True` (`ERR_NETWORK_EGRESS_ATTEMPTED`), missing Hyper-V/image, or negative/`NaN`/`> 15.0` durations fail-closed.
  - **AC-16.2.2:** `evaluate_five_act_hil_gate()` passes only when all 5 Acts succeed and `parent_sha_before == parent_sha_after`; empty/short Act lists (`ERR_HIL_ACT_FAILED`) or hash mismatches (`ERR_PARENT_HASH_DRIFT`) fail closed.
