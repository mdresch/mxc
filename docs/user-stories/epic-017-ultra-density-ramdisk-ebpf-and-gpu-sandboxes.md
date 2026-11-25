---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
  - "docs/project-docs/Business-Requirements/BRD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
  - "docs/project-docs/Functional-Design/FDD-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
process: "Decompose ultra-density memory floor, CrossGen2 normalization, NUMA pinning, RAM-disk/DAX differencing, kernel TLS probes, subsystem telemetry, and GPU-P sandboxes into testable user stories"
outputs:
  - "docs/user-stories/epic-017-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
status: "Approved — Ready for Implementation"
---

# Epic 017: Ultra-Density Memory, RAM-Disk/DAX Differencing, Kernel TLS Probes & GPU-P Sandboxes

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 3)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-018](../07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | **WBS:** `18.0` | **Topic Pillar:** `TP-16`  
> **Status:** Approved — Ready for Implementation (2026-11-24) (`IMP-MXC-001`, `005`, `006`, `012`, `014`, `015`, `016`, `029` + `HYP-mxc-019`, `021`)

---

## Story 17.1 — 640 MB Paused Floor, CrossGen2 Alignment, Disposable Trim Bypass & Local NUMA Pinning
- **WBS:** 18.1
- **Status:** Planned
- **As a** Hyper-V Capacity Architect,  
  **I want** `evaluate_density_and_numa()` to enforce a `<= 640 MB` paused baseline, CrossGen2 `>= 65%` page sharing (`< 350 MB` effective RAM/guest), `0` remote NUMA pages, and disposable in-session trim bypass,  
  **so that** enterprise 64 GB hosts sustain ultra-high micro-VM density with zero cross-socket bus penalty.
- **Acceptance Criteria:**
  - **AC-17.1.1:** With `paused_ram_mb <= 640.0`, `shared_page_ratio >= 0.65`, and `remote_numa_pages == 0`, effective RAM calculates strictly `< 350.0 MB` and `trim_bypass_ms_saved == 50.0` when `disposable_discard=True`.
  - **AC-17.1.2:** Non-finite floats (`NaN`/`inf`), out-of-range `shared_page_ratio` outside `[0.0, 1.0]`, or `remote_numa_pages > 0` (`ERR_NUMA_REMOTE_PAGES`) raise `ValueError`.

---

## Story 17.2 — Pure In-Memory RAM-Disk/DAX Differencing, Kernel TLS Probes & Neural Forecaster
- **WBS:** 18.2
- **Status:** Planned
- **As a** High-Throughput Infrastructure Engineer,  
  **I want** quota-bounded RAM-disk/DAX differencing (`<= 50 ms` mount, `0` NVMe write bytes) alongside root-partition eBPF/WFP TLS ClientHello probing and continuous neural pre-warm forecasting,  
  **so that** high-churn bursts eliminate SSD wear and shave 2–3 ms off predictive tier wake.
- **Acceptance Criteria:**
  - **AC-17.2.1:** `allocate_ramdisk_overlay()` succeeds when `0 < requested_mb <= available_ramdisk_mb` and `mount_latency_ms <= 50.0`, rejecting quota overflow (`ERR_RAMDISK_QUOTA_EXCEEDED`), non-finite values, or empty/zero requests fail-closed.
  - **AC-17.2.2:** `inspect_kernel_tls_promotion()` parses TLS `ClientHello` SNI hints and non-TLS payloads cleanly (empty `packet_bytes` returns safe pass-through dict), triggers fast promotion when `neural_prewarm_confidence >= 0.90` and `false_positive_rate <= 0.05`.

---

## Story 17.3 — Automated Subsystem Differential Telemetry Matrix & `GPU-P`/DDA Agent Sandbox Tier
- **WBS:** 18.3
- **Status:** Planned
- **As a** Windows & AI Platform Lead,  
  **I want** pre-dispatch WMI/COM+/Service/GPO differential telemetry verification and an opt-in `GPU-P`/DDA sandbox profile with explicit hardware capability gating,  
  **so that** degraded Windows guests are caught prior to lease and GPU-accelerated agents achieve `>= 85%` throughput without cross-session residue.
- **Acceptance Criteria:**
  - **AC-17.3.1:** `evaluate_subsystem_differential_matrix()` returns `(True, "OK")` only when WMI, COM+, Services, and GPO checks all report healthy, and fails closed (`(False, "ERR_SUBSYSTEM_DEGRADED")`) on `None`, empty dicts, or any unhealthy subsystem.
  - **AC-17.3.2:** `provision_gpup_sandbox()` admits partitioned guests when `gpu_supported=True`, `0.0 < partition_ratio <= 1.0`, and `throughput_ratio >= 0.85`, failing closed with `ERR_GPUP_UNSUPPORTED` on CPU-only hosts and `ERR_GPUP_SLA_BELOW_FLOOR` below `0.85`.
