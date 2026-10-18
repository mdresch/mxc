# Pillar IV: User Stories & Acceptance Criteria
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes (ADPA / SIDPA)

---

## User Story US-01: Low-Latency On-Demand Processing (End User)

> **As an** Enterprise Automation Operator or Upstream REST Client,  
> **I want** to dispatch requests to the ADPA / SIDPA production endpoints at any time of day,  
> **So that** my data is processed immediately with sub-second response times without encountering gateway 502/504 errors or waiting for a server cold boot.

### Acceptance Criteria
* **AC-01.1 (Cold Wake TTFB & Platform Overhead)**:
  * *Given* the target Hyper-V VM (`hv:prod-adpa-01`) is in a dormant (`Paused`) state,
  * *When* the client transmits an HTTP POST payload to `https://gateway.internal/api/v1/adpa/process`,
  * *Then* the gateway must hold the connection, wake the VM via `mxc-pool-lease` ($\le 300\text{ms}$ platform wake overhead), establish the socket connection, and return the initial HTTP response/header flush within **$\le 800\text{ms}$** total wall-clock Time to First Byte (TTFB), before streaming subsequent business logic payloads.
* **AC-01.2 (Subsequent Warm Traffic)**:
  * *Given* the VM is already active (`Running`),
  * *When* subsequent HTTP requests arrive within the active session window,
  * *Then* the gateway must forward requests immediately with a proxy overhead of **$\le 5\text{ms}$** ($\le 15\text{ms} - 25\text{ms}$ total response overhead) plus application processing time.
* **AC-01.3 (Zero Connection Drops & Saturation Fallback)**:
  * *Given* normal operating conditions, incoming client requests shall experience zero HTTP 502 Bad Gateway or HTTP 504 Gateway Timeout errors due to VM wake-up latency.
  * *Given* an extreme host saturation event where wake-up exceeds `wake_timeout_ms` ($3000\text{ms}$), the gateway must gracefully return a structured HTTP 503 Service Unavailable with a `Retry-After` header rather than dropping the TCP socket.

> [!TIP]
> **Future Horizon & Scaling Enhancement (US-01): Interactive SSE Wake-Up Telemetry**  
> Provide an optional client-side loading skeleton or progress stream via Server-Sent Events (SSE) for browser portals so end users receive immediate visual confirmation ("Resuming isolated secure enclave...") within $10\text{ms}$ of connection hold.

---

## User Story US-02: Cryptographic State Rollback & Zero Persistence (SecOps)

> **As a** Chief Information Security Officer (CISO) and Compliance Auditor,  
> **I want** every execution session of SIDPA to run inside a hardware-isolated environment that is mathematically wiped clean upon completion,  
> **So that** malicious payloads, memory scrapers, or sensitive customer records cannot persist across different user sessions.

### Acceptance Criteria
* **AC-02.1 (Ephemeral Differencing Disks & Execution Safety Timeout)**:
  * *Given* an active processing session where files, temporary tables, or registry keys were modified in the guest,
  * *When* the session ends or the 300-second inactivity timer expires (with `active_open_requests == 0`),
  * *Then* the Differencing Delta Disk (`.avhdx`) must be permanently deleted from host storage, leaving zero residual files or logs,
  * *And* if an in-flight request hangs or client connection leaks beyond `max_request_execution_timeout_seconds` (default: 900s / 15 minutes), the gateway must forcefully terminate the socket with HTTP 504 Gateway Timeout, decrement `active_open_requests`, and trigger instance reaping.
* **AC-02.2 (Cryptographic Baseline Verification)**:
  * *Given* a completed session rollback,
  * *When* the VM is reverted to the `baseline-hot-ready` checkpoint,
  * *Then* SHA-256 verification of the parent base VHDX (`winserv2025-prod-adpa.vhdx`) must remain bit-for-bit identical before and after execution.
* **AC-02.3 (Network Airgap & Datastore/Directory Egress Whitelist)**:
  * *Given* a production guest instance,
  * *When* the instance is active or dormant,
  * *Then* arbitrary public internet egress must be strictly blocked (airgap mode),
  * *And* outbound traffic is restricted exclusively to internal enterprise infrastructure and datastore endpoints:
    * Enterprise Datastores: TCP `:1433` (SQL Server), TCP `:5432` (PostgreSQL), and TCP `:443` (Private S3/Blob storage endpoints).
    * Core Directory & Name Resolution: UDP/TCP `:53` (Internal DNS for enterprise FQDN resolution) and UDP/TCP `:88` (Active Directory Domain Controller Kerberos for Windows Integrated Authentication).
* **AC-02.4 (PRNG Hardware Entropy, DB Connection Pool Flush, & Clock Synchronization)**:
  * *Given* a VM restored from `baseline-hot-ready` memory checkpoint,
  * *When* the guest service initializes upon wake,
  * *Then* it must forcibly re-seed its random number generator from CPU hardware (`RDRAND` / `BCryptGenRandom`) to guarantee unique cryptographic nonces and UUIDs across sibling cloned VMs,
  * *And* flush and clear active database driver connection pools (e.g., ADO.NET `ClearAllPools()` or Npgsql reset) to prevent TCP connection resets caused by dead pooled sockets held across checkpoint sleep,
  * *And* the guest clock must verify synchronization against host UTC time before returning `HTTP 200` on the health probe, preventing clock-skew authentication errors.

> [!TIP]
> **Future Horizon & Scaling Enhancement (US-02): Zero-Fill Scrubbing & Per-Session Key Rotation**  
> Integrate automated zero-fill block scrubbing passes and ephemeral per-session BitLocker/virtual-TPM key rotation so that discarded `.avhdx` sectors leave zero physical data remanence on host NVMe arrays.

---

## User Story US-03: High-Density Scale-to-Zero Virtualization (DevOps & SRE)

> **As an** Infrastructure Platform Engineer,  
> **I want** dormant production instances to release active CPU and compress RAM usage,  
> **So that** our on-premise Windows Server / Hyper-V cluster can host $5\times$ to $10\times$ more application workloads than traditional always-on VMs.

### Acceptance Criteria
* **AC-03.1 (Zero CPU Utilization)**:
  * *Given* 10 registered production service VMs in the warm standby pool,
  * *When* no client requests are active (`Paused` state),
  * *Then* total host CPU utilization across all 10 VMs must measure strictly **0.0%** on the Hyper-V host performance monitor.
* **AC-03.2 (Lean Static Host Memory Footprint)**:
  * *Given* suspended standby instances in `StandbyPaused` state,
  * *When* measured on the host hypervisor,
  * *Then* each dormant VM's host RAM commitment must not exceed $\approx 1.0\text{ – }1.2\text{ GB}$ (achieved via working set pre-trimming prior to snapshot capture), eliminating host swap-in disk page latency on resume.
* **AC-03.3 (Sub-300ms Hypervisor Wakeup & Pool Queue)**:
  * *Given* a configurable ready queue size ($N$),
  * *When* the Ingress Gateway dispatches a wake signal,
  * *Then* the elapsed time for Hyper-V to complete `Resume-VM` must be $\le 300\text{ms}$.


> [!TIP]
> **Future Horizon & Scaling Enhancement (US-03): Automated NUMA Node Alignment**  
> Implement host-level Non-Uniform Memory Access (NUMA) node pinning and intelligent memory overcommit policies in `wxc-exec`, maximizing physical server tenant density by up to $300\%$ without cross-socket memory latency degradation.

---

## User Story US-04: Automated Release Image Baking (CI/CD Pipeline)

> **As a** Software Release Engineer,  
> **I want** an automated host-driven pipeline to bake production-ready application releases into a clean base VHDX,  
> **So that** production images are consistent, pre-jitted, and guaranteed free of development debris.

### Acceptance Criteria
* **AC-04.1 (Clean Image Specification)**:
  * *Given* a newly built production base VHDX (`winserv2025-prod-adpa.vhdx`),
  * *When* inspected by the release audit script,
  * *Then* it must contain only the compiled application binary, required Windows runtime dependencies, and hardened security profiles—with all compilers, package managers (Scoop, uv, cargo), and source code repositories completely absent.
* **AC-04.2 (Automated Pre-Warming & Connection Pool Hygiene)**:
  * *Given* the automated image baking script,
  * *When* provisioning completes,
  * *Then* the script must start the ADPA/SIDPA Windows Service, execute a synthetic health-check request against `localhost:8080/health`, verify database connectivity, explicitly close all open database connection handles / clear connection pools to prevent persisting stale TCP sockets in RAM, and capture the `baseline-hot-ready` checkpoint while the application working set is hot in memory.

> [!TIP]
> **Future Horizon & Scaling Enhancement (US-04): Canary Baseline Verification & Auto-Rollback**  
> Extend the CI/CD baking pipeline to automatically route $5\%$ of live ingress traffic to the newly baked VHDX baseline for a 15-minute canary window, automatically reverting the pool pointer to the previous baseline checkpoint if error rates or latency thresholds deviate.

---

## User Story US-05: Elastic Standby Capacity & Concurrency Burst Scaling (DevOps & SRE)

> **As an** SRE and Capacity Planning Engineer,  
> **I want** the warm pool manager to automatically replenish and expand the ready-state paused instances as soon as demand indicators increase,  
> **So that** concurrent client requests and unexpected traffic surges always find a pre-warmed instance immediately available with zero queuing delays.

### Acceptance Criteria
* **AC-05.1 (Instant Buffer Replenishment)**:
  * *Given* a configured minimum standby buffer ($K_{\text{min}} = 1$),
  * *When* an incoming request leases the active standby VM (`hv:prod-adpa-01`),
  * *Then* the pool manager must immediately dispatch an asynchronous worker to unpause or promote the next standby VM (`hv:prod-adpa-02`) into `StandbyPaused` state in the background before the next request arrives.
* **AC-05.2 (Velocity-Triggered Dynamic Expansion)**:
  * *Given* incoming request velocity exceeds the configured threshold ($> 10\text{ req/s}$) or Ingress Buffer queue depth $> 0$,
  * *When* the autoscaling trigger evaluates,
  * *Then* the pool manager must dynamically scale the ready-state buffer up to $K_{\text{max}}$ (up to 5 instances in RAM), ensuring concurrent requests are served without cold-boot penalties.
* **AC-05.3 (Schedule & Requirement-Based Pre-Warming)**:
  * *Given* scheduled batch processing or calendar events (e.g., 08:00 AM shift start),
  * *When* an automated or manual pre-warm signal (`POST /pool/warm --target prod-adpa --count 4`) is received,
  * *Then* the pool manager must pre-warm the requested ready instances in `StandbyPaused` state prior to traffic arrival.
* **AC-05.4 (Graceful Scale-Down & Memory Reclamation)**:
  * *Given* traffic has normalized and surplus burst instances have remained idle past `reaping_cooldown_seconds` ($180\text{s}$),
  * *When* the reaper evaluates the fleet,
  * *Then* surplus instances beyond $K_{\text{min}}$ must be systematically restored to baseline, differencing disks discarded, and VMs suspended or deallocated to return host RAM to baseline.

> [!TIP]
> **Future Horizon & Scaling Enhancement (US-05): Cross-Host Predictive Pool Rebalancing**  
> Coordinate with multi-node hypervisor schedulers to dynamically distribute ready-state buffers across secondary physical Hyper-V nodes when local host memory pressure exceeds 80%.

