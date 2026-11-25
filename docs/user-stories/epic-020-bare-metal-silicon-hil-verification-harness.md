---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md"
  - "docs/project-docs/Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md"
  - "docs/project-docs/Functional-Design/FDD-020-bare-metal-silicon-hil-verification-harness.md"
process: "Decompose bare-metal Hyper-V silicon HIL capability probe and benchmark verification harness into testable user stories"
outputs:
  - "docs/user-stories/epic-020-bare-metal-silicon-hil-verification-harness.md"
status: "Approved — Ready for Implementation"
---

# Epic 020: Bare-Metal Silicon HIL Verification Harness

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 4)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-021](../07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md) | **WBS:** `21.0` | **Topic Pillar:** `TP-19`  
> **Status:** Approved — Ready for Implementation (2026-11-25) (`HYP-mxc-033`, `BEN-27`)

---

## Story 20.1 — Honest Fail-Closed Host Hardware Capability Probe (`TEE`, `GPU-P`, `NUMA`, `RAM-Disk`)
- **WBS:** 21.1
- **Status:** Planned
- **As a** Hyper-V Systems Architect,  
  **I want** `evaluate_silicon_capabilities()` and `scripts/hyperv/run_silicon_hil_probe.ps1` to probe real host hardware capabilities without faking compliance on unsupported workstations,  
  **so that** Windows 11 Pro dev hosts and Windows Server 2025 servers emit honest, auditable capability verdicts.
- **Acceptance Criteria:**
  - **AC-20.1.1:** When `require_tee=True`, `require_gpup=True`, or `require_multisocket_numa=True` on hosts lacking those capabilities, `evaluate_silicon_capabilities()` returns explicit fail-closed codes (`ERR_TEE_UNSUPPORTED`, `ERR_GPUP_UNSUPPORTED`, `SKIPPED_NO_MULTISOCKET_NUMA`) rather than simulated passes.
  - **AC-20.1.2:** Passing `None` or invalid capability values fails closed cleanly with `ValueError` or explicit error verdict without raising `AttributeError`.

---

## Story 20.2 — Non-Destructive Bare-Metal HIL Benchmark Validator & Protected-VM Isolation Guard
- **WBS:** 21.2
- **Status:** Planned
- **As a** Release Verification Engineer,  
  **I want** `verify_hil_benchmark_report()` to validate density, RAM-disk, parent SHA-256 invariance, and protected-VM exclusion across live silicon runs,  
  **so that** bare-metal benchmarks never mutate golden parent VHDXs or touch `Windows 11 Pro Dev` / active user sandboxes.
- **Acceptance Criteria:**
  - **AC-20.2.1:** Compliant benchmark reports with `parent_sha_before == parent_sha_after`, `0` protected VMs touched, and finite in-bounds density/mount metrics return `(True, "OK")`.
  - **AC-20.2.2:** `None`, empty dicts, parent hash drift (`ERR_PARENT_HASH_DRIFT`), or any protected VM listed in `touched_vms` (`ERR_PROTECTED_VM_TOUCHED`) fail closed deterministically.
