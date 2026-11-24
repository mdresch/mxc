---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation (Phase 3)"
lifecycle_stage: "Stage 1 (Intent) & Stage 3 (Hypothesis)"
governance_policy: "approve-ideation & classify-hypothesis-status"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-3.md"
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-2.md"
  - "docs/project-docs/OUTCOME-Phase-2-Actual-Outcomes.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Formulate empirical Phase 3 hypotheses with measurable falsification criteria"
outputs:
  - "docs/project-docs/Ideation-Document-Phase-3.md"
status: "Approved (approve-ideation 2026-11-24) — Hypotheses Formulated"
---

# Ideation Document — Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `Pre-Project / Design Assumption Formulation (Phase 3)` (Initiating)  
> **Governance Policy:** `approve-ideation & classify-hypothesis-status` | **Lifecycle Stage:** `Stage 1 (Intent) & Stage 3 (Hypothesis)`  
> **Inputs:** [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md), [Intent-Refinement-Proposal-Phase-2.md](Intent-Refinement-Proposal-Phase-2.md), [OUTCOME-Phase-2-Actual-Outcomes.md](OUTCOME-Phase-2-Actual-Outcomes.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md)  
> **Process:** Formulate empirical Phase 3 hypotheses with measurable falsification criteria  
> **Outputs:** Ideation-Document-Phase-3.md, Hypotheses HYP-mxc-023 through HYP-mxc-030 (plus Carried-Forward HYP-mxc-019, HYP-mxc-021)  
> **Gate Approval Record:** [approve-ideation-phase3-2026-11-24.adjudication.json](gates/approve-ideation-phase3-2026-11-24.adjudication.json) (`approve-ideation` resolved `2026-11-24`, policy `dcdf7865-7d06-40cd-b282-18c01c3aaed0`)

---

## 1. Executive Summary & Strategic Motivation

Phases 1 and 2 (`PMP-BL-v1.0.0` and `PMP-BL-v2.0.0`, 12/12 Epics complete, 204 Python contracts passing, plus live Hyper-V verification of `win11-agent-lean.vhdx` booting in 9 seconds) decisively proved that hardware-isolated Type-1 Hyper-V Generation 2 micro-VMs can match container responsiveness without shared-kernel exposure.

However, the late-2026 autonomous AI agent infrastructure market (E2B Embed and Managed Secrets, Daytona and Modal GPU sandboxes, Microsoft Entra Agent ID and Global Secure Access MCP Firewall, Confidential Micro-VMs, and EU regulatory enforcement across the **EU AI Act Annex III** compliance deadline of **December 2, 2027** per **Regulation (EU) 2026/1744**, **DORA**, and **NIS2**) introduces a third-generation operational challenge that shared or credential-holding sandboxes cannot resolve.

Phase 3 advances MXC from a predictive Hyper-V pool fabric into a **Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance**, anchored by [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md) and gated under `approve-ideation`.

---

## 2. Operational Problem Definition (The 2027 Sovereign Agentic Execution Quintet)

Rather than collapsing prematurely into fixed pool counts, pricing tiers, or Charter schedules, Phase 3 Stage 1 frames five distinct architectural and operational tensions observed in fieldwork and 2026 market intelligence:

1. **Credential Seppuku vs. Secret Exposure inside Agent Sandboxes (`IMP-MXC-017`, `024`, `026`):** Autonomous coding and enterprise agents require authenticated Git access, external APIs, and Model Context Protocol (MCP) tools, yet any static API key or PAT placed inside a guest VM can be exfiltrated via prompt injection, malicious dependencies, or guest memory inspection.
2. **Sequential Sandbox Bottlenecks vs. Parallel Coding Hypotheses & CLI Ergonomics (`IMP-MXC-019`, `021`, `022`, `027`):** Modern coding agents explore multiple competing fixes concurrently from a warm repository checkpoint, whereas single-branch sandboxes, `cmd.exe` 8 KB payload limits over VMBus, and Windows PowerShell UTF-8 BOM friction stall parallel agent iteration and IDE worker orchestration.
3. **Siloed Compliance Logs vs. Unified EU AI Act / DORA / NIS2 Evidence & Hardware Trust (`IMP-MXC-025`, `028`, `030`):** Regulated enterprises face fragmented audit trails across runtime execution, IAM identity, and security monitoring, lacking append-only retention ($\ge 6$ months under EU AI Act Art. 19), instant Hit-L `freeze-and-rollback` kill switches, and cryptographic boot attestation.
4. **Cloud-Hosted SaaS Rejection vs. Turnkey Airgapped On-Premises Appliances (`IMP-MXC-018`, `023`, `031`):** European banks, healthcare providers, and public-sector buyers increasingly mandate sovereign, zero-cloud single-host deployment ("MXC Embed") with reproducible CI image builds and automated Hardware-in-the-Loop verification.
5. **Memory Density Ceilings, NVMe Wear & Missing GPU Acceleration (`IMP-MXC-001`, `005`, `006`, `012`, `014`, `015`, `016`, `029`):** High-churn ephemeral micro-VMs remain bounded by ~1 GB paused floors, NVMe `.avhdx` write amplification, user-space TLS inspection hops, unnormalized ASLR page layouts, and CPU-only execution when agents need local ONNX/Ollama validation or GPU-backed visual RPA.

`classify-hypothesis-status` (`agent-learning-governance`) has not been run for Phase 3. Every hypothesis below remains strictly `Formulated` until live Phase 3 outcomes are empirically observed.

---

## 3. Phase 3 Formulated Hypotheses (`HYP-mxc-023` .. `HYP-mxc-030` + Carried-Forward Phase 2 Horizons)

### HYP-mxc-023: Zero-Secret Host-Side Git (`mxc-sync`) & Credential-Injecting Sidecar Proxy
- **Source Improvements:** `IMP-MXC-017`, `IMP-MXC-024`
- **Statement:** Moving Git bundle transfer (`mxc-sync`) and outbound API/MCP credential injection into a host-side sidecar proxy over airgapped VMBus eliminates 100% of static secrets inside the guest OS while maintaining interactive tool latency.
- **Empirical Evaluation Criteria:**
  1. Scanned guest filesystem and environment contain **0 bytes** of static GitHub PATs, SSH keys, or upstream API tokens during live repository workflows.
  2. Host-side proxy credential injection adds **$\le 5\text{ ms}$** p95 overhead per outbound call.
  3. Complete round-trip patch extraction from guest to host succeeds over VMBus with **0** guest network adapters attached.
- **Status:** Formulated

### HYP-mxc-024: Protocol-Aware MCP Firewall Enforcement over VMBus
- **Source Improvements:** `IMP-MXC-026`
- **Statement:** Inspecting Model Context Protocol (MCP) JSON-RPC envelopes at the host VMBus boundary enables deterministic server, tool, prompt, and argument policy enforcement beyond legacy IP/port whitelists.
- **Empirical Evaluation Criteria:**
  1. Unapproved MCP servers, rug-pull tool mutations, and disallowed argument patterns fail closed with **100%** block accuracy.
  2. Approved tool inspection latency overhead remains **$\le 2\text{ ms}$** p95 per tool call.
- **Status:** Formulated

### HYP-mxc-025: Sub-500ms Parallel Snapshot Forking, Chunked VMBus Streaming & Ergonomic CLI
- **Source Improvements:** `IMP-MXC-019`, `IMP-MXC-021`, `IMP-MXC-022`, `IMP-MXC-027`
- **Statement:** Adding nested `.avhdx` snapshot-and-fork (`wxc-exec --hyperv-op fork`), chunked binary VMBus framing, BOM-tolerant JSON parsing, and standardized IDE worker profiles enables concurrent multi-hypothesis agent execution without PowerShell or 8 KB shell limits.
- **Empirical Evaluation Criteria:**
  1. Forking 3–5 parallel child sandboxes from a warm repository checkpoint completes in **$\le 500\text{ ms}$** per branch with **0%** parent mutation.
  2. Native chunked `copy-file` / `exec` streams **$\ge 100\text{ MB}$** workspace bundles reliably across VMBus with bit-exact SHA-256 integrity.
  3. `wxc-exec` parses UTF-8 with BOM (`\u{FEFF}`) manifests and CLI flag overrides with **100%** acceptance and **0** false parse errors.
- **Status:** Formulated

### HYP-mxc-026: Tamper-Evident EU AI Act / DORA / NIS2 Unified Evidence Ledger & Hit-L Kill Switch
- **Source Improvements:** `IMP-MXC-030`, `IMP-MXC-025`
- **Statement:** Recording every session dispatch, Entra Conditional Access identity context, VMBus command, file diff, and checkpoint rollback in an append-only SHA-256 hash-chained ledger paired with a `freeze-and-rollback` kill switch provides single-pipeline compliance evidence for EU AI Act Art. 19, DORA, and NIS2.
- **Empirical Evaluation Criteria:**
  1. Tampering with any historical ledger entry invalidates the cryptographic hash chain with **100%** detection during audit verification.
  2. Ledger retention metadata enforces a **$\ge 180\text{-day}$** (6-month minimum) retention floor per EU AI Act Art. 19 alongside bound `Entra Agent ID` Conditional Access attributes.
  3. Invoking `freeze-and-rollback` halts active guest execution and restores clean state in **$\le 250\text{ ms}$**.
- **Status:** Formulated

### HYP-mxc-027: Hardware-Rooted vTPM 2.0 & Confidential VM (SEV-SNP / TDX) Remote Attestation
- **Source Improvements:** `IMP-MXC-028`
- **Statement:** Integrating Hyper-V Gen2 vTPM 2.0 PCR measurements and Confidential VM (AMD SEV-SNP / Intel TDX) attestation quotes into `PoolRegistrationGuard` prevents compromised enclaves from unlocking host-proxy secrets with zero hot-dispatch runtime penalty.
- **Empirical Evaluation Criteria:**
  1. Tampered boot/PCR quotes fail closed before any host-proxy secret or private repository bundle is released (**100%** rejection rate).
  2. Post-admission hot/warm dispatch preserves **0 ms** additional cryptographic overhead on cached attested guests.
- **Status:** Formulated

### HYP-mxc-028: Turnkey Zero-Cloud "MXC Embed" Sovereign Appliance & Reproducible ISO Factory
- **Source Improvements:** `IMP-MXC-031`, `IMP-MXC-018`, `IMP-MXC-023`
- **Statement:** Packaging `wxc-exec`, an automated ISO-to-Lean image CI factory with automatic SHA-256 registry generation, and a gated 5-Act Hardware-in-the-Loop verification suite delivers an offline-capable sovereign appliance installable on a single Windows 11 Pro or Server 2025 host.
- **Empirical Evaluation Criteria:**
  1. Clean single-host installation plus unattended 5-Act self-test finishes in **$\le 15\text{ minutes}$** with **0** outbound internet calls.
  2. CI ISO-to-Lean build outputs reproducible image digests and SLSA provenance bundles compatible with `ADR-012` without manual hash edits.
- **Status:** Formulated

### HYP-mxc-029: Ultra-Lean 640 MB Paused Floor, CrossGen2 Page Alignment & eBPF/WFP Kernel TLS Wake
- **Source Improvements:** `IMP-MXC-001`, `IMP-MXC-005`, `IMP-MXC-006`, `IMP-MXC-014`, `IMP-MXC-015`, `IMP-MXC-016`
- **Statement:** Combining a ~512–640 MB trimmed golden bake floor, disposable in-session trim bypass, CrossGen2 ASLR base normalization, root-partition eBPF/WFP TLS sniffing, and automated subsystem differential telemetry compresses effective per-guest host RAM below 350 MB while cutting wake/teardown overhead.
- **Empirical Evaluation Criteria:**
  1. Hyper-V Memory Combining shared page ratio increases to **$\ge 65\%$**, driving effective host RAM below **350 MB** per paused guest.
  2. Kernel-level TLS SNI snooping reduces predictive tier promotion latency by **2–3 ms** while in-session trim bypass cuts disposable teardown overhead by **$\ge 50\text{ ms}$**.
  3. Automated WMI/COM+/Service/GPO telemetry validates **100%** of guest subsystem prerequisites prior to session dispatch.
- **Status:** Formulated

### HYP-mxc-030: GPU-Partitioned (`GPU-P` / DDA) Agent Sandbox Acceleration
- **Source Improvements:** `IMP-MXC-029`
- **Statement:** Adding an optional Hyper-V `GPU-P` / Discrete Device Assignment (DDA) sandbox profile enables hardware-accelerated local ONNX/Ollama validation and Windows visual UI automation while preserving sterile `.avhdx` reset.
- **Empirical Evaluation Criteria:**
  1. Partitioned guest workloads sustain **$\ge 85\%$** of bare-host single-tenant GPU inference/rendering throughput.
  2. Session teardown clears ephemeral GPU allocations and `.avhdx` state with **0** cross-session residue.
- **Status:** Formulated

### Carried-Forward Phase 2 Horizon Hypotheses (Still `Formulated`)

- **HYP-mxc-019 (Pure In-Memory Ephemeral RAM-Disk / DAX Differencing Layers — `IMP-MXC-012`):** Backing `.avhdx` transient differencing disks with host RAM-disk or DAX memory achieves **$\le 50\text{ ms}$** mount/teardown and **0 bytes** host NVMe write amplification. **Status:** Formulated.
- **HYP-mxc-021 (NUMA-Aware Micro-VM Placement & Core Affinity):** Pinning standby VM memory and vCPU scheduling to local host NUMA nodes achieves **0** remote physical pages (`\Hyper-V VM Vid Partition\Remote Physical Pages == 0`) and reduces resume latency variance by **$\ge 20\%$**. **Status:** Formulated.

---

## 4. Grounded Scope Boundary (Stage 1 Deferrals)

This Stage 1 artifact stays strictly at strategic intent, problem framing, and falsifiable hypotheses:
- **Deferred to Stage 2:** Execution timeline, named sponsorship authority, WBS milestone commitments, and resource ceilings (`Project-Charter-Phase-3.md` / `approve-charter`).
- **Deferred to Stage 4:** Commercial ROI, FinOps pricing brackets, and quantified benefit targets (`Business-Case` / `Benefits-Statement-Phase-3.md` / `approve-business-case`).
- **Deferred to Stages 5–6:** Topic Pillars (`TP-12+`), architectural trade-offs (`ADR-014+`), business rules (`BRD-013+`), functional interfaces (`FDD-013+`), and sprint user stories (`Epics 013–017`).
