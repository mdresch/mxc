---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-17"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/07-architecture/PILLARS-Phase-4.md"
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md"
process: "Specify compiled Rust implementation architecture for UTF-8 BOM manifest parsing, CLI override precedence, chunked VMBus framing, snapshot forking, and zero-secret git-sync"
outputs:
  - "docs/07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md"
status: "Approved"
---

# ADR 019: Native Rust `wxc-exec` & `mxc-sdk` Phase 3 Runtime Parity

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 4)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-17` Native Rust `wxc-exec` & `mxc-sdk` Runtime Parity. Also touches `TP-12`, `TP-13`.  
> **Inputs:** [PILLARS-Phase-4.md](PILLARS-Phase-4.md), [Ideation-Document-Phase-4.md](../project-docs/Ideation-Document-Phase-4.md) (`HYP-mxc-031`), [ADR-014](ADR-014-zero-secret-sidecar-and-mcp-firewall.md), [ADR-015](ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md)  
> **Outputs:** ADR-019-native-rust-wxc-exec-phase3-parity.md

---

## 1. Executive Summary

Phase 3 verified the zero-secret `mxc-sync`, bounded parallel `.avhdx` snapshot forking, chunked binary VMBus framing, and UTF-8 BOM-tolerant manifest parsing invariants in Python (`scripts/lib/zero_secret_mcp_gateway.py` and `scripts/lib/snapshot_fork_and_vmbus.py`). `ADR-019` ports these primitives natively into `src/tools/wxc/` (`wxc-exec.exe`) and `src/mxc-sdk/` so operators and AI coding agents execute a single compiled Rust binary with zero Python runtime dependency and exact error-code parity.

---

## 2. Decision & Architectural Mechanics

1. **BOM-Tolerant Manifest Deserialization & CLI Override Precedence (`src/tools/wxc/src/main.rs`):**
   - Strip leading UTF-8 BOM bytes (`\xEF\xBB\xBF` / `'\u{FEFF}'`) prior to `serde_json::from_str`.
   - Accept manifests containing `phase` and `sandboxId` while treating explicit `--operation` and `--container-id` CLI flags as authoritative overrides.
2. **Native Chunked Binary VMBus Framing (`src/mxc-sdk/`):**
   - Split arbitrary payloads (`0 B` through `>= 100 MB`) into fixed frames (`65536` bytes default) carrying `seq`, `total_frames`, `chunk_sha256`, and `stream_sha256`, failing closed with `ERR_CHUNK_CHECKSUM_MISMATCH` on tamper, truncation, or out-of-order frames.
3. **Bounded Parallel Snapshot Forking (`--hyperv-op fork`) & Zero-Secret Git Sync (`--hyperv-op git-sync`):**
   - Enforce `max_depth <= 4` (`ERR_FORK_DEPTH_EXCEEDED`) and `max_parallel <= 5` (`ERR_FORK_BOUNDS_INVALID`) in `<= 500 ms` per branch with immutable parent hash preservation.
   - Run token-boundary static secret scanning (`ERR_STATIC_SECRET_DETECTED`, avoiding `PATH`/`PAT` false positives per `LL-014`) before shipping bare git bundles over `0`-NIC VMBus.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Invoke Python `scripts/lib/*.py` as subprocesses from `wxc-exec.exe` | Adds Python runtime dependency to sovereign single-binary deployments and introduces process-spawn latency. |
| Diverge Rust error codes from Phase 3 Python contracts | Breaks cross-language contract verification and audit log correlation (`RISK-P4-02`). |

---

## 4. Consequences & Trade-Offs

- **Positive:** Single-binary compiled Rust execution (`BEN-25`), zero PowerShell BOM failures, and bit-exact multi-100 MB VMBus transfers.
- **Negative:** Requires maintaining shared fixture parity between Rust `cargo test` and Python `pytest` suites.
- **Mitigation:** Share canonical error codes and JSON test vectors across both suites.
