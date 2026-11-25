---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification (Phase 4)"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
spark_id: "SPARK-MXC-Phase4-v4.0.0"
inputs:
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-3.md"
  - "docs/project-docs/OUTCOME-Phase-3-Actual-Outcomes.md"
  - "docs/registers/Audit-Register.md"
  - "docs/registers/Lessons-Learned-Register.md"
process: "Capture Phase 4 strategic intent for Native Rust wxc-exec / mxc-sdk runtime parity, bare-metal silicon verification, and turnkey commercial MXC Embed packaging"
outputs:
  - "docs/project-docs/Spark-Capture-Phase-4.md"
status: "Approved"
---

# Spark Capture — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification (Phase 4)` (Initiating)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Governing Candidate Baseline:** `PMP-BL-v4.0.0-candidate` | **Spark ID:** `SPARK-MXC-Phase4-v4.0.0`  
> **Inputs:** [Intent-Refinement-Proposal-Phase-3.md](Intent-Refinement-Proposal-Phase-3.md), [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md), [Audit-Register.md](../registers/Audit-Register.md) (`AUDIT-013`..`017`, `GOV-EX-003`)  
> **Outputs:** Spark-Capture-Phase-4.md

**Date:** 2026-11-25  
**Captured by:** Menno Drescher  
**Project Name:** MXC Phase 4 — Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization  
**Preceding Lineage:** Phase 1 (`PMP-BL-v1.0.0`, Epics 001..006) $\rightarrow$ Phase 2 (`PMP-BL-v2.0.0`, Epics 007..012) $\rightarrow$ Phase 3 (`PMP-BL-v3.0.0`, Epics 013..017 Complete, `358/358` Python tests, `31/31` IMPs Delivered)

---

## 1. Problem Statement & Productionization Catalyst

Phases 1 through 3 established the complete, contract-verified control plane and architectural specification across `17` Epics (`ADR-001..006`, `ADR-008..018`), `358/358` passing Python contract tests, and `31/31` delivered improvements. However, as honestly bounded in [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md) §3, Phase 3 validated the new capabilities (`ADR-014..018`) at the Python control-plane contract layer (`scripts/lib/`), while the compiled Rust runtime (`src/Cargo.toml`, `src/mxc-sdk/`, `src/tools/wxc/`, `src/host/`) and bare-metal silicon harnesses still carry Phase 2 feature parity.

Phase 4 closes the **contract-to-silicon gap** across four productionization workstreams:

1. **Native Rust `wxc-exec` & `mxc-sdk` Feature Parity (`src/tools/wxc/`, `src/mxc-sdk/`):** Implement UTF-8 BOM-tolerant JSON manifest parsing and CLI flag precedence (`IMP-MXC-019`), native chunked binary VMBus payload streaming (`IMP-MXC-021`), `wxc-exec --hyperv-op fork` bounded `.avhdx` snapshot branching (`IMP-MXC-027`), and `wxc-exec --hyperv-op git-sync` (`mxc-sync`, `IMP-MXC-017`) directly in compiled Rust with full `cargo test` coverage.
2. **Compiled Host-Side Zero-Secret Sidecar, MCP Firewall & EU Evidence Daemon (`src/host/`):** Operationalize the `ADR-014` credential-injecting proxy + MCP JSON-RPC firewall PEP and the `ADR-016` SHA-256 hash-chained EU AI Act / DORA / NIS2 Evidence Ledger + `freeze-and-rollback` kill switch into native host services (`src/host/wxc_winhttp_proxy_shim/` and companion host daemon) communicating over airgapped VMBus.
3. **Bare-Metal Silicon & Hardware-in-the-Loop Benchmarks (`scripts/hyperv/`):** Execute empirical hardware measurements on real Hyper-V silicon for `640 MB` paused RAM floor + CrossGen2 page sharing (`HYP-mxc-029`), RAM-disk/DAX differencing (`HYP-mxc-019`), NUMA local-node pinning (`HYP-mxc-021`), vTPM 2.0 / AMD SEV-SNP / Intel TDX attestation quotes (`HYP-mxc-027`), and `GPU-P`/DDA inference throughput (`HYP-mxc-030`).
4. **Turnkey Commercial "MXC Embed" Sovereign Appliance Installer (`ADR-017`):** Package the compiled `wxc-exec.exe`, signed golden image registry (`ADR-012`), ISO-to-Lean CI factory scripts, and automated 5-Act HIL self-test into an offline, single-host Windows 11 Pro / Server 2025 enterprise pilot bundle (`<= 15 min` install, `0` outbound internet calls).

---

## 2. Phase 4 Candidate Work Breakdown Structure (`PMP-BL-v4.0.0-candidate`)

| WBS | Candidate Epic | Target Codebase / Hardware Scope | Primary Productionization Outcome |
|---|---|---|---|
| **WBS 19.0** | **Epic 018 — Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Parity** | `src/mxc-sdk/`, `src/tools/wxc/` | Compiled Rust UTF-8 BOM manifest parser, CLI flag precedence, chunked binary VMBus `copy-file`/`exec`, `--hyperv-op fork`, and `--hyperv-op git-sync` with passing `cargo test` suite. |
| **WBS 20.0** | **Epic 019 — Native Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Service** | `src/host/`, `src/host/wxc_winhttp_proxy_shim/` | Compiled host-side secret-injecting proxy (`<= 5 ms`), MCP JSON-RPC PEP (`<= 2 ms`), append-only SHA-256 EU Evidence Ledger (`>= 180d`), and `freeze-and-rollback` kill switch (`<= 250 ms`). |
| **WBS 21.0** | **Epic 020 — Bare-Metal Silicon HIL Verification (Density, RAM-Disk, NUMA, TEE & `GPU-P`)** | `scripts/hyperv/`, live Hyper-V host & Server 2025 silicon | Empirical silicon proof and reproducible benchmark reports promoting `HYP-mxc-019`, `021`, `027`, `029`, `030` from contract-validated to silicon-verified. |
| **WBS 22.0** | **Epic 021 — Signed Offline "MXC Embed" Enterprise Pilot Installer** | `scripts/hyperv/`, release packaging & SLSA manifest | Turnkey zero-cloud Windows 11 Pro / Server 2025 appliance package (`<= 15 min` setup + 5-Act HIL self-test) ready for sovereign EU customer PoCs. |

---

## 3. Immutable Core Invariants Carried Forward

Phase 4 strictly preserves all ratified invariants from Phases 1–3 (`ADR-001..006`, `ADR-008..018`, `358/358` Python contract tests, and `LL-001..018`). No existing Python contract test or `ADR-002` `path_only` / `ADR-005` sterile `.avhdx` guarantee may be weakened.

---

## 4. Immediate Next Step (Phase 4 Stage 1 Gate)

Author **`docs/project-docs/Ideation-Document-Phase-4.md`** (formulating falsifiable Rust & silicon hypotheses `HYP-mxc-031`..`034`) and adjudicate **`approve-ideation`** before advancing to Phase 4 Stage 2/4 (`Business-Case`, `Benefits-Statement`, `Project-Charter`).

---

## 5. Gate Approval Record

- **Gate:** `approve-ideation` (`approve_ideation`, policy `dcdf7865-7d06-40cd-b282-18c01c3aaed0`) — **Approved (`2026-11-25`, margin `+0.8026`)**
- **Adjudication Record:** [approve-ideation-phase4-2026-11-25.adjudication.json](gates/approve-ideation-phase4-2026-11-25.adjudication.json)
- **Ideation Companion:** [Ideation-Document-Phase-4.md](Ideation-Document-Phase-4.md) (`HYP-mxc-031`..`034` `Formulated`)
