---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md"
  - "docs/project-docs/Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md"
  - "docs/project-docs/Functional-Design/FDD-018-native-rust-wxc-exec-phase3-parity.md"
process: "Decompose native Rust wxc-exec and mxc-sdk Phase 3 parity into testable user stories"
outputs:
  - "docs/user-stories/epic-018-native-rust-wxc-exec-phase3-parity.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# Epic 018: Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Runtime Parity

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 4)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-019](../07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md) | **WBS:** `19.0` | **Topic Pillar:** `TP-17`  
> **Status:** Draft — Ready for Stage 5/6 Approval (`HYP-mxc-031`, `BEN-25`)

---

## Story 18.1 — Native Rust UTF-8 BOM Manifest Parser, CLI Precedence & Chunked VMBus Framing
- **WBS:** 19.1
- **Status:** Planned
- **As a** Windows Hyper-V Platform Engineer,  
  **I want** `wxc-exec` and `mxc-sdk` to parse UTF-8 BOM manifests with CLI flag precedence and stream arbitrary payloads via SHA-256 chunked binary frames in compiled Rust,  
  **so that** Windows PowerShell scripts never fail on `\xEF\xBB\xBF` BOM bytes and `>= 100 MB` transfers bypass the `cmd.exe` 8 KB ceiling.
- **Acceptance Criteria:**
  - **AC-18.1.1:** `parse_manifest_bom_safe()` strips leading UTF-8 BOM bytes, preserves `phase`/`sandboxId` keys, applies non-empty `Some(...)` CLI overrides cleanly (and falls back cleanly on `None`), and rejects empty or invalid UTF-8/JSON byte slices with explicit `Err(...)`.
  - **AC-18.1.2:** `chunk_payload_frames()` and `reassemble_chunk_frames()` round-trip empty `0`-byte slices (`&[]` returning empty `Vec`) through multi-MB payloads with SHA-256 verification, returning `Err("ERR_CHUNK_CHECKSUM_MISMATCH")` on corrupted, missing, or out-of-order frames.

---

## Story 18.2 — Native Rust Bounded Parallel Snapshot Forking & Zero-Secret Git Sync Scanner
- **WBS:** 19.2
- **Status:** Planned
- **As an** Autonomous Coding Agent Orchestrator,  
  **I want** compiled Rust implementations of bounded `.avhdx` snapshot forking (`--hyperv-op fork`) and token-boundary static secret scanning (`--hyperv-op git-sync`),  
  **so that** `wxc-exec.exe` forks 3–5 sibling sandboxes in `<= 500 ms` per branch with zero guest PAT/key exposure.
- **Acceptance Criteria:**
  - **AC-18.2.1:** `create_parallel_forks()` allocates 3–5 active branches (`max_depth <= 4`, `max_parallel <= 5`) with `0%` parent hash drift on discard, returning `Err("ERR_FORK_DEPTH_EXCEEDED")` or `Err("ERR_FORK_BOUNDS_INVALID")` on depth overflow, fan-out overflow, duplicate/blank names, or empty branch slices.
  - **AC-18.2.2:** `scan_git_sync_secrets()` passes clean URLs and benign env keys like `PATH` (`Ok(())`), handles `None` URLs and empty env slices safely, and rejects embedded credentials/PATs/private keys with `Err("ERR_STATIC_SECRET_DETECTED")`.
