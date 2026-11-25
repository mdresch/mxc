---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Architectural Strategy Formulation (Phase 3)"
lifecycle_stage: "Stage 5 (Pillars & Architecture)"
governance_policy: "approve-adr"
pmp_baseline: "PMP-BL-v3.0.0"
status: "Approved"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/project-docs/Business-Case-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Define Phase 3 topic pillars (TP-12 through TP-16), map all 21 open improvements, and establish end-to-end Stage 6 traceability to ADRs, BRDs, FDDs, and Epics"
outputs:
  - "docs/07-architecture/PILLARS-Phase-3.md"
---

# Pillars Exercise — Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 5 (Pillars & Architecture)`  
> **Governing Baseline:** `PMP-BL-v3.0.0` | **Status:** Approved (2026-11-24) (`2026-11-24`)  
> **Inputs:** [Project-Charter-Phase-3.md](../project-docs/Project-Charter-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md), [Business-Case-Phase-3.md](../project-docs/Business-Case-Phase-3.md), [Benefits-Statement-Phase-3.md](../project-docs/Benefits-Statement-Phase-3.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md)  
> **Outputs:** PILLARS-Phase-3.md, Full-Traceability Architecture Matrix (Phase 3)

---

## 1. Executive Purpose & Scope

Phases 1 and 2 (`PMP-BL-v1.0.0` and `PMP-BL-v2.0.0`) established the 12-Epic Type-1 Hyper-V micro-VM core, delivering 10 of 31 continuous improvements (`IMP-MXC-002`, `003`, `004`, `007`, `008`, `009`, `010`, `011`, `013`, `020`).

Phase 3 structures the **21 remaining open and partially delivered improvements** (`IMP-MXC-001`, `005`, `006`, `012`, `014`..`019`, `021`..`031`) alongside carried-forward horizon hypotheses `HYP-mxc-019` and `HYP-mxc-021` into five Topic Pillars (**`TP-12` through `TP-16`**), decomposed into `ADR-014..018`, `BRD-013..017`, `FDD-013..017`, and `Epics 013–017` (`WBS 14.0–18.0`).

---

## 2. Phase 3 Topic Pillars & Architectural Coverage

### Topic Pillar 12: `TP-12` Zero-Secret Agentic Execution & MCP Protocol Containment
- **Domain Focus:** Airgapped credential isolation and application-protocol filtering for autonomous agents.
- **Key Architectural Responsibilities:**
  - Host-side zero-secret git bundle sync (`mxc-sync`) with zero GitHub PATs/SSH keys in guests (`IMP-MXC-017`).
  - Host-side outbound credential-injecting sidecar proxy keeping static secrets out of guest RAM/disk (`IMP-MXC-024`).
  - Protocol-aware Model Context Protocol (MCP) JSON-RPC Firewall Policy Enforcement Point (`IMP-MXC-026`).
- **Governing Chain:** [ADR-014](ADR-014-zero-secret-sidecar-and-mcp-firewall.md) $\rightarrow$ [BRD-013](../project-docs/Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md) $\rightarrow$ [FDD-013](../project-docs/Functional-Design/FDD-013-zero-secret-sidecar-and-mcp-firewall.md) $\rightarrow$ [Epic 013](../user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md) (`WBS 14.0` · `HYP-mxc-023`, `024` · `BEN-19`)

### Topic Pillar 13: `TP-13` Parallel Snapshot Branching, Chunked VMBus & Agentic CLI/IDE Ergonomics
- **Domain Focus:** Multi-hypothesis coding agent throughput, reliable multi-MB VMBus transport, and IDE integration.
- **Key Architectural Responsibilities:**
  - Millisecond nested `.avhdx` + checkpoint branching (`wxc-exec --hyperv-op fork`) (`IMP-MXC-027`).
  - Native chunked binary VMBus streaming eliminating `cmd.exe` 8 KB limits (`IMP-MXC-021`).
  - UTF-8 BOM-tolerant manifest parsing and flag precedence in `wxc-exec` (`IMP-MXC-019`).
  - Standardized declarative ephemeral IDE worker profiles for Cursor, Antigravity, and Claude Code (`IMP-MXC-022`).
- **Governing Chain:** [ADR-015](ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) $\rightarrow$ [BRD-014](../project-docs/Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) $\rightarrow$ [FDD-014](../project-docs/Functional-Design/FDD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) $\rightarrow$ [Epic 014](../user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) (`WBS 15.0` · `HYP-mxc-025` · `BEN-20`)

### Topic Pillar 14: `TP-14` Unified EU Regulatory Evidence Ledger & Hardware Enclave Trust
- **Domain Focus:** Cross-regulation tamper-evident auditability, operator circuit breakers, Entra Conditional Access, and hardware roots of trust.
- **Key Architectural Responsibilities:**
  - Append-only SHA-256 hash-chained Evidence Ledger (`>= 180-day` EU AI Act Art. 19 retention + DORA/NIS2 telemetry) and `freeze-and-rollback` Hit-L kill switch (`IMP-MXC-030`).
  - Microsoft Entra Conditional Access hook extending `ADR-008` / `IMP-MXC-025` prior to VM lease and secret injection (`IMP-MXC-025`).
  - Hyper-V Gen2 vTPM 2.0 and AMD SEV-SNP / Intel TDX Confidential VM attestation inside `PoolRegistrationGuard` (`IMP-MXC-028`).
- **Governing Chain:** [ADR-016](ADR-016-eu-evidence-ledger-and-confidential-attestation.md) $\rightarrow$ [BRD-015](../project-docs/Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md) $\rightarrow$ [FDD-015](../project-docs/Functional-Design/FDD-015-eu-evidence-ledger-and-confidential-attestation.md) $\rightarrow$ [Epic 015](../user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md) (`WBS 16.0` · `HYP-mxc-026`, `027` · `BEN-21`, `BEN-22`)

### Topic Pillar 15: `TP-15` Turnkey Sovereign On-Premises Appliance ("MXC Embed") & Reproducible Image Factory
- **Domain Focus:** Zero-cloud single-host sovereign packaging, CI image fabrication, and gated Hardware-in-the-Loop proof.
- **Key Architectural Responsibilities:**
  - Parameterized ISO-to-Lean Agent CI factory with automatic SHA-256 registry updates feeding `ADR-012` SLSA signing (`IMP-MXC-018`).
  - Single-host Windows 11 Pro / Server 2025 airgapped appliance installer ("MXC Embed") (`IMP-MXC-031`).
  - Gated 5-Act Hardware-in-the-Loop (HIL) release verification & executive demo harness (`IMP-MXC-023`).
- **Governing Chain:** [ADR-017](ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) $\rightarrow$ [BRD-016](../project-docs/Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md) $\rightarrow$ [FDD-016](../project-docs/Functional-Design/FDD-016-mxc-embed-sovereign-appliance-and-image-factory.md) $\rightarrow$ [Epic 016](../user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md) (`WBS 17.0` · `HYP-mxc-028` · `BEN-23`)

### Topic Pillar 16: `TP-16` Next-Frontier Fleet Density, Zero-Wear Ephemeral I/O & GPU Agent Acceleration
- **Domain Focus:** Pushing standby density, storage/wake latency, subsystem health verification, and local AI/visual GPU acceleration beyond Phase 2 ceilings.
- **Key Architectural Responsibilities:**
  - ~512–640 MB paused floor (`IMP-MXC-006`), disposable trim bypass (`IMP-MXC-005`), CrossGen2 deterministic ASLR page normalization (`IMP-MXC-016`), and local NUMA pinning (`HYP-mxc-021`).
  - Pure in-memory RAM-disk / DAX `.avhdx` differencing (`IMP-MXC-012` / `HYP-mxc-019`) plus root-partition eBPF/WFP TLS probes and continuous neural shift forecaster (`IMP-MXC-014`, `015`).
  - Automated WMI/COM+/Service/GPO differential telemetry matrix (`IMP-MXC-001`) and optional `GPU-P`/DDA agent sandboxes (`IMP-MXC-029`).
- **Governing Chain:** [ADR-018](ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) $\rightarrow$ [BRD-017](../project-docs/Business-Requirements/BRD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) $\rightarrow$ [FDD-017](../project-docs/Functional-Design/FDD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) $\rightarrow$ [Epic 017](../user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) (`WBS 18.0` · `HYP-mxc-029`, `030`, `019`, `021` · `BEN-24`)

---

## 3. End-to-End Phase 3 Traceability Matrix

| Pillar | ADR | BRD | FDD | Epic | WBS | Target Status |
|---|---|---|---|---|:---:|---|
| **`TP-12`** | [ADR-014](ADR-014-zero-secret-sidecar-and-mcp-firewall.md) | [BRD-013](../project-docs/Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md) | [FDD-013](../project-docs/Functional-Design/FDD-013-zero-secret-sidecar-and-mcp-firewall.md) | [Epic 013](../user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md) | 14.0 | Approved — Ready for Implementation |
| **`TP-13`** | [ADR-015](ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | [BRD-014](../project-docs/Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) | [FDD-014](../project-docs/Functional-Design/FDD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) | [Epic 014](../user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) | 15.0 | Approved — Ready for Implementation |
| **`TP-14`** | [ADR-016](ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | [BRD-015](../project-docs/Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md) | [FDD-015](../project-docs/Functional-Design/FDD-015-eu-evidence-ledger-and-confidential-attestation.md) | [Epic 015](../user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md) | 16.0 | Approved — Ready for Implementation |
| **`TP-15`** | [ADR-017](ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | [BRD-016](../project-docs/Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md) | [FDD-016](../project-docs/Functional-Design/FDD-016-mxc-embed-sovereign-appliance-and-image-factory.md) | [Epic 016](../user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md) | 17.0 | Approved — Ready for Implementation |
| **`TP-16`** | [ADR-018](ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | [BRD-017](../project-docs/Business-Requirements/BRD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | [FDD-017](../project-docs/Functional-Design/FDD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | [Epic 017](../user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | 18.0 | Approved — Ready for Implementation |

---

## 4. Complete 21-of-21 Open Improvement Accounting Table

All 21 open or partially delivered entries from [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md) map deterministically into Phase 3 (`10` others were delivered in Epics 007–011 = `31/31` total):

| # | Improvement ID | Improvement Title | Pillar | ADR | BRD / FDD | Epic & Story |
|:---:|---|---|---|:---:|:---:|---|
| 1 | `IMP-MXC-017` | Zero-Secret Host-Side Git Bundle / VMBus Sync (`mxc-sync`) | `TP-12` | `ADR-014` | `BRD-013` / `FDD-013` | Epic 013 — Story 13.1 |
| 2 | `IMP-MXC-024` | Host-Side Credential-Injecting Sidecar Proxy | `TP-12` | `ADR-014` | `BRD-013` / `FDD-013` | Epic 013 — Story 13.1 |
| 3 | `IMP-MXC-026` | Protocol-Aware MCP Firewall & Tool-Call PEP | `TP-12` | `ADR-014` | `BRD-013` / `FDD-013` | Epic 013 — Story 13.2 |
| 4 | `IMP-MXC-027` | Millisecond Snapshot Branching & Parallel Hypothesis Forking | `TP-13` | `ADR-015` | `BRD-014` / `FDD-014` | Epic 014 — Story 14.1 |
| 5 | `IMP-MXC-021` | Native Chunked VMBus Payload Streaming (`copy-file` / `exec`) | `TP-13` | `ADR-015` | `BRD-014` / `FDD-014` | Epic 014 — Story 14.2 |
| 6 | `IMP-MXC-019` | UTF-8 BOM-Tolerant JSON Parsing & Flag Precedence in `wxc-exec` | `TP-13` | `ADR-015` | `BRD-014` / `FDD-014` | Epic 014 — Story 14.2 |
| 7 | `IMP-MXC-022` | First-Class Ephemeral IDE Worker Profile (Cursor / Antigravity) | `TP-13` | `ADR-015` | `BRD-014` / `FDD-014` | Epic 014 — Story 14.3 |
| 8 | `IMP-MXC-030` | Immutable EU AI Act / DORA / NIS2 Evidence Ledger & Hit-L Kill Switch | `TP-14` | `ADR-016` | `BRD-015` / `FDD-015` | Epic 015 — Story 15.1 |
| 9 | `IMP-MXC-025` | Microsoft Entra Agent ID Conditional Access Hook *(completion)* | `TP-14` | `ADR-016` | `BRD-015` / `FDD-015` | Epic 015 — Story 15.1 |
| 10 | `IMP-MXC-028` | Hyper-V Gen2 vTPM 2.0 & Confidential VM (SEV-SNP/TDX) Attestation | `TP-14` | `ADR-016` | `BRD-015` / `FDD-015` | Epic 015 — Story 15.2 |
| 11 | `IMP-MXC-018` | Reproducible ISO-to-Lean Agent Image CI Factory & Auto-Registry Hasher | `TP-15` | `ADR-017` | `BRD-016` / `FDD-016` | Epic 016 — Story 16.1 |
| 12 | `IMP-MXC-031` | Turnkey Single-Host On-Premises Appliance Mode ("MXC Embed") | `TP-15` | `ADR-017` | `BRD-016` / `FDD-016` | Epic 016 — Story 16.2 |
| 13 | `IMP-MXC-023` | Hardware-in-the-Loop (HIL) 5-Act Verification Gate & Demo Runner | `TP-15` | `ADR-017` | `BRD-016` / `FDD-016` | Epic 016 — Story 16.2 |
| 14 | `IMP-MXC-006` | Ultra-Lean Golden Bake Memory Floor (`~512–640 MB`, *paused floor*) | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.1 |
| 15 | `IMP-MXC-016` | Deterministic NGEN / CrossGen2 ASLR Base Normalization (`>= 65%` shared) | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.1 |
| 16 | `IMP-MXC-005` | Lifecycle Discard Decoupling: In-Session Trim Bypass for Disposables | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.1 |
| 17 | `IMP-MXC-012` | Pure In-Memory Ephemeral RAM-Disk / DAX Differencing (`HYP-mxc-019`) | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.2 |
| 18 | `IMP-MXC-014` | Predictive Micro-Tier Transitioning via Early Kernel TLS Probes | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.2 |
| 19 | `IMP-MXC-015` | eBPF / Kernel-Bypass TLS Sniffing & Continuous Neural Shift Forecaster | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.2 |
| 20 | `IMP-MXC-001` | Automated Subsystem Differential Telemetry Matrix | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.3 |
| 21 | `IMP-MXC-029` | GPU-Partitioned (`GPU-P` / DDA) Agent Sandbox Tier | `TP-16` | `ADR-018` | `BRD-017` / `FDD-017` | Epic 017 — Story 17.3 |

*(Also carried within Story 17.1 / `TP-16`: `HYP-mxc-021` NUMA-Aware Micro-VM Placement & Core Affinity.)*
