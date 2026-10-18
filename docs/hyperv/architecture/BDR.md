# Pillar I: Business Drivers & Requirements (BDR)
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

---

## 1. Executive Context & Problem Statement

Enterprises deploying automated processing services (such as **ADPA** — Automated Dynamic Process Automation, and **SIDPA** — Secured Intelligent Data Processing Application) face a critical operational dilemma:

1. **High Infrastructure & Idle Power Costs**:
   Traditional deployments maintain dedicated, always-on virtual machines to avoid slow startup times. A cluster of 10–20 always-on Windows Server instances consumes significant host CPU ticks (background services, telemetry, polling), saturates hypervisor RAM, and incurs 24/7 compute and licensing costs even when requests only arrive during business hours or sporadic triggers.

2. **Unacceptable Cold-Boot Delays**:
   When traditional virtual machines are shut down (`Stopped`) to save resources, waking them upon an incoming HTTP request takes **25 to 45 seconds**. This cold-boot latency leads to gateway timeouts (HTTP 504), failed webhooks, and degraded user experience.

3. **Inadequate Security in Shared Container Runtimes**:
   While Linux containers (Docker / Kubernetes) achieve fast spin-up, they share the host kernel. Multi-tenant or high-compliance workloads (processing confidential financial data, PII, or internal trade secrets) require a true Type-1 Hypervisor hardware boundary (Hyper-V hardware ring-0 isolation) to meet zero-trust enterprise compliance requirements.

---

## 2. Business Drivers (Strategic Goals)

### BDR-01: Maximum Resource Density & Cost Reduction (Scale-to-Zero)
* **Goal**: Minimize hardware footprint and operating costs by ensuring that when zero client requests are pending, virtual machine instances consume **0% CPU** and release idle memory pages.
* **Target Metric**:
  * 0.0% Host CPU consumption during idle periods.
  * $\ge 65\%$ compression in active hypervisor memory commitment via Dynamic Memory paging.
  * Support for 3× to 5× more concurrent registered services per physical host compared to always-on VMs.

### BDR-02: Strict Sub-Second Response SLAs (Instantaneous Readiness)
* **Goal**: Provide instantaneous, consumer-grade responsiveness to end users and API integrations without manual provisioning.
* **Target Metric**:
  * Time to First Byte (TTFB) from a completely dormant/paused state under **`800ms`** (typically $\approx 350\text{ms} - 550\text{ms}$).
  * Subsequent warm request latency under **`15ms`**.

### BDR-03: Zero-Trust Hardware-Grade Isolation
* **Goal**: Guarantee cryptographic and hardware-level isolation for every processing session.
* **Target Metric**:
  * Dedicated Virtual Processor (vCPU) and Second-Level Address Translation (SLAT) hardware isolation.
  * No shared kernel space between the application workload, other VMs, or the Hyper-V host operating system.

### BDR-04: Immutable State & Zero-Persistence Guarantee
* **Goal**: Eliminate configuration drift, accumulated file-system debris, and the risk of persistent malware or state contamination between client sessions.
* **Target Metric**:
  * 100% automated restoration to a pristine, cryptographically verifiable baseline snapshot upon session release.
  * Differencing disk deltas (`.avhdx`) discarded immediately upon session release.

---

## 3. High-Level Requirements Matrix

| Requirement ID | Category | Requirement Description | Success Verification |
| :--- | :--- | :--- | :--- |
| **REQ-BDR-01** | **Performance** | Ingress gateway must buffer incoming requests and wake dormant VM in $<300\text{ms}$. | Measured gateway latency logs $\le 300\text{ms}$ to socket connect. |
| **REQ-BDR-02** | **Lifecycle** | Instances with no traffic for $>300\text{s}$ must automatically revert to baseline and suspend. | Verified automated snapshot rollback and Hyper-V `Paused` state transition. |
| **REQ-BDR-03** | **Security** | Guest application must communicate strictly via an isolated virtual network segment. | Network traffic restricted to Ingress Gateway port forwarding; no unauthorized egress. |
| **REQ-BDR-04** | **Packaging** | Production image must exclude developer toolchains, debuggers, and source repositories. | Verified clean golden base image containing only pre-jitted production binaries and hardened OS. |
