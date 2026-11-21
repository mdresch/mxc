---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-011-hyperv-memory-combining-deduplication.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/Ideation-Document-Phase-2.md"
process: "Decompose host-level Hyper-V Page Sharing and memory deduplication into testable user stories"
outputs:
  - "docs/user-stories/epic-009-memory-combining-deduplication.md"
status: "Draft / Ready for Planning"
---

# Epic 009: Hyper-V Host-Level Memory Combining & Deduplication

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 2)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-011](../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md)  
> **Target Baseline:** `PMP-BL-v2.0.0` | **WBS Index:** 10.0  
> **Status:** Draft / Ready for Planning

---

## Story 9.1 — Hyper-V Page Sharing Configuration & Diagnostic Probe
- **WBS:** 10.1
- **As a** Virtualization Infrastructure Engineer,  
  **I want** to orchestrate Hyper-V Memory Combining across identical Windows Server 2025 standby micro-instances,  
  **so that** redundant read-only system and runtime pages are shared at the hypervisor layer.
- **Acceptance Criteria:**
  - **AC-9.1.1:** Memory combining scan is configured and verified via WMI/PowerShell hypervisor settings.
  - **AC-9.1.2:** Diagnostic probe reads `\Hyper-V Dynamic Memory\Memory Combining Shared Pages` and verifies non-zero page sharing across paused instances.

---

## Story 9.2 — Deduplication Floor & Host Saturation Verification
- **WBS:** 10.2
- **As a** Capacity Planner,  
  **I want** to verify that 40 identical paused micro-instances consume $\le 450\text{ MB}$ effective host RAM each,  
  **so that** host tenant density can be expanded to $\ge 120$ micro-VMs on a 64 GB host.
- **Acceptance Criteria:**
  - **AC-9.2.1:** Net host physical memory consumption across 40 identical standby VMs does not exceed 18 GB.
  - **AC-9.2.2:** Copy-On-Write (COW) memory isolation is verified: page modifications in one tenant VM never corrupt or leak into peer VM memory.
