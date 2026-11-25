---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md"
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
process: "Define business rules for native Rust wxc-exec and mxc-sdk Phase 3 parity"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# BRD-018: Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Runtime Parity

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 4)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-019](../../07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md) | **Topic Pillar:** `TP-17` | **Baseline:** `PMP-BL-v4.0.0-candidate`

---

## 1. Business Need

Operators and automated IDE workers invoke `wxc-exec.exe` directly from Windows PowerShell and CI pipelines. All Phase 3 ergonomics and safety guarantees (`ADR-014`, `ADR-015`) must operate natively inside compiled Rust (`src/tools/wxc/`, `src/mxc-sdk/`) with zero behavioral drift from the verified Python contracts.

---

## 2. Business Rules (BRU)

- **BRU-018-01 (UTF-8 BOM & CLI Precedence):** `wxc-exec` MUST strip leading UTF-8 BOM bytes (`\xEF\xBB\xBF`) cleanly before JSON parsing and apply explicit `--operation` / `--container-id` CLI flags over embedded `phase` / `sandboxId` keys without parse errors.
- **BRU-018-02 (Chunked VMBus Integrity):** Native chunked binary framing MUST round-trip `0 B` through `>= 100 MB` payloads with per-chunk and full-stream SHA-256 verification, failing closed with `ERR_CHUNK_CHECKSUM_MISMATCH` on tamper or missing frames.
- **BRU-018-03 (Bounded Parallel Forking):** `--hyperv-op fork` MUST bound branch depth to `<= 4` (`ERR_FORK_DEPTH_EXCEEDED`) and fan-out to `<= 5` (`ERR_FORK_BOUNDS_INVALID`), preserving `0%` parent hash drift upon discard.
- **BRU-018-04 (Zero-Secret Git Sync):** `--hyperv-op git-sync` MUST reject embedded static PATs, tokens, or private keys (`ERR_STATIC_SECRET_DETECTED`) using token-boundary scanning (`PATH` allowed, `PAT` rejected) over `0`-NIC VMBus.

---

## 3. Traceability

- **Topic Pillar:** `TP-17` | **ADR:** [ADR-019](../../07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md) | **FDD:** [FDD-018](../Functional-Design/FDD-018-native-rust-wxc-exec-phase3-parity.md) | **Epic:** [epic-018](../../user-stories/epic-018-native-rust-wxc-exec-phase3-parity.md) (`WBS 19.0`, `HYP-mxc-031`, `BEN-25`)
