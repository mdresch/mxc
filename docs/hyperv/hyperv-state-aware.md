# Hyper-V State-Aware Lifecycle

This document describes the **state-aware lifecycle** for the Hyper-V containment backend:
the multi-invocation `provision → start → exec → stop → deprovision` surface that keeps a
Hyper-V Virtual Machine **warm** across separate `wxc-exec` phase processes.

It complements:

- [`../state-aware-lifecycle/mxc-state-aware-sandbox-api.md`](../state-aware-lifecycle/mxc-state-aware-sandbox-api.md) — the cross-backend state-aware wire format, the Rust `StatefulSandboxBackend` trait, and the dispatcher contract.
- [`../schema.md`](../schema.md) — the configuration contract reference.

The Hyper-V backend is available under exact development schemas and requires the
`hyperv` Cargo feature (`--features hyperv`) as well as the runtime experimental opt-in
(`--experimental`).

---

## 1. Architecture: Why No Daemon

Unlike Windows Sandbox (which offers a single host-wide VM slot requiring a daemon to hold
it open) or WSLc (which uses an in-process SDK session handle with an idle-watchdog
lifecycle), **Hyper-V does not require a custom host daemon**.

A Hyper-V virtual machine is a first-class host OS object managed by Windows' always-on
**Virtual Machine Management Service (`vmms`)**. Any process running with appropriate
privileges (Elevated Administrator or membership in the local `Hyper-V Administrators`
security group) can query, start, inspect, or execute commands against the VM at any time
via the Hyper-V PowerShell cmdlets and PowerShell Direct.

```text
wxc-exec.exe (provision)   ──> New differencing disk + New-VM ──> records in %ProgramData%
wxc-exec.exe (start)       ──> Start-VM
wxc-exec.exe (exec)        ──> PowerShell Direct (Invoke-Command over VMBus)
wxc-exec.exe (stop)        ──> Save-VM (hibernates to disk for warm restart)
wxc-exec.exe (deprovision) ──> Stop-VM -TurnOff + Remove-VM + delete differencing disk
                                        │
                                        ▼
                         Hyper-V Host Service (vmms)
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
             VM: mxc-hv-a1b2c3d4                   VM: mxc-hv-e5f60718
             (Independent Sandbox)                 (Independent Sandbox)
```

Each phase call is a short-lived process. Intra-sandbox state is recorded in a durable
on-disk record, and a per-sandbox transition file lock (`TransitionLock`) serializes
concurrent phase calls targeted at the *same* sandbox.

---

## 2. Components

| Component | Location | Role |
|-----------|----------|------|
| `hyperv_common` | `src/backends/hyperv/common/` | Low-level PowerShell/Hyper-V cmdlet wrappers (`cmdlets.rs`), host availability probe (`probe.rs`), Windows Credential Manager client (`credential.rs`), and VM naming conventions (`vm_naming.rs`). |
| `hyperv_lifecycle` | `src/backends/hyperv/lifecycle/` | Implements `StatefulSandboxBackend` (`HypervRunner` in `state_aware.rs`), durable record storage (`control_plane.rs`), owner-only ACLs (`os.rs`), base image validation (`image.rs`), and backend-private operations (`backend_ops.rs`). |
| Engine arm | `src/core/mxc_engine/src/state_aware.rs` | Dispatches `ContainmentBackend::HyperV` to `HypervRunner` when compiled with the `hyperv` feature on Windows. |
| Dispatch registration | `src/core/wxc_common/src/state_aware_dispatch.rs` | Maps `hv:` sandbox ID prefix to `ContainmentBackend::HyperV` for post-provision phases. |
| Configuration contracts | `src/core/mxc_config_contract/src/dev/state_aware/provision/hyperv.rs` | Exact development schema contract for `hyperv.provision`. |
| CLI surface | `src/core/wxc/src/main.rs` | Accepts `--operation <provision|start|exec|stop|deprovision>` and dedicated `--hyperv-op` flags. |
| Credential registration | `scripts/hyperv/register-guest-credential.ps1` | Operator script to register guest credentials in Windows Credential Manager. |

---

## 3. Host and Guest Prerequisites

### 3.1 Host Prerequisites

1. **Hyper-V Role / Feature**:
   The Hyper-V Windows feature must be installed and active:
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   ```
   The `vmms` service must be running (`Get-Service vmms`).
2. **Execution Privileges**:
   Calling processes must run with elevation (Run as Administrator) or the user must be a
   member of the local **`Hyper-V Administrators`** security group.
3. **Storage Directory**:
   Per-sandbox metadata and differencing disks are maintained under:
   `%ProgramData%\mxc\hyperv\state-aware\<token>\`
   Directory permissions are secured to system and administrator/owner access.

### 3.2 Guest Image Prerequisites

MXC does not build or sysprep the base guest OS. Preparing the golden base image is an
operator prerequisite:

- **Format**: Must be a `.vhdx` or `.vhd` disk image containing a bootable Windows OS.
- **PowerShell Direct**: The guest OS must support PowerShell Direct (Windows 10, Windows 11,
  Windows Server 2016, or newer) with Hyper-V Integration Services enabled.
- **Local User Account**: A local administrator or user account must exist inside the
  guest image.
- **Credential Registration**: The guest account credentials must be stored in the Windows
  Credential Manager on the host using `scripts/hyperv/register-guest-credential.ps1` or `cmdkey`.

---

## 4. Sandbox IDs and Naming

- **Sandbox ID**: `provision` generates a random 8-character lowercase hexadecimal token
  and formats the ID as `hv:<token>` (e.g., `hv:3f8a9b21`).
- **VM Name**: Hyper-V virtual machines are named with the convention:
  `mxc-hv-<token>` (e.g., `mxc-hv-3f8a9b21`).
- **Differencing Disk**: Created per sandbox at:
  `%ProgramData%\mxc\hyperv\state-aware\<token>\disk.vhdx` (or `disk.vhd`).
  The parent base image remains completely read-only and unmodified.
- **Durable Record**: State metadata is saved at:
  `%ProgramData%\mxc\hyperv\state-aware\<token>\record.json`.

---

## 5. Phase → Hyper-V SDK / Cmdlet Mapping

| Phase | Action / Hyper-V Cmdlets | Details |
|---|---|---|
| `provision` | `New-VHD`, `New-VM`, `Add-VMHardDiskDrive`, `Set-VMProcessor` | Validates base image and host availability; creates child differencing disk; mints VM; sets generation, memory, and CPU count; writes durable record. On failure, partial resources are immediately deleted. |
| `start` | `Start-VM` | Starts the virtual machine. Transitions state from `Provisioned` or `Stopped` to `Started`. |
| `exec` | PowerShell Direct (`Invoke-Command -VMName ...`) | Executes `cmd.exe /c <command>` inside the guest via VMBus; relays stdout/stderr live to host process; retrieves exit code via guest marker file. |
| `stop` | `Save-VM` | Saves the VM state to disk (hibernates memory), persisting warm state for fast subsequent start. |
| `deprovision` | `Stop-VM -TurnOff -Force`, `Remove-VMSnapshot`, `Remove-VM`, file deletion | If running, forcibly powers off VM (discarding memory); removes any snapshots; removes the VM from Hyper-V; deletes differencing disk and sandbox directory. |

---

## 6. Per-Phase Config and Metadata Shapes

### 6.1 `provision`

**Config shape** (`hyperv.provision`):

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `baseImagePath` | `string` | **Yes** | — | Absolute path to the existing parent `.vhdx` or `.vhd` golden image. |
| `guestCredentialTarget` | `string` | No | `null` | Windows Credential Manager generic target name used to resolve credentials for PowerShell Direct. |
| `generation` | `integer` (`u8`) | No | `2` | Hyper-V VM generation (`1` or `2`). |
| `memoryStartupBytes` | `integer` (`u64`)| No | `2147483648` (2 GB)| Initial memory assigned to the VM at startup. |
| `cpuCount` | `integer` (`u32`)| No | `2` | Number of virtual processors. |

**Example provision configuration**:

```json
{
  "$schema": "https://mxc.azureedge.net/schemas/development/mxc.json",
  "version": "1.1.0-alpha",
  "containment": "hyperv",
  "hyperv": {
    "provision": {
      "baseImagePath": "D:\\HyperV\\BaseImages\\Win11-Golden.vhdx",
      "guestCredentialTarget": "mxc-guest",
      "generation": 2,
      "memoryStartupBytes": 4294967296,
      "cpuCount": 4
    }
  }
}
```
*(Note: When using `wxc-exec --operation provision`, the CLI injects `"phase"` automatically, so omit it from the JSON file).*

**Provision metadata**:
Returns `HypervProvisionMetadata` in the standard response envelope:
```json
{
  "result": {
    "sandboxId": "hv:3f8a9b21",
    "metadata": {
      "vmName": "mxc-hv-3f8a9b21"
    }
  }
}
```

### 6.2 `start`, `stop`, `deprovision`

These phases accept no backend-specific configuration options (`type StartConfig = ()`, etc.)
and return no phase-specific metadata (`metadata: null`).

These operations require a minimal JSON config declaring the contract version (e.g., `lifecycle.json` with `{"version": "1.1.0-alpha"}`):
```bash
wxc-exec --operation start --sandbox-id hv:3f8a9b21 --config lifecycle.json
wxc-exec --operation stop --sandbox-id hv:3f8a9b21 --config lifecycle.json
wxc-exec --operation deprovision --sandbox-id hv:3f8a9b21 --config lifecycle.json
```

### 6.3 `exec`

`exec` runs a command inside the warm guest VM using PowerShell Direct.

- **Process configuration**:
  - `commandLine`: The command to execute (run inside the guest via `cmd.exe /c <commandLine>`).
  - `workingDirectory`: If specified, sets the guest current working directory before running the command (`Set-Location`).
  - `script_timeout`: Parsed and accepted. Active host-side PID watchdog enforcement is scheduled for a future milestone.
- **Output semantics**:
  - Attached execution relays guest `stdout` and `stderr` directly to the calling host process's streams in real time.
  - The process exits with the guest command's actual exit code.
  - Piped execution (`ExecStdio::Piped`) is not supported and fails with `unsupported_piped_exec`.

---

## 7. Cross-Cutting Policy Honor Matrix

Hyper-V is a dedicated virtual machine containment boundary that relies on PowerShell
Direct over the Hyper-V VMBus rather than host networking or shared directories.

| Policy Category | Field | Status | Behavior / Rationale |
|---|---|---|---|
| **Filesystem** | `readwritePaths`<br>`readonlyPaths`<br>`deniedPaths` | **Rejected** | Rejected with `policy_validation`. Hyper-V has no host-to-guest mapped-folder primitive in this architecture; all disk operations occur inside the guest's differencing VHDX. |
| **Network** | `network`<br>`allowedHosts`<br>`blockedHosts` | **Rejected** | Rejected with `policy_validation` if specified. PowerShell Direct requires no IP network connectivity, virtual switches, or guest network adapters. |
| **UI** | `ui` | **Rejected** | Schema-level rejection; Hyper-V state-aware VMs run headlessly in background sessions without interactive host desktop exposure. |
| **Process** | `commandLine` | **Honored** | Relayed to guest `cmd.exe /c`. |
| **Process** | `workingDirectory` | **Honored** | Translated to `Set-Location` in the guest. |
| **Process** | `timeout` | **Accepted** | Parsed; host-side watchdog kill is tracked as a follow-up. |

---

## 8. PowerShell Direct and Credential Management

### 8.1 How PowerShell Direct Works

PowerShell Direct enables running PowerShell commands inside a guest VM without network
connectivity, virtual network switches, or firewall rules. Communication travels over
the Hyper-V **VMBus** directly between the host OS and the Hyper-V Integration Services
inside the guest VM.

### 8.2 Windows Credential Manager Integration

PowerShell Direct requires authentication with a guest account. To ensure sensitive
passwords are never passed over command-line arguments, JSON configuration files, or logs,
MXC integrates directly with the **Windows Credential Manager**:

1. **Operator Setup**:
   The operator stores the credential once under a generic target name using
   `scripts/hyperv/register-guest-credential.ps1`:
   ```powershell
   .\scripts\hyperv\register-guest-credential.ps1 -Target "mxc-guest" -Username "Administrator"
   ```
2. **Request Binding**:
   The provision configuration specifies only the target name:
   `"guestCredentialTarget": "mxc-guest"`.
3. **Host-Side Resolution**:
   During `exec`, MXC calls the Win32 `CredReadW` API to retrieve the password in memory.
   The password memory is held in a zeroize-on-drop buffer (`GuestCredential`).
4. **Secure Execution Relay**:
   The password is fed to a host PowerShell process via **standard input** (never command-line
   arguments), where it is securely converted into a `System.Management.Automation.PSCredential`
   object and passed to `Invoke-Command -VMName ... -Credential $cred`.
5. **Exit Code Propagation**:
   The guest script runs the command, captures `$LASTEXITCODE`, and writes it to a temporary
   marker file inside the guest (`$env:TEMP\mxc-hv-exit-<nanos>.txt`). A fast follow-up call
   reads the marker and deletes it, ensuring the exit code is accurately returned to MXC.

---

## 9. Backend-Private Operations: Pause, Checkpoint, Rollback

In addition to the standard 5-phase lifecycle, the Hyper-V backend provides dedicated
operations for virtual machine state control, checkpointing, and rollbacks. These sit
outside the shared 5-phase lifecycle and are invoked via `--hyperv-op`.

### 9.1 Supported Operations

| Operation | CLI Flag | Hyper-V Cmdlet | Description |
|---|---|---|---|
| **Pause** | `--hyperv-op pause` | `Suspend-VM` | Suspends the VM execution in RAM. Fast memory-resident pause (VM state remains in memory). VM must be `Started`. |
| **Resume** | `--hyperv-op resume` | `Resume-VM` | Resumes a suspended VM back to execution. VM must be `Started`. |
| **Force Poweroff**| `--hyperv-op force-poweroff` | `Stop-VM -TurnOff -Force` | Discards in-memory state and immediately powers off the VM. Transitions state to `Stopped`. |
| **Checkpoint** | `--hyperv-op checkpoint` | `Checkpoint-VM` | Creates a named checkpoint (snapshot) of current VM disk and memory state. Requires `--hyperv-checkpoint-name <name>`. |
| **Restore** | `--hyperv-op restore` | `Restore-VMSnapshot` | Reverts the VM disk and state to a named checkpoint. Requires `--hyperv-checkpoint-name <name>`. |
| **List Checkpoints**| `--hyperv-op list-checkpoints`| `Get-VMSnapshot` | Returns a JSON array of existing checkpoints with their creation timestamps. |

### 9.2 CLI Examples

```bash
# Pause a running sandbox
wxc-exec --hyperv-op pause --hyperv-sandbox-id hv:3f8a9b21

# Resume execution
wxc-exec --hyperv-op resume --hyperv-sandbox-id hv:3f8a9b21

# Take a checkpoint before running untrusted code
wxc-exec --hyperv-op checkpoint --hyperv-sandbox-id hv:3f8a9b21 --hyperv-checkpoint-name "clean-state"

# Inspect available checkpoints
wxc-exec --hyperv-op list-checkpoints --hyperv-sandbox-id hv:3f8a9b21

# Roll back to the checkpoint
wxc-exec --hyperv-op restore --hyperv-sandbox-id hv:3f8a9b21 --hyperv-checkpoint-name "clean-state"

# Forcibly power off
wxc-exec --hyperv-op force-poweroff --hyperv-sandbox-id hv:3f8a9b21
```

All `--hyperv-op` commands return standard JSON result envelopes:
```json
{"result": {}}
```
or for `list-checkpoints`:
```json
{
  "result": {
    "checkpoints": [
      {
        "name": "clean-state",
        "creationTime": "2026-10-04T08:30:00Z"
      }
    ]
  }
}
```

---

## 10. Idempotence and Lifecycle State Machine

The sandbox state is tracked in `record.json` as `Provisioned`, `Started`, or `Stopped`.

```text
                  ┌──────────────────────┐
                  │      provision       │
                  └──────────┬───────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Provisioned   │
                    └────────┬────────┘
                             │ start
                             ▼
 ┌───────────────┐  start   ┌─────────────────┐
 │               ├─────────>│                 │
 │    Stopped    │          │     Started     │ (exec, pause, resume)
 │               │<─────────┤                 │
 └───────┬───────┘   stop   └────────┬────────┘
         │ (or force-poweroff)       │
         │                           │
         └───────────┬───────────────┘
                     │ deprovision
                     ▼
             [Resources Deleted]
```

### Idempotence Rules

- **`start`**:
  - Valid from `Provisioned` or `Stopped`.
  - Calling `start` on an already `Started` sandbox returns error `already_started`.
- **`stop`**:
  - Always uses `Save-VM` (saving memory to disk for fast warm boot).
  - Calling `stop` on an already `Stopped` or `Provisioned` sandbox returns error `already_stopped`.
- **`exec`**:
  - Requires sandbox state to be `Started`.
  - Calling `exec` on `Provisioned` or `Stopped` returns error `not_started`.
- **`deprovision`**:
  - Valid from any state (`Provisioned`, `Started`, or `Stopped`).
  - If `Started`, the VM is forcibly powered off with `Stop-VM -TurnOff -Force` (skipping `Save-VM` since disks are about to be destroyed).
  - Removes all snapshots, removes the VM, deletes the differencing disk, and deletes the record directory.
  - Calling `deprovision` on an unprovisioned or already-deprovisioned sandbox returns `not_provisioned`.

---

## 11. Concurrency Story

1. **Inter-Sandbox Concurrency**:
   Because Hyper-V is an OS-level virtualization platform with a dedicated management service,
   multiple distinct sandboxes (`hv:11111111`, `hv:22222222`) execute completely in parallel.
   There is no single-VM bottleneck.
2. **Intra-Sandbox Serialization**:
   Concurrent calls against the *same* sandbox ID are serialized using an OS-level file lock:
   `%ProgramData%\mxc\hyperv\state-aware\<token>\transition.lock`.
   Locks are acquired with a 120-second timeout (`TRANSITION_LOCK_TIMEOUT`). If an operation
   is already modifying the VM, subsequent operations wait for the lock rather than conflicting.

---

## 12. Error Mapping Table

| Error Condition | Source | Wire Error Code |
|---|---|---|
| `vmms` service not found or not running | `hyperv_common::probe` | `backend_unavailable` |
| Compiled without `hyperv` feature or off-Windows | Engine / CLI | `backend_unavailable` |
| `--experimental` flag omitted | Dispatcher | `backend_unavailable` |
| Base image path empty, missing, or not `.vhdx`/`.vhd` | `image::validate_base_image_path` | `policy_validation` |
| Filesystem policy specified (`readwritePaths`, etc.) | `state_aware.rs` | `policy_validation` |
| Network policy specified (`network`, `allowedHosts`, etc.) | `state_aware.rs` | `policy_validation` |
| Guest credential target not found in Credential Manager | `credential::resolve_guest_credential` | `policy_validation` |
| Sandbox record not found / invalid token | `control_plane::read_sandbox_record` | `not_provisioned` |
| Calling `start` when sandbox is already `Started` | `state_aware.rs` | `already_started` |
| Calling `stop` when sandbox is `Stopped` or `Provisioned` | `state_aware.rs` | `already_stopped` |
| Calling `exec` or `pause` when sandbox is not `Started` | `state_aware.rs` | `not_started` |
| Checkpoint name missing, blank, or contains `/` or `\` | `backend_ops::validate_checkpoint_name` | `malformed_request` |
| Piped stdio requested (`ExecStdio::Piped`) | `state_aware.rs` | `backend_error` |
| Hyper-V PowerShell cmdlet execution failure | `hyperv_common::cmdlets` | `backend_error` |

---

## 13. Known Limitations and Future Work

- **Watchdog Timeout Enforcement**:
  `script_timeout` is accepted during `exec` requests, but active host-side watchdog killing
  is deferred. PowerShell Direct does not directly expose the guest child process PID to the
  host caller; plumbing a PID watchdog or guest-side timeout is scheduled as a follow-up.
- **Piped Stdio**:
  `ExecStdio::Piped` is currently rejected (`unsupported_piped_exec`). Interactive or streaming
  piped execution over named pipes into PowerShell Direct is not yet implemented.
- **Explicit UI Policy Rejection**:
  UI policy is currently rejected at the exact schema parsing stage (`deny_unknown_fields`);
  an explicit runtime policy validation check mirroring the filesystem/network checks will be
  added in a future release.

