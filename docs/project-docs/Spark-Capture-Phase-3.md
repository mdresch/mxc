---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification (Phase 3)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
spark_id: "SPARK-MXC-Phase3-v3.0.0"
inputs:
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-2.md"
  - "docs/project-docs/OUTCOME-Phase-2-Actual-Outcomes.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Capture Phase 3 strategic catalysts for Sovereign Zero-Secret Agentic Execution, Millisecond Snapshot Forking, EU Compliance Evidence, and MXC Embed Appliance"
outputs:
  - "docs/project-docs/Spark-Capture-Phase-3.md"
status: "Approved"
---

# Spark Capture — Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification (Phase 3)` (Initiating)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Inputs:** [Intent-Refinement-Proposal-Phase-2.md](Intent-Refinement-Proposal-Phase-2.md), [OUTCOME-Phase-2-Actual-Outcomes.md](OUTCOME-Phase-2-Actual-Outcomes.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md)  
> **Outputs:** Spark-Capture-Phase-3.md

**Date:** 2026-11-24  
**Captured by:** Menno Drescher  
**Project Name:** MXC Phase 3 — Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance  
**Preceding Lineage:** Phase 1 (`PMP-BL-v1.0.0`, Epics 001..006) $\rightarrow$ Phase 2 (`PMP-BL-v2.0.0`, Epics 007..012 Complete)

---

## 1. Problem Statement & 2026–2027 Market Catalyst

With Phases 1 and 2 complete (`12/12` Epics, `204` Python contract tests + `83` Rust Hyper-V unit tests, `9s` stripped Win11 Lean Agent boot), MXC has proven hardware-isolated micro-VM execution at container speed. The late-2026 AI agent sandbox market (E2B Embed & Managed Secrets, Daytona/Modal GPU sandboxes, Microsoft Entra Agent ID & Global Secure Access MCP Firewall, Confidential Micro-VMs, and EU AI Act Art. 19 / DORA / NIS2 enforcement ahead of the **December 2, 2027** Annex III deadline per Regulation (EU) 2026/1744) defines five decisive Phase 3 differentiators:

1. **Credential Seppuku ("Zero-Secret Guest"):** Autonomous coding and enterprise agents must never see static API keys, GitHub PATs, or production tokens inside the guest VM—all secrets must be injected at the host-side VMBus/proxy boundary and gated by a protocol-aware MCP Firewall.
2. **Parallel Multi-Hypothesis Coding Workflows:** Modern AI coding agents fork 3–5 sandbox branches from a single warm repository snapshot simultaneously to test competing fixes in parallel, requiring millisecond snapshot-and-fork (`wxc-exec --hyperv-op fork`) and chunked VMBus streaming.
3. **Unified EU Regulatory Evidence & Hit-L Kill Switches:** Regulated EU buyers need one append-only, hash-chained execution ledger (6+ months retention) satisfying EU AI Act Art. 19, DORA, and NIS2 simultaneously, paired with an instant `freeze-and-rollback` kill switch and hardware vTPM/TEE attestation.
4. **Turnkey On-Premises Sovereign Appliance ("MXC Embed"):** Regulated banks, healthcare providers, and government agencies refuse cloud-hosted sandboxes; a zero-cloud single-host Windows 11 Pro / Server 2025 installer with an automated ISO-to-Lean CI factory directly counters E2B Embed.
5. **Next-Frontier Density & GPU Agent Sandboxes:** Pushing paused standby footprints to ~640 MB, eliminating NVMe wear via RAM-disk/DAX differencing, adding eBPF/WFP kernel TLS probes, and enabling `GPU-P`/DDA tiers for local ONNX/Ollama validation and visual RPA agents.

---

## 2. Phase 3 Candidate Work Breakdown Structure (`PMP-BL-v3.0.0-candidate`)

| WBS | Candidate Epic | Harvested Improvements | Primary Commercial & Technical Outcome |
|---|---|---|---|
| **WBS 14.0** | **Epic 013 — Zero-Secret Agentic Execution & MCP Protocol Firewall** | `IMP-MXC-017`, `IMP-MXC-024`, `IMP-MXC-026` | Host-side `mxc-sync` git bundles, outbound credential-injecting sidecar proxy, and protocol-aware MCP tool firewall over VMBus. |
| **WBS 15.0** | **Epic 014 — Millisecond Snapshot Forking, VMBus Streaming & IDE Workers** | `IMP-MXC-027`, `IMP-MXC-021`, `IMP-MXC-022`, `IMP-MXC-019` | `wxc-exec --hyperv-op fork`, native chunked VMBus payload streaming, BOM-tolerant Rust CLI ergonomics, and standardized Cursor/IDE worker profiles. |
| **WBS 16.0** | **Epic 015 — Unified EU AI Act / DORA / NIS2 Evidence Ledger & Confidential Enclaves** | `IMP-MXC-030`, `IMP-MXC-028`, `IMP-MXC-025` | Tamper-evident hash-chained session audit ledger (`>= 6 mo` retention), `freeze-and-rollback` Hit-L kill switch, vTPM 2.0 / SEV-SNP / TDX attestation, and Entra Conditional Access hooks. |
| **WBS 17.0** | **Epic 016 — "MXC Embed" Sovereign Appliance & Automated Image Factory** | `IMP-MXC-031`, `IMP-MXC-018`, `IMP-MXC-023` | Single-host zero-cloud Windows installer, CI ISO-to-Lean image factory feeding Epic 010 SLSA signing, and gated HIL 5-Act release check. |
| **WBS 18.0** | **Epic 017 — Ultra-Density Hardware Acceleration & Kernel-Bypass Frontiers** | `IMP-MXC-001`, `005`, `006`, `012`, `014`, `015`, `016`, `029` | 640 MB paused bake floor, RAM-disk/DAX differencing, eBPF/WFP root-partition TLS probes, CrossGen2 ASLR normalization, differential telemetry, and `GPU-P`/DDA agent sandboxes. |

---

## 3. Immediate Next Step (Phase 3 Stage 1 Gate)

Submit `SPARK-MXC-Phase3-v3.0.0` for sponsor approval under `approve-ideation` and select the first Phase 3 Wave (recommended Wave 1: **Epic 013 Zero-Secret + Epic 014 Snapshot Forking / CLI Ergonomics + Epic 015 EU Evidence Ledger**).

---

## 4. Gate Approval Record

- **Gate:** `approve-ideation` (`approve_ideation`, policy `dcdf7865-7d06-40cd-b282-18c01c3aaed0`) — **Approved (`2026-11-24`)**
- **Adjudication Record:** [approve-ideation-phase3-2026-11-24.adjudication.json](gates/approve-ideation-phase3-2026-11-24.adjudication.json)
- **Ideation Companion:** [Ideation-Document-Phase-3.md](Ideation-Document-Phase-3.md) (`HYP-mxc-023`..`030` + `HYP-mxc-019`, `HYP-mxc-021` `Formulated`)
