---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Benefits-Statement-Phase-2.md"
  - "docs/user-stories/epic-009-memory-combining-deduplication.md"
process: "Define business requirements and capacity rules for Hyper-V host-level page sharing and memory deduplication"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-009-memory-combining-deduplication.md"
status: "Approved"
---

# BRD-009: Hyper-V Host-Level Memory Combining & Deduplication

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 2)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md), [Project-Charter-Phase-2.md](../Project-Charter-Phase-2.md), [Benefits-Statement-Phase-2.md](../Benefits-Statement-Phase-2.md)  
> **Process:** Define business requirements and capacity rules  
> **Outputs:** BRD-009-memory-combining-deduplication.md

**Source ADR:** [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md) — Hyper-V Host-Level Memory Combining & Fleet Page Deduplication  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved  
**Stakeholders:** Menno Drescher (Product Owner / Architect), Datacenter Operations, FinOps Team  

---

## 1. Business Need

With 80+ micro-instances running identical Windows Server 2025 images, allocating 640–1024 MB of dedicated physical host RAM per instance rapidly exhausts physical host capacity on standard 64 GB nodes. Because operating system kernels, .NET CLR assemblies, and core Windows DLLs are bit-for-bit identical across all guests, host-level memory combining enables massive RAM consolidation, compressing effective host memory to 300–450 MB per guest and doubling fleet density.

---

## 2. Business Rules (BRU)

- **BRU-009-01 (Host Memory Deduplication Floor):** Effective physical host memory consumption for paused identical standby instances must not exceed **450 MB per guest** when measured across a cohort of $\ge 20$ instances.
- **BRU-009-02 (Zero Isolation Compromise):** Page sharing must operate strictly via hardware-enforced Copy-On-Write (COW). Any guest writing to a shared page must trigger an immediate fault that clones the page into private memory with zero cross-tenant contamination.
- **BRU-009-03 (Host CPU Overhead Cap):** The background memory combining scanner must not consume more than **0.5% aggregate host CPU** during steady-state operation.
- **BRU-009-04 (Density Target):** Fleet infrastructure must support $\ge 120$ micro-instances on a single 64 GB host without inducing memory balloon starvation or host swapping.

---

## 3. Stakeholder Success Metrics

| Metric | Business Target | Baseline Reference |
|---|---|---|
| **Effective RAM per Guest** | $\le 450\text{ MB}$ host RAM | `BEN-14` / `HYP-mxc-017` |
| **Fleet Deduplication Ratio** | $\ge 40\%$ shared memory pages | `HYP-mxc-017` |
| **Scanner CPU Overhead** | $< 0.5\%$ host CPU | `HYP-mxc-017` |
| **Practical Host Density** | $\ge 120$ micro-VMs per 64 GB host | `BEN-15` |

---

## 4. Traceability

- **Topic Pillar:** `TP-09` Host Memory Deduplication
- **Architectural Decision:** [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md)
- **User Story Epic:** [epic-009-memory-combining-deduplication.md](../../user-stories/epic-009-memory-combining-deduplication.md) (WBS 10.0)
- **Hypotheses:** `HYP-mxc-017`

---

## 5. Out of Scope

- Guest-internal heap compression beyond pre-suspend working set trimming (`ADR-004`).
- Storage-level block deduplication on differencing disks (`ADR-005`).
