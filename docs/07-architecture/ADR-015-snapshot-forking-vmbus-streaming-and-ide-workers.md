---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-13"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-005-transient-differencing-disk.md"
process: "Formulate architectural decisions for nested .avhdx snapshot branching, chunked binary VMBus streaming, BOM-tolerant wxc-exec manifest parsing, and declarative IDE worker profiles"
outputs:
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
status: "Proposed"
---

# ADR 015: Parallel Snapshot Branching, Chunked VMBus Streaming, BOM-Tolerant CLI & IDE Workers

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-13` Parallel Snapshot Branching, Chunked VMBus & Agentic CLI/IDE Ergonomics.  
> **Inputs:** [PILLARS-Phase-3.md](PILLARS-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md) (`HYP-mxc-025`), [ADR-005](ADR-005-transient-differencing-disk.md)  
> **Outputs:** ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md

---

## 1. Executive Summary

During Phase 2 live Hyper-V verification and Cursor "My Machines" integration (`PR #6`), four developer-experience and throughput constraints surfaced:
1. Autonomous coding agents benefit from testing 3–5 competing patches in parallel from one warm repo checkpoint (`IMP-MXC-027`).
2. Transferring repositories or bundles via `cmd.exe` or PowerShell strings hits the **8 KB `cmd.exe` command-line limit** and Base64 overhead (`IMP-MXC-021`).
3. Windows PowerShell 5.1's `Set-Content -Encoding utf8` writes a leading UTF-8 BOM (`\u{FEFF}`), breaking strict `serde_json` parsing in `wxc-exec`, alongside rejecting `"phase"` / `"sandboxId"` fields when CLI flags override them (`IMP-MXC-019`).
4. Ephemeral AI IDE workers (`Cursor`, `Antigravity`, `Claude Code`) need one standardized, repeatable MXC workload profile (`IMP-MXC-022`).

`ADR-015` unifies these four capabilities into MXC's high-velocity developer and coding-agent plane.

---

## 2. Decision & Architectural Mechanics

1. **Nested `.avhdx` Parallel Snapshot Branching (`wxc-exec --hyperv-op fork`, `IMP-MXC-027`):**
   - A warm parent checkpoint freezes clean repository + dependency state; up to `N <= 5` child differencing disks branch simultaneously against that immutable snapshot (`<= 500 ms` per fork) with bounded nesting depth (`max_fork_depth <= 4`).
   - Losing branches tear down cleanly without mutating the parent or winning branch (`0%` parent drift).
2. **Native Chunked Binary VMBus Streaming (`IMP-MXC-021`):**
   - Replace single-invocation Base64 CLI strings with fixed-size framed chunks (`chunk_bytes = 65536` / `1048576` configurable) carrying sequence numbers and per-chunk + overall SHA-256 verification so multi-100 MB archives stream reliably over airgapped VMBus.
3. **UTF-8 BOM-Tolerant Manifest Parser & Flag Precedence (`IMP-MXC-019`):**
   - Normalize manifest inputs by stripping leading `\u{FEFF}` BOM bytes before JSON deserialization and granting `--operation` / `--container-id` CLI flags explicit precedence over duplicate manifest keys (`phase`, `sandboxId`).
4. **First-Class Ephemeral IDE Worker Profile (`IMP-MXC-022`):**
   - Define a validated `IdeWorkerProfile` schema pairing archetype sizing (`ADR-013`), Git/toolchain bootstrap (`PR #6`), `mxc-sync` zero-secret repo binding (`ADR-014`), and scheduled agent runner health checks.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Clone full VHDX copies for each coding hypothesis | Copying 22 GB golden VHDXs per branch wastes tens of seconds and gigabytes of NVMe per agent attempt. |
| Require operators to remember UTF-8 No-BOM encodings everywhere in WinPS 5.1 | Fragile human/script trap already triggered repeatedly in live Hyper-V automation; making the parser BOM-tolerant fixes it once at the boundary. |
| Keep ad-hoc PowerShell Base64 one-liners for guest file sync | Hits the 8 KB `cmd.exe` limit and fails unpredictably on larger workspaces. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Unlocks concurrent multi-hypothesis coding agent runs, multi-100 MB VMBus transfers, reliable WinPS automation, and plug-and-play AI IDE remote workers (`BEN-20`).
- **Negative:** Nested differencing disks add minor block lookup indirection if left unpruned after multi-round trials.
- **Mitigation:** Enforce `max_fork_depth <= 4` (`ERR_FORK_DEPTH_EXCEEDED`) and automatically reap discarded branches immediately after winner selection.
