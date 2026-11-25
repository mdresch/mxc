---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation (Phase 4)"
lifecycle_stage: "Stage 1 (Intent) & Stage 3 (Hypothesis)"
governance_policy: "approve-ideation & classify-hypothesis-status"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-4.md"
  - "docs/project-docs/Intent-Refinement-Proposal-Phase-3.md"
  - "docs/project-docs/OUTCOME-Phase-3-Actual-Outcomes.md"
  - "docs/registers/Audit-Register.md"
process: "Formulate empirical Phase 4 Rust runtime and bare-metal silicon hypotheses with measurable falsification criteria"
outputs:
  - "docs/project-docs/Ideation-Document-Phase-4.md"
status: "Approved (approve-ideation 2026-11-25) — Hypotheses Formulated"
---

# Ideation Document — Phase 4: Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization

> **PMBOK 8 Process:** `Pre-Project / Design Assumption Formulation (Phase 4)` (Initiating)  
> **Governance Policy:** `approve-ideation & classify-hypothesis-status` | **Lifecycle Stage:** `Stage 1 (Intent) & Stage 3 (Hypothesis)`  
> **Governing Candidate Baseline:** `PMP-BL-v4.0.0-candidate`  
> **Inputs:** [Spark-Capture-Phase-4.md](Spark-Capture-Phase-4.md), [Intent-Refinement-Proposal-Phase-3.md](Intent-Refinement-Proposal-Phase-3.md), [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md), [Audit-Register.md](../registers/Audit-Register.md) (`AUDIT-013`..`017`, `GOV-EX-003`)  
> **Outputs:** Ideation-Document-Phase-4.md, Hypotheses `HYP-mxc-031` through `HYP-mxc-034`  
> **Gate Approval Record:** [approve-ideation-phase4-2026-11-25.adjudication.json](gates/approve-ideation-phase4-2026-11-25.adjudication.json) (`approve_ideation` resolved `2026-11-25`, margin `+0.8026`, policy `dcdf7865-7d06-40cd-b282-18c01c3aaed0`)

---

## 1. Executive Summary & Strategic Motivation

Phases 1 through 3 (`PMP-BL-v1.0.0`, `PMP-BL-v2.0.0`, and `PMP-BL-v3.0.0`) delivered **17 complete Epics (`Epics 001–017`)**, **`358/358` passing Python contract & governance tests**, and **`31/31` Continuous Improvements Delivered (`IMP-MXC-001`..`031`)**. Every Phase 3 architectural invariant (`ADR-014..018`) is now formally verified at the Python control-plane contract layer (`scripts/lib/`) and audited in [Audit-Register.md](../registers/Audit-Register.md).

Phase 4 (**Native Rust `wxc-exec` Runtime Parity & Bare-Metal Silicon Productionization**) bridges the remaining **contract-to-silicon gap**: porting the verified Phase 3 Python contracts into the compiled Rust workspace (`src/Cargo.toml`, `src/mxc-sdk/`, `src/tools/wxc/`, `src/host/`), measuring bare-metal Hyper-V silicon ceilings on real hardware, and packaging the zero-cloud "MXC Embed" sovereign pilot bundle.

---

## 2. Operational Problem Definition (The Contract-to-Silicon Quartet)

Phase 4 Stage 1 frames four concrete engineering and empirical gaps identified in [OUTCOME-Phase-3-Actual-Outcomes.md](OUTCOME-Phase-3-Actual-Outcomes.md) §3:

1. **Python Contract vs. Compiled Rust CLI & SDK Gap (`WBS 19.0`):** `wxc-exec.exe` (`src/tools/wxc/`) and `mxc-sdk` (`src/mxc-sdk/`) still lack native compiled implementations of UTF-8 BOM-tolerant JSON parsing, CLI flag precedence, chunked binary VMBus framing, `--hyperv-op fork`, and `--hyperv-op git-sync` (`mxc-sync`).
2. **Control-Plane Spec vs. Running Host Security & Compliance Services (`WBS 20.0`):** The `ADR-014` credential-injecting sidecar proxy + MCP JSON-RPC firewall PEP and the `ADR-016` SHA-256 hash-chained EU Evidence Ledger + `freeze-and-rollback` circuit breaker must run as compiled host-side services (`src/host/`) enforcing real latency and zero-secret boundaries over live VMBus channels.
3. **Simulated Metrics vs. Bare-Metal Silicon Verification (`WBS 21.0`):** Hardware-dependent bounds—640 MB paused floor + CrossGen2 page sharing, RAM-disk/DAX differencing, local NUMA node pinning, vTPM 2.0 / AMD SEV-SNP / Intel TDX quotes, and `GPU-P`/DDA throughput—require live Hyper-V silicon benchmarks to graduate from contract-validated to silicon-verified.
4. **Scripted PoC vs. Turnkey Offline Enterprise Pilot Appliance (`WBS 22.0`):** Regulated EU on-premises buyers require a single signed, zero-cloud Windows 11 Pro / Server 2025 installer bundling `wxc-exec.exe`, `ADR-012` SLSA registry verification, ISO-to-Lean factory scripts, and an unattended 5-Act HIL self-test completing in `<= 15 minutes`.

`classify-hypothesis-status` (`agent-learning-governance`) has not been run for Phase 4. Every hypothesis below remains strictly `Formulated` until Phase 4 Rust and bare-metal silicon outcomes are empirically observed.

---

## 3. Phase 4 Formulated Hypotheses (`HYP-mxc-031` .. `HYP-mxc-034`)

### HYP-mxc-031: Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Runtime Parity
- **Target Scope:** `src/mxc-sdk/`, `src/tools/wxc/` (`WBS 19.0`, Candidate Epic 018; mirrors `ADR-014` / `ADR-015`)
- **Statement:** Implementing UTF-8 BOM-tolerant JSON manifest parsing with CLI override precedence, native chunked binary VMBus framing (`copy-file`/`exec`), bounded parallel `.avhdx` snapshot forking (`--hyperv-op fork`), and host-side zero-secret git sync (`--hyperv-op git-sync`) directly in compiled Rust eliminates PowerShell/8 KB `cmd.exe` ceilings while preserving 100% behavioral parity with the Phase 3 Python contracts.
- **Empirical Evaluation Criteria:**
  1. `wxc-exec` parses UTF-8 with BOM (`\u{FEFF}`) manifests and `--operation` / `--container-id` CLI overrides with **100%** acceptance (`0` false parse errors) across `cargo test` unit and integration suites.
  2. Native chunked VMBus framing transfers **>= 100 MB** payloads with bit-exact SHA-256 verification and **0** `cmd.exe` 8 KB truncation errors.
  3. `wxc-exec --hyperv-op fork` allocates 3–5 sibling `.avhdx` branches (`max_depth <= 4`) in **<= 500 ms** per branch with **0%** parent VHDX hash drift upon discard.
- **Status:** Formulated

### HYP-mxc-032: Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service
- **Target Scope:** `src/host/`, `src/host/wxc_winhttp_proxy_shim/` (`WBS 20.0`, Candidate Epic 019; mirrors `ADR-014` / `ADR-016`)
- **Statement:** Running the `ADR-014` outbound credential-injecting sidecar proxy, protocol-aware MCP JSON-RPC firewall, and `ADR-016` SHA-256 hash-chained EU Evidence Ledger + `freeze-and-rollback` kill switch as compiled host services over airgapped VMBus enforces zero-secret guest execution and EU AI Act / DORA / NIS2 auditability within interactive latency budgets.
- **Empirical Evaluation Criteria:**
  1. Scanned guest filesystem and environment contain **0 bytes** of static GitHub PATs or API secrets while host-side credential injection completes in **<= 5 ms** p95 with redacted audit logs.
  2. MCP JSON-RPC policy enforcement blocks unapproved servers, drifted schemas, disallowed tools, and blocked argument patterns with **100%** fail-closed accuracy in **<= 2 ms** p95.
  3. Invoking `freeze-and-rollback` halts active guest execution, restores the clean checkpoint, and appends a verified SHA-256 ledger entry (`>= 180-day` retention metadata) in **<= 250 ms**.
- **Status:** Formulated

### HYP-mxc-033: Bare-Metal Silicon Proof for Ultra-Density, RAM-Disk/DAX, NUMA, Confidential TEE & `GPU-P`
- **Target Scope:** `scripts/hyperv/`, live Hyper-V host & Windows Server 2025 silicon (`WBS 21.0`, Candidate Epic 020; mirrors `ADR-016` / `ADR-018`)
- **Statement:** Executing automated Hardware-in-the-Loop benchmarks on live Hyper-V silicon confirms the Phase 3 hardware ceilings across paused RAM floor, CrossGen2 page sharing, RAM-disk/DAX differencing, local NUMA pinning, vTPM 2.0 / AMD SEV-SNP / Intel TDX quotes, and `GPU-P`/DDA throughput without silent fallback or faked compliance.
- **Empirical Evaluation Criteria:**
  1. Trimmed paused guests achieve **<= 640 MB** baseline and **< 350 MB** effective host RAM/guest (`>= 65%` shared pages) with **0** remote NUMA physical pages on multi-socket hosts.
  2. RAM-disk/DAX `.avhdx` overlays mount in **<= 50 ms** with **0 bytes** host NVMe write amplification.
  3. Unsupported TEE or CPU-only hosts fail closed honestly (`ERR_TEE_UNSUPPORTED` / `ERR_GPUP_UNSUPPORTED`), while capable hardware verifies PCR quotes offline and sustains **>= 85%** bare-host GPU inference throughput with **0** cross-session residue.
- **Status:** Formulated

### HYP-mxc-034: Turnkey Signed Offline "MXC Embed" Sovereign Enterprise Pilot Bundle
- **Target Scope:** `scripts/hyperv/`, release packaging & SLSA manifest (`WBS 22.0`, Candidate Epic 021; mirrors `ADR-012` / `ADR-017`)
- **Statement:** Packaging compiled `wxc-exec.exe`, signed `golden_image_registry.json` (`ADR-012` SLSA provenance), ISO-to-Lean factory scripts, and the unattended 5-Act HIL self-test into a single-host offline installer delivers a repeatable, zero-cloud sovereign appliance deployable on Windows 11 Pro or Server 2025.
- **Empirical Evaluation Criteria:**
  1. Clean single-host installation plus unattended 5-Act HIL self-test finishes in **<= 15 minutes** with **0** outbound internet calls.
  2. Parent `win11-agent-lean.vhdx` SHA-256 hash remains **100% bit-for-bit identical** before and after the 5-Act rogue mutation and Hyper-V checkpoint rollback sequence.
- **Status:** Formulated

---

## 4. Grounded Scope Boundary (Stage 1 Deferrals)

This Stage 1 artifact stays strictly at strategic intent, problem framing, and falsifiable hypotheses:
- **Deferred to Stage 2:** Execution timeline, named sponsorship authority, WBS milestone commitments, and resource ceilings (`Project-Charter-Phase-4.md` / `approve-charter`).
- **Deferred to Stage 4:** Commercial ROI, pilot pricing brackets, and quantified benefit targets (`Business-Case-Phase-4.md` / `Benefits-Statement-Phase-4.md` / `approve-business-case`).
- **Deferred to Stages 5–6:** Phase 4 Topic Pillars (`TP-17`..`TP-20`), Rust/silicon ADRs (`ADR-019`..`022`), BRDs (`BRD-018`..`021`), FDDs (`FDD-018`..`021`), and sprint user stories (`Epics 018–021`).
