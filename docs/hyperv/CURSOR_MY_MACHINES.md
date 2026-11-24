# Cursor Cloud Agents on MXC Hyper-V (`My Machines`)

Run Cursor Cloud Agent tool calls on an MXC Hyper-V guest (hardware-isolated dev sandbox) instead of Cursor’s shared cloud VM.

## Naming

| Host VM name | Sandbox id | Default worker name |
|--------------|------------|---------------------|
| `mxc-hv-6b34439e` | `hv:6b34439e` | `mxc-hv-6b34439e` |

The worker **name** should match the VM name so triggers like `worker=mxc-hv-6b34439e` route correctly.

## One-time host setup

On the **Hyper-V host**, from an elevated PowerShell session in your `mxc` clone on `feat/hyperv-v2-rebased`:

```powershell
. .\scripts\hyperv\mxc-hyperv.ps1
.\scripts\hyperv\configure_cursor_my_machines.ps1 -VmToken 6b34439e
```

Optional: pass a [personal user API key](https://cursor.com/dashboard) so the worker starts without an interactive browser login on the guest:

```powershell
$env:CURSOR_API_KEY = 'key_...'   # Dashboard → API Keys (personal key, not service account)
.\scripts\hyperv\configure_cursor_my_machines.ps1 -VmToken 6b34439e -GuestApiKey $env:CURSOR_API_KEY
```

The script will:

1. Start or resume `mxc-hv-6b34439e`
2. Attach the **Default Switch** for outbound HTTPS (`agent worker` needs Cursor APIs)
3. Sync the repo to guest `C:\workspace` (`mxc-sync`) — note: sync **excludes `.git`** for speed; the configure script runs `git init` + `origin` in the guest so My Machines can route `mdresch/mxc`
4. Install the Cursor CLI in the guest and register scheduled task `MXC-Cursor-MyMachines-Worker`

Guest logs: `%ProgramData%\mxc\cursor-worker\worker.log`

## Guest login (if no API key)

Open the VM console:

```powershell
mxc-gui -SandboxId hv:6b34439e
```

Inside the guest:

```powershell
agent login
agent worker debug
```

Restart the scheduled task if needed:

```powershell
Start-ScheduledTask -TaskName MXC-Cursor-MyMachines-Worker
```

## Use from Cursor

1. [cursor.com/agents](https://cursor.com/agents) → **Run on** → **My Machines** → **mxc-hv-6b34439e**
2. Or in Slack/GitHub: `@Cursor worker=mxc-hv-6b34439e …` on repository `mdresch/mxc`

The guest checkout remote must be `github.com/mdresch/mxc` (set by `mxc-sync`).

## Networking

Workers use outbound HTTPS only. From the guest, verify reachability:

```powershell
foreach ($h in 'api2.cursor.sh','api2direct.cursor.sh','api3.cursor.sh','downloads.cursor.com') {
  try { (Invoke-WebRequest -Uri "https://$h/" -TimeoutSec 10 -UseBasicParsing).StatusCode }
  catch { "BLOCKED: $h" }
}
```

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Machine missing in picker | `agent worker debug` on guest; task running; same Cursor account as desktop |
| Wrong repo | `git -C C:\workspace remote -v`; re-run configure script or `git remote set-url origin …` |
| `not a git checkout` after sync | Expected once: re-run configure (bootstraps git). Pull latest `guest_configure_cursor_worker.ps1` |
| Worker stops after VM pause | Resume VM; `mxc-net-enable`; start scheduled task |
| `Git for Windows is required` on `worker start` | Guest has portable/scoop git only. Run `guest_install_git_for_windows.ps1` or `winget install Git.Git` in the guest |
| JIT pool recycled VM | Re-run `configure_cursor_my_machines.ps1` after `mxc-pool-release` on a fresh lease |

Official reference: [My Machines](https://cursor.com/docs/cloud-agent/self-hosted/my-machines).