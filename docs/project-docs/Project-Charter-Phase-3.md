---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "4.1 Develop Project Charter (Phase 3)"
lifecycle_stage: "Stage 2 (Objective)"
governance_policy: "approve-charter"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/project-docs/Business-Case-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-2.md"
process: "Formally authorize Phase 3, establish sponsor authority, and define measurable objectives and boundaries for Sovereign Zero-Secret Agentic Execution"
outputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
status: "Approved"
---

# Project Charter — MXC Micro-Execution Platform Phase 3: Sovereign Zero-Secret Agentic Execution Fabric & EU Regulated Appliance

> **PMBOK 8 Process:** `4.1 Develop Project Charter (Phase 3)` (Initiating)  
> **Governance Policy:** `approve-charter` | **Lifecycle Stage:** `Stage 2 (Objective)`  
> **Status:** Approved (`2026-11-24`) — Gate record: [approve-charter-phase3-2026-11-24.adjudication.json](gates/approve-charter-phase3-2026-11-24.adjudication.json) (`approve-charter`, policy `8ec22760-9d76-4683-b1ff-fa4a847b73a1`)  
> **Preceding Baseline:** `PMP-BL-v2.0.0` (Phase 2 Closed) | **Target Baseline:** `PMP-BL-v3.0.0`  
> **Inputs:** [Spark-Capture-Phase-3.md](Spark-Capture-Phase-3.md), [Ideation-Document-Phase-3.md](Ideation-Document-Phase-3.md), [Business-Case-Phase-3.md](Business-Case-Phase-3.md), [Benefits-Statement-Phase-3.md](Benefits-Statement-Phase-3.md), [Intent-Refinement-Proposal-Phase-2.md](Intent-Refinement-Proposal-Phase-2.md)  
> **Outputs:** Project-Charter-Phase-3.md

---

## 1. Executive Summary

Phases 1 and 2 (`PMP-BL-v1.0.0` and `PMP-BL-v2.0.0`) delivered **12/12 Epics** and **204/204 Python contract tests** plus live Hyper-V verification of MXC's isolated standby pool engine (`win11-agent-lean.vhdx`, 9-second cold boot). This Charter formally authorizes **Phase 3 (`PMP-BL-v3.0.0`)** to deliver five sovereign agentic execution, compliance, and packaging capabilities across `WBS 14.0` through `WBS 18.0`:
1. **Zero-Secret Agentic Execution & MCP Protocol Firewall (`WBS 14.0` / `Epic 013`)**
2. **Millisecond Parallel Snapshot Forking, Chunked VMBus Streaming & CLI/IDE Workers (`WBS 15.0` / `Epic 014`)**
3. **Unified EU AI Act / DORA / NIS2 Evidence Ledger, Hit-L Kill Switch & Enclave Attestation (`WBS 16.0` / `Epic 015`)**
4. **Turnkey "MXC Embed" Sovereign On-Premises Appliance & Reproducible ISO Factory (`WBS 17.0` / `Epic 016`)**
5. **Ultra-Density Hardware Acceleration, RAM-Disk/DAX Differencing, eBPF/WFP TLS Probes & `GPU-P`/DDA (`WBS 18.0` / `Epic 017`)**

---

## 2. Leadership and Investment Authority

| Role or Control | Phase 3 Charter Record |
|---|---|
| **Project Sponsor** | Menno Drescher |
| **Project Manager / Lead Architect** | Menno Drescher |
| **Operational Benefit Owner** | Menno Drescher |
| **PM Spending Authority** | `USD 50,000` carried envelope (`\$0` new external capital required for core software R&D) |
| **Steering Committee** | Sponsor, CFO, Finance Controller, IT Infrastructure, Platform Security |
| **Target Phase 3 Timeline** | Sprints 13 through 18 (Waves 1–2 ahead of the **December 2, 2027** EU AI Act Annex III deadline) |

---

## 3. Phase 3 Measurable Project Objectives (`WBS 14.0–18.0`)

1. **Objective 1 (`WBS 14.0` / `Epic 013` — Zero-Secret Execution & MCP Firewall):** Deliver host-side `mxc-sync` git bundles, a credential-injecting outbound sidecar proxy (`<= 5 ms` overhead, `0` static keys inside guest), and a protocol-aware MCP JSON-RPC Firewall (`100%` block rate on disallowed servers/tools/arguments in `<= 2 ms`).
2. **Objective 2 (`WBS 15.0` / `Epic 014` — Parallel Forking, VMBus Streaming & CLI/IDE Profiles):** Deliver nested `.avhdx` snapshot-and-fork (`wxc-exec --hyperv-op fork` in `<= 500 ms`), `>= 100 MB` chunked binary VMBus streaming, BOM-tolerant `wxc-exec` JSON/CLI parsing, and standardized Cursor/IDE worker profiles.
3. **Objective 3 (`WBS 16.0` / `Epic 015` — Unified EU Regulatory Ledger & Enclave Attestation):** Deliver a SHA-256 hash-chained audit ledger (`>= 180-day` retention metadata per EU AI Act Art. 19 + Entra Agent ID Conditional Access claims), `<= 250 ms` `freeze-and-rollback` kill switch, and vTPM 2.0 / AMD SEV-SNP / Intel TDX attestation inside `PoolRegistrationGuard`.
4. **Objective 4 (`WBS 17.0` / `Epic 016` — "MXC Embed" Sovereign Appliance & ISO Factory):** Package MXC as a zero-cloud single-host Windows 11 Pro / Server 2025 installer (`<= 15-minute` setup with `0` internet calls), paired with an automated ISO-to-Lean CI factory (`ADR-012` aligned) and gated 5-Act HIL verification suite.
5. **Objective 5 (`WBS 18.0` / `Epic 017` — Ultra-Density Hardware Acceleration & Kernel-Bypass):** Deliver `< 350 MB` effective host RAM/guest (`>= 65%` shared pages), `<= 50 ms` RAM-disk/DAX `.avhdx` mounts (`0` NVMe write bytes), `2–3 ms` faster eBPF/WFP TLS wake, `0` NUMA remote pages, differential subsystem telemetry, and `GPU-P`/DDA sandboxes (`>= 85%` native GPU throughput).

---

## 4. Scope Boundaries, Exclusions & Dependencies

- **In Scope:** All work packages across `WBS 14.0–18.0` (`Epics 013–017`), implementing the 21 remaining/queued improvements (`IMP-MXC-001`, `005`, `006`, `012`, `014`..`019`, `021`..`031`) while preserving Phases 1–2 invariants (`ADR-001`..`013`).
- **Explicit Exclusions:**
  - Implementing a standalone OIDC/SAML/MFA identity provider inside MXC (`ADR-008` delegates auth to enterprise IdPs).
  - Cross-region WAN live VM migration or public multi-tenant SaaS cloud hosting operations.
  - Contracting or claiming unvalidated commercial ARR before Wave 1 customer PoCs conclude.
- **Technical Dependencies:** Windows 11 Pro / Windows Server 2025 Hyper-V host (Build `26100`/`26300`+); optional vTPM 2.0, AMD SEV-SNP / Intel TDX, NUMA multi-socket, and `GPU-P`/DDA host hardware detected dynamically with fail-closed policy enforcement when hardware profiles are requested.

---

## 5. Traceable Success Criteria (`BEN-19` .. `BEN-24`)

| Benefit ID | Benefit Statement | Phase 3 Target Metric |
|---|---|---|
| **`BEN-19`** | Zero-Secret Guest & MCP Protocol Containment | `0` static credentials in guest disk or RAM (`<= 5 ms` sidecar injection) + `100%` block rate on unapproved MCP servers/tools/arguments (`<= 2 ms` overhead). |
| **`BEN-20`** | Parallel Multi-Hypothesis Agent Velocity & CLI Ergonomics | `<= 500 ms` per branch for 3–5 parallel `.avhdx` forks, `>= 100 MB` chunked VMBus streaming, and `100%` BOM-tolerant `wxc-exec` parsing. |
| **`BEN-21`** | Unified EU AI Act / DORA / NIS2 Audit Evidence & Instant Kill Switch | `100%` tamper-evident SHA-256 hash-chained session ledger (`>= 180-day` retention floor per EU AI Act Art. 19 + Entra Agent ID Conditional Access claims) + `<= 250 ms` `freeze-and-rollback` containment. |
| **`BEN-22`** | Hardware-Rooted Enclave Trust | `100%` fail-closed rejection of tampered vTPM 2.0 / SEV-SNP / TDX boot quotes at `PoolRegistrationGuard` with `0 ms` post-admission hot dispatch overhead. |
| **`BEN-23`** | Sovereign Zero-Cloud Turnkey Appliance ("MXC Embed") | `<= 15-minute` single-host offline installation + unattended 5-Act HIL verification pass (`0` outbound internet calls) + reproducible ISO-to-Lean CI digests. |
| **`BEN-24`** | Next-Frontier Fleet Density, Zero-Wear Ephemeral I/O & GPU Acceleration | `< 350 MB` effective host RAM/guest (`>= 65%` shared pages), `<= 50 ms` RAM-disk/DAX `.avhdx` mount (`0` host NVMe write bytes), `2–3 ms` faster eBPF/WFP TLS wake, `0` NUMA remote pages, and `>= 85%` native GPU throughput via `GPU-P`/DDA. |
