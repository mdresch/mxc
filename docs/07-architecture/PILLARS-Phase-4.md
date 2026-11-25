---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Architectural Strategy Formulation (Phase 4)"
lifecycle_stage: "Stage 5 (Pillars & Architecture)"
governance_policy: "approve-adr"
pmp_baseline: "PMP-BL-v4.0.0"
status: "Approved"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/project-docs/Business-Case-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
  - "docs/project-docs/OUTCOME-Phase-3-Actual-Outcomes.md"
process: "Define Phase 4 topic pillars (TP-17 through TP-20) and establish end-to-end Stage 6 traceability to ADR-019..022, BRD-018..021, FDD-018..021, and Epics 018-021"
outputs:
  - "docs/07-architecture/PILLARS-Phase-4.md"
---

# Pillars Exercise — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation (Phase 4)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 5 (Pillars & Architecture)`  
> **Governing Candidate Baseline:** `PMP-BL-v4.0.0` | **Status:** Approved (`2026-11-25`)  
> **Inputs:** [Project-Charter-Phase-4.md](../project-docs/Project-Charter-Phase-4.md), [Ideation-Document-Phase-4.md](../project-docs/Ideation-Document-Phase-4.md), [Business-Case-Phase-4.md](../project-docs/Business-Case-Phase-4.md), [Benefits-Statement-Phase-4.md](../project-docs/Benefits-Statement-Phase-4.md)  
> **Outputs:** PILLARS-Phase-4.md, Full-Traceability Architecture Matrix (Phase 4)

---

## 1. Executive Purpose & Scope

Phases 1–3 (`PMP-BL-v1.0.0`..`v3.0.0`) established the 17-Epic Hyper-V micro-VM architecture (`TP-01..TP-16`, `ADR-001..006`, `ADR-008..018`, `358/358` passing Python tests, `31/31` Continuous Improvements Delivered). Phase 4 organizes the **contract-to-silicon productionization workstreams** into four Topic Pillars (**`TP-17` through `TP-20`**), decomposed into `ADR-019..022`, `BRD-018..021`, `FDD-018..021`, and `Epics 018–021` (`WBS 19.0–22.0`).

---

## 2. Phase 4 Topic Pillars & Architectural Coverage

### Topic Pillar 17: `TP-17` Native Rust `wxc-exec` & `mxc-sdk` Runtime Parity
- **Domain Focus:** Compiled Rust CLI ergonomics, chunked binary VMBus streaming, bounded `.avhdx` snapshot forking, and zero-secret git sync inside `src/tools/wxc/` and `src/mxc-sdk/`.
- **Governing Chain:** [ADR-019](ADR-019-native-rust-wxc-exec-phase3-parity.md) $\rightarrow$ [BRD-018](../project-docs/Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md) $\rightarrow$ [FDD-018](../project-docs/Functional-Design/FDD-018-native-rust-wxc-exec-phase3-parity.md) $\rightarrow$ [Epic 018](../user-stories/epic-018-native-rust-wxc-exec-phase3-parity.md) (`WBS 19.0` · `HYP-mxc-031` · `BEN-25`)

### Topic Pillar 18: `TP-18` Compiled Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Daemon
- **Domain Focus:** Native host-side secret injection (`<= 5 ms`), MCP JSON-RPC protocol enforcement (`<= 2 ms`), SHA-256 hash-chained EU Evidence Ledger (`>= 180d`), and `freeze-and-rollback` kill switch (`<= 250 ms`) inside `src/host/` and `src/host/wxc_winhttp_proxy_shim/`.
- **Governing Chain:** [ADR-020](ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) $\rightarrow$ [BRD-019](../project-docs/Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) $\rightarrow$ [FDD-019](../project-docs/Functional-Design/FDD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) $\rightarrow$ [Epic 019](../user-stories/epic-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) (`WBS 20.0` · `HYP-mxc-032` · `BEN-26`)

### Topic Pillar 19: `TP-19` Bare-Metal Silicon HIL Verification Harness
- **Domain Focus:** Empirical Hyper-V hardware probes and benchmark harnesses (`scripts/hyperv/`) verifying paused RAM floor, CrossGen2 sharing, RAM-disk/DAX overlays, local NUMA pinning, vTPM 2.0 / SEV-SNP / TDX attestation, and `GPU-P`/DDA throughput with honest fail-closed capability gating.
- **Governing Chain:** [ADR-021](ADR-021-bare-metal-silicon-hil-verification-harness.md) $\rightarrow$ [BRD-020](../project-docs/Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md) $\rightarrow$ [FDD-020](../project-docs/Functional-Design/FDD-020-bare-metal-silicon-hil-verification-harness.md) $\rightarrow$ [Epic 020](../user-stories/epic-020-bare-metal-silicon-hil-verification-harness.md) (`WBS 21.0` · `HYP-mxc-033` · `BEN-27`)

### Topic Pillar 20: `TP-20` Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer
- **Domain Focus:** Single-host zero-cloud Windows 11 Pro / Server 2025 appliance packaging (`<= 15 min`, `0` outbound internet calls) bundling compiled `wxc-exec.exe`, `ADR-012` SLSA registry verification, ISO-to-Lean factory scripts, and the gated 5-Act HIL self-test.
- **Governing Chain:** [ADR-022](ADR-022-signed-offline-mxc-embed-pilot-installer.md) $\rightarrow$ [BRD-021](../project-docs/Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md) $\rightarrow$ [FDD-021](../project-docs/Functional-Design/FDD-021-signed-offline-mxc-embed-pilot-installer.md) $\rightarrow$ [Epic 021](../user-stories/epic-021-signed-offline-mxc-embed-pilot-installer.md) (`WBS 22.0` · `HYP-mxc-034` · `BEN-28`)

---

## 3. End-to-End Phase 4 Traceability Matrix

| Pillar | ADR | BRD | FDD | Epic | WBS | Target Status |
|---|---|---|---|---|:---:|---|
| **`TP-17`** | [ADR-019](ADR-019-native-rust-wxc-exec-phase3-parity.md) | [BRD-018](../project-docs/Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md) | [FDD-018](../project-docs/Functional-Design/FDD-018-native-rust-wxc-exec-phase3-parity.md) | [Epic 018](../user-stories/epic-018-native-rust-wxc-exec-phase3-parity.md) | 19.0 | Approved — Ready for Implementation |
| **`TP-18`** | [ADR-020](ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | [BRD-019](../project-docs/Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | [FDD-019](../project-docs/Functional-Design/FDD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | [Epic 019](../user-stories/epic-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | 20.0 | Approved — Ready for Implementation |
| **`TP-19`** | [ADR-021](ADR-021-bare-metal-silicon-hil-verification-harness.md) | [BRD-020](../project-docs/Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md) | [FDD-020](../project-docs/Functional-Design/FDD-020-bare-metal-silicon-hil-verification-harness.md) | [Epic 020](../user-stories/epic-020-bare-metal-silicon-hil-verification-harness.md) | 21.0 | Approved — Ready for Implementation |
| **`TP-20`** | [ADR-022](ADR-022-signed-offline-mxc-embed-pilot-installer.md) | [BRD-021](../project-docs/Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md) | [FDD-021](../project-docs/Functional-Design/FDD-021-signed-offline-mxc-embed-pilot-installer.md) | [Epic 021](../user-stories/epic-021-signed-offline-mxc-embed-pilot-installer.md) | 22.0 | Approved — Ready for Implementation |
