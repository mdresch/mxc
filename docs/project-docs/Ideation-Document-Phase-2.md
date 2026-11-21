---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation (Phase 2)"
lifecycle_stage: "Stage 3 (Hypothesis)"
governance_policy: "classify-hypothesis-status"
pmp_baseline: "PMP-BL-v2.0.0-candidate"
inputs:
  - "docs/project-docs/Spark-Capture-Phase-2.md"
  - "docs/project-docs/Project-Charter-Phase-2.md"
  - "docs/project-docs/OUTCOME-Phase-1-Actual-Outcomes.md"
  - "docs/registers/Continuous-Improvement-Register.md"
process: "Formulate empirical Phase 2 hypotheses with measurable falsification criteria"
outputs:
  - "docs/project-docs/Ideation-Document-Phase-2.md"
status: "Formulated"
---

# Ideation Document — Phase 2: Predictive Orchestration, Memory Deduplication & Enterprise Execution Fabric

> **PMBOK 8 Process:** `Pre-Project / Design Assumption Formulation (Phase 2)` (Initiating)  
> **Governance Policy:** `classify-hypothesis-status` | **Lifecycle Stage:** `Stage 3 (Hypothesis)`  
> **Inputs:** [Spark-Capture-Phase-2.md](Spark-Capture-Phase-2.md), [Project-Charter-Phase-2.md](Project-Charter-Phase-2.md), [Continuous-Improvement-Register.md](../registers/Continuous-Improvement-Register.md)  
> **Process:** Formulate empirical Phase 2 hypotheses with measurable falsification criteria  
> **Outputs:** Ideation-Document-Phase-2.md, Hypotheses HYP-mxc-015 through HYP-mxc-022

---

## 1. Executive Summary & Intent

Phase 2 advances the validated Type-1 Hyper-V Gen2 micro-VM foundation into a predictive, multi-tier enterprise execution fabric. The design assumptions governing this next evolutionary stage are formalized as eight testable, falsifiable hypotheses (`HYP-mxc-015` through `HYP-mxc-022`).

---

## 2. Phase 2 Hypotheses

### HYP-mxc-015: Multi-Tier Standby Economics & Response Slicing
- **Statement:** Partitioning the standby capacity into Hot (running), Warm (paused), and Cold (saved VM) tiers delivers sub-5ms dispatch for top-tier tenants while reducing aggregate idle host RAM by $\ge 40\%$ compared to an all-warm pool.
- **Empirical Evaluation Criteria:**
  1. Hot tier instance dispatch completes in $\le 5\text{ ms}$ TTFB.
  2. Warm tier instance unpauses in $\le 250\text{ ms}$.
  3. Cold tier VM restore from disk checkpoint completes in $\le 4.0\text{ s}$.
  4. Aggregate host RAM consumption for 100 provisioned tenants (10 Hot, 20 Warm, 70 Cold) does not exceed 35 GB host RAM.
- **Status:** Formulated

### HYP-mxc-016: Zero Perceived Wake via Predictive Pre-Warming
- **Statement:** Intercepting early TLS ClientHello / SNI frames and combining them with historical time-series activity forecasting pre-warms instances ahead of traffic bursts, achieving 0 ms perceived wake latency for $\ge 95\%$ of active requests.
- **Empirical Evaluation Criteria:**
  1. Early TLS ClientHello extraction initiates VM wake $\ge 50\text{ ms}$ before the HTTP payload completes.
  2. Activity forecasting accurately predicts recurring workload windows ($\pm 60\text{ s}$) with precision $\ge 90\%$.
  3. End-to-end client perceived TTFB is indistinguishable from an always-on VM ($< 10\text{ ms}$).
- **Status:** Formulated

### HYP-mxc-017: Host-Level Hyper-V Memory Combining & Page Sharing
- **Statement:** Enabling Hyper-V Page Sharing across identical Windows Server 2025 guest kernels, .NET runtimes, and system binaries reduces the effective host physical memory consumption from 640–1024 MB down to 300–450 MB per paused guest.
- **Empirical Evaluation Criteria:**
  1. Performance counter `\Hyper-V Dynamic Memory\Memory Combining Shared Pages` records positive deduplication.
  2. Net host physical RAM consumption for 40 identical paused guests is $\le 18\text{ GB}$ (effective $\le 450\text{ MB/guest}$).
  3. Memory combining introduces zero CPU overhead ($< 0.5\%$ host CPU during scan) and zero page-corruption errors.
- **Status:** Formulated

### HYP-mxc-018: End-to-End Cryptographic Supply Chain & SLSA Attestation
- **Statement:** Enforcing SLSA Level 3 provenance with Sigstore/Cosign image signatures and CycloneDX SBOM verification at pool registration eliminates untrusted image execution without impacting deployment velocity.
- **Empirical Evaluation Criteria:**
  1. `PoolRegistrationGuard` strictly rejects any golden base image lacking a valid cryptographic signature.
  2. Verification latency at registration is $\le 100\text{ ms}$.
  3. 100% of deployed images trace to reproducible Git commit SHAs and audited SBOM manifests.
- **Status:** Formulated

### HYP-mxc-019: Pure In-Memory Ephemeral RAM-Disk Differencing Layers
- **Statement:** Backing transient `.avhdx` differencing disks by an ephemeral RAM-disk storage tier eliminates NVMe I/O wear and reduces session discard / recreate cycles to $< 50\text{ ms}$.
- **Empirical Evaluation Criteria:**
  1. Child differencing layer creation and mount latency is $\le 50\text{ ms}$.
  2. Host physical disk write operations during session lifecycle measure exactly 0 bytes.
- **Status:** Formulated

### HYP-mxc-020: Time-Series Predictive Pre-Warming Accuracy
- **Statement:** Workload time-series modeling of tenant request frequency accurately forecasts surge events $\ge 120\text{ seconds}$ in advance, maintaining $K_{\min}$ buffer depth without reactive surge starvation.
- **Empirical Evaluation Criteria:**
  1. Standby pool buffer starvation rate during scheduled traffic spikes is 0.0%.
  2. False positive pre-warm rate remains $\le 5.0\%$.
- **Status:** Formulated

### HYP-mxc-021: NUMA-Aware Micro-VM Placement & Core Affinity
- **Statement:** Pinning standby VM memory and vCPU scheduling to matching host NUMA nodes reduces cross-socket bus contention and improves resume latency by $\ge 15\%$ on dual-socket enterprise hosts.
- **Empirical Evaluation Criteria:**
  1. 100% of guest RAM resides on the local NUMA node (`\Hyper-V VM Vid Partition\Remote Physical Pages` == 0).
  2. Resume latency variance drops by $\ge 20\%$.
- **Status:** Formulated

### HYP-mxc-022: Autonomous Fleet Economics Sizing Controller
- **Statement:** A dynamic closed-loop feedback controller dynamically adjusting pool low-watermark and tier boundaries optimizes cost-per-session while maintaining $\le 85\%$ host RAM saturation under peak load.
- **Empirical Evaluation Criteria:**
  1. Host memory never breaches 90% emergency threshold under 2x surge.
  2. Cooldown reaping reclaims idle capacity within 180 seconds of load decay.
- **Status:** Formulated
