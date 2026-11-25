---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md"
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
process: "Define business rules for bare-metal silicon HIL verification and honest fail-closed hardware capability reporting"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# BRD-020: Bare-Metal Silicon HIL Verification Harness

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 4)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-021](../../07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md) | **Topic Pillar:** `TP-19` | **Baseline:** `PMP-BL-v4.0.0-candidate`

---

## 1. Business Need

Before claiming silicon-verified performance for paused RAM density, RAM-disk/DAX overlays, NUMA pinning, confidential TEE enclaves, or `GPU-P` acceleration, MXC requires an automated HIL verification harness that measures real Hyper-V host telemetry honestly and never fabricates hardware passes on unsupported machines.

---

## 2. Business Rules (BRU)

- **BRU-020-01 (Honest Hardware Capability Probing):** Hosts lacking physical vTPM/SEV-SNP/TDX, partitionable GPUs, or multi-socket NUMA MUST emit explicit fail-closed codes (`ERR_TEE_UNSUPPORTED`, `ERR_GPUP_UNSUPPORTED`, `SKIPPED_NO_MULTISOCKET_NUMA`) rather than simulated passes.
- **BRU-020-02 (Empirical Density & Storage Ceilings):** Measured benchmarks MUST assert `paused_ram_mb <= 640.0`, `effective_ram_mb < 350.0` (`shared_page_ratio >= 0.65`), `remote_numa_pages == 0`, and RAM-disk mount `<= 50.0 ms` (`0` NVMe write bytes) when those profiles are enabled.
- **BRU-020-03 (Zero Side-Effects on Existing VMs & Golden Parents):** HIL runs MUST verify bit-for-bit parent VHDX SHA-256 invariance before and after execution and MUST exclude protected VMs (`Windows 11 Pro Dev`, active user sandboxes).

---

## 3. Traceability

- **Topic Pillar:** `TP-19` | **ADR:** [ADR-021](../../07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md) | **FDD:** [FDD-020](../Functional-Design/FDD-020-bare-metal-silicon-hil-verification-harness.md) | **Epic:** [epic-020](../../user-stories/epic-020-bare-metal-silicon-hil-verification-harness.md) (`WBS 21.0`, `HYP-mxc-033`, `BEN-27`)
