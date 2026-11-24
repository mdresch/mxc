---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-09"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/07-architecture/PILLARS-Phase-2.md"
process: "Formulate architectural decisions for host-level Hyper-V Page Sharing and memory combining across identical micro-VMs"
outputs:
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
status: "Approved"
---

# ADR 011: Hyper-V Host-Level Memory Combining & Fleet Page Deduplication

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 2)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-09` Host Memory Deduplication. Also touches `TP-04` (Paused Footprint).  
> **Inputs:** [Spark-Capture-Phase-2.md](../project-docs/Spark-Capture-Phase-2.md), [Ideation-Document-Phase-2.md](../project-docs/Ideation-Document-Phase-2.md), [Benefits-Statement-Phase-2.md](../project-docs/Benefits-Statement-Phase-2.md)  
> **Outputs:** ADR-011-hyperv-memory-combining-deduplication.md

---

## 1. Executive Summary

Phase 1 trimmed the internal guest working set prior to pause, achieving ~1024–1228 MB assigned RAM per guest. However, when deploying 50–100 micro-instances on a 64 GB host, physical host RAM is quickly exhausted.

Because all standby instances run identical Windows Server 2025 golden images, large memory regions—including `ntoskrnl.exe`, .NET CLR binaries, `user32.dll`, COM+ runtime infrastructure, and read-only assemblies—are bit-for-bit identical across all guests.

`ADR-011` enables and orchestrates **Hyper-V Host-Level Page Sharing & Memory Combining**, compressing physical host memory consumption from 640–1024 MB down to **300–450 MB effective RAM per guest**. This refinement yields greater density improvements than further guest trimming alone.

---

## 2. Decision & Architectural Mechanics

1. **Hyper-V Memory Combining Architecture:**
   - Host hypervisor background scanner scans guest memory pages and merges identical read-only pages into single copy-on-write (COW) physical host pages.
   - Any guest write operation instantly unshares the page via hardware COW fault without affecting peer guests.
2. **Deterministic Golden Bake Page Alignment:**
   - Base image baking (`ADR-003`) is updated to enforce consistent memory layout:
     - ASLR base randomization within shared system DLLs is normalized across standby fleet builds where feasible.
     - NGEN/.NET CrossGen2 pre-compilation is pre-baked, eliminating dynamic JIT cache variation across instances.
3. **Telemetry & Verification:**
   - Performance counters monitored:
     - `\Hyper-V Dynamic Memory\Memory Combining Shared Pages`
     - `\Hyper-V Dynamic Memory\Memory Combining Saved Memory (MB)`
   - Target deduplication ratio: $\ge 40\%$ shared page coverage across standby instances.

---

## 3. Consequences & Trade-Offs

- **Positive:** Reduces physical host memory per paused guest to 300–450 MB. Enables 120–160 micro-VMs on a standard 64 GB enterprise host.
- **Negative:** Background page scanner consumes fractional host CPU ($< 0.5\%$).
- **Mitigation:** Memory scanner is configured to run at low I/O priority during periods of active tenant execution and schedule deep scans during quiescent standby intervals.
