---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/project-docs/Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/project-docs/Functional-Design/FDD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
process: "Decompose parallel snapshot forking, chunked VMBus streaming, BOM-tolerant CLI parsing, and IDE worker profiles into testable user stories"
outputs:
  - "docs/user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
status: "Closed — Implemented & Validated"
---

# Epic 014: Parallel Snapshot Branching, Chunked VMBus Streaming, BOM-Tolerant CLI & IDE Workers

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 3)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-015](../07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | **WBS:** `15.0` | **Topic Pillar:** `TP-13`  
> **Status:** Closed — Implemented & Validated (2026-11-25) (`IMP-MXC-019`, `021`, `022`, `027`)

---

## Story 14.1 — Sub-500ms Parallel `.avhdx` Snapshot Branching (`wxc-exec --hyperv-op fork`)
- **WBS:** 15.1
- **Status:** Implemented & Validated
- **As an** Autonomous Coding Agent Orchestrator,  
  **I want** to fork 3–5 concurrent sibling sandboxes from a single warm checkpoint with bounded `.avhdx` chain depth and clean rollback of losing branches,  
  **so that** competing bug fixes and test runs execute in parallel in `<= 500 ms` per branch with zero parent mutation.
- **Acceptance Criteria:**
  - **AC-14.1.1:** `create_parallel_forks()` allocates 3–5 independent active `SnapshotBranch` records tied to an immutable `parent_checkpoint_id` within `<= 500 ms`, while discarding losing branches leaves `parent_hash` identical.
  - **AC-14.1.2:** Requests exceeding `max_depth=4` (`ERR_FORK_DEPTH_EXCEEDED`), exceeding `max_parallel=5`, or passing empty/`None` branch lists raise explicit `ValueError`.

---

## Story 14.2 — Native Chunked VMBus Payload Streaming & UTF-8 BOM-Tolerant CLI Manifest Parser
- **WBS:** 15.2
- **Status:** Implemented & Validated
- **As a** Windows & Hyper-V Platform Engineer,  
  **I want** fixed-frame chunked VMBus payload streaming and UTF-8 BOM-tolerant `wxc-exec` manifest parsing with explicit CLI flag precedence,  
  **so that** multi-100 MB transfers bypass the `cmd.exe` 8 KB limit with bit-exact integrity and WinPS 5.1 scripts never break on leading BOM bytes or override flags.
- **Acceptance Criteria:**
  - **AC-14.2.1:** `chunk_payload_frames()` and `reassemble_chunk_frames()` round-trip arbitrary byte payloads (`0` bytes empty input through multi-MB payloads) with verified SHA-256 hashes, raising `ValueError` (`ERR_CHUNK_CHECKSUM_MISMATCH`) on corrupted, out-of-order, or missing frames.
  - **AC-14.2.2:** `parse_wxc_manifest_bom_safe()` strips leading UTF-8 BOM bytes (`\xef\xbb\xbf`), prioritizes optional `cli_operation` / `cli_container_id` overrides cleanly when present or `None`, and returns a deterministic normalized dict without raising `JSONDecodeError`.

---

## Story 14.3 — Standardized Ephemeral IDE Worker Profile (`Cursor` / `Antigravity` / `Claude Code`)
- **WBS:** 15.3
- **Status:** Implemented & Validated
- **As an** AI IDE Developer,  
  **I want** a validated declarative `IdeWorkerProfile` specifying client type, pre-installed agent tools, archetype sizing floor, and zero-secret `mxc-sync` mode,  
  **so that** ephemeral remote Hyper-V workspaces provision consistently across AI IDEs without storing Git credentials inside guests.
- **Acceptance Criteria:**
  - **AC-14.3.1:** Valid profiles for `cursor`, `antigravity`, and `claude-code` with `zero_secret=True` and non-empty toolchains return `(True, "OK")`.
  - **AC-14.3.2:** `None`, empty dicts, missing fields, or `zero_secret=False` profiles fail closed returning `(False, "ERR_WORKER_PROFILE_INVALID")`.
