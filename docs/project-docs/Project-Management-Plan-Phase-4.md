---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Business-Case-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/07-architecture/PILLARS-Phase-4.md"
  - "docs/07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md"
  - "docs/07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md"
  - "docs/07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md"
  - "docs/user-stories/epic-018-native-rust-wxc-exec-phase3-parity.md"
  - "docs/user-stories/epic-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/user-stories/epic-020-bare-metal-silicon-hil-verification-harness.md"
  - "docs/user-stories/epic-021-signed-offline-mxc-embed-pilot-installer.md"
process: "Integrate Phase 4 scope, schedule, cost, quality, and architectural baselines under PMP-BL-v4.0.0"
outputs:
  - "docs/project-docs/Project-Management-Plan-Phase-4.md"
status: "Approved"
---

# Project Management Plan — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `4.2 Develop Project Management Plan (Phase 4)` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 7 (Planning: Integrated PMP & Baselines)`  
> **Status:** Approved (`2026-11-25`) — Gate record: [approve-pmp-phase4-2026-11-25.adjudication.json](gates/approve-pmp-phase4-2026-11-25.adjudication.json) (`approve-pmp`, policy `46c60639-c24f-4045-8ace-a3dbe2142e61`)  
> **Governing Baseline:** **`PMP-BL-v4.0.0`** | **Preceding Baseline:** `PMP-BL-v3.0.0` (Closed)

---

## 1. Executive Summary & Baseline Authorization

Building upon Phases 1–3 (`PMP-BL-v1.0.0`..`v3.0.0`, `17/17` Epics complete, `358/358` Python contract & governance tests passing, `31/31` Continuous Improvements Delivered), this integrated management plan ratifies baseline **`PMP-BL-v4.0.0`** for **Phase 4 (Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization)**. It governs **4 Topic Pillars (`TP-17`..`TP-20`)**, **4 ADRs (`ADR-019`..`022`)**, **4 Epics (`Epics 018–021`)**, and **8 User Stories (`18.1`..`21.2`)**.

---

## 2. Phase 4 Work Breakdown Structure (`WBS 19.0–22.0`) & Scope Baseline

| WBS | Work Package / Epic / Story | Topic Pillar | Governing ADR | Target Deliverable / Crate or Module |
|:---:|---|:---:|:---:|---|
| **19.0** | **Epic 018 — Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Parity** | `TP-17` | `ADR-019` | `src/tools/wxc/src/`, `src/mxc-sdk/src/` (`BEN-25`) |
| **19.1** | Story 18.1: Native Rust UTF-8 BOM Manifest Parser, CLI Precedence & Chunked VMBus Framing | `TP-17` | `ADR-019` | `cargo test` + parity contract tests (`HYP-mxc-031`) |
| **19.2** | Story 18.2: Native Rust Bounded Parallel Snapshot Forking & Zero-Secret Git Sync Scanner | `TP-17` | `ADR-019` | `cargo test` + parity contract tests (`HYP-mxc-031`) |
| **20.0** | **Epic 019 — Compiled Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Service** | `TP-18` | `ADR-020` | `src/host/wxc_winhttp_proxy_shim/src/` (`BEN-26`) |
| **20.1** | Story 19.1: Compiled Host Credential Sidecar Proxy & Protocol-Aware MCP JSON-RPC Firewall | `TP-18` | `ADR-020` | `cargo test -p wxc_winhttp_proxy_shim` (`HYP-mxc-032`) |
| **20.2** | Story 19.2: Compiled Host EU Evidence Ledger (`>= 180d`) & Hit-L `freeze-and-rollback` Circuit Breaker | `TP-18` | `ADR-020` | `cargo test -p wxc_winhttp_proxy_shim` (`HYP-mxc-032`) |
| **21.0** | **Epic 020 — Bare-Metal Silicon HIL Verification Harness** | `TP-19` | `ADR-021` | `scripts/lib/silicon_hil_harness.py`, `scripts/hyperv/run_silicon_hil_probe.ps1` (`BEN-27`) |
| **21.1** | Story 20.1: Honest Fail-Closed Host Hardware Capability Probe (`TEE`, `GPU-P`, `NUMA`, `RAM-Disk`) | `TP-19` | `ADR-021` | `tests/contracts/test_story_20_1_*.py` (`HYP-mxc-033`) |
| **21.2** | Story 20.2: Non-Destructive Bare-Metal HIL Benchmark Validator & Protected-VM Isolation Guard | `TP-19` | `ADR-021` | `tests/contracts/test_story_20_2_*.py` (`HYP-mxc-033`) |
| **22.0** | **Epic 021 — Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer** | `TP-20` | `ADR-022` | `scripts/lib/mxc_embed_packager.py`, `scripts/hyperv/install_mxc_embed.ps1` (`BEN-28`) |
| **22.1** | Story 21.1: Deterministic Offline Pilot Bundle Manifest Builder (`mxc-embed-manifest.json`) | `TP-20` | `ADR-022` | `tests/contracts/test_story_21_1_*.py` (`HYP-mxc-034`) |
| **22.2** | Story 21.2: Zero-Cloud Offline Bundle Verifier & Unattended `<= 15 min` 5-Act Installer Gate | `TP-20` | `ADR-022` | `tests/contracts/test_story_21_2_*.py` (`HYP-mxc-034`) |

---

## 3. Subsidiary Management Plans Integration (PMBOK 8 — All 9 Knowledge Areas)

| PMBOK 8 Domain | Phase 4 Integrated Control & Baseline Rule |
|---|---|
| **5.1 Scope** | Strictly bounded to `WBS 19.0–22.0` (`Epics 018–021`) bridging Phase 3 Python contracts to Rust binaries, bare-metal HIL probes, and offline pilot packaging. Invariants `ADR-001..006` and `ADR-008..018` remain non-negotiable. |
| **6.1 Schedule** | Executed across **Sprints 19–22** (can execute as a 4-way parallel blitz across disjoint crates/modules): **Epic 018** (`src/tools/wxc/`, `src/mxc-sdk/`), **Epic 019** (`src/host/wxc_winhttp_proxy_shim/`), **Epic 020** (`scripts/lib/silicon_hil_harness.py` + `scripts/hyperv/run_silicon_hil_probe.ps1`), **Epic 021** (`scripts/lib/mxc_embed_packager.py` + `scripts/hyperv/install_mxc_embed.ps1`). |
| **7.1 Cost** | Operates inside the carried **`USD 50,000`** PM spending authority envelope with **\$0 new external capital** required (`Business-Case-Phase-4.md`). |
| **8.1 Quality** | Mandatory `implement-story` loop per story: `scripts/spec_gate.py` (`margin >= +0.05`) $\rightarrow$ RED contracts $\rightarrow$ Tier-2 `.claude/skills/<component>/SKILL.md` (`LL-019..022`) $\rightarrow$ GREEN implementation $\rightarrow$ full `pytest tests -q` + targeted `cargo test` verification $\rightarrow$ Step 9 breakout. |
| **9.1 Resource** | Lead Architect / PM (`Menno Drescher`), local Windows 11 Pro Hyper-V host (`hv:930733af` kept running untouched; `Windows 11 Pro Dev` never touched), and Rust/Python toolchains. |
| **10.1 Communications** | Live traceability maintained in `Project-Status-Register.md`, `Audit-Register.md`, `Lessons-Learned-Register.md`, and `Story-Execution-Register.md`. |
| **11.1 Risk** | Active tracking of `RISK-P4-01..04`: targeted crate `cargo test` commands, shared cross-language error codes, honest hardware capability probing (`ERR_TEE_UNSUPPORTED`, `ERR_GPUP_UNSUPPORTED`), and zero-egress offline bundle verification. |
| **12.1 Procurement** | Zero external cloud SaaS dependencies; all Rust/Python dependencies vendored/offline-capable. |
| **13.2 Stakeholder** | Project Sponsor (`Menno Drescher`), Steering Committee, CISO/SecOps, EU Compliance, and Regulated Enterprise PoC Sponsors. |
