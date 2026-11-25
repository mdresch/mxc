---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Business Documents / Economic & Operational Feasibility Analysis (Phase 4)"
lifecycle_stage: "Stage 4 (Benefit)"
governance_policy: "approve-business-case"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
inputs:
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/project-docs/Spark-Capture-Phase-4.md"
  - "docs/project-docs/OUTCOME-Phase-3-Actual-Outcomes.md"
process: "Evaluate operational feasibility, investment limits, alternatives, and hypothesis-linked risks for Phase 4 Rust runtime parity and bare-metal silicon productionization"
outputs:
  - "docs/project-docs/Business-Case-Phase-4.md"
status: "Approved"
---

# Business Case — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `Business Documents / Economic & Operational Feasibility Analysis (Phase 4)` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 4 (Benefit)`  
> **Governing Candidate Baseline:** `PMP-BL-v4.0.0-candidate`  
> **Status:** Approved (`2026-11-25`) — Gate record: [approve-business-case-phase4-2026-11-25.adjudication.json](gates/approve-business-case-phase4-2026-11-25.adjudication.json) (`approve-business-case`, policy `91a33a4f-7d22-43e1-85ff-51026f350df0`)  
> **Inputs:** [Ideation-Document-Phase-4.md](Ideation-Document-Phase-4.md) (`HYP-mxc-031`..`034`), [Spark-Capture-Phase-4.md](Spark-Capture-Phase-4.md), [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md)  
> **Outputs:** Business-Case-Phase-4.md (Input to [Benefits-Statement-Phase-4.md](Benefits-Statement-Phase-4.md) and [Project-Charter-Phase-4.md](Project-Charter-Phase-4.md))

---

## 1. Executive Purpose & Investment Bound

Phases 1 through 3 (`PMP-BL-v1.0.0`..`v3.0.0`) delivered **17/17 Epics**, **`358/358` passing Python contract & governance tests**, and **`31/31` Continuous Improvements Delivered**. Phase 4 bridges the remaining contract-to-silicon gap documented in [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md) §3 by porting Phase 3 control-plane invariants (`ADR-014..018`) into compiled Rust (`src/mxc-sdk/`, `src/tools/wxc/`, `src/host/`), executing live Hyper-V silicon benchmarks, and packaging the offline "MXC Embed" pilot installer.

- **Investment Envelope & Capital Discipline:** Phase 4 carries forward the existing **USD 50,000** PM spending authority ceiling established in earlier Charters, with **\$0 new external capital** required for core Rust engineering and workstation Hyper-V verification (using existing local Windows 11 Pro Hyper-V hardware and Rust/Python toolchains).
- **No Unvalidated Currency ROI Claimed:** Every operational value premise below traces strictly to open `Formulated` hypotheses (`HYP-mxc-031`..`034`). Commercial ARR, enterprise license pricing, and contracted PoC revenue remain **explicitly excluded** until customer pilots conclude.

---

## 2. Hypothesis-to-Value Premise Table (All Hypotheses `Formulated`)

| Hypothesis ID | Operational Value Premise | Target Ceiling Under Test | Current Status |
|---|---|---|:---:|
| **`HYP-mxc-031`** | Porting UTF-8 BOM manifest parsing, CLI overrides, chunked VMBus streaming, `--hyperv-op fork`, and `--hyperv-op git-sync` into compiled Rust removes shell/8 KB transport limits and eliminates Python-vs-Rust behavioral drift. | `100%` BOM manifest acceptance (`0` false parse errors); `>= 100 MB` bit-exact chunked VMBus transfer; `<= 500 ms` per branch across 3–5 parallel `.avhdx` forks (`0%` parent hash drift). | `Formulated` |
| **`HYP-mxc-032`** | Running the credential-injecting sidecar proxy, MCP JSON-RPC firewall PEP, and EU Evidence Ledger + `freeze-and-rollback` kill switch as compiled host services enforces zero-secret guest execution and EU AI Act / DORA / NIS2 auditability on live VMBus traffic. | `0` static secret bytes in guest; `<= 5 ms` p95 sidecar injection; `100%` fail-closed MCP block accuracy (`<= 2 ms` p95); `<= 250 ms` `freeze-and-rollback` with `>= 180-day` hash-chained ledger. | `Formulated` |
| **`HYP-mxc-033`** | Automated bare-metal Hyper-V HIL benchmarks verify ultra-density, RAM-disk/DAX, NUMA pinning, confidential TEE attestation, and `GPU-P`/DDA ceilings without faking hardware capabilities on unsupported workstations. | `<= 640 MB` paused floor / `< 350 MB` effective RAM (`>= 65%` shared pages); `0` remote NUMA pages; `<= 50 ms` RAM-disk mount (`0` NVMe write bytes); honest `ERR_TEE_UNSUPPORTED` / `ERR_GPUP_UNSUPPORTED` on unsupported hosts and `>= 85%` native GPU throughput on capable hosts. | `Formulated` |
| **`HYP-mxc-034`** | Packaging compiled `wxc-exec.exe`, signed `golden_image_registry.json`, ISO-to-Lean scripts, and the 5-Act HIL self-test into an offline single-host installer turns MXC into a turnkey sovereign EU pilot appliance. | `<= 15-minute` clean offline single-host install + unattended 5-Act HIL pass (`0` outbound internet calls) with `100%` bit-for-bit parent VHDX SHA-256 invariance. | `Formulated` |

---

## 3. Business Alternatives Comparison

| Option | Capabilities & Operational Posture | Why Rejected or Selected |
|---|---|---|
| **(A) Stop at Phase 3 Python Control-Plane Contracts (`PMP-BL-v3.0.0`)** | Preserves all `358/358` Python contract tests and architectural docs, but leaves `wxc-exec.exe` and host services without compiled Phase 3 features (`fork`, chunked VMBus, BOM parser, sidecar/MCP daemon). | **Rejected:** Python contract proofs alone cannot be deployed as a native Windows enterprise binary or demonstrated end-to-end inside `wxc-exec.exe`. |
| **(B) Rewrite Entire Hyper-V Engine in Python / PowerShell** | Avoids Rust compilation complexity, but sacrifices native Win32/VMBus binary performance, single-binary distribution, and existing `src/mxc-sdk` / `src/tools/wxc` investment. | **Rejected:** Regresses execution latency, deployment simplicity, and existing Rust SDK safety guarantees. |
| **(C) Cloud-Dependent Installer + External Telemetry SaaS** | Simplifies packaging via online downloads and hosted attestation/logging backends. | **Rejected:** Breaks sovereign zero-cloud airgap guarantees (`ADR-012`, `ADR-017`) required by regulated EU banking, healthcare, and public-sector buyers. |
| **(D) Recommended — MXC Phase 4 Native Rust Parity & Bare-Metal Silicon Productionization** | Translates verified Phase 3 invariants into `src/mxc-sdk`, `src/tools/wxc`, and `src/host`, validates bare-metal hardware ceilings honestly with fail-closed capability probes, and packages offline "MXC Embed" within `\$0` new external capital. | **Selected:** Bridges contract-to-silicon cleanly while preserving all `ADR-001..018` invariants and `358/358` Python tests. |

---

## 4. Material Risk Register (Tied to Open `Formulated` Hypotheses)

| Risk ID | Risk Description | Linked Open Hypotheses | Mitigation & Boundary |
|---|---|---|---|
| **RISK-P4-01** | Rust incremental build / MSVC linker instability inside Windows sandboxed shells (observed earlier on unfiltered `cargo test`) could slow CI/verification loops. | `HYP-mxc-031`, `HYP-mxc-032` | Run targeted crate tests (`cargo test -p mxc-sdk`, `cargo test -p wxc`) with clean target paths and document deterministic build flags. |
| **RISK-P4-02** | Behavioral drift between Python Phase 3 contracts (`scripts/lib/`) and newly ported Rust implementations (`src/mxc-sdk/`, `src/tools/wxc/`). | `HYP-mxc-031`, `HYP-mxc-032` | Cross-validate shared JSON fixtures and identical error codes (`ERR_STATIC_SECRET_DETECTED`, `ERR_MCP_*`, `ERR_FORK_DEPTH_EXCEEDED`, `ERR_CHUNK_CHECKSUM_MISMATCH`) across both suites. |
| **RISK-P4-03** | Local workstation lacks physical AMD SEV-SNP / Intel TDX or multi-socket NUMA / `GPU-P` server silicon during initial development. | `HYP-mxc-033` | Enforce honest hardware capability detection returning `ERR_TEE_UNSUPPORTED` / `ERR_GPUP_UNSUPPORTED` locally, while keeping benchmark scripts ready for Windows Server 2025 target hosts. |
| **RISK-P4-04** | Offline "MXC Embed" installer accidentally pulls PowerShell Gallery modules or external binaries during airgapped deployment. | `HYP-mxc-034` | Gate installer preflight and 5-Act HIL verification with zero-egress firewall checks (`ERR_NETWORK_EGRESS_ATTEMPTED`) and vendored offline artifacts. |
