---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-19"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/07-architecture/PILLARS-Phase-4.md"
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md"
process: "Specify bare-metal Hyper-V silicon HIL benchmark harness and honest fail-closed hardware capability probing"
outputs:
  - "docs/07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# ADR 021: Bare-Metal Silicon HIL Verification Harness (Density, RAM-Disk, NUMA, TEE & `GPU-P`)

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 4)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-19` Bare-Metal Silicon HIL Verification Harness. Also touches `TP-14`, `TP-16`.  
> **Inputs:** [PILLARS-Phase-4.md](PILLARS-Phase-4.md), [Ideation-Document-Phase-4.md](../project-docs/Ideation-Document-Phase-4.md) (`HYP-mxc-033`), [ADR-016](ADR-016-eu-evidence-ledger-and-confidential-attestation.md), [ADR-018](ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md)  
> **Outputs:** ADR-021-bare-metal-silicon-hil-verification-harness.md

---

## 1. Executive Summary

`ADR-021` defines an automated, read-safe Hardware-in-the-Loop (HIL) silicon verification harness (`scripts/hyperv/` + `scripts/lib/silicon_hil_harness.py`) that probes real Hyper-V host hardware capabilities and emits structured JSON benchmark reports for paused RAM floor (`<= 640 MB`), CrossGen2 shared page density (`< 350 MB` effective RAM), RAM-disk/DAX overlay mount latency (`<= 50 ms`, `0` NVMe writes), local NUMA node pinning (`0` remote pages), vTPM 2.0 / AMD SEV-SNP / Intel TDX attestation, and `GPU-P`/DDA throughput (`>= 85%`).

---

## 2. Decision & Architectural Mechanics

1. **Honest Capability Probing (`NO_FAKED_HARDWARE_PASS`):**
   - Every hardware tier checks real host capabilities first (`Get-VMHost`, `Get-VMHostNumaNode`, `Get-VMHostPartitionableGpu`, TPM/SEV-SNP/TDX flags).
   - Unsupported workstations return explicit fail-closed verdicts (`ERR_TEE_UNSUPPORTED`, `ERR_GPUP_UNSUPPORTED`, `SKIPPED_NO_MULTISOCKET_NUMA`) rather than fabricating passing silicon scores.
2. **Non-Destructive Host Isolation:**
   - Benchmark runs create ephemeral test VMs anchored to read-only golden parents and verify parent SHA-256 invariance before and after every run; they NEVER touch `Windows 11 Pro Dev` or active user sandboxes (`hv:930733af`).
3. **Structured Evidence Emission:**
   - Emits canonical JSON benchmark reports feeding Stage 12 `OUTCOME-Phase-4-Actual-Outcomes.md` and `classify-hypothesis-status`.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Mock hardware counters as passing on unsupported laptops | Violates SIDPA empirical honesty and masks real silicon deployment failures (`RISK-P4-03`). |
| Run destructive benchmarks against existing user VMs | Risks corrupting live development workspaces and golden parent VHDXs. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Produces auditable, reproducible silicon proof on both workstation and Windows Server 2025 hosts (`BEN-27`).
- **Negative:** Full SEV-SNP/TDX and `GPU-P` throughput confirmation requires executing the harness on capable Server 2025 hardware.
- **Mitigation:** Harness runs deterministically on local Windows 11 Pro hosts today (proving density, parent immutability, and fail-closed capability detection) and runs identically on Server 2025 pilot hosts without code changes.
