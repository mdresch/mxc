---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "Pre-Project / Design Assumption Formulation"
lifecycle_stage: "Stage 1 (Intent) & Stage 3 (Hypothesis)"
governance_policy: "approve-ideation & classify-hypothesis-status"
inputs:
  - "Spark-Capture.md"
  - "Historical telemetry & lessons learned"
process: "Formulate falsifiable hypotheses with empirical evaluation criteria"
outputs:
  - "Ideation-Document.md"
  - "HYP-* hypotheses with status logs"
---

# Ideation Document — Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

> **PMBOK 8 Process:** `Pre-Project / Design Assumption Formulation` (Initiating)  
> **Governance Policy:** `approve-ideation & classify-hypothesis-status` | **Lifecycle Stage:** `Stage 1 (Intent) & Stage 3 (Hypothesis)`  
> **Inputs:** [Spark-Capture.md](Spark-Capture.md), Historical telemetry & lessons learned  
> **Process:** Formulate falsifiable hypotheses with empirical evaluation criteria  
> **Outputs:** Ideation-Document.md, HYP-* hypotheses with status logs

**Source:** [Spark-Capture.md](Spark-Capture.md)  
**Date:** 2026-10-29  
**Project Name:** MXC Hyper-V for ADPA / SIDPA  
**Project Description:** Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes  
**Captured by:** Menno Drescher  
**Drawn from:** [Spark-Capture.md](Spark-Capture.md), [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md), [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md), [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md), [FDD.md](../hyperv/architecture/FDD.md), [ADR.md](../hyperv/architecture/ADR.md), [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md), [BDR.md](../hyperv/architecture/BDR.md)

The MXC JIT Virtualization Engine hosts critical enterprise workloads, such as automated process automation and data processing applications, within Windows Server 2025 Type-1 Hyper-V micro-instances. This architecture resolves the traditional operational trilemma by achieving Scale-to-Zero economics with 0.0% idle CPU utilization, maintaining a lean memory footprint, and delivering sub-second response times through an intelligent ingress gateway that buffers incoming requests while waking dormant virtual machines in under 300 milliseconds. The framework enforces sterile session isolation by executing sessions on transient differencing disks that are automatically discarded upon completion, returning the environment to a pristine, immutable checkpoint baseline to prevent state drift and security vulnerabilities. The system incorporates dynamic watermark autoscaling and proactive warm pool management to ensure seamless concurrency handling and high infrastructure density without sacrificing bank-grade hardware security.

The enterprise architecture records this strategy as six core decisions. At its heart, the system uses Type-1 Hyper-V virtualization rather than container namespaces to ensure complete hardware isolation and seamless compatibility with native Windows services. To achieve near-instantaneous responsiveness, the architecture employs an intelligent connection-buffering ingress gateway alongside a memory-preserved standby mechanism, keeping dormant virtual machines paused in host RAM for sub-300ms wake times without idle CPU overhead. Security and operational cleanliness are enforced by separating production base images from development tooling, executing sessions against transient differencing disks to prevent state drift, and regulating traffic through secure internal datastores. The system scales using an adaptive watermark autoscaling model that proactively replenishes warm standby pools, so enterprise automation workloads remain secure, isolated, and instantaneously accessible during traffic surges.

The lesson that walks through the trilemma, the wake path, sterile sessions, and watermark replenishment is [JIT-Scale-to-Zero-Lesson.md](JIT-Scale-to-Zero-Lesson.md).

---

## Intent carried from the spark

ADPA and SIDPA are long-running services on Windows Server 2025. They handle confidential records, and they are idle between requests. The design assumption under test is that a Hyper-V guest can sit paused at no CPU, hold an incoming web request, deliver that request to the correct image, and resume so the caller gets the first byte without a cold boot.

The numbers in the spark are ceilings from the acceptance criteria, recorded here as hypotheses:

- Unpause (`Resume-VM`) completes in ≤ 300 ms.
- Time to first byte is ≤ 800 ms.
- A paused guest stays resident in host RAM, keeps its image disks allocated, and accounts for 0.0% host CPU and 0.0% GPU.
- Username/password login and MFA finish against a guest that is already awake, so sign-in does not wait on a cold boot.

`classify-hypothesis-status` (`agent-learning-governance`) has not been run. Status stays `Formulated` until a live outcome is classified. Notes below cite what the existing suite already records. They do not change status.

---

## Hypotheses

### HYP-mxc-001: A paused guest uses no CPU

**Statement:** A Windows Server 2025 Hyper-V guest in the `Paused` state consumes 0.0% host CPU for that guest while it waits.

**Empirical evaluation criteria:**

1. On the Hyper-V host performance monitor, each registered standby guest in `Paused` measures 0.0% CPU (`AC-03.1`).
2. The same reading holds for a set of paused guests at once (the acceptance note uses 10).
3. Zero CPU does not free the disk. The host still has the image disks allocated for that guest, including the parent VHDX and any `.avhdx`, as stated with `HYP-mxc-007`.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from [Spark-Capture.md](Spark-Capture.md). [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `AC-03.1` states the 0.0% criterion. [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md) marks `US-03` complete and says 10 standby VMs were verified at 0.0% CPU while `Paused`. That claim was not re-measured for this document. Status stays Formulated.
- 2026-10-29: Amended the same day. A paused guest at 0.0% CPU still requires its image disk space to stay allocated. That disk check is shared with `HYP-mxc-007`. Status stays Formulated.

### HYP-mxc-002: Unpause to available is at most 300 ms

**Statement:** After the gateway holds a request, `Resume-VM` on a paused Windows Server 2025 guest finishes in ≤ 300 ms, and that completion is what "available" means. The figure is a ceiling, not a constant 300 ms.

**Empirical evaluation criteria:**

1. Elapsed time for Hyper-V to complete `Resume-VM` is ≤ 300 ms (`AC-03.3`).
2. A resume that finishes in 301 ms or more fails this hypothesis even if the later first-byte time still passes `HYP-mxc-003`.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the spark sentence "Unpause to available is 300 ms." [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md) records `Resume-VM` from Saved or paused RAM at 180–290 ms. [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `AC-03.3` states the ≤ 300 ms ceiling. No new live resume was timed for this document. Status stays Formulated.

### HYP-mxc-003: The first byte returns in at most 800 ms

**Statement:** When the target guest starts `Paused`, the gateway holds the connection, wakes the guest, and returns the first byte of the HTTP response within ≤ 800 ms wall-clock time to first byte. The spark's "first bit" is this first byte.

**Empirical evaluation criteria:**

1. Cold-wake time to first byte, from request arrival on a paused guest to the initial HTTP response or header flush, is ≤ 800 ms (`AC-01.1`).
2. Warm traffic after the guest is already running is a separate check (`AC-01.2`, about 15–25 ms) and does not by itself pass this hypothesis.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the spark. [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md) `AC-01.1` states ≤ 300 ms platform wake and ≤ 800 ms time to first byte. [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md) marks the buffering gateway complete against that ceiling. The only published timing sample in that plan is warm keep-alive time to first byte, 11.41–16.96 ms (`AC-01.2`). No cold-wake first-byte sample is recorded there. Status stays Formulated.

### HYP-mxc-004: The request reaches the image that owns it

**Statement:** An incoming web request is held, then delivered to the Hyper-V image that owns that request. Two observable routes exist in the current suite, and both have to be named or the hypothesis is ambiguous:

1. URL path selects the pool: `/api/v1/adpa` selects `prod-adpa`, `/api/v1/sidpa` selects `prod-sidpa`.
2. Listen port selects the image in the golden-image catalog: `:8090` selects the dev image, `:8091` selects the ADPA proof-of-concept image, `:8092` selects the SIDPA dev image.

**Empirical evaluation criteria:**

1. A request whose path starts with `/api/v1/adpa` is leased from pool `prod-adpa`, and a path starting with `/api/v1/sidpa` is leased from pool `prod-sidpa` (`scripts/hyperv/dev_harness/jit_ingress_gateway.py`).
2. A request accepted on a catalogued listen port is served by the image that [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md) binds to that port.
3. The guest service port after the route is `:8080`.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the spark sentence "The requested port is routed to the correct image." The gateway in tree routes by URL path on one listen port, then proxies to guest port `:8080`. The image catalog maps listen ports to images. `img-mxc-dev-v2.3` is `baked_ready` on `:8090`. `img-adpa-poc-v1` (`:8091`) is `poc_planned`. `img-sidpa-dev-v1` (`:8092`) is `in_development`. Path routing and port-to-image routing are both present in the suite and are not the same mechanism. Status stays Formulated.

### HYP-mxc-005: The fast wake is resume from pause, and a fresh image is the checkpoint underneath

**Statement:** The sub-second wake is `Resume-VM` from a guest already in `Paused` RAM, captured at the `baseline-hot-ready` checkpoint. A production-ready fresh-state image is that checkpoint. Starting a stopped guest from the parent VHDX is a cold boot and misses the 800 ms first-byte ceiling. The parent golden disk `winserv2025-golden.vhdx` is the base the workload image is stamped from. It is not itself the paused guest.

**Empirical evaluation criteria:**

1. A guest resumed from `Paused` at `baseline-hot-ready` meets `HYP-mxc-002` and `HYP-mxc-003`.
2. A guest started from `Stopped` takes longer than 800 ms before `:8080` accepts a connection.
3. After a session, the guest returns to that same checkpoint before it is paused again.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the spark's "paused Golden Image, or a production-ready fresh-state image." [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md) records a Windows Server 2025 cold boot of 14–28 seconds before `:8080` accepts. [BDR.md](../hyperv/architecture/BDR.md) records 25–45 seconds to wake a stopped VM. Those are two different notes, and both sit above 800 ms. [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md) still has production image baking in an active phase. The dedicated production ADPA image is not marked complete. Status stays Formulated.

### HYP-mxc-006: A shared kernel does not meet the isolation bar for these workloads

**Statement:** ADPA and SIDPA, as named in this suite, process confidential records and require a dedicated Hyper-V guest with its own kernel. A container that shares the host kernel fails that isolation bar even when it starts faster than a cold boot.

**Empirical evaluation criteria:**

1. The workload runs in a Hyper-V guest whose kernel is not the host kernel (`AC` isolation notes in [BDR.md](../hyperv/architecture/BDR.md) and [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md)).
2. A shared-kernel container is recorded as insufficient for the financial, personal, or otherwise confidential records these services are said to handle.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the spark's third bad choice and from [SCOPE_DRIFT_AND_UPSTREAM_MAINTENANCE.md](../hyperv/architecture/SCOPE_DRIFT_AND_UPSTREAM_MAINTENANCE.md), which contrasts upstream shared-kernel sandboxes with a Type-1 Hyper-V guest. This is a design assumption stated by the suite. It is not a new isolation test. Status stays Formulated.

### HYP-mxc-007: A paused guest stays in RAM and uses no CPU or GPU

**Statement:** A Windows Server 2025 Hyper-V guest in the `Paused` state keeps its memory resident in host RAM and consumes 0.0% host CPU and 0.0% GPU while it waits. The disk space required to run its images stays allocated on the host. `Suspend-VM` is the pause. `Save-VM` and a stopped guest are different states and do not satisfy this hypothesis.

**Empirical evaluation criteria:**

1. While the guest is `Paused`, the Hyper-V host still accounts memory for that guest. The assignment is the pre-trimmed standby footprint, about 1.0–1.2 GB (`AC-03.2`). A reading of 0 MB means the guest was saved or stopped, and this hypothesis fails.
2. Host CPU charged to that paused guest is 0.0% (`AC-03.1`, same reading as `HYP-mxc-001`).
3. Host GPU utilization charged to that paused guest is 0.0%. A production guest has no GPU partition assigned. If a partition is assigned, its utilization is 0 while the guest is `Paused`.
4. The host still has disk allocated for the parent image and any `.avhdx` that belongs to that guest. A paused guest with those files removed fails this hypothesis. Zero CPU and zero GPU do not release that disk.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the request to record RAM residency with no CPU and no GPU. The architecture notes state that a `Paused` guest keeps guest memory in host RAM and freezes the vCPU at 0.0% CPU. The Hyper-V suite does not mention a GPU, a vGPU, or RemoteFX. No GPU counter was read for this document. Status stays Formulated.
- 2026-10-29: Amended the same day, with `HYP-mxc-001`. Disk space for the images stays allocated while the guest is paused. The image catalog lists a 10.88 GB golden parent and a 39.25 GB developer image, each with a 64 GB maximum. Those sizes are inventory, not a measured paused-guest total. An example of one, two, or three standby copies on the NVMe tier is in [Business-Case.md](Business-Case.md). Status stays Formulated.

### HYP-mxc-008: Username/password login and MFA are seamless across wake

**Statement:** A sign-in that uses a username and password, then a second factor, reaches a Windows Server 2025 guest that was `Paused` when the request arrived. The wake that serves that sign-in stays inside `HYP-mxc-002` and `HYP-mxc-003`. The person does not watch a cold boot. The guest clock is aligned to the host before the sign-in is accepted, so a pause does not fail the password check, the second factor, Kerberos, or TLS.

**Empirical evaluation criteria:**

1. A username and password, followed by MFA, succeed against a guest that was `Paused` at the start of the request. The user-visible wait does not include a 25–45 second cold boot.
2. The wake itself, up to the guest accepting the sign-in request, stays within ≤ 300 ms for `Resume-VM` and ≤ 800 ms to the first byte. Time the person spends entering the password or the second factor is outside that ceiling.
3. After the guest has been paused longer than 5 minutes, Kerberos and TLS still succeed because the guest clock is stepped to host UTC before the health check reports ready ([LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md)).
4. Directory traffic for that sign-in stays on the existing whitelist: DNS `:53`, Kerberos `:88`, and HTTPS `:443` when the second factor is reached over HTTPS.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated from the request that login be optimized for username and password plus MFA, and that boot stay seamless. The suite already whitelists Kerberos `:88` for Windows integrated authentication and requires clock sync so a paused guest does not fail tickets or TLS. It does not specify a username/password form or an MFA factor. No sign-in was run for this document. Status stays Formulated.

### HYP-mxc-009: A Generation 2 guest keeps the Windows subsystems a container drops

**Statement:** ADPA and SIDPA run on a Hyper-V Generation 2 virtual machine. WMI, COM+, native Windows services, performance counters, and Group Policy keep working. The same workload inside a container namespace does not.

**Empirical evaluation criteria:**

1. The guest is a Generation 2 Hyper-V VM using hardware virtualization and second-level address translation.
2. A representative call to WMI, COM+, a Windows service, and Group Policy succeeds in the guest.
3. The same call fails or is unsupported inside a Windows Server container namespace.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-009`. The architecture notes name those subsystems as the reason to reject container namespaces. No side-by-side subsystem test was run for this document. Status stays Formulated.

### HYP-mxc-010: A held request wakes the guest without a gateway error

**Statement:** An HTTPS request that arrives while the guest is `Paused` is held open. The gateway wakes the guest, probes `:8080/health` in about 50 ms, then flushes the request. The caller receives the response with no HTTP 502 or 504, and no custom wake-up client.

**Empirical evaluation criteria:**

1. A standard HTTPS client, with no wake SDK, completes a request that started against a `Paused` guest.
2. The health probe after `Resume-VM` finishes in about 50 ms.
3. The response is not HTTP 502 or HTTP 504 because of the wake. A saturation timeout past `wake_timeout_ms` may still return HTTP 503 with `Retry-After`, and that case is outside this hypothesis.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-010`. The implementation plan marks the buffering gateway complete against the 800 ms ceiling. No new cold-wake capture of status codes was taken for this document. Status stays Formulated.

### HYP-mxc-011: The production image has no developer toolchain and is checkpointed warm

**Statement:** Production runs from `winserv2025-prod-adpa.vhdx`, not from the developer golden image. Compilers, Scoop, cargo, git, and developer SDKs are absent. The `baseline-hot-ready` checkpoint is taken after a smoke request has warmed the service, so the first wake does not pay a JIT compile.

**Empirical evaluation criteria:**

1. A file inventory of the production VHDX finds no Scoop, cargo, git, or compiler toolchain (AC-04.1).
2. The developer image `winserv2025-golden.vhdx` is not the parent used for the production pool.
3. A wake from `baseline-hot-ready` serves the first request without a JIT compilation stall.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-011`. [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md) still lists production image baking as an active phase. `img-adpa-poc-v1` in the image catalog is `poc_planned`. Status stays Formulated.

### HYP-mxc-012: The working set is trimmed before pause, to about 1.0–1.2 GB

**Statement:** Guest memory is trimmed while the vCPUs are still running, and only then does `Suspend-VM` run. The paused guest occupies about 1.0–1.2 GB of host RAM. A balloon driver cannot perform that trim after the pause, because the vCPUs are frozen.

**Empirical evaluation criteria:**

1. `EmptyWorkingSet` or the equivalent trim runs before `Suspend-VM` on the bake path and on pool replenishment (AC-03.2).
2. Host RAM charged to each `Paused` standby guest is about 1.0–1.2 GB.
3. A resume does not page that working set in from disk. A resume that waits on disk page-in fails this hypothesis and `HYP-mxc-002`.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-012`. The bake script calls `/admin/pre-trim` before `Checkpoint-VM`. On idle release, `pool-release` restores `baseline-hot-ready` and then suspends, so the paused footprint is the checkpoint's footprint when the restore succeeds. Lessons learned also cite a trim under 700 MB. That figure and the 1.0–1.2 GB figure are both in the suite and are not the same measurement. Status stays Formulated.

### HYP-mxc-013: Session disk writes disappear, and egress stays on the whitelist

**Statement:** Every production session writes only to a transient `.avhdx` anchored at `baseline-hot-ready`. After the session ends, or after 300 seconds with no open requests, that differencing disk is discarded and the guest returns to the baseline. Ingress reaches the guest only on `:8080` from the proxy. Public internet egress is denied. Allowed egress is SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88`.

**Empirical evaluation criteria:**

1. A file written in the guest during a session is gone after release (AC-02.1).
2. The parent baseline hash is unchanged across that release (AC-02.2).
3. A connection to a public internet address is dropped. A connection to each whitelisted port on an approved internal endpoint is allowed (AC-02.3).

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-013`. Port-ACL automation is recorded as implemented in the lessons note. Milestone 3.2 in the architecture document still marks the ACL work active. No new packet capture was taken for this document. Status stays Formulated.

### HYP-mxc-014: The warm pool refills itself, and wake hygiene runs before traffic

**Statement:** When the last ready guest is leased, a background worker promotes a `ColdProvisioned` guest to `StandbyPaused` in about 1.5 seconds. A request surge raises the ready count up to \(K_{\max}\). Before the guest accepts traffic it reseeds the random-number generator from hardware, steps the clock to host UTC, and clears stale database connection pools. Surplus guests return to the low watermark after 300 seconds with no open requests.

**Empirical evaluation criteria:**

1. After a lease, a new `StandbyPaused` guest is ready in about 1.5 seconds without blocking the in-flight request.
2. A surge expands the ready pool up to \(K_{\max}\) and does not cold-boot the next caller.
3. The first `/health` after wake reports entropy reseeded, clock synced, and database pools cleared.
4. After 300 seconds with `active_open_requests` at 0, surplus guests leave `ActiveRunning`.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-014`. One architecture note sets the surge example above 5 requests per second. [LESSONS_LEARNED.md](../hyperv/architecture/LESSONS_LEARNED.md) sets it at 10 or more requests per second over 5 seconds. Both figures stay in the log until one is measured. No surge run was captured for this document. Status stays Formulated.

---

### HYP-mxc-021: A closed idle guest is a smaller security risk than a running one

**Statement:** A Windows Server 2025 guest that is closed and idle, in the `Paused` state, is a smaller security risk than the same guest left running. While it is paused it does not execute guest code and it does not accept a new session. The attack window is the time the guest is actually awake.

**Empirical evaluation criteria:**

1. While the guest is `Paused`, a direct connection to the guest service port fails. A new session starts only after the gateway resumes the guest.
2. Over an idle day, the time the guest spends `Paused` is time it is not executing workload code.
3. The same guest left `Running` with no requests still accepts connections and still executes. That is the higher-risk case this hypothesis compares against.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-021`. The spark now states that a closed idle machine is a smaller security risk than one left running. No exposure comparison has been measured. Status stays Formulated.

---

### HYP-mxc-022: Discard the whole guest or only the `.avhdx`, then reproduce from the approved image

**Statement:** After a session, two discards are both valid. One discards the whole Hyper-V guest, the entire session. The other discards only the `.avhdx`. Either discard causes the next session to be reproduced from the approved production image, not from the used copy and not from the developer image.

**Empirical evaluation criteria:**

1. **Whole guest.** The Hyper-V session is removed. A file written only in that guest is gone. The next guest is a new reproduction from the approved production image.
2. **Differencing disk only.** The guest remains and the `.avhdx` is discarded. A file written only on that disk is gone. The guest's parent is still the approved production image.
3. In both cases the parent matches the approved production image and does not match the developer golden image. The next session does not inherit disk changes from the previous one.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-022`, then amended the same day: both discards are in scope. The whole Hyper-V guest can be discarded, or only the `.avhdx`. `HYP-mxc-013` already covers discarding the differencing disk back to `baseline-hot-ready`. `HYP-mxc-011` names `winserv2025-prod-adpa.vhdx` as the production image and records that bake as still active. No discard-and-reproduce run was captured for either path. Status stays Formulated.

---

## Future hypotheses to review

These six are research hypotheses. They are open for review alongside `HYP-mxc-001` through `HYP-mxc-014`. Status stays `Formulated` until a live outcome is classified.

### HYP-mxc-015: A micro-VM footprint stays under 256 MB while paused

**Statement:** A minimal Server Core guest in a lightweight Hyper-V partition stays under 256 MB of host RAM while `Paused`, down from about 1 GB.

**Empirical evaluation criteria:**

1. A paused minimal guest measures under 256 MB host RAM.
2. That guest still meets `HYP-mxc-002` on wake.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-015` for later review. No micro-VM image has been measured. Status stays Formulated.

### HYP-mxc-016: A long-lived stream survives an idle pause

**Statement:** A WebSocket or Server-Sent Events connection stays held across an idle pause and resumes when the guest wakes, without the client opening a new socket.

**Empirical evaluation criteria:**

1. A stream that is open when the guest is paused still delivers the next event after `Resume-VM`.
2. The client does not reconnect.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-016` for later review. The current gateway proxies request/response HTTP. No stream hold has been tested. Status stays Formulated.

### HYP-mxc-017: A pool accepts only a signed, scanned image

**Statement:** Before a host registers an image in a pool, the bake pipeline has scanned it for vulnerabilities, produced a software bill of materials, and the host has checked a signature on the VHDX.

**Empirical evaluation criteria:**

1. An unsigned VHDX is refused at pool registration.
2. A signed image with a current bill of materials is accepted.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-017` for later review. The bake path does not sign images or emit a bill of materials today. Status stays Formulated.

### HYP-mxc-018: Hot guests stay in RAM and deep guests stay on NVMe

**Statement:** A small hot set stays `Paused` in RAM and wakes in under 300 ms. A larger deep set is saved to NVMe at 0 MB host RAM, wakes in about 1.5 seconds, and is promoted into RAM as leases grow.

**Empirical evaluation criteria:**

1. A hot guest wakes within the ceiling in `HYP-mxc-002`.
2. A deep guest uses 0 MB host RAM while saved and becomes `StandbyPaused` in about 1.5 seconds when promoted.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-018` for later review. The running pool uses paused RAM only. No saved-to-NVMe tier has been measured. Status stays Formulated.

### HYP-mxc-019: Session scratch lives in memory and is wiped on release

**Statement:** Session scratch I/O uses a write-once memory disk attached over VMBus. On release that memory is wiped. The session does not depend on a file-backed `.avhdx` for scratch.

**Empirical evaluation criteria:**

1. Scratch writes during a session are not present on the host filesystem after release.
2. A read of that memory range after release returns zeros.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-019` for later review. Sessions still use a file-backed `.avhdx`, covered by `HYP-mxc-013`. Status stays Formulated.

### HYP-mxc-020: A forecast pre-warms the pool about 60 seconds ahead

**Statement:** A small on-host time-series model pre-warms a pool about 60 seconds before a predicted demand peak, with no manual schedule.

**Empirical evaluation criteria:**

1. Ahead of a repeated daily peak, ready guests are `StandbyPaused` at least 60 seconds before the first request of that peak.
2. No operator runs a manual pre-warm for that peak.

**Status:** Formulated

**Updates:**

- 2026-10-29: Formulated as `HYP-mxc-020` for later review. Pre-warm today is an explicit pool command or a surge reaction under `HYP-mxc-014`. No forecast model is running. Status stays Formulated.

---

## What this is not yet

Objectives, benefits, and a cost model are the business-case stage. Pool size, density multiples, and license savings are not hypotheses here.

Those already appear further down the Hyper-V suite. This document does not re-approve them:

- Business drivers and requirements: [BDR.md](../hyperv/architecture/BDR.md)
- Decisions: [ADR.md](../hyperv/architecture/ADR.md)
- Functional design: [FDD.md](../hyperv/architecture/FDD.md)
- Stories and acceptance: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md)
- Implementation plan: [IMPLEMENTATION_PLAN.md](../hyperv/architecture/IMPLEMENTATION_PLAN.md)
- Architecture: [ARCHITECTURE_DESIGN_DOCUMENT.md](../hyperv/architecture/ARCHITECTURE_DESIGN_DOCUMENT.md)

Next in the SIDPA sequence is [Business-Case.md](Business-Case.md), then [Benefits-Statement.md](Benefits-Statement.md), before any charter. `classify-hypothesis-status` is the gate that may move a hypothesis off `Formulated` once a live outcome exists.
