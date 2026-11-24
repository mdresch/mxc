---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md"
process: "Define business requirements for reproducible ISO-to-Lean image CI factory, turnkey zero-cloud MXC Embed installer, and gated 5-Act HIL release check"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md"
status: "Proposed"
---

# BRD-016: Turnkey "MXC Embed" Sovereign Appliance & Reproducible ISO-to-Lean Factory

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 3)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-017](../../07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | **Topic Pillar:** `TP-15` | **Status:** Proposed

---

## 1. Business Need

Regulated EU buyers running Phase 0 pilots want a repeatable, zero-cloud installer ("MXC Embed") that brings up hardware-isolated AI agent sandboxes on a single Windows 11 Pro or Windows Server 2025 host in minutes—backed by automated CI image fabrication and a pass/fail 5-Act proof suite.

---

## 2. Business Rules (BRU)

- **BRU-016-01 (Automated Image Registry & SLSA Handoff):** Every ISO-to-Lean factory build MUST compute the output VHDX SHA-256 digest automatically and emit an updated `golden_image_registry.json` record ready for `ADR-012` attestation (`0` manual hash edits).
- **BRU-016-02 (Zero-Cloud Installation Guarantee):** "MXC Embed" single-host installation and self-test MUST complete in **$\le 15\text{ minutes}$** with **0** outbound internet calls (`ERR_NETWORK_EGRESS_ATTEMPTED`).
- **BRU-016-03 (Gated 5-Act HIL Proof):** All 5 verification Acts (Boot $\rightarrow$ VMBus Copy $\rightarrow$ Toolchain Run $\rightarrow$ Mutation + Rollback $\rightarrow$ Immutable Parent Hash Check) MUST pass deterministically (`ERR_HIL_ACT_FAILED` / `ERR_PARENT_HASH_DRIFT` on any failure).

---

## 3. Traceability

- **Topic Pillar:** `TP-15` | **ADR:** [ADR-017](../../07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | **FDD:** [FDD-016](../Functional-Design/FDD-016-mxc-embed-sovereign-appliance-and-image-factory.md) | **Epic:** [epic-016](../../user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md) (`WBS 17.0`)
- **Hypotheses & Benefits:** `HYP-mxc-028`, `BEN-23` | **Improvements:** `IMP-MXC-018`, `023`, `031`
