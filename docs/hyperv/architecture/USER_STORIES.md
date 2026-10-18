# Pillar IV: User Stories & Acceptance Criteria
## Just-in-Time (JIT) Scale-to-Zero Production Hyper-V Sandboxes

---

## User Story US-01: Low-Latency On-Demand Processing (End User)

> **As an** Enterprise Automation Operator or Upstream REST Client,  
> **I want** to dispatch requests to the ADPA / SIDPA production endpoints at any time of day,  
> **So that** my data is processed immediately with sub-second response times without encountering gateway 502/504 errors.

### Acceptance Criteria
* **AC-01.1 (Cold Wake TTFB)**:
  * *Given* the target Hyper-V VM (`hv:prod-adpa-01`) is in dormant (`Paused`) state,
  * *When* the client transmits an HTTP POST payload to `https://gateway.internal/api/v1/adpa/process`,
  * *Then* the gateway must hold the connection, wake the VM via `mxc-pool-lease`, and return the initial HTTP response within **$\le 800\text{ms}$** total wall-clock time.
* **AC-01.2 (Subsequent Warm Traffic)**:
  * *Given* the VM is already active,
  * *When* subsequent HTTP requests arrive,
  * *Then* the gateway must forward requests immediately with an overhead of $\le 5\text{ms}$ plus application processing time.
* **AC-01.3 (Zero Connection Drops)**:
  * Under no circumstances shall an incoming client request receive an HTTP 502 Bad Gateway or HTTP 504 Gateway Timeout due to VM wake-up latency.

---

## User Story US-02: Cryptographic State Rollback & Zero Persistence (SecOps)

> **As a** Chief Information Security Officer (CISO) and Compliance Auditor,  
> **I want** every execution session of SIDPA to run inside a hardware-isolated environment that is mathematically wiped clean upon completion,  
> **So that** malicious payloads, memory scrapers, or sensitive customer records cannot persist across different user sessions.

### Acceptance Criteria
* **AC-02.1 (Ephemeral Differencing Disks)**:
  * *Given* an active processing session where files, temporary tables, or registry keys were modified in the guest,
  * *When* the session ends or the 300-second inactivity timer expires,
  * *Then* the Differencing Delta Disk (`.avhdx`) must be permanently deleted from host storage.
* **AC-02.2 (Baseline Verification)**:
  * The VM must be reverted to the cryptographic hash of the `baseline-hot-ready` checkpoint.
  * SHA-256 verification of the parent base VHDX (`winserv2025-prod-adpa.vhdx`) must remain identical before and after execution.
* **AC-02.3 (Network Airgap Default)**:
  * The VM virtual network adapter must be strictly disconnected (`mxc-net-disable`) or restricted exclusively to the internal gateway virtual switch, preventing any unauthorized outbound internet egress.

---

## User Story US-03: High-Density Scale-to-Zero Virtualization (DevOps & SRE)

> **As an** Infrastructure Platform Engineer,  
> **I want** dormant production instances to release active CPU and compress RAM usage,  
> **So that** our on-premise Windows Server / Hyper-V cluster can host 5× to 10× more application workloads than traditional always-on VMs.

### Acceptance Criteria
* **AC-03.1 (Zero CPU Utilization)**:
  * *Given* 10 registered production service VMs in the warm standby pool,
  * *When* no client requests are active,
  * *Then* total host CPU utilization for all 10 VMs must measure strictly **0.0%**.
* **AC-03.2 (Dynamic Memory Compression)**:
  * Hyper-V Dynamic Memory must allow the host hypervisor to compress idle memory allocation down to the configured minimum RAM baseline (e.g., 1024 MB).
* **AC-03.3 (Sub-300ms Hypervisor Wakeup)**:
  * The elapsed time between the Ingress Gateway sending the wake signal and Hyper-V completing `Resume-VM` must be $\le 300\text{ms}$.

---

## User Story US-04: Automated Release Image Baking (CI/CD Pipeline)

> **As a** Software Release Engineer,  
> **I want** an automated host-driven pipeline to bake production-ready application releases into a clean base VHDX,  
> **So that** production images are consistent, pre-jitted, and free of development debris.

### Acceptance Criteria
* **AC-04.1 (Clean Image Specification)**:
  * Production base VHDX must contain only the compiled application binary, required Windows runtime dependencies, and hardened security profiles.
  * Compilers, package managers (Scoop, uv, cargo), and source code repositories must be absent from the image.
* **AC-04.2 (Automated Pre-Warming)**:
  * The baking script must start the application service, execute a synthetic health-check request, verify database connectivity, and take the baseline checkpoint while the application is hot.
