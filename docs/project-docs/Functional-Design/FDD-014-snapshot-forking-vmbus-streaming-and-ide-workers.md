---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
  - "docs/project-docs/Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
process: "Specify snapshot-fork manager, chunked binary VMBus streamer, BOM-tolerant manifest parser, and IDE worker profile validator"
outputs:
  - "docs/project-docs/Functional-Design/FDD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md"
status: "Proposed"
---

# FDD-014: Parallel Snapshot Branching, Chunked VMBus Streaming, BOM-Tolerant CLI & IDE Workers

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-015](../../07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | **Source BRD:** [BRD-014](../Business-Requirements/BRD-014-snapshot-forking-vmbus-streaming-and-ide-workers.md)  
> **Governing Baseline:** `PMP-BL-v3.0.0-candidate` | **Status:** Proposed

---

## 1. Technical Architecture & Interfaces (`scripts/lib/snapshot_fork_and_vmbus.py`)

```python
@dataclass(frozen=True)
class SnapshotBranch:
    branch_id: str
    parent_checkpoint_id: str
    depth: int
    diff_disk_path: str
    status: str  # "ACTIVE" | "DISCARDED"

def create_parallel_forks(
    parent_checkpoint_id: str,
    branch_names: list[str],
    *,
    current_depth: int = 0,
    max_depth: int = 4,
    max_parallel: int = 5,
) -> list[SnapshotBranch]: ...

def chunk_payload_frames(
    payload: bytes,
    *,
    chunk_size_bytes: int = 65536,
) -> list[dict]: ...

def reassemble_chunk_frames(frames: list[dict]) -> bytes: ...

def parse_wxc_manifest_bom_safe(
    raw_bytes: bytes,
    *,
    cli_operation: str | None = None,
    cli_container_id: str | None = None,
) -> dict: ...

def validate_ide_worker_profile(profile: dict) -> tuple[bool, str]: ...
```

---

## 2. Invariant Contracts & Error Codes

| Condition | Error / Return | Contract |
|---|---|---|
| `current_depth + 1 > max_depth` or `len(branch_names) > max_parallel` or empty `branch_names` | Raises `ValueError` (`ERR_FORK_DEPTH_EXCEEDED` / invalid bounds) | Prevents unbounded `.avhdx` chain growth. |
| Corrupted chunk digest or missing sequence index | Raises `ValueError` (`ERR_CHUNK_CHECKSUM_MISMATCH`) | Bit-exact transfer integrity required across empty/100MB+ streams. |
| UTF-8 BOM `\xef\xbb\xbf` + duplicate `phase` / `sandboxId` in manifest | Parsed cleanly with CLI override precedence | Resolves Windows PowerShell 5.1 BOM failures. |
| Missing `ide_client`, missing toolchain list, or non-zero guest secrets in IDE profile | Returns `(False, "ERR_WORKER_PROFILE_INVALID")` | Ensures Cursor/Antigravity/Claude Code workers remain zero-secret. |
