---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Closing"
pmbok_process: "4.7 Close Project or Phase & Strategic Cognitive Feedback (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
refinement_id: "IR-PROP-MXC-Phase2-Closeout"
lifecycle_stage: "Stage 18 (Intent Refinement)"
governance_policy: "approve-intent-refinement"
readiness_audit_ref: "Audit-Register.md#AUDIT-007..009 + Stage 6/10 Gate Records"
disposition_type: "phase_handoff"
status: "Approved — Ready for Phase 3 Initiation"
refinesIntent: "docs/project-docs/Spark-Capture-Phase-3.md"
inputs:
  - "docs/project-docs/Project-Management-Plan-Phase-2.md"
  - "docs/project-docs/OUTCOME-Phase-2-Actual-Outcomes.md"
  - "docs/registers/Lessons-Learned-Register.md"
  - "docs/registers/Continuous-Improvement-Register.md"
  - "docs/registers/Project-Status-Register.md"
process: "Synthesize Phase 2 empirical outcomes, live Hyper-V fieldwork, and 2026 market intelligence into Phase 3 strategic intent (SPARK-v3)"
outputs:
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-2.md"
  - "docs/project-docs/Spark-Capture-Phase-3.md"
lineage:
  root_spark: "docs/project-docs/Spark-Capture.md"
  parent_refinement: "docs/project-docs/Intent-Refinement-Proposal.md"
  generational_index: 3
  immutable_core_invariants:
    - "ADR-001..006: Phase 1 Type-1 Hyper-V Isolation, Buffering Ingress, Golden Images, Paused RAM, Sterile .avhdx, Watermark Pools"
    - "ADR-008: Opt-In Auth-Gated Provisioning & TTL-Bounded Identity-Bound Leasing (ADR-002 path_only unchanged)"
    - "ADR-009: Multi-Tier Standby Pools (Hot <= 5ms, Warm <= 250ms, Cold 0.0 MB RAM)"
    - "ADR-010: Predictive Wake Interception & Time-Series Workload Forecasting"
    - "ADR-011: Hyper-V Host Memory Combining & COW Page Deduplication"
    - "ADR-012: Offline SLSA v1.0 Provenance, CycloneDX 1.5 SBOM & Fail-Closed PoolRegistrationGuard"
    - "ADR-013: Autonomous Fleet Economics, RAM Pressure Autotuner & Archetype Sizing Floors"
---

# Intent Refinement Proposal — MXC Hyper-V Phase 2 Closeout & Phase 3 Handoff

> **PMBOK 8 Process:** `4.7 Close Project or Phase & Strategic Cognitive Feedback (Phase 2)` (Closing)  
> **Governance Policy:** `approve-intent-refinement` | **Lifecycle Stage:** `Stage 18 (Intent Refinement)`  
> **Governing Baseline:** `PMP-BL-v2.0.0` | **Refinement ID:** `IR-PROP-MXC-Phase2-Closeout`  
> **Disposition Type:** `phase_handoff` | **Generational Index:** `3`  
> **Inputs:** [OUTCOME-Phase-2-Actual-Outcomes.md](OUTCOME-Phase-2-Actual-Outcomes.md), [Lessons-Learned-Register.md](../registers/Lessons-Learned-Register.md) (`LL-008`..`LL-013`), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md) (`IMP-MXC-001`..`031`)  
> **Outputs:** Intent-Refinement-Proposal-Phase-2.md, [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md)

---

## 1. Executive Evaluation Brief

Phase 2 (**Predictive Orchestration & Enterprise Execution Fabric**) has delivered **100% of its planned and expanded scope** under `PMP-BL-v2.0.0`. All **6 Phase 2 Epics (Epics 007..012)**—including the full Stage 6 decomposition and implementation of `ADR-012` (SLSA/SBOM Supply Chain), `ADR-013` (Autonomous Fleet Economics), and `ADR-008` (Auth-Gated & Identity-Bound Leasing)—are implemented, contract-verified (**204/204 Python contracts passing** + **83/83 Rust Hyper-V unit tests**), and backed by live Hyper-V silicon proof (`win11-agent-lean.vhdx` 9-second cold boot + 5-Act autonomous agent sandbox demo).

Phase 2 is hereby **formally closed**. This document executes the third-generation cybernetic return loop (Stage 18 $\rightarrow$ Stage 1), synthesizing **18 harvested improvements (`IMP-MXC-014`..`031`, plus remaining Phase 1/2 horizon items)** from live Hyper-V fieldwork and our November 2026 market scan (E2B Embed & Managed Secrets, Daytona/Modal GPU sandboxes, Microsoft Entra Agent ID & MCP Firewall, Confidential Micro-VMs, and EU AI Act Art. 19 / DORA / NIS2 unified audit trails) into **Phase 3 (`SPARK-MXC-Phase3-v3.0.0`)**.

---

## 2. Phase 2 Close Readiness Gate Checklist (Invariant 7)

- [x] **Work Packages Closed:** 100% of Phase 2 Work Packages (Epics 007..012; WBS 8.0–12.0 + WBS 3.4/13.0) are `Complete` on `feat/hyperv-v2-rebased`.
- [x] **Verification Passed:** **204/204 Python contract tests** passing (`pytest tests -q`) with zero regressions, plus **83/83 Rust Hyper-V unit tests** and live 5-Act Hyper-V silicon verification.
- [x] **Lessons Operationalized:** `LL-008` through `LL-013` recorded in [Lessons-Learned-Register.md](../registers/Lessons-Learned-Register.md) and propagated to Tier 2 component skills (`.claude/skills/`).
- [x] **Improvement Inventory Reconciled:** All 31 improvements (`IMP-MXC-001`..`031`) reconciled in [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md) (10 Delivered, 2 Partially Delivered, 19 Rolled/Queued into Phase 3).

---

## 3. Continuous Improvement Synthesis Rolled into Phase 3 (`IMP-MXC-014`..`031` + Open Horizons)

| Phase 3 Pillar | Harvested Improvement IDs | Strategic Objective |
|---|---|---|
| **Pillar 1: Zero-Secret Agentic Execution & Protocol Security** | `IMP-MXC-017` (`mxc-sync`), `IMP-MXC-024` (Credential-Injecting Sidecar Proxy), `IMP-MXC-026` (Protocol-Aware MCP Firewall PEP) | Guarantee zero static API keys, GitHub PATs, or unvetted MCP tool calls inside any guest sandbox—even under full prompt injection. |
| **Pillar 2: Millisecond Snapshot Forking & Ephemeral IDE Workers** | `IMP-MXC-027` (`wxc-exec --hyperv-op fork`), `IMP-MXC-021` (Chunked VMBus Streaming), `IMP-MXC-022` (Cursor/IDE Worker Profile), `IMP-MXC-019` (BOM-Tolerant `wxc-exec` CLI) | Unlock parallel multi-hypothesis coding agent branching, multi-MB VMBus workspace hydration, and frictionless Rust CLI / IDE integration. |
| **Pillar 3: EU AI Act / DORA / NIS2 Evidence Ledger & Confidential Attestation** | `IMP-MXC-030` (Unified Evidence Ledger & Hit-L Kill Switch), `IMP-MXC-028` (vTPM 2.0 & SEV-SNP/TDX Attestation), `IMP-MXC-025` (Entra Conditional Access Hook) | Deliver tamper-evident 6-month regulatory audit trails (EU AI Act Art. 19), instant `freeze-and-rollback` kill switches, and hardware enclave trust. |
| **Pillar 4: Turnkey Sovereign Appliance ("MXC Embed") & Image Factory** | `IMP-MXC-031` (MXC Embed Single-Host Installer), `IMP-MXC-018` (Automated ISO-to-Lean CI Image Factory), `IMP-MXC-023` (HIL 5-Act Release Gate) | Counter E2B Embed for regulated EU banks, healthcare, and public-sector buyers with a zero-cloud Windows 11 Pro / Server 2025 appliance. |
| **Pillar 5: Ultra-Density Hardware Acceleration & Kernel-Bypass Frontiers** | `IMP-MXC-001` (Subsystem Telemetry), `IMP-MXC-005` (Discard Trim Bypass), `IMP-MXC-006` (640 MB Paused Floor), `IMP-MXC-012` (RAM-Disk/DAX Differencing), `IMP-MXC-014`/`015` (eBPF/WFP TLS Probes), `IMP-MXC-016` (CrossGen2 ASLR Normalization), `IMP-MXC-029` (`GPU-P`/DDA Sandboxes) | Push host density, sub-millisecond kernel wake, and GPU-accelerated local AI / visual RPA sandboxes beyond Phase 2 ceilings. |

---

## 4. Closed-Loop Intent Handoff (Primary Catalyst for Phase 3)

**Primary Catalyst for Phase 3:** [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md) (`SPARK-MXC-Phase3-v3.0.0`)

This proposal closes **Phase 2 (`PMP-BL-v2.0.0`)** and authorizes the initiation of **Phase 3 (Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance)** under candidate baseline **`PMP-BL-v3.0.0-candidate`**.
