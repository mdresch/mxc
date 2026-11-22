---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
  - "docs/project-docs/Business-Requirements/BRD-009-memory-combining-deduplication.md"
process: "Specify Hyper-V page sharing configuration, performance counter hooks, and COW verification probes"
outputs:
  - "docs/project-docs/Functional-Design/FDD-009-memory-combining-deduplication.md"
status: "Approved"
---

# FDD-009: Hyper-V Host-Level Memory Combining & Deduplication

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md), [BRD-009](../Business-Requirements/BRD-009-memory-combining-deduplication.md)  
> **Process:** Specify Hyper-V page sharing configuration, performance counter hooks, and COW verification probes  
> **Outputs:** FDD-009-memory-combining-deduplication.md

**Source ADR:** [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md) — Hyper-V Host-Level Memory Combining & Fleet Page Deduplication  
**Source BRD:** [BRD-009](../Business-Requirements/BRD-009-memory-combining-deduplication.md)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved  

---

## 1. Technical Architecture & Interfaces

### 1.1 Hyper-V Memory Combining Subsystem
Hyper-V Page Sharing scans physical guest page tables in the host root partition (`vid.sys` and `vmswitch.sys`).
```
+-------------------------------------------------------------------------------+
| Hyper-V Root Partition (Host)                                                 |
|                                                                               |
|  [ Memory Combining Background Scanner (Priority: Low / Idle) ]              |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | Host Physical RAM (Shared Read-Only COW Pool)                           |  |
|  |   [ Shared ntoskrnl.exe ] [ Shared coreclr.dll ] [ Shared user32.dll ]  |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
         ^                               ^                               ^
         | Page Table Pointer (RO)       | Page Table Pointer (RO)       | Page Table Pointer (RO)
+-----------------+             +-----------------+             +-----------------+
| Guest VM #1     |             | Guest VM #2     |             | Guest VM #3     |
| (Windows 2025)  |             | (Windows 2025)  |             | (Windows 2025)  |
| - Private Heap  |             | - Private Heap  |             | - Private Heap  |
+-----------------+             +-----------------+             +-----------------+
```

### 1.2 Telemetry & Diagnostic Interface (`scripts/lib/memory_combining_probe.py`)
- **Performance Counter Set:** `\Hyper-V Dynamic Memory(*)\*`
  - `Memory Combining Shared Pages`: Number of 4 KB physical pages currently merged.
  - `Memory Combining Saved Memory (MB)`: Physical RAM freed on the host.
  - `Memory Combining CPU Usage`: Root partition CPU consumed by the scanner.
- **Probe Function:**
  ```python
  def get_fleet_deduplication_metrics() -> MemoryDeduplicationReport:
      """Polls Hyper-V WMI performance counters and returns host memory metrics."""
  ```

---

## 2. Invariant Contracts & Error Handling

| Metric / Check | Contract Invariant | Verification Method |
|---|---|---|
| **COW Isolation** | Modifying a shared page in VM #1 must never alter memory in VM #2. | Automated contract test writes canary value to shared mapped file and checks peer VM memory. |
| **Scanner Throttling** | If host CPU utilization exceeds 80%, the memory combining scan rate is automatically throttled down. | WMI dynamic tuning hook. |
| **Effective Memory Bound** | Total Host RAM / Total VMs $\le 450\text{ MB}$ per guest at steady state. | Performance monitor audit assertion (`AC-9.2.1`). |
