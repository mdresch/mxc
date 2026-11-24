---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Strategic Need Identification"
lifecycle_stage: "Stage 1 (Intent)"
governance_policy: "approve-ideation"
inputs:
  - "Business need or raw strategic impulse"
  - "Market / environment trigger event"
process: "Capture raw problem statement and motivation without premature solutioning"
outputs:
  - "Spark-Capture.md (Source for Ideation)"
---

# Spark Capture — Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

> **PMBOK 8 Process:** `Pre-Project / Strategic Need Identification` (Initiating)  
> **Governance Policy:** `approve-ideation` | **Lifecycle Stage:** `Stage 1 (Intent)`  
> **Inputs:** Business need or raw strategic impulse, Market / environment trigger event  
> **Process:** Capture raw problem statement and motivation without premature solutioning  
> **Outputs:** Spark-Capture.md (Source for Ideation)

**Date:** 2026-10-29 (impulse first committed 2026-10-15)  
**Captured by:** Menno Drescher  
**Project Name:** MXC Hyper-V for ADPA / SIDPA  
**Project Description:** Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes  
**Drawn from:** [BDR.md](../hyperv/architecture/BDR.md), [ADR.md](../hyperv/architecture/ADR.md), [SCOPE_DRIFT_AND_UPSTREAM_MAINTENANCE.md](../hyperv/architecture/SCOPE_DRIFT_AND_UPSTREAM_MAINTENANCE.md), [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md), [EXECUTIVE_SUMMARY_AND_LINKEDIN.md](../hyperv/architecture/EXECUTIVE_SUMMARY_AND_LINKEDIN.md)

The MXC JIT Virtualization Engine hosts critical enterprise workloads, such as automated process automation and data processing applications, within Windows Server 2025 Type-1 Hyper-V micro-instances. This architecture resolves the traditional operational trilemma by achieving Scale-to-Zero economics with 0.0% idle CPU utilization, maintaining a lean memory footprint, and delivering sub-second response times through an intelligent ingress gateway that buffers incoming requests while waking dormant virtual machines in under 300 milliseconds. The framework enforces sterile session isolation by executing sessions on transient differencing disks that are automatically discarded upon completion, returning the environment to a pristine, immutable checkpoint baseline to prevent state drift and security vulnerabilities. The system incorporates dynamic watermark autoscaling and proactive warm pool management to ensure seamless concurrency handling and high infrastructure density without sacrificing bank-grade hardware security.

The enterprise architecture records this strategy as six core decisions. At its heart, the system uses Type-1 Hyper-V virtualization rather than container namespaces to ensure complete hardware isolation and seamless compatibility with native Windows services. To achieve near-instantaneous responsiveness, the architecture employs an intelligent connection-buffering ingress gateway alongside a memory-preserved standby mechanism, keeping dormant virtual machines paused in host RAM for sub-300ms wake times without idle CPU overhead. Security and operational cleanliness are enforced by separating production base images from development tooling, executing sessions against transient differencing disks to prevent state drift, and regulating traffic through secure internal datastores. The system scales using an adaptive watermark autoscaling model that proactively replenishes warm standby pools, so enterprise automation workloads remain secure, isolated, and instantaneously accessible during traffic surges.

The lesson that walks through the trilemma, the wake path, sterile sessions, and watermark replenishment is [JIT-Scale-to-Zero-Lesson.md](JIT-Scale-to-Zero-Lesson.md).

---

## The spark

MXC was built to run something untrusted for a moment — a script, a tool call, a plugin — and then throw the process away. ADPA and SIDPA are not that kind of work. They are services that sit there and handle sensitive records, and most of the time nobody is calling them.

The choice in front of that work is a bad one:

1. Leave a Windows Server running so the next request is fast, and pay for CPU, memory, and licenses through the night for a machine that is waiting.
2. Turn it off, and make the next caller wait through a full boot. Webhooks time out. People watch a spinner.
3. Put it in a container so it starts quickly, and share the host kernel with everything else on the box. That is not enough when the data is financial, personal, or otherwise something a neighbor workload must not be able to reach.

The impulse is simple. These services should be allowed to sleep, and they should still be isolated as if they were their own machine. Waiting half a minute, or leaving a server humming for a request that has not arrived, should not be the price of that isolation.

What that looks like, in the words it arrived in: a paused Windows Server 2025 Golden Image, or a production-ready fresh-state image, sits there closed and idle, with no CPU usage, while the disk for those images stays allocated. A closed idle machine is a smaller security risk than the same machine left running. When the work is finished, either the whole Hyper-V guest is discarded, or only its `.avhdx` is discarded. Either way, the next session is reproduced from the approved production image. An HTTPS request, or any web request, shows up. The request is held. The requested port is routed to the correct image. That Hyper-V image is resumed from its paused or fresh state, and the caller gets an instant activation instead of a cold boot. Unpause to available is 300 ms. The first bit is back in under 800 ms. The caller should not be able to tell the machine was asleep. Username and password login, and the MFA step that follows, ride that same wake. The guest is up before the person finishes signing in. They do not sit through a boot.

Upstream `microsoft/mxc` assumes a desktop, a short-lived command, and a sandbox that shares the host. The workloads that showed up do not.

---

## Why now

1. **The boot is too slow for the way requests arrive.** A stopped Windows Server 2025 guest takes on the order of 14–45 seconds before it will accept work. Callers and upstream webhooks do not wait that long.
2. **The named workloads need a harder boundary than a shared kernel.** The October 2026 notes name ADPA (Automated Dynamic Process Automation) and SIDPA (Secured Intelligent Data Processing Application) as the services that process confidential records. A container that shares the host kernel does not meet that bar.
3. **The fork has already left upstream's assumptions.** The Hyper-V backend was first committed on 15 October 2026 (`402aadcb`, Menno Drescher) on `feat/hyperv-v2-rebased`. The scope-drift note records that this line of work no longer matches upstream's run-to-exit, shared-kernel model. That departure needs a Stage 1 record of *why*, before later documents are treated as if the intent had always been settled.
4. **The work arrives as a request, then nothing.** Agents and callers show up, run a job, and go quiet. A sandbox that only exists while someone sits in front of it does not match that rhythm.

---

## What this is not yet

This is pre-Ideation. It records the problem, the trigger, and the picture of a paused or fresh Windows Server 2025 image that uses no CPU while paused, then wakes when a web request is held for it: the requested port is routed to the correct image, 300 ms from unpause to available, and the first bit in under 800 ms, with username/password login and MFA riding that same wake so sign-in does not wait on a boot. It does not choose a pool size or a cost model.

Those choices already live further down this suite. They must not be read back into this capture as if Stage 1 had settled them:

- Business drivers and requirements: [BDR.md](../hyperv/architecture/BDR.md)
- Decisions: [ADR.md](../hyperv/architecture/ADR.md)
- Functional design: [FDD.md](../hyperv/architecture/FDD.md)
- Stories and acceptance: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md)
- Implementation plan: [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md)
- Architecture: [ARCHITECTURE_DESIGN_DOCUMENT.md](../hyperv/architecture/ARCHITECTURE_DESIGN_DOCUMENT.md)

Hypotheses, objectives, and a business case remain the next documents' job if this capture is taken through the SIDPA lifecycle. A spark that already quotes idle-CPU percentages and density multiples has collapsed the stages.
