---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md"
  - "docs/project-docs/Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md"
process: "Specify compiled Rust interfaces for UTF-8 BOM manifest parsing, CLI overrides, chunked VMBus framing, snapshot forking, and zero-secret git-sync"
outputs:
  - "docs/project-docs/Functional-Design/FDD-018-native-rust-wxc-exec-phase3-parity.md"
status: "Approved"
---

# FDD-018: Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Runtime Parity

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-019](../../07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md) | **Source BRD:** [BRD-018](../Business-Requirements/BRD-018-native-rust-wxc-exec-phase3-parity.md)

---

## 1. Technical Interfaces (`src/tools/wxc/src/` & `src/mxc-sdk/src/`)

```rust
// BOM-tolerant manifest parser & CLI override precedence
pub fn parse_manifest_bom_safe(
    raw_bytes: &[u8],
    cli_operation: Option<&str>,
    cli_container_id: Option<&str>,
) -> Result<serde_json::Value, String>;

// Chunked binary VMBus framing
pub struct VmbusChunkFrame {
    pub seq: usize,
    pub total_frames: usize,
    pub data: Vec<u8>,
    pub chunk_sha256: String,
    pub stream_sha256: String,
}
pub fn chunk_payload_frames(payload: &[u8], chunk_size_bytes: usize) -> Result<Vec<VmbusChunkFrame>, String>;
pub fn reassemble_chunk_frames(frames: &[VmbusChunkFrame]) -> Result<Vec<u8>, String>;

// Bounded parallel snapshot forking & zero-secret git-sync
pub fn create_parallel_forks(
    parent_checkpoint_id: &str,
    branch_names: &[&str],
    current_depth: usize,
    max_depth: usize,
    max_parallel: usize,
) -> Result<Vec<SnapshotBranch>, String>;

pub fn scan_git_sync_secrets(
    remote_url: Option<&str>,
    guest_env: &[(&str, &str)],
) -> Result<(), String>;
```

---

## 2. Error Codes & Parity Invariants

| Condition | Error Code | Parity Target |
|---|---|---|
| Leading UTF-8 BOM `\xEF\xBB\xBF` + `phase`/`sandboxId` | Stripped & normalized with CLI precedence | `IMP-MXC-019` (`LL-015`) |
| Corrupted chunk digest, missing/out-of-order `seq` | `ERR_CHUNK_CHECKSUM_MISMATCH` | `IMP-MXC-021` (`LL-015`) |
| `current_depth + 1 > max_depth` or `len > max_parallel` / empty | `ERR_FORK_DEPTH_EXCEEDED` / `ERR_FORK_BOUNDS_INVALID` | `IMP-MXC-027` (`LL-015`) |
| Token-boundary PAT/key in `remote_url` or `guest_env` (`PATH` allowed) | `ERR_STATIC_SECRET_DETECTED` | `IMP-MXC-017` (`LL-014`) |
