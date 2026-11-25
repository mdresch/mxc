---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Benefits Planning & Business Case (Phase 4)"
lifecycle_stage: "Stage 4 (Benefit)"
governance_policy: "approve-business-case"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/project-docs/Business-Case-Phase-4.md"
process: "Define target operational benefits, measurable realization metrics, and business value propositions for Phase 4 Rust runtime parity and bare-metal silicon productionization"
outputs:
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
status: "Approved"
---

# Benefits Statement — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `Benefits Planning & Business Case (Phase 4)` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 4 (Benefit)`  
> **Governing Candidate Baseline:** `PMP-BL-v4.0.0-candidate`  
> **Status:** Approved (`2026-11-25`) — Gate record: [approve-business-case-phase4-2026-11-25.adjudication.json](gates/approve-business-case-phase4-2026-11-25.adjudication.json)  
> **Inputs:** [Spark-Capture-Phase-4.md](Spark-Capture-Phase-4.md), [Ideation-Document-Phase-4.md](Ideation-Document-Phase-4.md), [Business-Case-Phase-4.md](Business-Case-Phase-4.md)  
> **Outputs:** Benefits-Statement-Phase-4.md, Traceable Benefit Realization Matrix (`BEN-25`..`BEN-28`)

---

## 1. Executive Purpose

Following the full contract-level realization of Phases 1–3 (`BEN-01`..`BEN-24`), Phase 4 establishes four measurable productionization benefits (`BEN-25`..`BEN-28`) translating verified Python control-plane contracts into compiled Rust binaries, running host security/compliance services, bare-metal Hyper-V silicon benchmarks, and a turnkey offline sovereign pilot installer. All metrics below trace directly to `Formulated` hypotheses in [Ideation-Document-Phase-4.md](Ideation-Document-Phase-4.md).

---

## 2. Phase 4 Target Benefits Realization Matrix (`BEN-25` .. `BEN-28`)

| Benefit ID | Benefit Domain | Strategic Intent | Target Metric / Evaluation Criteria | Traceable Hypotheses |
|---|---|---|---|---|
| **`BEN-25`** | Native Rust `wxc-exec` & `mxc-sdk` Parity | Eliminate Windows PowerShell BOM/flag friction, `cmd.exe` 8 KB payload limits, and Python-only prototypes by compiling Phase 3 primitives directly into `wxc-exec.exe` and `mxc-sdk`. | `100%` UTF-8 BOM manifest acceptance, `>= 100 MB` bit-exact chunked VMBus streaming, `<= 500 ms` per branch for 3–5 `--hyperv-op fork` sandboxes (`0%` parent drift), and `0` static secrets in `--hyperv-op git-sync`, verified via `cargo test`. | `HYP-mxc-031` |
| **`BEN-26`** | Compiled Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Daemon | Enforce zero-secret credential injection, MCP JSON-RPC tool containment, and tamper-evident EU AI Act / DORA / NIS2 logging in native host services on live VMBus traffic. | `0` static secrets in guest, `<= 5 ms` p95 sidecar injection with redacted audit logs, `100%` fail-closed MCP block accuracy (`<= 2 ms` p95), and `<= 250 ms` `freeze-and-rollback` writing to a `>= 180-day` SHA-256 hash-chained ledger. | `HYP-mxc-032` |
| **`BEN-27`** | Bare-Metal Hyper-V Silicon Proof | Replace simulated hardware assumptions with empirical Windows 11 Pro / Server 2025 Hyper-V silicon benchmarks and honest capability gating. | `<= 640 MB` paused floor / `< 350 MB` effective RAM (`>= 65%` shared pages), `0` remote NUMA pages, `<= 50 ms` RAM-disk/DAX mount (`0` NVMe write bytes), honest `ERR_TEE_UNSUPPORTED` / `ERR_GPUP_UNSUPPORTED` on unsupported hosts, and `>= 85%` native GPU throughput on capable hosts. | `HYP-mxc-033` |
| **`BEN-28`** | Turnkey Signed Offline "MXC Embed" Pilot Appliance | Enable regulated European enterprises to deploy and self-verify MXC locally without cloud connectivity or manual scripting. | `<= 15-minute` single-host offline installation + unattended 5-Act HIL verification pass (`0` outbound internet calls) with `100%` immutable parent `win11-agent-lean.vhdx` SHA-256 verification. | `HYP-mxc-034` |
