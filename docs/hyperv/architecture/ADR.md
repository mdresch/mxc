# Pillar II: Architectural Decision Records (ADR)
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)

---

## ADR-001: Type-1 Hyper-V Generation 2 instead of a container namespace

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-01` Isolation
* **Also**: `TP-04` for the paused footprint. This record states the security comparison. `ADR-004` states the RAM, CPU, GPU, and disk readings.

### Context
ADPA and SIDPA process confidential records. Financial, personal, and otherwise sensitive data must not share a kernel with a neighbor workload. The spark names three bad choices for a service that is idle between requests. This decision rejects the third: put the work in a container so it starts quickly, and share the host kernel with everything else on the box.

The business case records the same rejection as Alternative 3. A shared-kernel container is not enough for these records, even when it starts faster than a cold boot (`HYP-mxc-006`).

The same workloads also need Windows subsystems a container drops. A Generation 2 guest keeps WMI, COM+, native Windows services, and Group Policy. The same calls fail or are unsupported inside a container namespace (`HYP-mxc-009`, `BEN-05`).

A paused guest is part of this isolation choice. A machine that is closed and idle is a smaller security risk than the same machine left running (`HYP-mxc-021`, `BEN-11`). While it is paused it does not execute guest code and it does not accept a new session. The attack window is the time the guest is awake.

### Decision
Standardize on **Type-1 Hyper-V Generation 2 virtual machines** orchestrated by the native Rust control plane (`wxc-exec --features hyperv`).

* The workload runs in a guest whose kernel is not the host kernel.
* A shared-kernel container does not meet the isolation bar for ADPA and SIDPA.
* Windows work stays on that guest: WMI, COM+, a Windows service, and Group Policy succeed there.
* When the guest is idle it is `Paused`, not left `Running`. A direct connection to the guest service port fails while it is paused. A new session starts only after the gateway resumes the guest.
* Over an idle day, time spent `Paused` is time the guest is not executing workload code. The same guest left `Running` with no requests still accepts connections and still executes. That is the higher-risk case.

### Rationale
* **Confidential records (`TP-01`)**: The spark's third bad choice, `HYP-mxc-006`, and business-case Alternative 3 reject a shared kernel. Hyper-V partitions use Intel VT-x or AMD-V and Second-Level Address Translation (SLAT). That boundary is what keeps one workload from reading another workload's memory.
* **Windows subsystems (`TP-01`)**: `HYP-mxc-009` and `BEN-05` require a Generation 2 guest. WMI, COM+, native Windows services, performance counters, and Group Policy keep working. A container namespace does not provide that guest.
* **Closed idle guest (`TP-01`, also `TP-04`)**: The spark, `HYP-mxc-021`, and `BEN-11` treat a paused guest as the smaller attack window. `ADR-002` already notes that the guest socket is unreachable while `Paused`, because the gateway must hold the request. This decision records the security comparison against leaving the guest running. The 0.0% CPU reading, the resident RAM, and the allocated image disks stay with `ADR-004`.
* **Warm checkpoint**: A Hyper-V checkpoint can freeze the guest after it has booted. That is how a later resume avoids a cold boot. The resume ceiling itself is `ADR-004`.

### Consequences
* *Positive*: The workload has its own kernel. The named Windows subsystems keep working. An idle guest is paused, so it is not executing and not accepting a new session.
* *Trade-off*: The host must be Windows Pro, Enterprise, or Windows Server with Hyper-V enabled. A paused guest still occupies host RAM and its image disks. Those costs are `ADR-004`, not a reason to leave the guest running.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 3 | A shared-kernel container is not enough for confidential records. | TP-01 | — |
| Spark | Closed idle guest | A paused machine is a smaller security risk than one left running. | TP-01 | TP-04 |
| Hypothesis | HYP-mxc-006 | A shared kernel does not meet the isolation bar. | TP-01 | — |
| Hypothesis | HYP-mxc-009 | A Generation 2 guest keeps WMI, COM+, services, and Group Policy. | TP-01 | — |
| Hypothesis | HYP-mxc-021 | A closed idle guest is a smaller security risk than a running one. | TP-01 | TP-04 |
| Hypothesis | HYP-mxc-015 | Future: paused micro-VM under 256 MB. | TP-01 | ADR-001 horizon |
| Benefit | BEN-05 | Windows work stays on its own guest. | TP-01 | — |
| Benefit | BEN-11 | A closed idle guest accepts no new session. | TP-01 | TP-04 |
| Business case | Alternative 3 | Use a shared-kernel container. Rejected for confidential records. | TP-01 | — |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-001): Hyper-V Direct Micro-VM Partitions**  
> `HYP-mxc-015`. Explore lightweight Hyper-V micro-VM profiles and a minimal Windows Server Core footprint so a paused guest stays under 256 MB of host RAM, down from about 1 GB. That guest still has to meet the resume ceiling in `ADR-004`. No micro-VM image has been measured. The hypothesis stays `Formulated`.

---

## ADR-002: Connection-buffering ingress gateway

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-02` Ingress
* **Also**: `TP-04` for the 300 ms unpause. `TP-05` for the Kerberos whitelist. `TP-06` for the clock step before sign-in.

### Context
Turning the guest off makes the next caller wait through a 14–45 second boot. Webhooks time out. That alternative is rejected when the wake ceilings hold (spark bad choice 2, business-case Alternative 2, `BEN-02`).

While the guest is `Paused`, its TCP socket is unreachable. Callers still send an ordinary HTTPS request. The gateway has to hold that request, wake the guest, and deliver it to the image that owns it.

### Decision
Deploy a **connection-buffering ingress reverse proxy** (YARP / Envoy / FastMCP Gateway) in front of the VM cluster.

1. The client opens TLS to the proxy. No custom wake SDK is required.
2. If the guest is dormant, the proxy holds the request open and dispatches `pool_lease` / `resume`.
3. `Resume-VM` itself is the `TP-04` ceiling: at most 300 ms. This decision does not restate that measurement. It does require the first byte of the HTTP response, from request arrival on a paused guest to the header flush, within 800 ms (`HYP-mxc-003`, `BEN-02`). Warm traffic after the guest is already running does not pass that check.
4. The proxy probes `:8080/health` (about 50 ms) and then flushes the held request. The response is not HTTP 502 or 504 because of the wake (`HYP-mxc-010`, `BEN-03`). A 503 after `wake_timeout_ms` is a different case.
5. Two routes are both in force (`HYP-mxc-004`, `BEN-04`). A path starting with `/api/v1/adpa` leases pool `prod-adpa`. A path starting with `/api/v1/sidpa` leases pool `prod-sidpa`. A catalogued listen port selects the image: `:8090` the dev image, `:8091` the ADPA proof-of-concept image, `:8092` the SIDPA dev image. After either route the guest service port is `:8080`. A check records which rule fired. Passing one rule does not pass the other.
6. Username, password, and a second factor ride that same wake (`HYP-mxc-008`, `BEN-06`). The guest was `Paused` when the request arrived. The person does not watch a 25–45 second boot. Time spent typing is outside the 300 ms and 800 ms ceilings. The second-factor product is still unnamed, so the check cannot be scripted until that name exists. Kerberos `:88` stays with `ADR-005` (`TP-05`). The clock step to host UTC stays with `ADR-006` (`TP-06`).

### Consequences
* *Positive*: A standard client gets the first byte without a cold boot and without a wake-caused 502 or 504. The request reaches the image that owns it. Sign-in uses the same wake.
* *Trade-off*: The 800 ms ceiling includes the resume. If `Resume-VM` misses 300 ms, this decision fails even when a later byte still arrives. The two routing rules must both be tested.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 2 | Turn it off and make the caller wait through a 14–45 s boot. | TP-02 | TP-04 |
| Spark | Held request | The request is held and the port is routed to the correct image. | TP-02 | — |
| Spark | 800 ms first byte | The first byte is back in under 800 ms. | TP-02 | TP-04 |
| Spark | Sign-in | Username, password, and MFA ride the same wake. | TP-02 | TP-05, TP-06 |
| Hypothesis | HYP-mxc-003 | First byte within 800 ms from a paused guest. | TP-02 | TP-04 |
| Hypothesis | HYP-mxc-004 | Path selects the pool. Listen port selects the catalogued image. | TP-02 | — |
| Hypothesis | HYP-mxc-008 | Username, password, and MFA meet a guest that was paused. | TP-02 | TP-05, TP-06 |
| Hypothesis | HYP-mxc-010 | A held request wakes the guest with no HTTP 502 or 504. | TP-02 | — |
| Hypothesis | HYP-mxc-016 | Future: a long-lived stream survives an idle pause. | TP-02 | ADR-002 horizon |
| Benefit | BEN-02 | Wake without a cold boot: 300 ms unpause and 800 ms first byte. | TP-02 | TP-04 |
| Benefit | BEN-03 | No wake-caused HTTP 502 or 504. | TP-02 | — |
| Benefit | BEN-04 | The request lands on the owning image. | TP-02 | — |
| Benefit | BEN-06 | Sign-in does not wait on boot. | TP-02 | TP-05, TP-06 |
| Business case | Alternative 2 | Turn the server off. Rejected if the wake ceilings hold. | TP-02 | TP-04 |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-002): WebSocket & SSE Suspension Multiplexing**  
> `HYP-mxc-016`. A WebSocket or Server-Sent Events connection stays held across an idle pause and resumes when the guest wakes, without the client opening a new socket. The current gateway proxies request/response HTTP. No stream hold has been tested. The hypothesis stays `Formulated`.

---

## ADR-003: Production base image separate from the developer image

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-03` Image supply
* **Also**: none. `HYP-mxc-017` stays the future-horizon note on this record.

### Context
The catalogued developer image is `winserv2025-mxc-dev.vhdx` (`img-mxc-dev-v2.3`, `baked_ready`). It carries Rust, MSVC, .NET, Python, Node, and Git. The OS stamp `winserv2025-golden.vhdx` (`img-os-ws2025-base`) is the parent used to stamp new workload images. It is not a production pool parent.

`HYP-mxc-011` and `BEN-08` require production to run from `winserv2025-prod-adpa.vhdx`. That file is not in the image catalog. `img-adpa-poc-v1` (`winserv2025-adpa-poc.vhdx`) is `poc_planned`. The ideation update records the production bake as still active, so `BEN-08` stays unrealized and `HYP-mxc-011` stays `Formulated`.

### Decision
Maintain a separate production base image (`winserv2025-prod-adpa.vhdx`). The production pool does not use the developer image and does not use `winserv2025-golden.vhdx` as its running parent.

* **Minimal footprint**: Windows Server 2025 Server Core or a CIS-hardened Desktop Experience. Print Spooler, Xbox, and telemetry services are disabled.
* **Pre-baked application**: ADPA / SIDPA is installed as a pre-jitted Windows service under a local service account with least privilege.
* **No developer toolchain** (`HYP-mxc-011`, `BEN-08`, `AC-04.1`): a file inventory finds no Scoop, cargo, git, or compiler. `AC-04.1` also requires uv and source repositories to be absent.
* **Warm checkpoint** (`AC-04.2`): the bake starts the service, runs a smoke request against `localhost:8080/health`, closes database handles, and captures `baseline-hot-ready` while the working set is hot. The first wake from that checkpoint does not pay a JIT compile. The wake-time database-pool purge stays with `ADR-006`. The paused RAM reading stays with `ADR-004`.

### Consequences
* *Positive*: The production image is not a developer image. A finished bake has no developer toolchain and a warm checkpoint.
* *Trade-off*: Until `winserv2025-prod-adpa.vhdx` exists and passes the inventory, `BEN-08` stays unrealized. Session discard of the `.avhdx` or the whole guest stays with `ADR-005`.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Hypothesis | HYP-mxc-011 | The production image has no developer toolchain and is checkpointed warm. | TP-03 | — |
| Hypothesis | HYP-mxc-017 | Future: a pool accepts only a signed, scanned image. | TP-03 | ADR-003 horizon |
| Benefit | BEN-08 | The production image is not a developer image. | TP-03 | — |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-003): Automated Supply-Chain Attestation (SBOM & Cosign)**  
> `HYP-mxc-017`. Before a host registers an image in a pool, the bake pipeline has scanned it, produced a software bill of materials, and the host has checked a signature on the VHDX. An unsigned VHDX is refused. The bake path does not sign images or emit a bill of materials today. The hypothesis stays `Formulated`.

---

## ADR-004: Paused RAM standby, trimmed before suspend

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-04` Paused footprint
* **Also**: `TP-02` for the 300 ms caller ceiling. `HYP-mxc-005` also names the warm checkpoint (`TP-03`). `HYP-mxc-018` stays the future-horizon note on this record.

### Context
Leaving Windows Server running keeps the next request fast and keeps paying for an idle machine (spark bad choice 1, business-case Alternative 1). That alternative is rejected when the paused footprint holds: 0.0% CPU, 0.0% GPU, RAM still assigned, and the image disks still allocated.

Cold-booting a stopped guest takes 14–45 seconds. `Save-VM` drops host RAM to 0 MB. Neither state is this standby.

### Decision
The warm pool state is a Hyper-V guest in `Paused`, reached by `Suspend-VM` after the working set has been trimmed.

1. Host CPU charged to each `Paused` standby guest is 0.0% (`HYP-mxc-001`, `AC-03.1`).
2. Host GPU charged to that same guest is 0.0% (`HYP-mxc-007`, `BEN-01`). A production guest has no GPU partition. A missing partition counts as 0.0%, and the record says the partition was absent. No GPU sample exists in the suite, so the first reading is the test.
3. Guest memory stays resident in host RAM. A reading of 0 MB means the guest was saved or stopped, and this decision fails. A balloon driver cannot trim after the vCPUs are frozen. The host does not satisfy the resume by paging the working set in from disk.
4. Trim runs while the vCPUs are still running, on the bake path and on pool replenishment, and only then does `Suspend-VM` run (`HYP-mxc-012`, `AC-03.2`). The paused footprint is about 1.0–1.2 GB (`BEN-10`). On idle release, restore of `baseline-hot-ready` and then suspend means the paused size is the checkpoint size when that restore succeeds. A lessons note also cites a trim under 700 MB. That figure is a different measurement. `BEN-10` cannot pass until one figure is the target.
5. `Resume-VM` finishes in at most 300 ms (`HYP-mxc-002`, `AC-03.3`). The figure is a ceiling. A resume of 301 ms or more fails even when a later first byte still meets the 800 ms check. The 800 ms first byte stays with `ADR-002` (`TP-02`). This decision supplies the 300 ms platform wake inside that caller ceiling.
6. The fast wake is `Resume-VM` from `Paused` RAM at `baseline-hot-ready` (`HYP-mxc-005`). Starting a stopped guest from the parent VHDX is a cold boot. The checkpoint itself stays with `ADR-003` (`TP-03`).
7. Zero CPU and zero GPU do not free the image disks (`HYP-mxc-001`, `HYP-mxc-007`, `BEN-01`). For each `Paused` guest the parent VHDX and any `.avhdx` that belongs to it stay allocated. The catalog sizes are inventory, not a measured paused-guest total: `winserv2025-golden.vhdx` at 10.88 GB with a 64 GB cap, `winserv2025-mxc-dev.vhdx` at 39.25 GB with a 64 GB cap. Production images are still planned, each with a 64 GB cap and no current size. The operator guide asks for at least 50 GB free on the NVMe tier. One, two, or three full copies are an example of the standing cost. A shared parent plus a per-guest `.avhdx` stores the parent once. The catalog gives no `.avhdx` size, so the example does not add one.

### Consequences
* *Positive*: An idle guest uses no processor and no graphics. Resume stays inside 300 ms because the trimmed pages stay in host RAM. The image disks remain allocated.
* *Trade-off*: Host RAM must hold each paused guest at the trimmed size. Two RAM figures are in the suite. GPU has not been read. No paused-guest disk total has been measured.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 1 | Leave the server running and pay for an idle machine. | TP-04 | — |
| Spark | Disk stays allocated | Zero CPU does not free the image disks. | TP-04 | — |
| Spark | 300 ms unpause | Unpause to available is at most 300 ms. | TP-04 | — |
| Hypothesis | HYP-mxc-001 | A paused guest uses 0.0% host CPU. | TP-04 | — |
| Hypothesis | HYP-mxc-002 | Resume-VM finishes in at most 300 ms. | TP-04 | — |
| Hypothesis | HYP-mxc-005 | The fast wake is resume from the hot checkpoint, not a cold boot. | TP-04 | TP-03 |
| Hypothesis | HYP-mxc-007 | Paused RAM stays resident. CPU and GPU stay at 0.0%. Disk stays allocated. | TP-04 | — |
| Hypothesis | HYP-mxc-012 | Trim before pause, to about 1.0–1.2 GB. | TP-04 | — |
| Hypothesis | HYP-mxc-018 | Future: hot guests in RAM, deep guests on NVMe. | TP-04 | ADR-004 horizon |
| Benefit | BEN-01 | Idle processor and graphics, with RAM and image disks still allocated. | TP-04 | — |
| Benefit | BEN-10 | Paused size is the trimmed checkpoint, about 1.0–1.2 GB. | TP-04 | — |
| Business case | Alternative 1 | Leave Windows Server running. Rejected if the paused footprint holds. | TP-04 | — |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-004): Two-Tier Hibernation Hierarchy (RAM Pause vs. NVMe Save-VM)**  
> `HYP-mxc-018`. A small hot set stays `Paused` in RAM and wakes within 300 ms. A larger deep set is saved to NVMe at 0 MB host RAM, wakes in about 1.5 seconds, and is promoted into RAM as leases grow. The running pool uses paused RAM only. No saved-to-NVMe tier has been measured. The hypothesis stays `Formulated`.

---

## ADR-005: Transient differencing disk and egress whitelist

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-05` Session sterility
* **Also**: `TP-03` for the approved production image the next session is reproduced from. `HYP-mxc-019` stays the future-horizon note on this record.

### Context
A session that writes files, logs, or registry entries onto a lasting disk leaves residue for the next caller. The spark discards either the whole Hyper-V guest or only its `.avhdx`, then reproduces the next session from the approved production image.

`HYP-mxc-013` and `BEN-07` cover the differencing-disk path and the egress whitelist. `HYP-mxc-022` and `BEN-12` add the whole-guest path. The approved image is `winserv2025-prod-adpa.vhdx` (`ADR-003`). That file is not in the catalog yet, so `BEN-12` stays open while `BEN-08` waits on the production bake. No discard-and-reproduce run has been captured. The hypotheses stay `Formulated`.

### Decision
Every production session writes only to a transient `.avhdx` anchored at `baseline-hot-ready`. Persistent business data lives in external datastores.

1. **Differencing disk only** (`HYP-mxc-013`, `BEN-07`, `AC-02.1`). The guest remains. On session end, or after 300 seconds with `active_open_requests` at 0, the `.avhdx` is deleted. A file written only on that disk is gone. The parent hash of `winserv2025-prod-adpa.vhdx` is unchanged (`AC-02.2`). The guest returns to `baseline-hot-ready` before it re-enters the warm pool.
2. **Whole guest** (`HYP-mxc-022`, `BEN-12`). The Hyper-V session is removed. A file written only in that guest is gone. The next guest is a new reproduction from the approved production image. This path stays open while that image is unfinished.
3. In both paths the next session's parent matches the approved production image and does not match the developer image. The next session does not inherit disk changes from the previous one. Which file counts as the developer image is `ADR-003` (`TP-03`).
4. **Egress whitelist** (`HYP-mxc-013`, `BEN-07`, `AC-02.3`). Public internet egress is denied. Ingress reaches the guest only on `:8080` from the proxy. Allowed egress, to approved internal endpoints, is SQL `:1433`, PostgreSQL `:5432`, private blob `:443`, DNS `:53`, and Kerberos `:88`. Every other outbound destination is dropped and logged.
5. A request that hangs past `max_request_execution_timeout_seconds` (default 900 seconds) ends with HTTP 504, then the instance is reaped (`AC-02.1`). That 504 is a hung request. It is not a wake-caused 504. Wake-caused 502 and 504 stay with `ADR-002`. Entropy reseed, the clock step, and the database-pool purge stay with `ADR-006`.

### Consequences
* *Positive*: Session residue does not remain. The next session is reproduced from the approved production image. Egress stays on the named whitelist.
* *Trade-off*: Both discard paths have to be checked. The whole-guest path cannot pass until the production image exists. A file-backed `.avhdx` is still the scratch disk.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Discard and reproduce | Discard the whole guest or only the .avhdx, then reproduce from the approved image. | TP-05 | TP-03 |
| Hypothesis | HYP-mxc-013 | Session disk writes disappear. Egress stays on the whitelist. | TP-05 | — |
| Hypothesis | HYP-mxc-022 | Discard the whole guest or only the .avhdx, then reproduce from the approved image. | TP-05 | TP-03 |
| Hypothesis | HYP-mxc-019 | Future: session scratch in memory, wiped on release. | TP-05 | ADR-005 horizon |
| Benefit | BEN-07 | Session residue does not remain. | TP-05 | — |
| Benefit | BEN-12 | Discard and reproduce from the approved production image. | TP-05 | TP-03 |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-005): WORM Memory-Backed Ephemeral Scratch Disks**  
> `HYP-mxc-019`. Session scratch I/O uses a write-once memory disk attached over VMBus. On release that memory is wiped, and a read of the range returns zeros. Scratch writes are absent from the host filesystem. Sessions still use a file-backed `.avhdx`. The hypothesis stays `Formulated`.

---

## ADR-006: Watermark pool, replenish, and wake hygiene

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-06` Pool and wake hygiene
* **Also**: `TP-02` for ingress queue depth. `TP-04` for RAM per extra paused guest. `TP-05` for discard on cooldown. `HYP-mxc-020` stays the future-horizon note on this record.

### Context
One paused guest serves one caller. A burst can lease that guest and leave the next caller with a cold provision. `HYP-mxc-014` and `BEN-09` require the warm pool to refill itself, and require wake hygiene before traffic. No surge run has been captured. The hypothesis stays `Formulated`.

Two surge figures are in the suite. They are not the same target. This record's example is above 5 requests per second, or an ingress queue depth above 0. The lessons note and `US-05` `AC-05.2` use 10 or more requests per second. The functional design stores `surge_velocity_threshold_rps: 10`. The lessons window is a rolling 5 seconds. `BEN-09` cannot treat those figures as one target.

### Decision
The control plane keeps a watermark pool. States run `ColdProvisioned` → `StandbyPaused` → `ActiveRunning`.

1. **`ColdProvisioned`** holds a differencing disk on NVMe and commits 0 MB of host RAM. It is inventory, not the paused standby in `ADR-004`.
2. **`StandbyPaused`** is the warm guest. The trim, the 0.0% CPU reading, and the 300 ms `Resume-VM` stay with `ADR-004` (`TP-04`). Each extra paused guest adds that same RAM cost.
3. **`ActiveRunning`** is the leased guest serving HTTP.
4. **Low watermark.** When a ready guest is leased, a background worker promotes a `ColdProvisioned` guest to `StandbyPaused` in about 1.5 seconds. The in-flight request is not blocked (`HYP-mxc-014`, `AC-05.1`). The default ready count is at least 1.
5. **High watermark.** A surge raises the ready count up to the configured \(K_{\max}\) so the next caller does not cold-boot (`BEN-09`). Two figures are both recorded, and a passing check names which one was configured:
   * Above 5 requests per second, or ingress queue depth above 0. Queue depth is the `TP-02` touch.
   * 10 or more requests per second over a rolling 5-second window (`AC-05.2`, lessons note).
   A pass at 5 requests per second does not pass the 10-request figure, and the reverse is also true. Until one figure is chosen, `BEN-09` cannot treat them as a single target. Suite examples of \(K_{\max}\) are 5 and 5–10. The check records the configured cap.
6. **Explicit pre-warm.** `mxc-pool-warm --target prod-adpa --count N` can raise the ready count before a known peak. That command is not a forecast.
7. **Wake hygiene**, before the guest accepts traffic. The first `/health` reports all three (`AC-02.4`):
   * Entropy is reseeded from hardware (`RDRAND` / `RDSEED` or `BCryptGenRandom`), because siblings restored from `baseline-hot-ready` share a PRNG state.
   * The guest clock is stepped to host UTC (`VMICTimeSync`) before `/health` returns HTTP 200. That step is what sign-in in `ADR-002` waits on. The sign-in itself stays there.
   * Stale database connection pools are cleared (`ClearAllPools()` or the Npgsql equivalent). Handles may also be closed before the checkpoint is captured.
8. **Cooldown.** After the configured idle time with `active_open_requests` at 0, surplus guests above \(K_{\min}\) leave `ActiveRunning`. Differencing disks are discarded and the guest returns toward the low watermark. Discard of the disk is `ADR-005` (`TP-05`). This record's idle figure is 300 seconds (`HYP-mxc-014`, `BEN-09`). `AC-05.4` uses `reaping_cooldown_seconds` of 180 seconds. The check records which cooldown was configured. A pass at one figure does not pass the other.

### Consequences
* *Positive*: A burst refills the ready pool in about 1.5 seconds. The next caller does not cold-boot. Wake hygiene runs before traffic.
* *Trade-off*: Each extra paused guest holds the `ADR-004` RAM footprint until cooldown. `BEN-09` stays open while two surge figures and two cooldown figures are both in the suite.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Hypothesis | HYP-mxc-014 | The warm pool refills, and wake hygiene runs before traffic. | TP-06 | — |
| Hypothesis | HYP-mxc-020 | Future: a forecast pre-warms the pool about 60 seconds ahead. | TP-06 | ADR-006 horizon |
| Benefit | BEN-09 | A burst does not cold-boot the next caller. | TP-06 | — |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-006): AI-Driven Predictive Ingress Forecasting**  
> `HYP-mxc-020`. A small on-host time-series model pre-warms a pool about 60 seconds before a predicted demand peak, with no manual schedule. Pre-warm today is an explicit pool command or a surge reaction under `HYP-mxc-014`. No forecast model is running. The hypothesis stays `Formulated`.

---

## ADR-008: Authentication-Gated Session Provisioning & Identity-Bound VM Leasing

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team
* **Topic pillar**: `TP-02` Ingress
* **Also**: `TP-05` when a route selects identity-bound leasing. Path-only leasing, `HYP-mxc-008`, and `BEN-06` stay with `ADR-002`. No spark row, hypothesis id, or benefit id states this decision.

### Context
ADR-002's Connection-Buffering Ingress Gateway issues `pool_lease` on **any** inbound HTTPS request matched to a route's path — before any application-layer authentication occurs. The guest VM becomes `ActiveRunning` and begins executing before the gateway knows who, if anyone, is actually requesting access. Routing (FDD §2.1) is pool-scoped by path only (`/api/v1/adpa/*` → `pool:prod-adpa`), never by requester identity — every leased instance comes from the same fungible pool, and a released instance returns to that same shared pool rather than remaining associated with the user who leased it (ADR-005's differencing-disk rollback erases session state specifically to prevent any such binding, by design).

This leaves two real, related gaps wherever the woken environment is meant to be a personalized desktop/application session rather than a stateless API backend: (1) no mechanism ties VM wake specifically to a credential-submission event, as distinct from mere connection arrival; (2) no mechanism lets a specific user's repeated sessions route to a dedicated VM identity, as distinct from the next available instance in a shared pool. Neither gap is covered by US-01 through US-05 (`USER_STORIES.md`) — all five assume path-routed, identity-agnostic leasing.

### Decision
Add an **Authentication-Gated Leasing** mode to the JIT Ingress Gateway (ADR-002), selectable per route, alongside the existing path-only matching:

1. **Credential-Triggered Wake**: for a route configured `leasing_mode: "auth_gated"`, the gateway holds the inbound connection (identical buffering mechanism to ADR-002) but does **not** issue `pool_lease` on connection arrival. It terminates TLS, proxies the request to the organization's existing IdP (OIDC/SAML; MFA handled entirely by that IdP, never by MXC), and issues `pool_lease` only after a successful authentication assertion. A failed or abandoned login never wakes a VM — a real, measurable resource-efficiency property, not only a security one.
2. **Identity-to-Pool-Target Resolution**: the authentication assertion's claims (group, role, tenant) resolve, via a configurable claims-to-pool-target mapping, to a target pool or golden-image variant — ADR-003's production-vs-developer image separation generalizes directly to more than two variants, selected by claim rather than hardcoded per route.
3. **Two leasing strategies, named explicitly, never conflated**:
   * **Pool-generic leasing** (the ADR-002 default, unchanged): next available instance from the resolved pool; on release, returns to that shared pool per ADR-005. Fits the existing US-01/US-02 stateless-processing scenarios.
   * **Identity-bound leasing** (new): the control plane persists a durable `(authenticated_identity, pool_target) → VM instance id` mapping. A returning user's later authentication resolves to the *same* instance if it still exists in the pool (paused, not yet reaped past `StandbyPaused`), rather than an arbitrary one. This is the mode that lets per-user settings persist across sessions — pool-generic leasing cannot do this by design, since ADR-005 deliberately erases differencing-disk state on every release.
4. **Timing budget stays inside the MFA latency users already tolerate**: the credential-gated Resume-VM step (≤300ms, ADR-004) happens *after* the IdP's own authentication round-trip completes, not before or in parallel in a way that adds a second, separately-perceived wait. Total added latency on top of a normal MFA login is the same ≤300ms Resume plus the existing ≈50ms health-probe handshake (ADR-002 §Mechanism step 5) — inside the multi-second budget users already experience for an MFA challenge.

### Rationale
* **Resource efficiency compounds correctly only if the trigger is real intent, not mere connection arrival.** ADR-002/ADR-004 already guarantee 0.0% idle CPU while paused; gating wake behind a *successful* authentication — rather than any TCP connection — means an anonymous scan, a bot, or an abandoned login page never wakes a VM at all, a strictly stronger property than connection-triggered wake alone provides.
* **Identity-bound leasing is a genuinely different commitment from ADR-005's stateless rollback, and must be declared, not silently inferred.** A route operator must explicitly opt into `identity_bound` leasing, because it changes a real property ADR-005 otherwise guarantees unconditionally (full rollback to baseline on every release). Making this opt-in per route prevents a route that only needs pool-generic leasing from accidentally inheriting persistent per-user state it never asked for.
* **MXC does not re-implement authentication or MFA.** Delegating credential validation entirely to the organization's existing IdP keeps this ADR's scope to *when* MXC wakes a VM and *which* VM it wakes, not *how* a user proves who they are — consistent with the existing guest-credential mechanism (`hyperv-state-aware.md`), which is for MXC's own internal automation and is unaffected by this decision.

### Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Keep path-only wake, then authenticate inside the already-running guest | Rejected for routes that need a person rather than a path. The guest would be `ActiveRunning` before the gateway knows who asked. This remains the `ADR-002` default for stateless API routes. |
| Identity-bind every release | Rejected. It would silently remove `ADR-005`'s unconditional rollback. Binding is opt-in. |
| MXC implements OIDC, SAML, or MFA | Rejected. The organization's identity provider already does that. |

### Consequences
* *Positive*: Enables genuine per-user VDI-style desktop/application provisioning on the existing scale-to-zero infrastructure, with no VM running — and no cost incurred — until a real, successfully authenticated user needs one. Added latency is bounded and lands inside the window users already tolerate for MFA, not a new, separately-perceived delay.
* *Trade-off*: Identity-bound leasing requires a new durable mapping that must itself be reaped/expired on its own policy — an abandoned identity-bound VM cannot be silently returned to the shared pool the way a pool-generic one is, without first deciding how long to hold the binding. This ADR names that need; it does not set the expiry parameters, deferring to a follow-up FDD change.
* *Trade-off*: A compromised or over-privileged IdP claim could now select a higher-privilege image variant (ADR-003) or rebind to another user's retained instance. The claims-to-pool-target mapping becomes a real, security-relevant configuration surface that did not exist when routing was purely path-based, and warrants the same review rigor as any other access-control configuration.

### Project details carried in

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Architecture suite | ADR-002 boundary | Path-only `pool_lease` stays the default. | TP-02 | — |
| Hypothesis | HYP-mxc-008 | Guest sign-in after wake. Not this decision. | TP-02 | ADR-002 |
| Benefit | BEN-06 | Sign-in does not wait on boot. Not this decision. | TP-02 | ADR-002 |
| — | No register row | No spark row, hypothesis id, or benefit id states credential-triggered wake or identity-bound leasing. | TP-02 | TP-05 |

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-008): Graceful Session Hand-Back for Identity-Bound Desktops**  
> Extend identity-bound leasing with an explicit "disconnect, don't release" state distinct from both `ActiveRunning` and the existing `ReapingState` (ADR-006), so a user who closes their client without logging out can reconnect to the same paused instance within a configurable grace window before normal idle-timeout rollback applies — the VDI equivalent of session reconnect, layered on the existing Paused-state mechanism (ADR-004) rather than requiring a new suspend primitive.


