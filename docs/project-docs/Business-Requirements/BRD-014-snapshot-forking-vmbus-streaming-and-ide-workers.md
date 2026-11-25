---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
process: "Define business requirements for parallel snapshot branching, chunked VMBus streaming, BOM-tolerant CLI manifest handling, and IDE worker profiles"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
status: "Approved"
---

# BRD-014: Parallel Snapshot Branching, Chunked VMBus Streaming, BOM-Tolerant CLI & IDE Workers

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 3)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-015](../../07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | **Topic Pillar:** `TP-13` | **Status:** Approved (2026-11-24)

---

## 1. Business Need

Autonomous coding agents and remote AI IDEs (`Cursor`, `Antigravity`, `Claude Code`) require instant environment branching to test parallel fixes, multi-megabyte workspace hydration without network shares, and frictionless Windows CLI execution across WinPS 5.1 and `pwsh 7`.

---

## 2. Business Rules (BRU)

- **BRU-014-01 (Bounded Parallel Snapshot Forking):** Forking 3–5 sibling sandboxes from a single warm checkpoint MUST finish in **$\le 500\text{ ms}$** per branch, forbid nesting deeper than **4** levels (`ERR_FORK_DEPTH_EXCEEDED`), and preserve **0%** parent mutation.
- **BRU-014-02 (Chunked Binary VMBus Integrity):** Multi-megabyte transfers (`>= 100 MB`) MUST split cleanly into bounded chunks avoiding the `cmd.exe` 8 KB command limit, validating sequential indices and exact SHA-256 digests (`ERR_CHUNK_CHECKSUM_MISMATCH` on tamper or missing chunks).
- **BRU-014-03 (BOM-Tolerant Manifest & CLI Precedence):** `wxc-exec` manifest parsing MUST tolerate leading UTF-8 BOM (`\u{FEFF}`) bytes (`100%` parse success) and resolve `--operation` / `--container-id` flags as explicit overrides over in-file `phase` / `sandboxId` keys.
- **BRU-014-04 (Declarative IDE Worker Profile):** IDE worker profiles MUST declare required toolchains, `mxc-sync` zero-secret posture, and compliant archetype sizing (`ADR-013`), rejecting incomplete specs (`ERR_WORKER_PROFILE_INVALID`).

---

## 3. Traceability

- **Topic Pillar:** `TP-13` | **ADR:** [ADR-015](../../07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | **FDD:** [FDD-014](../Functional-Design/FDD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) | **Epic:** [epic-014](../../user-stories/epic-014-snapshot-forking-vmbus-streaming-and-ide-workers.md) (`WBS 15.0`)
- **Hypotheses & Benefits:** `HYP-mxc-025`, `BEN-20` | **Improvements:** `IMP-MXC-019`, `IMP-MXC-021`, `IMP-MXC-022`, `IMP-MXC-027`
