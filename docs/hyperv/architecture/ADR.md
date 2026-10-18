# Pillar II: Architectural Decision Records (ADR)
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

---

## ADR-001: Selection of Type-1 Hyper-V Virtualization over Container Namespaces

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
Enterprise automation workloads (such as ADPA and SIDPA) require running Windows-native services, COM+ dependencies, and proprietary data processing tasks. We evaluated Windows Server Containers vs. Hyper-V Generation 2 Type-1 Virtual Machines.

### Decision
Standardize on **Type-1 Hyper-V Generation 2 Virtual Machines** orchestrated by the native Rust control plane (`wxc-exec --features hyperv`).

### Rationale
* **Hardware-Level Security**: Hyper-V partitions utilize hardware virtualization extensions (Intel VT-x / AMD-V) and Second-Level Address Translation (SLAT), providing a verifiable hardware boundary that prevents kernel privilege escalation or cross-tenant memory snooping.
* **Full Subsystem Compatibility**: ADPA/SIDPA frequently depend on Windows Server components that are unsupported or unstable inside container namespaces (WMI, Windows Performance Counters, native Windows Services, GPO enforcements).
* **Deterministic Memory State**: Hyper-V memory checkpoints allow freezing the entire operating system in a fully-booted, warm state.

### Consequences
* *Positive*: Total isolation, cryptographic immutability, full Windows Server API compatibility.
* *Trade-off*: Requires a Windows Pro, Enterprise, or Windows Server host with Hyper-V enabled.

---

## ADR-002: Just-in-Time (JIT) Connection-Buffering Ingress Gateway

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
End users and upstream webhooks send standard HTTPS requests to public endpoints (e.g., `https://adpa.internal.company.com/api/v1/process`). When the backend VM is dormant (`Paused`), the socket is closed or unreachable.

### Decision
Deploy an intelligent **Connection-Buffering Ingress Reverse Proxy** (YARP / Envoy / FastMCP Gateway) in front of the VM cluster.

### Mechanism
1. Client establishes TLS connection to the Ingress Proxy.
2. Ingress Proxy checks whether the target sandbox VM is active.
3. If dormant, the proxy **holds the client request buffer open** and synchronously dispatches a wake signal (`pool_lease` / `resume`) to the MXC control plane.
4. MXC wakes the VM in $<300\text{ms}$.
5. The proxy performs a TCP loopback handshake against the guest service port (`:8080`) until confirmed ready ($\approx 50\text{ms}$).
6. The held request is flushed to the guest application and the response streamed back to the client.

### Consequences
* *Positive*: Clients experience zero connection drops, resets, or 502/504 errors. Standard REST and browser clients work seamlessly without custom wake-up SDKs.

---

## ADR-003: Dedicated Production Base Image Separation

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
The developer golden image (`winserv2025-golden.vhdx`) includes compilation toolchains (Rust MSVC, Node.js, .NET SDK, Scoop, uv, Playwright, compilers, source repositories). Production deployments require minimized attack surfaces and zero unauthorized tooling.

### Decision
Maintain a separate, hardened **Production Base Image** (`winserv2025-prod-adpa.vhdx`) distinct from the development image:
* **Minimal Footprint**: Windows Server 2025 Server Core or Hardened Desktop Experience.
* **Pre-Baked Application**: ADPA / SIDPA installed as pre-jitted, auto-starting Windows Services under local service accounts with least privilege.
* **No Compilers or Package Managers**: Scoop, cargo, git, and dev SDKs are strictly excluded.
* **Pre-Warmed State**: During image baking, smoke-test requests are run against the application to pre-warm memory caches and ensure JIT compilation is complete before capturing the golden checkpoint.

---

## ADR-004: Memory-Preserved Standby (Paused Hypervisor RAM State)

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
Cold-booting Windows Server takes 25–45 seconds. Pausing an active VM keeps guest physical memory intact in host RAM, freezing the virtual CPU instruction pointer.

### Decision
Implement the warm pool state as **Hyper-V Paused Instances**:
* When dormant, VMs remain in Hyper-V `Paused` state.
* The host hypervisor stops scheduling vCPU execution ticks (0.0% CPU usage).
* Dynamic Memory allows the hypervisor to trim and page unneeded working set memory.
* Resuming the VM via `Resume-VM` executes in **`<300ms`**.

---

## ADR-005: Automated Checkpoint Differencing Disks for Stateless Execution

* **Status**: Accepted
* **Date**: October 2026
* **Deciders**: Systems Architecture Team

### Context
If production services write temporary files, logs, or registry entries during an end-user session, those modifications could accumulate over time, leading to disk bloat, performance degradation, or security cross-contamination.

### Decision
Execute all production sessions against a **transient differencing disk (`.avhdx`)**:
* When an instance is leased, Hyper-V creates an active differencing checkpoint anchored to the clean production baseline.
* All disk writes are captured in the differencing disk.
* Upon session release or inactivity timeout, the differencing disk is discarded and the VM is reverted to the immutable baseline snapshot before returning to the warm standby pool.
* Persistent business data is stored exclusively in external enterprise datastores (SQL Server, PostgreSQL, S3/Blob storage), guaranteeing that the compute instance remains 100% ephemeral.
