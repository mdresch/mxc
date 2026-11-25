---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "4.1 Develop Project Charter (Phase 4)"
lifecycle_stage: "Stage 2 (Objective)"
governance_policy: "approve-charter"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/project-docs/Business-Case-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-3.md"
process: "Formally authorize Phase 4, establish sponsor authority, and define measurable objectives and boundaries for Native Rust wxc-exec Runtime Parity & Bare-Metal Silicon Productionization"
outputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
status: "Approved"
---

# Project Charter — MXC Micro-Execution Platform Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `4.1 Develop Project Charter (Phase 4)` (Initiating)  
> **Governance Policy:** `approve-charter` | **Lifecycle Stage:** `Stage 2 (Objective)`  
> **Status:** Approved (`2026-11-25`) — Gate record: [approve-charter-phase4-2026-11-25.adjudication.json](gates/approve-charter-phase4-2026-11-25.adjudication.json) (`approve-charter`, policy `8ec22760-9d76-4683-b1ff-fa4a847b73a1`)  
> **Preceding Baseline:** `PMP-BL-v3.0.0` (Phase 3 Closed) | **Target Baseline:** `PMP-BL-v4.0.0`  
> **Inputs:** [Spark-Capture-Phase-4.md](Spark-Capture-Phase-4.md), [Ideation-Document-Phase-4.md](Ideation-Document-Phase-4.md), [Business-Case-Phase-4.md](Business-Case-Phase-4.md), [Benefits-Statement-Phase-4.md](Benefits-Statement-Phase-4.md), [Intent-Refinement-Proposal-Phase-3.md](Intent-Refinement-Proposal-Phase-3.md)  
> **Outputs:** Project-Charter-Phase-4.md

---

## 1. Executive Summary

Phases 1 through 3 (`PMP-BL-v1.0.0`..`v3.0.0`) delivered **17/17 Epics**, **`358/358` Python contract & governance tests**, and **`31/31` Continuous Improvements Delivered**. This Charter formally authorizes **Phase 4 (`PMP-BL-v4.0.0`)** to deliver four compiled-Rust and bare-metal silicon productionization work packages across `WBS 19.0` through `WBS 22.0`:
1. **Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Parity (`WBS 19.0` / `Epic 018`)**
2. **Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service (`WBS 20.0` / `Epic 019`)**
3. **Bare-Metal Silicon HIL Verification — Density, RAM-Disk, NUMA, TEE & `GPU-P` (`WBS 21.0` / `Epic 020`)**
4. **Signed Offline "MXC Embed" Enterprise Pilot Installer (`WBS 22.0` / `Epic 021`)**

---

## 2. Leadership and Investment Authority

| Role or Control | Phase 4 Charter Record |
|---|---|
| **Project Sponsor** | Menno Drescher |
| **Project Manager / Lead Architect** | Menno Drescher |
| **Operational Benefit Owner** | Menno Drescher |
| **PM Spending Authority** | `USD 50,000` carried envelope (`\$0` new external capital required for core Rust R&D and local Hyper-V verification) |
| **Steering Committee** | Sponsor, CFO, Finance Controller, IT Infrastructure, Platform Security |
| **Target Phase 4 Timeline** | Sprints 19 through 22 (Waves 1–2 ahead of sovereign EU customer pilots) |

---

## 3. Phase 4 Measurable Project Objectives (`WBS 19.0–22.0`)

1. **Objective 1 (`WBS 19.0` / `Epic 018` — Native Rust `wxc-exec` & `mxc-sdk` Parity):** Deliver compiled Rust UTF-8 BOM manifest parsing, CLI override precedence, chunked binary VMBus `copy-file`/`exec` (`>= 100 MB` bit-exact SHA-256), `--hyperv-op fork` (`<= 500 ms` per branch, `max_depth <= 4`), and `--hyperv-op git-sync` (`0` guest static secrets) under `src/mxc-sdk/` and `src/tools/wxc/` with passing `cargo test` suites.
2. **Objective 2 (`WBS 20.0` / `Epic 019` — Compiled Host Sidecar, MCP Firewall & EU Evidence Service):** Deliver compiled host-side credential injection (`<= 5 ms`, `[REDACTED]` logs), MCP JSON-RPC policy enforcement (`<= 2 ms`), SHA-256 hash-chained EU Evidence Ledger (`>= 180-day` retention), and `freeze-and-rollback` kill switch (`<= 250 ms`) under `src/host/`.
3. **Objective 3 (`WBS 21.0` / `Epic 020` — Bare-Metal Silicon HIL Benchmarks):** Deliver automated Hyper-V hardware probes and benchmark harnesses (`scripts/hyperv/`) verifying `<= 640 MB` / `< 350 MB` CrossGen2 density, `0` remote NUMA pages, `<= 50 ms` RAM-disk/DAX overlays, and honest fail-closed vTPM/SEV-SNP/TDX & `GPU-P`/DDA capability/throughput gating.
4. **Objective 4 (`WBS 22.0` / `Epic 021` — Turnkey Signed Offline "MXC Embed" Installer):** Deliver a zero-cloud single-host Windows 11 Pro / Server 2025 pilot bundle (`<= 15 min` install, `0` outbound internet calls) integrating compiled `wxc-exec.exe`, `ADR-012` signed registry verification, and the unattended 5-Act HIL self-test.

---

## 4. Scope Boundaries, Exclusions & Dependencies

- **In Scope:** All work packages across `WBS 19.0–22.0` (`Epics 018–021`) spanning `src/mxc-sdk/`, `src/tools/wxc/`, `src/host/`, and `scripts/hyperv/`, while preserving 100% of Phases 1–3 invariants (`ADR-001..006`, `ADR-008..018`, `358/358` Python tests).
- **Explicit Exclusions:**
  - Public multi-tenant cloud SaaS control plane or external telemetry ingestion services.
  - Faking confidential computing (SEV-SNP/TDX) or `GPU-P` benchmark passes on workstations lacking physical hardware support.
  - Modifying or touching the user's manual `Windows 11 Pro Dev` VM or mutating parent golden VHDXs.
- **Technical Dependencies:** Local Windows 11 Pro Hyper-V host (Build `26100`+), Rust toolchain (`src/rust-toolchain.toml`), and optional Windows Server 2025 server hardware for physical SEV-SNP/TDX, multi-socket NUMA, and `GPU-P`/DDA silicon runs.

---

## 5. Traceable Success Criteria (`BEN-25` .. `BEN-28`)

| Benefit ID | Benefit Statement | Phase 4 Target Metric |
|---|---|---|
| **`BEN-25`** | Native Rust `wxc-exec` & `mxc-sdk` Parity | `100%` UTF-8 BOM acceptance, `>= 100 MB` bit-exact chunked VMBus streaming, `<= 500 ms` `--hyperv-op fork` (`0%` parent drift), and `0` static secrets in `--hyperv-op git-sync` via `cargo test`. |
| **`BEN-26`** | Compiled Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Daemon | `0` static secrets in guest, `<= 5 ms` sidecar injection, `100%` fail-closed MCP block accuracy (`<= 2 ms`), and `<= 250 ms` `freeze-and-rollback` writing to a `>= 180-day` SHA-256 ledger. |
| **`BEN-27`** | Bare-Metal Hyper-V Silicon Proof | `<= 640 MB` floor / `< 350 MB` effective RAM (`>= 65%` shared), `0` remote NUMA pages, `<= 50 ms` RAM-disk mount, honest `ERR_TEE_UNSUPPORTED`/`ERR_GPUP_UNSUPPORTED`, and `>= 85%` native GPU throughput on capable silicon. |
| **`BEN-28`** | Turnkey Signed Offline "MXC Embed" Pilot Appliance | `<= 15-minute` offline single-host install + unattended 5-Act HIL self-test (`0` outbound internet calls) with `100%` immutable parent VHDX SHA-256 verification. |
