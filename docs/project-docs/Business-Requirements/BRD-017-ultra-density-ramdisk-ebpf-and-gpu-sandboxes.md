---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
process: "Define business rules for 640 MB paused floor, CrossGen2 alignment, NUMA locality, RAM-disk differencing, eBPF/WFP TLS probes, subsystem telemetry, and GPU-P sandboxes"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
status: "Approved"
---

# BRD-017: Ultra-Density Memory, RAM-Disk/DAX Differencing, Kernel TLS Probes & GPU-P Sandboxes

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 3)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-018](../../07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | **Topic Pillar:** `TP-16` | **Status:** Approved (2026-11-24)

---

## 1. Business Need

Maximize fleet hardware ROI per 64–256 GB Hyper-V node (`< 350 MB` effective RAM/guest), eliminate NVMe SSD wear under high-churn agent execution, trim kernel TLS wake latency by 2–3 ms, guarantee healthy Windows subsystems pre-dispatch, and unlock GPU-accelerated AI/RPA agent workloads.

---

## 2. Business Rules (BRU)

- **BRU-017-01 (Sub-350 MB Effective Density & NUMA Locality):** Combined 640 MB paused floor + CrossGen2 normalization MUST yield `>= 65%` shared pages and `< 350 MB` effective RAM/guest, with `0` NUMA remote pages (`ERR_NUMA_REMOTE_PAGES`) and disposable trim bypass saving `>= 50 ms` teardown time.
- **BRU-017-02 (Quota-Bounded RAM-Disk / DAX Differencing):** RAM-disk differencing MUST enforce host DRAM quota ceilings (`ERR_RAMDISK_QUOTA_EXCEEDED`), achieve `<= 50 ms` mount/teardown, and incur **0 bytes** host NVMe write amplification.
- **BRU-017-03 (Kernel eBPF/WFP TLS & Neural Forecaster Bounds):** Root-partition TLS probes MUST shave `2–3 ms` off promotion latency without breaking non-TLS traffic, and the neural shift forecaster MUST keep false-positive pre-warm rate `<= 5.0%`.
- **BRU-017-04 (Pre-Dispatch Subsystem Telemetry Matrix):** Missing WMI, COM+, Service, or GPO prerequisites MUST be caught before dispatch (`ERR_SUBSYSTEM_DEGRADED`).
- **BRU-017-05 (Fail-Closed `GPU-P` / DDA Profile):** `GPU-P`/DDA sandboxes MUST verify `>= 85%` normalized throughput and clear allocations on teardown, returning `ERR_GPUP_UNSUPPORTED` on CPU-only hosts.

---

## 3. Traceability

- **Topic Pillar:** `TP-16` | **ADR:** [ADR-018](../../07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | **FDD:** [FDD-017](../Functional-Design/FDD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | **Epic:** [epic-017](../../user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) (`WBS 18.0`)
- **Hypotheses & Benefits:** `HYP-mxc-029`, `030`, `019`, `021`, `BEN-24` | **Improvements:** `IMP-MXC-001`, `005`, `006`, `012`, `014`, `015`, `016`, `029`
