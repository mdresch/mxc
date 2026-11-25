---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "4.2 Develop Project Management Plan (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Business-Case-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
  - "docs/user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/user-stories/epic-015-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/user-stories/epic-016-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
process: "Integrate Phase 3 scope, schedule, cost, quality, and architectural baselines under PMP-BL-v3.0.0"
outputs:
  - "docs/project-docs/Project-Management-Plan-Phase-3.md"
status: "Approved"
---

# Project Management Plan — Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `4.2 Develop Project Management Plan (Phase 3)` (Planning)  
> **Governance Policy:** `approve-pmp` | **Lifecycle Stage:** `Stage 7 (Planning: Integrated PMP & Baselines)`  
> **Status:** Approved (`2026-11-24`) — Gate record: [approve-pmp-phase3-2026-11-24.adjudication.json](gates/approve-pmp-phase3-2026-11-24.adjudication.json) (`approve-pmp`, policy `46c60639-c24f-4045-8ace-a3dbe2142e61`)  
> **Governing Baseline:** **`PMP-BL-v3.0.0`** | **Preceding Baseline:** `PMP-BL-v2.0.0` (Closed)

---

## 1. Executive Summary & Baseline Authorization

Building upon Phase 1 (`PMP-BL-v1.0.0`, Epics 001–006) and Phase 2 (`PMP-BL-v2.0.0`, Epics 007–012, `204/204` Python contracts passing), this integrated management plan ratifies baseline **`PMP-BL-v3.0.0`** for **Phase 3 (Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance)**. It governs all 21 remaining/queued continuous improvements (`IMP-MXC-001`, `005`, `006`, `012`, `014`..`019`, `021`..`031`) plus `HYP-mxc-019` and `HYP-mxc-021` across **5 Topic Pillars (`TP-12`..`TP-16`)**, **5 ADRs (`ADR-014`..`018`)**, **5 Epics (`Epics 013–017`)**, and **12 User Stories (`13.1`..`17.3`)**.

---

## 2. Phase 3 Work Breakdown Structure (`WBS 14.0–18.0`) & Scope Baseline

| WBS | Work Package / Epic / Story | Topic Pillar | Governing ADR | Target Deliverable / Module & Contract Target |
|:---:|---|:---:|:---:|---|
| **14.0** | **Epic 013 — Zero-Secret Guest Git Sync, Sidecar Proxy & MCP Firewall** | `TP-12` | `ADR-014` | `scripts/lib/zero_secret_mcp_gateway.py` (`BEN-19`) |
| **14.1** | Story 13.1: Host-Side `mxc-sync` Git Bundle Sync & Credential Sidecar Proxy | `TP-12` | `ADR-014` | `tests/contracts/test_story_13_1_*.py` (`IMP-MXC-017`, `024`) |
| **14.2** | Story 13.2: Protocol-Aware MCP JSON-RPC Firewall over VMBus | `TP-12` | `ADR-014` | `tests/contracts/test_story_13_2_*.py` (`IMP-MXC-026`) |
| **15.0** | **Epic 014 — Parallel Snapshot Branching, Chunked VMBus & IDE Workers** | `TP-13` | `ADR-015` | `scripts/lib/snapshot_fork_and_vmbus.py` (`BEN-20`) |
| **15.1** | Story 14.1: Sub-500ms Parallel `.avhdx` Snapshot Branching (`fork`) | `TP-13` | `ADR-015` | `tests/contracts/test_story_14_1_*.py` (`IMP-MXC-027`) |
| **15.2** | Story 14.2: Native Chunked VMBus Streaming & BOM-Tolerant CLI Parser | `TP-13` | `ADR-015` | `tests/contracts/test_story_14_2_*.py` (`IMP-MXC-021`, `019`) |
| **15.3** | Story 14.3: Standardized Ephemeral IDE Worker Profile (`Cursor` / `Antigravity` / `Claude Code`) | `TP-13` | `ADR-015` | `tests/contracts/test_story_14_3_*.py` (`IMP-MXC-022`) |
| **16.0** | **Epic 015 — Unified EU Evidence Ledger, Kill Switch & Enclave Attestation** | `TP-14` | `ADR-016` | `scripts/lib/eu_evidence_and_enclave.py` (`BEN-21`, `BEN-22`) |
| **16.1** | Story 15.1: Tamper-Evident EU Evidence Ledger, Entra Conditional Access & Kill Switch | `TP-14` | `ADR-016` | `tests/contracts/test_story_15_1_*.py` (`IMP-MXC-030`, `025`) |
| **16.2** | Story 15.2: vTPM 2.0 & Confidential VM (SEV-SNP / TDX) Remote Attestation Gate | `TP-14` | `ADR-016` | `tests/contracts/test_story_15_2_*.py` (`IMP-MXC-028`) |
| **17.0** | **Epic 016 — Turnkey "MXC Embed" Sovereign Appliance & ISO Factory** | `TP-15` | `ADR-017` | `scripts/lib/mxc_embed_appliance.py` (`BEN-23`) |
| **17.1** | Story 16.1: Reproducible ISO-to-Lean Agent CI Factory & Auto-Registry Hasher | `TP-15` | `ADR-017` | `tests/contracts/test_story_16_1_*.py` (`IMP-MXC-018`) |
| **17.2** | Story 16.2: Turnkey Zero-Cloud "MXC Embed" & Gated 5-Act HIL Suite | `TP-15` | `ADR-017` | `tests/contracts/test_story_16_2_*.py` (`IMP-MXC-031`, `023`) |
| **18.0** | **Epic 017 — Ultra-Density RAM-Disk/DAX, Kernel TLS Probes & `GPU-P` Sandboxes** | `TP-16` | `ADR-018` | `scripts/lib/frontier_density_and_gpu.py` (`BEN-24`) |
| **18.1** | Story 17.1: 640 MB Paused Floor, CrossGen2 Alignment, Trim Bypass & NUMA Pinning | `TP-16` | `ADR-018` | `tests/contracts/test_story_17_1_*.py` (`IMP-MXC-006`, `016`, `005`, `HYP-mxc-021`) |
| **18.2** | Story 17.2: Pure In-Memory RAM-Disk/DAX Differencing, Kernel TLS & Neural Forecaster | `TP-16` | `ADR-018` | `tests/contracts/test_story_17_2_*.py` (`IMP-MXC-012`/`HYP-mxc-019`, `014`, `015`) |
| **18.3** | Story 17.3: Automated Subsystem Differential Telemetry Matrix & `GPU-P`/DDA Tier | `TP-16` | `ADR-018` | `tests/contracts/test_story_17_3_*.py` (`IMP-MXC-001`, `029`) |

---

## 3. Subsidiary Management Plans Integration (PMBOK 8 — All 9 Knowledge Areas)

| PMBOK 8 Domain | Phase 3 Integrated Control & Baseline Rule |
|---|---|
| **5.1 Scope** | Strictly bounded to `WBS 14.0–18.0` covering all 21 remaining improvements (`IMP-MXC-001`, `005`, `006`, `012`, `014`..`019`, `021`..`031`) + `HYP-mxc-019`, `021`. Invariants `ADR-001`..`013` remain non-negotiable. |
| **6.1 Schedule** | Executed across **Sprints 13–18** in two delivery waves ahead of the **December 2, 2027** EU AI Act Annex III deadline: **Wave 1 (Sprints 13–15)** delivers `Epic 013` (Zero-Secret & MCP Firewall), `Epic 014` (Parallel Forking & CLI/IDE), and `Epic 015` (EU Evidence Ledger & Enclave Attestation); **Wave 2 (Sprints 16–18)** delivers `Epic 016` ("MXC Embed" & ISO Factory) and `Epic 017` (Ultra-Density, RAM-Disk/DAX, Kernel TLS & `GPU-P`). |
| **7.1 Cost** | Operates inside the carried **`USD 50,000`** PM spending authority envelope with **\$0 new external capital** required (`Business-Case-Phase-3.md`). |
| **8.1 Quality** | Mandatory `implement-story` loop per story: `scripts/spec_gate.py` (`margin >= +0.05`) $\rightarrow$ RED contract (`tests/contracts/test_story_1X_Y_*.py`) $\rightarrow$ `.claude/skills/<module>/SKILL.md` $\rightarrow$ GREEN implementation (`scripts/lib/`) $\rightarrow$ full `pytest tests -q` regression check $\rightarrow$ Step 9 breakout (`LL-###`, `IMP-MXC-###`, `Project-Status-Register.md`). |
| **9.1 Resource** | Lead Architect / PM (`Menno Drescher`), local Hyper-V workstation/server silicon (`win11-agent-lean.vhdx`, `winserv2025-golden.vhdx`), and autonomous coding workers operating zero-secret over VMBus. |
| **10.1 Communications** | Live traceability maintained in `Project-Status-Register.md`, `Audit-Register.md`, `Lessons-Learned-Register.md`, and executive commercial packs (`docs/marketing/`). |
| **11.1 Risk** | Active tracking of `RISK-P3-01`..`05`: p95 sidecar/MCP overhead guards (`<= 5 ms` / `<= 2 ms`), fork nesting depth caps (`<= 4`), fail-closed hardware capability probing for SEV-SNP/TDX/GPU-P (`ERR_TEE_UNSUPPORTED`, `ERR_GPUP_UNSUPPORTED`), RAM-disk quota enforcement, and pre-dispatch subsystem checks. |
| **12.1 Procurement** | Zero third-party cloud SaaS sandbox dependencies (`MXC Embed` offline installer + Python stdlib / Rust offline crates). |
| **13.2 Stakeholder** | Project Sponsor (`Menno Drescher`), Steering Committee, CISO/SecOps, EU Compliance (`OP-RSK-004`), and Regulated Enterprise PoC Sponsors (`OP-ITG-017` / `OP-ITG-018`). |
