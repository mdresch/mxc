---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-16"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-010-predictive-wake-interception.md"
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
process: "Formulate architectural decisions for 640 MB paused floor, CrossGen2 ASLR page alignment, disposable trim bypass, NUMA pinning, RAM-disk/DAX differencing, eBPF/WFP TLS probes, differential telemetry, and GPU-P/DDA sandboxes"
outputs:
  - "docs/07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
status: "Proposed"
---

# ADR 018: Ultra-Density Memory, RAM-Disk/DAX Differencing, Kernel TLS Probes, Subsystem Telemetry & GPU-P Sandboxes

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-16` Next-Frontier Fleet Density, Zero-Wear Ephemeral I/O & GPU Agent Acceleration. Also touches `TP-04`, `TP-08`, `TP-09`.  
> **Inputs:** [PILLARS-Phase-3.md](PILLARS-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md) (`HYP-mxc-029`, `030`, `019`, `021`), [ADR-010](ADR-010-predictive-wake-interception.md), [ADR-011](ADR-011-hyperv-memory-combining-deduplication.md)  
> **Outputs:** ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md

---

## 1. Executive Summary

Phases 1 and 2 achieved ~1.1 GB raw paused RAM (`ADR-004`), `<= 450 MB` deduplicated effective RAM (`ADR-011`), user-space TLS SNI pre-wake (`ADR-010`), and file-backed NVMe `.avhdx` differencing (`ADR-005`). `ADR-018` captures the eight high-leverage hardware & kernel frontiers harvested across Epics 01–09 and our 2026 market scan:
- **Sub-350 MB Effective Density & Local NUMA Pinning** (`IMP-MXC-006`, `016`, `005`, `HYP-mxc-021`),
- **Pure In-Memory RAM-Disk / DAX Differencing & Root-Partition eBPF/WFP Kernel TLS + Neural Forecasting** (`IMP-MXC-012` / `HYP-mxc-019`, `IMP-MXC-014`, `015`), and
- **Automated Subsystem Differential Telemetry & Opt-In `GPU-P` / DDA Agent Sandboxes** (`IMP-MXC-001`, `IMP-MXC-029`).

---

## 2. Decision & Architectural Mechanics

1. **640 MB Paused Floor, CrossGen2 Normalization, Disposable Trim Bypass & Local NUMA Pinning:**
   - Prompt-only bake stripping + `EmptyWorkingSet` compresses paused baseline to `<= 640 MB` (`IMP-MXC-006`), while CrossGen2/NGEN base normalization (`IMP-MXC-016`) raises `ADR-011` page sharing to `>= 65%`, lowering effective host RAM to `< 350 MB/guest`.
   - Under whole-guest discard (`ADR-005 §4.3`), skip redundant post-session trim to save `>= 50 ms` teardown overhead (`IMP-MXC-005`).
   - Pin standby VMs to local host NUMA nodes (`Remote Physical Pages == 0`, `HYP-mxc-021`, `ERR_NUMA_REMOTE_PAGES`).
2. **In-Memory RAM-Disk / DAX Differencing & Kernel eBPF/WFP TLS + Neural Forecaster:**
   - Mount high-churn `.avhdx` overlays in quota-bounded host RAM-disk/DAX (`<= 50 ms` mount, `0` NVMe write bytes, `ERR_RAMDISK_QUOTA_EXCEEDED`) (`IMP-MXC-012` / `HYP-mxc-019`).
   - Root-partition eBPF/WFP TLS `ClientHello` filters cut 2–3 ms off tier promotions (`IMP-MXC-014`) alongside an online shift forecaster adapting to drifting burst curves (`IMP-MXC-015`).
3. **Differential Subsystem Telemetry & `GPU-P` / DDA Sandboxes:**
   - Pre-dispatch probe streams structured WMI, COM+, Service, and GPO health (`ERR_SUBSYSTEM_DEGRADED` on missing prerequisite, `IMP-MXC-001`).
   - Optional Hyper-V `GPU-P` / DDA profile exposes partitioned GPU compute (`>= 85%` native throughput, explicit `ERR_GPUP_UNSUPPORTED` on CPU-only hosts, clean GPU state clear on teardown, `IMP-MXC-029`).

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Leave NVMe `.avhdx` for extreme micro-session bursts | Causes high SSD write amplification and slower ephemeral teardown compared to bounded RAM-disk/DAX mounts. |
| Expose full unpartitioned host GPU to untrusted agents without cleanup | Violates isolation guarantees; `GPU-P`/DDA quotas and teardown scrubbing keep multi-tenant boundaries intact. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Pushes host capacity beyond Phase 2 ceilings (`< 350 MB` effective RAM), eliminates SSD wear on burst overlays, catches subsystem drift before dispatch, and unlocks GPU AI/RPA agents (`BEN-24`).
- **Negative:** RAM-disk overlays trade host DRAM for zero SSD wear, and `GPU-P`/NUMA features depend on physical host hardware topology.
- **Mitigation:** Enforce hard host RAM quotas (`ADR-013`) before RAM-disk allocation and detect `GPU-P` / NUMA capabilities explicitly fail-closed.
