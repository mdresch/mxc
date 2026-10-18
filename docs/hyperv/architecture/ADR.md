# Pillar II: Architectural Decision Records (ADR)
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)

---

## ADR-001: Selection of Type-1 Hyper-V Virtualization over Container Namespaces

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
Enterprise automation workloads (such as ADPA and SIDPA) require running Windows-native services, COM+ dependencies, and proprietary data processing tasks. We evaluated Windows Server Containers against Hyper-V Generation 2 Type-1 Virtual Machines with saved-state memory resumption.

### Decision
Standardize on **Type-1 Hyper-V Generation 2 Virtual Machines** orchestrated by the native Rust control plane (`wxc-exec --features hyperv`).

### Rationale
* **Hardware-Level Security**: Hyper-V partitions utilize hardware virtualization extensions (Intel VT-x / AMD-V) and Second-Level Address Translation (SLAT), providing a verifiable hardware boundary that prevents kernel privilege escalation or cross-tenant memory snooping.
* **Full Subsystem Compatibility**: ADPA/SIDPA frequently depend on Windows Server components that are unsupported or unstable inside container namespaces (WMI, Windows Performance Counters, native Windows Services, COM+, GPO enforcements).
* **Deterministic Memory State**: Hyper-V memory checkpoints allow freezing the entire operating system in a fully booted, warm state.

### Consequences
* *Positive*: Total hardware isolation, cryptographic immutability, full Windows Server 2025 API compatibility.
* *Trade-off*: Requires a Windows Pro, Enterprise, or Windows Server host with Hyper-V enabled (Machine A).

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-001): Hyper-V Direct Micro-VM Partitions**  
> Explore integration with lightweight Hyper-V micro-VM profiles and custom minimal Windows Server Core footprints to reduce baseline memory commitment per suspended instance from $1\text{GB}$ down to $<256\text{MB}$.

---

## ADR-002: Just-in-Time (JIT) Connection-Buffering Ingress Gateway

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
End users and upstream webhooks send standard HTTPS requests to public endpoints (e.g., `https://adpa.internal.company.com/api/v1/process`). When the backend VM is dormant (`Paused`), the guest TCP socket is unreachable.

### Decision
Deploy an intelligent **Connection-Buffering Ingress Reverse Proxy** (YARP / Envoy / FastMCP Gateway) in front of the VM cluster.

### Mechanism
1. Client establishes a TLS connection to the Ingress Proxy.
2. Ingress Proxy checks whether the target sandbox VM is active.
3. If dormant, the proxy **holds the client request buffer open** and synchronously dispatches a wake signal (`pool_lease` / `resume`) to the MXC control plane.
4. MXC wakes the VM in $<300\text{ms}$.
5. The proxy performs a TCP loopback handshake against the guest service port (`:8080/health`) until confirmed ready ($\approx 50\text{ms}$).
6. The held request is flushed to the guest application and the response streamed back to the client.

### Consequences
* *Positive*: Clients experience zero connection drops, resets, or 502/504 errors. Standard REST and browser clients work seamlessly without custom wake-up SDKs.

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-002): WebSocket & SSE Suspension Multiplexing**  
> Upgrade the JIT Ingress Proxy to support long-lived WebSocket and Server-Sent Events (SSE) connection suspension, enabling real-time UI progress streams and transparent session resumption across mid-conversation idle pauses.

---

## ADR-003: Dedicated Production Base Image Separation

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
The developer golden image (`winserv2025-golden.vhdx`) includes compilation toolchains (Rust MSVC, Node.js, .NET SDK, Scoop, uv, Playwright, compilers, source repositories). Production deployments require minimized attack surfaces, reduced disk footprint, and zero unauthorized developer tooling.

### Decision
Maintain a separate, hardened **Production Base Image** (`winserv2025-prod-adpa.vhdx`) strictly isolated from the development image pipeline:
* **Minimal Footprint**: Windows Server 2025 Server Core or CIS-Hardened Desktop Experience with unnecessary services (Print Spooler, Xbox, Telemetry) disabled.
* **Pre-Baked Application**: ADPA / SIDPA installed as pre-jitted, auto-starting Windows Services under local service accounts with least privilege.
* **No Compilers or Package Managers**: Scoop, cargo, git, and dev SDKs are strictly excluded.
* **Pre-Warmed State**: During image baking, synthetic smoke-test requests are executed against the application to pre-warm memory caches and verify JIT compilation before capturing the golden checkpoint (`baseline-hot-ready`).

### Consequences
* *Positive*: Drastically reduced attack surface, CIS benchmark compliance, and zero JIT compilation latency on wake.

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-003): Automated Supply-Chain Attestation (SBOM & Cosign)**  
> Integrate automated vulnerability scanning (Trivy), Software Bill of Materials (SBOM) generation, and cryptographic VHDX image signing (Cosign) directly into the CI/CD image baking pipeline so the Hyper-V host verifies image signatures prior to pool registration.

---

## ADR-004: Memory-Preserved Standby (Paused Hypervisor RAM State)

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
Cold-booting Windows Server takes 25–45 seconds. Pausing an active VM keeps guest physical memory intact in host RAM while freezing the virtual CPU instruction pointer.

### Decision
Implement the warm pool state as **Hyper-V Paused Instances**:
* When dormant, VMs remain in Hyper-V `Paused` state with instruction pointers frozen (`0.0% CPU`).
* **Pre-Trimmed Working Set**: Rather than relying on the guest balloon driver to actively reclaim memory while its vCPUs are frozen (which is impossible when paused) or forcing host smart-paging/swap (which violates the `<300ms` resume SLA due to disk I/O page-ins), guest memory is aggressively trimmed and compacted **prior** to issuing `Suspend-VM` during pool replenishment and image baking. This locks each dormant instance into a lean static host RAM allocation ($\approx 1.0\text{ – }1.2\text{ GB}$).
* Resuming the VM via `Resume-VM` executes in **`<300ms`** because physical memory pages remain resident in host RAM.

### Consequences
* *Positive*: Guaranteed deterministic sub-300ms wake times with 0.0% idle CPU overhead.
* *Trade-off*: Requires sizing host physical RAM to accommodate $K_{\text{ready}}$ warm paused instances without triggering host-level memory overcommit swap.

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-004): Two-Tier Hibernation Hierarchy (RAM Pause vs. NVMe Save-VM)**  
> Introduce a tiered standby hierarchy where hot-queue instances ($N=2$) remain in Paused RAM state ($<300\text{ms}$ wake), while deep-standby instances ($N=10$) are placed in Saved NVMe state ($0\text{MB}$ host RAM, $\approx 1.5\text{s}$ wake) and promoted into RAM dynamically as active leases increase.

---

## ADR-005: Automated Checkpoint Differencing Disks for Stateless Execution

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
If production services write temporary files, logs, or registry entries during an end-user session, those modifications accumulate over time, leading to disk bloat, configuration drift, performance degradation, or cross-tenant security contamination.

### Decision
Execute all production sessions against a **transient differencing disk (`.avhdx`)**:
* When an instance is leased, Hyper-V operates on an active differencing checkpoint anchored to the clean production baseline (`baseline-hot-ready`).
* All disk writes during the session are captured exclusively in the `.avhdx` differencing layer.
* Upon session release or inactivity timeout ($300\text{s}$), the differencing disk is discarded and the VM is reverted to the immutable baseline snapshot before returning to the warm standby pool.
* **Internal Data Plane & Egress Whitelist**: Persistent business data is stored exclusively in external enterprise datastores (SQL Server, PostgreSQL, S3/Blob storage). To balance zero-trust network isolation with database persistence, the guest firewall implements a strict egress whitelist:
  * Public Internet Egress: **Strictly Blocked** (Default Deny).
  * Ingress Traffic: **Port `:8080` only**, restricted to the Ingress Reverse Proxy Gateway on the internal vSwitch.
  * Egress Traffic: **Restricted to Internal Enterprise Datastore Subnets**: TCP `:1433` (SQL Server), TCP `:5432` (PostgreSQL), and TCP `:443` (S3 / Blob Storage Private Endpoints). All other outbound destinations are dropped and logged.


### Consequences
* *Positive*: Zero post-session state drift and guaranteed eradication of any session residue.

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-005): WORM Memory-Backed Ephemeral Scratch Disks**  
> Transition high-throughput temporary scratch I/O from file-backed `.avhdx` delta layers to Write-Once-Read-Many (WORM) host RAM-disks attached via VMBus SCSI, achieving near-zero I/O latency and instantaneous physical memory zeroing upon release.

---

## ADR-006: Dynamic Watermark-Based Standby Pool Autoscaling & Predictive Warm-Up

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
While maintaining a single dormant instance in Paused RAM achieves sub-300ms wake-up for a single request, a burst of concurrent requests or high-volume batch processing for ADPA/SIDPA could exhaust the standby capacity. If the solitary warm instance is leased, the next simultaneous client request would either wait in a queue or trigger an unbuffered cold provision. Production systems require elastic, proactive ready-state replenishment so multiple warm instances are immediately available whenever demand indicators surge.

### Decision
Implement an **Adaptive Low/High Watermark Standby Pool Manager** with proactive replenishment and predictive event-driven scaling:
1. **Tiered Lifecycle States (`ColdProvisioned` $\rightarrow$ `StandbyPaused` $\rightarrow$ `ActiveRunning`)**:
   * **`ColdProvisioned`**: Differencing disk `.avhdx` created and attached to VM container on NVMe, but memory is *not* committed to host RAM ($0\text{ MB}$ RAM). Used for background inventory.
   * **`StandbyPaused`**: VM booted, working set pre-warmed, pre-trimmed, and frozen in Hyper-V Paused state ($\approx 1.0\text{ – }1.2\text{ GB}$ RAM, $0.0\%\text{ CPU}$). Resumes in $<300\text{ms}$.
   * **`ActiveRunning`**: Unpaused and actively routing HTTP traffic.
2. **Immediate Standby Replenishment (Low Watermark $K_{\text{min}}$)**: The control plane maintains a minimum target of ready-state instances (default $K_{\text{ready}} \ge 1$ or $2$). As soon as an instance is leased (`StandbyPaused` $\rightarrow$ `ActiveRunning`), an asynchronous background worker promotes a `ColdProvisioned` instance into `StandbyPaused` state in $\approx 1.5\text{s}$ in the background so the ready buffer is never depleted.
3. **Surge Velocity & Queue Depth Autoscaling (High Watermark $K_{\text{max}}$)**: If request arrival velocity exceeds threshold (e.g. $> 5\text{ req/s}$) or Ingress Buffer queue depth $> 0$, the ready pool target dynamically expands up to $K_{\text{max}}$ (e.g., 5–10 ready instances).
4. **Requirement & Schedule-Driven Pre-Warming**: The pool manager exposes an API (`mxc-pool-warm --target prod-adpa --count 5`) allowing external schedulers, calendar triggers, or upstream batch orchestrators to pre-warm instances minutes before known workload peaks (e.g., market open, shift changes, end-of-day reconciliation).
5. **PRNG Entropy Re-Seeding on Wake**: Because sibling VMs restored from the same `baseline-hot-ready` checkpoint share identical kernel PRNG states, the guest service forcibly re-seeds its cryptographic random pool from hardware CPU instructions (`RDRAND` / `RDSEED` or `BCryptGenRandom` with `BCRYPT_RNG_USE_ENTROPY_IN_BUFFER`) upon receiving the initial wake signal, preventing duplicate UUIDs or nonce collisions.
6. **Clock-Skew Synchronization Assertion**: To prevent TLS handshake, JWT validation, or Kerberos ticket failures due to stale snapshot timestamps, the guest health probe verifies that Hyper-V Time Synchronization (`VMICTimeSync`) has stepped the guest clock to host UTC time before reporting `HTTP 200 {"status": "healthy"}`.
7. **Dynamic Cooldown & Graceful Reaping**: When traffic subsides and instances remain idle past the inactivity threshold ($300\text{s}$) with zero active open requests, surplus instances are systematically rolled back, differencing disks discarded, and VMs suspended or deallocated back to baseline $K_{\text{min}}$.

### Consequences
* *Positive*: Seamless multi-tenant concurrency handling with zero queuing delay during traffic spikes; zero cold-boot delays; cryptographic security against PRNG entropy duplication; zero clock-skew authentication errors.
* *Trade-off*: Burst expansion momentarily consumes additional host RAM ($\approx 1.0\text{ – }1.2\text{ GB}$ per additional paused instance), which is reclaimed back to disk upon idle cooldown.

> [!TIP]
> **Future Horizon & Scaling Enhancement (ADR-006): AI-Driven Predictive Ingress Forecasting**  
> Train an on-host lightweight time-series model (e.g., ONNX-based ARIMA or temporal transformer) analyzing historical request telemetry to automatically pre-warm pools 60 seconds ahead of anticipated demand cycles with zero manual scheduling.


