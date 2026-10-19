# MXC Hyper-V JIT Scale-to-Zero: End-User & Operator Guide

Welcome to the **MXC Hyper-V Just-in-Time (JIT) Scale-to-Zero Virtualization Engine** guide. This document provides clear, step-by-step instructions for developers, operators, and platform consumers to configure, run, and develop against hardware-isolated Hyper-V sandboxes with zero idle CPU overhead and sub-second wake times.

---

## Table of Contents

1. [Mental Model: How JIT Scale-to-Zero Works](#1-mental-model-how-jit-scale-to-zero-works)
2. [Prerequisites & Host Setup](#2-prerequisites--host-setup)
3. [Building the Control Plane (`wxc-exec`)](#3-building-the-control-plane-wxc-exec)
4. [Managing Multi-Pools with `wxc-exec`](#4-managing-multi-pools-with-wxc-exec)
5. [Running the JIT Ingress Reverse Proxy Gateway](#5-running-the-jit-ingress-reverse-proxy-gateway)
6. [Developing Inside Guest VM Sandboxes](#6-developing-inside-guest-vm-sandboxes)
7. [Running Verification & Benchmarks](#7-running-verification--benchmarks)
8. [Operator Runbook & Troubleshooting](#8-operator-runbook--troubleshooting)

---

## 1. Mental Model: How JIT Scale-to-Zero Works

Traditional virtual machines consume gigabytes of host memory and between 2%–8% continuous idle CPU even when waiting for requests. Cold-booting a VM takes 25 to 45 seconds.

MXC solves this dilemma through **Type-1 Hyper-V Scale-to-Zero**:

```text
               ┌────────────────────────────────────────────────────────┐
               │              Standby Pool (0.0% CPU)                   │
               │  VMs pre-warmed, working sets compacted, suspended     │
               │  in RAM or saved on NVMe (status: "ready")             │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                        Client HTTP Request (:8090)
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │           JIT Ingress Gateway (Hold Queue)             │
               │  1. Holds incoming HTTP request connection             │
               │  2. Calls `wxc-exec pool-lease` (<300ms wake)          │
               │  3. Probes guest :8080/health (PRNG & clock sync)      │
               │  4. Proxies payload to guest in <15ms warm TTFB        │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │               Active Session Execution                 │
               │  VM runs workload in complete hardware isolation       │
               │  In-flight request counter tracks active traffic       │
               └──────────────────────────┬─────────────────────────────┘
                                          │
                        Inactivity Timeout (300s) or /gateway/reap
                                          │
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │             Compaction & Snapshot Revert               │
               │  1. Pre-trims memory via Win32 EmptyWorkingSet         │
               │  2. Drops dirty delta disk (.avhdx)                    │
               │  3. Reverts to `pool-clean-baseline` snapshot          │
               │  4. Recycles VM back to Standby Pool at 0% CPU         │
               └────────────────────────────────────────────────────────┘
```

### Key Pillars:
- **0.0% Idle CPU**: Dormant VMs sit in `StandbyPaused` state in hypervisor RAM.
- **Fast Wake (`<300ms`)**: Hypervisor `Resume-VM` unpauses execution in milliseconds.
- **Cryptographic & Temporal Hygiene (`ADR-006`)**: On unpause, the guest re-seeds its PRNG from physical CPU hardware (`RDRAND`/`RDSEED` via CNG `BCryptGenRandom`), clears database connection pools, and verifies VMBus clock synchronization before serving traffic.
- **Stateless Isolation**: Changes are discarded upon release by rolling back to clean snapshot `pool-clean-baseline`.

---

## 2. Prerequisites & Host Setup

### System Requirements
- **Host Operating System**: Windows Server 2025 (Build 26100+) or Windows 11 Enterprise / Pro (Build 26100+).
- **CPU**: x86_64 processor with hardware virtualization (Intel VT-x or AMD-V) and SLAT.
- **RAM**: Minimum 16 GB physical RAM (32+ GB recommended).
- **Disk**: NVMe SSD with at least 50 GB free storage.

### Step 1: Enable Hyper-V
Run in an **Elevated PowerShell** window:
```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
```
*(Restart the host if prompted).*

### Step 2: Grant Permissions
Your user account must be an Administrator or a member of the local `Hyper-V Administrators` security group:
```powershell
net localgroup "Hyper-V Administrators" "$env:USERNAME" /add
```

### Step 3: Register Guest Credentials
Store guest administrative credentials in Windows Credential Manager:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\hyperv\register-guest-credential.ps1 `
    -Target "mxc-guest" `
    -Username "Administrator" `
    -Password "YourSecurePasswordHere"
```

### Step 4: Verify Base Image Location
Ensure a golden base VHDX exists on your storage tier:
- Hot Tier: `C:\HyperV\BaseImages\winserv2025-golden.vhdx`
- Capacity Tier: `F:\HyperV\BaseImages\winserv2025-golden.vhdx`

---

## 3. Building the Control Plane (`wxc-exec`)

The MXC Hyper-V control plane is compiled with the `hyperv` feature flag enabled.

```powershell
cd src
cargo build --features hyperv -p wxc --bin wxc-exec
```

Binary output:
`src\target\debug\wxc-exec.exe`

### Verify Host Probe Coverage
Run:
```powershell
.\src\target\debug\wxc-exec.exe --available-backends
```
Output must display `hyperv` as **supported**:
```json
{
  "backends": [
    {
      "name": "hyperv",
      "supported": true,
      "details": "Hyper-V Virtual Machine Management Service (vmms) detected"
    }
  ]
}
```

---

## 4. Managing Multi-Pools with `wxc-exec`

The pool manager enables managing isolated pools of pre-warmed VMs (`hv:<token>`) for different application workloads (e.g. `prod-adpa`, `prod-sidpa`, `default`).

### Configure a Named Pool
Configure target pool size (number of ready standby instances) and base image:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-configure `
    --pool prod-adpa `
    --target-size 1 `
    --max-ready-standby 5 `
    --base-image "C:\HyperV\BaseImages\winserv2025-golden.vhdx"
```

### Inspect Pool Status
List all configured pools, their members, and current states:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-list
```
Output:
```json
{
  "result": {
    "pools": [
      {
        "pool_id": "prod-adpa",
        "target_size": 1,
        "max_ready_standby": 5,
        "ready_count": 1,
        "leased_count": 0,
        "total_members": 1,
        "members": [
          {
            "token": "a7df7452",
            "sandbox_id": "hv:a7df7452",
            "vm_name": "mxc-hv-a7df7452",
            "status": "ready"
          }
        ]
      }
    ]
  }
}
```

### Pre-Warm Standby Instances (Replenish)
Provision and warm VMs until the pool reaches its target buffer:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-replenish --pool prod-adpa
```
*Note: When a VM is leased, the system automatically triggers background replenishment (`AC-05.1`) without blocking the caller.*

### Manual Lease & Release
Check out a sandbox manually:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-lease --pool prod-adpa --pool-lease-holder "operator"
```
Returns: `{"result": {"sandbox_id": "hv:a7df7452", "vm_name": "mxc-hv-a7df7452"}}`

Release the sandbox back to the clean snapshot baseline:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-release --pool prod-adpa --hyperv-sandbox-id hv:a7df7452
```

### Tear Down a Pool
Forcibly power off and delete all VMs and differencing disks in a pool:
```powershell
.\src\target\debug\wxc-exec.exe --experimental --hyperv-op pool-drain --pool prod-adpa
```

---

## 5. Running the JIT Ingress Reverse Proxy Gateway

The JIT Ingress Gateway acts as an intelligent HTTP reverse proxy. It intercepts client requests, unpauses dormant VMs on demand, validates health, and routes payloads.

### Starting the Gateway
Run the gateway on port `8090` pointing to your pool:
```powershell
python scripts\hyperv\dev_harness\jit_ingress_gateway.py --port 8090 --pool prod-adpa --idle-timeout 300
```

CLI Options:
- `--port`: Listen port (default: `8090`).
- `--host`: Host binding (default: `0.0.0.0`).
- `--pool`: Default standby pool to lease from (default: `prod-adpa`).
- `--idle-timeout`: Inactivity seconds before automatically reaping leased VMs (default: `300`).
- `--guest-port`: Guest HTTP service port (default: `8080`).

### Sending HTTP Requests
Send traffic to the gateway:
```powershell
Invoke-RestMethod -Uri "http://localhost:8090/api/v1/adpa/process" `
    -Method Post `
    -Body '{"job": "reconciliation", "records": 100}' `
    -ContentType "application/json"
```

### Reading Telemetry Response Headers
Each proxied HTTP response includes real-time MXC performance headers:
- `X-MXC-Cold-Wake`: `true` if the request triggered a hypervisor wake; `false` if already warm.
- `X-MXC-Wake-Ms`: Milliseconds taken by the hypervisor to unpause the VM.
- `X-MXC-Health-Probe-Ms`: Milliseconds taken to probe `:8080/health` (PRNG + clock sync).
- `X-MXC-Total-TTFB-Ms`: End-to-end Time to First Byte.
- `X-MXC-Sandbox-Id`: The sandbox handling the request (e.g. `hv:a7df7452`).
- `X-MXC-Pool-Id`: The origin pool (e.g. `prod-adpa`).

### Checking Gateway Status
Inspect active leases and in-flight request counters at any time:
```powershell
curl http://localhost:8090/gateway/status
```
Example Response:
```json
{
  "gateway": "MXC JIT Scale-to-Zero Ingress Reverse Proxy",
  "listen_port": 8090,
  "active_sandbox_id": "hv:a7df7452",
  "active_vm_name": "mxc-hv-a7df7452",
  "active_guest_ip": "172.24.166.125",
  "active_pool": "prod-adpa",
  "active_open_requests": 0,
  "idle_elapsed_seconds": 14.2,
  "idle_timeout_seconds": 300.0,
  "total_leases": 1,
  "total_requests_proxied": 6
}
```

### Enforcing Execution Timeouts (`AC-02.1`)
Clients can supply the `X-Max-Timeout-Ms` header. If processing exceeds this duration, the gateway forcefully severs the socket and returns **HTTP 504 Gateway Timeout**, protecting the instance from becoming hung:
```powershell
curl -X POST "http://localhost:8090/api/v1/adpa/process" \
     -H "X-Max-Timeout-Ms: 500" \
     -H "Content-Type: application/json" \
     -d '{"delay_ms": 2000}'
```

### Manual Compaction & Reaping
Forcibly trigger working set compaction and baseline rollback:
```powershell
curl -X POST http://localhost:8090/gateway/reap
```
- If requests are currently in flight, the gateway rejects with **HTTP 409 Conflict**.
- If idle, it executes guest `POST /admin/pre-trim`, reverts `.avhdx` delta, and returns **HTTP 200 OK**.

---

## 6. Developing Inside Guest VM Sandboxes

You can run self-hosting Rust, .NET, or Python development directly inside an isolated Hyper-V sandbox.

### Step 1: Check Out or Resume Developer Sandbox
The active developer sandbox is `mxc-hv-0b1e0d7e` (6 vCPUs, 4–6 GB RAM).
Verify its state:
```powershell
Get-VM -Name "mxc-hv-0b1e0d7e"
```
If `Paused`, resume it:
```powershell
Resume-VM -Name "mxc-hv-0b1e0d7e"
```

### Step 2: Connect via PowerShell Direct
PowerShell Direct connects directly over the hypervisor VMBus with no network setup required:
```powershell
$cred = Get-Credential -UserName "Administrator" -Message "Enter guest password"
Enter-PSSession -VMName "mxc-hv-0b1e0d7e" -Credential $cred
```

### Step 3: Work with the Codebase
Inside the guest session:
```powershell
# Navigate to the workspace
cd C:\workspace\mxc-repo\src

# Run tests
cargo test --features hyperv -p mxc-sdk --lib pool::tests

# Build executables
cargo build --features hyperv -p wxc --bin wxc-exec
```

### Step 4: Safeguard Clean Development State
Whenever your guest toolchain is updated or clean, stamp a checkpoint:
```powershell
Checkpoint-VM -Name "mxc-hv-0b1e0d7e" -SnapshotName "mxc-dev-warmed"
```

---

## 7. Running Verification & Benchmarks

To formally verify all architectural acceptance criteria on your host, execute the automated benchmark suite:

```powershell
python scripts\hyperv\dev_harness\benchmark_jit_wake.py
```

### Verification Criteria Checklist

| Acceptance Criterion | Verification Method | Target SLA |
| :--- | :--- | :--- |
| **AC-03.2 (Pre-Trim & Pause)** | Compaction via `psapi.dll EmptyWorkingSet` & `Suspend-VM` | 0.0% CPU, Compacted Host Footprint |
| **AC-01.1 (Cold Wake SLA)** | Gateway buffers request, calls `pool-lease`, resumes VM | Total TTFB $\le 800\text{ms}$ (Resume $\le 300\text{ms}$) |
| **AC-02.4 (Entropy & Clock Sync)** | Windows CNG `BCryptGenRandom` + VMBus clock skew check | Unique hardware nonce, Clock drift $<50\text{ms}$ |
| **AC-01.2 (Warm TTFB)** | 5 consecutive keep-alive HTTP requests over TCP | Average latency $\le 15\text{–}25\text{ms}$ |
| **AC-02.1 (In-Flight Guard)** | Mid-flight reap returns HTTP 409; hung request returns HTTP 504 | Zero request drop, zero state accumulation |

---

## 8. Operator Runbook & Troubleshooting

### Q1: "The Hyper-V backend is not available in this build"
- **Cause**: `wxc-exec` was compiled without the `--features hyperv` flag.
- **Fix**: Rebuild with `cargo build --features hyperv -p wxc --bin wxc-exec`.

### Q2: Host RAM Exhaustion / Freeing Memory
- **Cause**: Standby VMs in `Paused` state hold their assigned memory in host physical RAM.
- **Fix**: If host memory falls below 4 GB, save dormant pool members to NVMe disk:
  ```powershell
  Get-VM | Where-Object { $_.Name -like "mxc-hv-*" -and $_.State -eq "Paused" } | Save-VM
  ```
  *The control plane seamlessly unpauses both `Paused` and `Saved` VMs.*

### Q3: VM Fails to Acquire an IP Address
- **Cause**: Network adapter not connected to a Hyper-V switch.
- **Fix**: Connect adapter to `Default Switch`:
  ```powershell
  Connect-VMNetworkAdapter -VMName "mxc-hv-a7df7452" -SwitchName "Default Switch"
  ```

### Q4: Resetting Stale File Locks
- **Cause**: A killed process left an orphan `.lock` file in the ProgramData directory.
- **Fix**: Remove stale locks from the locks directory:
  ```powershell
  Remove-Item "C:\ProgramData\mxc\hyperv\locks\*.lock" -Force -ErrorAction SilentlyContinue
  ```

### Q5: Rolling Back to Clean Image Baseline
- **Cause**: A sandbox accumulated unwanted changes or corrupt dependencies.
- **Fix**: Restore the clean snapshot baseline:
  ```powershell
  Restore-VMSnapshot -VMName "mxc-hv-a7df7452" -Name "pool-clean-baseline" -Confirm:$false
  ```
