---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Business Documents / Economic & Operational Feasibility Analysis (Phase 3)"
lifecycle_stage: "Stage 4 (Benefit)"
governance_policy: "approve-business-case"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
inputs:
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/project-docs/Spark-Capture-Phase-3.md"
  - "docs/project-docs/OUTCOME-Phase-2-Actual-Outcomes.md"
process: "Evaluate operational feasibility, investment limits, alternatives, and hypothesis-linked risks for Phase 3"
outputs:
  - "docs/project-docs/Business-Case-Phase-3.md"
status: "Approved"
---

# Business Case — Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `Business Documents / Economic & Operational Feasibility Analysis (Phase 3)` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 4 (Benefit)`  
> **Governing Candidate Baseline:** `PMP-BL-v3.0.0-candidate`  
> **Status:** Approved (`2026-11-24`) — Gate record: [approve-business-case-phase3-2026-11-24.adjudication.json](gates/approve-business-case-phase3-2026-11-24.adjudication.json) (`approve-business-case`, policy `91a33a4f-7d22-43e1-85ff-51026f350df0`)  
> **Inputs:** [Ideation-Document-Phase-3.md](Ideation-Document-Phase-3.md) (`HYP-mxc-023`..`030`, `HYP-mxc-019`, `HYP-mxc-021`), [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md), [OUTCOME-Phase-2-Actual-Outcomes.md](OUTCOME-Phase-2-Actual-Outcomes.md)  
> **Outputs:** Business-Case-Phase-3.md (Input to [Benefits-Statement-Phase-3.md](Benefits-Statement-Phase-3.md) and [Project-Charter-Phase-3.md](Project-Charter-Phase-3.md))

---

## 1. Executive Purpose & Investment Bound

Phase 2 (`PMP-BL-v2.0.0`) delivered 12/12 Epics (`204/204` Python contracts passing) plus live Windows 11 Lean Agent micro-VM verification (`win11-agent-lean.vhdx`, 9-second cold boot). Phase 3 builds on that verified engine to close the five 2026–2027 sovereign enterprise gaps defined in [Ideation-Document-Phase-3.md](Ideation-Document-Phase-3.md).

- **Investment Envelope & Capital Discipline:** Phase 3 carries forward the existing **USD 50,000** PM spending authority ceiling established in [Project-Charter-Phase-2.md](Project-Charter-Phase-2.md), with **\$0 new external capital** required for core software R&D (relying on existing Hyper-V workstation/server hardware and Rust/Python toolchains).
- **No Unvalidated Currency ROI Claimed:** Every operational value premise below is tied strictly to open `Formulated` hypotheses (`HYP-mxc-023`..`030`, `HYP-mxc-019`, `HYP-mxc-021`). Commercial client ROI, license revenue projections, and contracted ARR figures are **explicitly excluded** from this business case until validated by live customer PoCs.

---

## 2. Hypothesis-to-Value Premise Table (All Hypotheses `Formulated`)

Every target metric below represents an empirical hypothesis ceiling carried verbatim from [Ideation-Document-Phase-3.md](Ideation-Document-Phase-3.md); **none is claimed as already realized**.

| Hypothesis IDs | Operational Value Premise | Target Ceiling Under Test | Current Status |
|---|---|---|:---:|
| **`HYP-mxc-023`** | Host-side `mxc-sync` Git bundle transfer and sidecar credential proxy eliminate static PATs/API keys from guest RAM and disk over airgapped VMBus. | `0` static secret bytes inside guest; sidecar token injection `<= 5 ms` p95; `0` guest NICs attached. | `Formulated` |
| **`HYP-mxc-024`** | Protocol-aware Model Context Protocol (MCP) JSON-RPC inspection at the host VMBus boundary blocks unapproved servers, tools, and prompt-injected arguments. | `100%` block rate on unapproved MCP servers/tools/args; `<= 2 ms` p95 inspection overhead. | `Formulated` |
| **`HYP-mxc-025`** | Sub-500ms nested `.avhdx` snapshot forking (`wxc-exec --hyperv-op fork`), chunked VMBus streaming, and BOM-tolerant CLI remove parallel coding agent bottlenecks. | `<= 500 ms` per branch across 3–5 parallel forks (`0%` parent mutation); `>= 100 MB` chunked VMBus transfer; `100%` BOM-tolerant `wxc-exec` parsing. | `Formulated` |
| **`HYP-mxc-026`** | Append-only SHA-256 hash-chained session ledger plus `freeze-and-rollback` Hit-L kill switch satisfy EU AI Act Art. 19, DORA, and NIS2 evidence rules from one pipeline. | `100%` tamper detection across ledger chain; `>= 180-day` retention metadata + Entra Conditional Access claims; `<= 250 ms` `freeze-and-rollback`. | `Formulated` |
| **`HYP-mxc-027`** | Hyper-V Gen2 vTPM 2.0 PCR quotes and AMD SEV-SNP / Intel TDX attestation inside `PoolRegistrationGuard` gate secret release on hardware enclave integrity. | `100%` fail-closed rejection on tampered PCR quotes; `0 ms` post-admission hot dispatch overhead. | `Formulated` |
| **`HYP-mxc-028`** | Turnkey zero-cloud "MXC Embed" single-host installer, automated ISO-to-Lean CI factory, and 5-Act HIL self-test replace complex manual host setup for airgapped EU buyers. | `<= 15-minute` single-host offline install + 5-Act HIL pass (`0` outbound internet calls); reproducible CI SHA-256 digests feeding `ADR-012`. | `Formulated` |
| **`HYP-mxc-029`**, **`HYP-mxc-019`**, **`HYP-mxc-021`** | 640 MB paused floor, disposable trim bypass, CrossGen2 page normalization, RAM-disk/DAX differencing, eBPF/WFP TLS probes, NUMA pinning, and subsystem telemetry push density and wake frontiers. | `< 350 MB` effective host RAM (`>= 65%` shared pages); `<= 50 ms` RAM-disk/DAX `.avhdx` mount (`0` NVMe write bytes); `2–3 ms` faster TLS promotion; `0` remote NUMA pages; `100%` pre-dispatch subsystem checks. | `Formulated` |
| **`HYP-mxc-030`** | Optional Hyper-V `GPU-P` / DDA sandbox profile unlocks local ONNX/Ollama validation and visual Windows UI/RPA agents with clean session teardown. | `>= 85%` native bare-host GPU inference/rendering throughput; `0` cross-session GPU residue. | `Formulated` |

---

## 3. Business Alternatives Comparison

| Option | Capabilities & Compliance Posture | Why Rejected or Selected |
|---|---|---|
| **(A) Do Nothing — Stay at Phase 2 (`PMP-BL-v2.0.0`)** | Retains strong Hyper-V isolation and multi-tier standby pools, but leaves guests handling static API tokens if external tools are used, runs sequential coding branches, lacks a unified 6-month EU AI Act Art. 19 ledger, and requires manual host deployment scripts. | **Rejected:** Misses 2026–2027 market table stakes (Managed Secrets, MCP Firewall, parallel snapshot forking, turnkey on-prem packaging) ahead of the Dec 2, 2027 EU AI Act Annex III deadline. |
| **(B) Adopt Cloud-Hosted Linux Micro-VM SaaS (e.g., E2B Cloud / Modal)** | Fast managed Linux sandboxes with cloud APIs, but requires outbound cloud data egress and offers Linux-only runtimes rather than native Windows 11 Pro / Server 2025 execution (`win32`, COM+, WMI, GPO). | **Rejected:** Violates data-residency, airgap, and native Windows enterprise software requirements of regulated European buyers. |
| **(C) Static Credentials Inside Guest VMs + IP/Port Whitelists** | Reuses `ADR-005` IP/port egress rules while mounting PATs/API keys into the sandbox environment for developer/agent tools. | **Rejected:** A prompt-injected dependency or agent shell command inside the guest can read mounted tokens or invoke rogue tools over an allowed `:443` MCP endpoint ("rug-pull MCP"). |
| **(D) Recommended — MXC Phase 3 Sovereign Zero-Secret Fabric & "MXC Embed" Appliance** | Combines host-side secret injection, protocol-level MCP inspection, millisecond `.avhdx` branching, hash-chained EU compliance evidence + Hit-L kill switch, and a zero-cloud Windows appliance while keeping Phase 1–2 invariants (`ADR-001`..`013`) intact. | **Selected:** Delivers sovereign defense-in-depth and developer ergonomics within existing `USD 50,000` / `\$0` new external capital bounds. *Does not prove commercial ARR or bare-metal SEV-SNP/GPU availability on non-capable hosts.* |

---

## 4. Material Risk Register (Tied to Open `Formulated` Hypotheses)

| Risk ID | Risk Description | Linked Open Hypotheses | Mitigation & Boundary |
|---|---|---|---|
| **RISK-P3-01** | Host sidecar credential proxy and MCP JSON-RPC envelope parsing introduce tail latency under concurrent burst traffic. | `HYP-mxc-023`, `HYP-mxc-024` | Benchmark and fail contract gates if p95 sidecar overhead exceeds `5 ms` or MCP parser exceeds `2 ms`. |
| **RISK-P3-02** | Deep nested `.avhdx` checkpoint chains during 5-way parallel coding forks degrade random write I/O or complicate parent cleanup. | `HYP-mxc-025` | Cap branch nesting depth, track per-fork latency (`<= 500 ms`), and guarantee unconditional cleanup of unmerged child differencing chains. |
| **RISK-P3-03** | Hardware heterogeneity prevents Confidential VMs (AMD SEV-SNP / Intel TDX) or `GPU-P`/DDA from running on developer workstations lacking silicon support. | `HYP-mxc-027`, `HYP-mxc-030` | Implement explicit hardware capability probing and graceful profile gating so non-TEE / CPU-only hosts fall back safely without faking attestation. |
| **RISK-P3-04** | Kernel-level eBPF/WFP TLS packet filters and RAM-disk/DAX differencing tiers risk root-partition instability or unexpected host RAM consumption. | `HYP-mxc-029`, `HYP-mxc-019` | Keep user-space TLS SNI fallback active and enforce hard host RAM quotas (`ADR-013`) before admitting RAM-disk differencing mounts. |
| **RISK-P3-05** | Aggressive ~512–640 MB golden bake trimming strips memory needed at wake time, causing soft page-fault stalls or subsystem failures. | `HYP-mxc-029` | Pair trimmed bakes with automated WMI/COM+/Service/GPO differential telemetry verification prior to standby pool promotion. |
