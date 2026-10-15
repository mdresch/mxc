# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

<#
.SYNOPSIS
    Convenience helpers and aliases for managing and executing commands in MXC Hyper-V sandboxes.

.DESCRIPTION
    Provides short, intuitive cmdlets and aliases for the most frequent MXC Hyper-V operations:
    - mxc-exec         : Execute a command inside the guest VM (PowerShell Direct)
    - mxc-status       : View state, memory, heartbeat, and IP of MXC sandboxes
    - mxc-pause        : Suspend / save VM state to disk (~6s hibernation)
    - mxc-resume       : Warm resume the saved VM (~4s wake)
    - mxc-checkpoint   : Create a named snapshot before risky operations
    - mxc-restore      : Roll back VM state to a named snapshot
    - mxc-checkpoints  : List all snapshots for the sandbox
    - mxc-stop         : Stop the VM
    - mxc-start        : Start the VM
    - mxc-deprovision  : Destroy sandbox and clean up differencing disk

.EXAMPLE
    . .\scripts\hyperv\mxc-hyperv.ps1
    mxc-status
    mxc-exec whoami
    mxc-exec powershell -Command "Get-Service"
    mxc-checkpoint "clean-baseline"
    mxc-pause
    mxc-resume
#>

$Script:RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Script:ExecExe = Join-Path $Script:RepoRoot "src\target\debug\wxc-exec.exe"
$Script:ExecJsonTemplate = Join-Path $Script:RepoRoot "exec.json"
$Script:StateAwareRoot = Join-Path $env:ProgramData "mxc\hyperv\state-aware"

function Get-MxcActiveSandboxId {
    param(
        [string]$ExplicitId
    )

    if ($ExplicitId) {
        if ($ExplicitId -notlike "hv:*") {
            return "hv:$ExplicitId"
        }
        return $ExplicitId
    }

    if ($global:MXC_DEFAULT_SANDBOX) {
        return $global:MXC_DEFAULT_SANDBOX
    }

    # Auto-detect: check running VMs with prefix mxc-hv-
    $runningVm = Get-VM "mxc-hv-*" -ErrorAction SilentlyContinue | Where-Object State -eq 'Running' | Select-Object -First 1
    if ($runningVm) {
        $token = $runningVm.Name -replace '^mxc-hv-', ''
        return "hv:$token"
    }

    # Fallback to any saved/off VM
    $anyVm = Get-VM "mxc-hv-*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($anyVm) {
        $token = $anyVm.Name -replace '^mxc-hv-', ''
        return "hv:$token"
    }

    # Fallback: scan state-aware directory
    if (Test-Path $Script:StateAwareRoot) {
        $records = Get-ChildItem -Path $Script:StateAwareRoot -Filter "record.json" -Recurse -ErrorAction SilentlyContinue
        if ($records.Count -gt 0) {
            $latest = $records | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $data = Get-Content $latest.FullName -Raw | ConvertFrom-Json
            return $data.sandbox_id
        }
    }

    throw "No active MXC Hyper-V sandbox found. Specify -SandboxId (e.g. hv:a7df7452)."
}

function Ensure-MxcExecBinary {
    if (-not (Test-Path $Script:ExecExe)) {
        Write-Host "wxc-exec.exe not found. Building with --features hyperv..." -ForegroundColor Yellow
        Push-Location $Script:RepoRoot
        try {
            cargo build --manifest-path src/Cargo.toml -p wxc --features hyperv
        } finally {
            Pop-Location
        }
    }
}

function Invoke-MxcGuest {
    Ensure-MxcExecBinary

    $rawArgs = @($args)
    $sandboxId = $null
    $cmdParts = [System.Collections.Generic.List[string]]::new()

    for ($i = 0; $i -lt $rawArgs.Count; $i++) {
        $arg = $rawArgs[$i]
        if ($arg -in @("-SandboxId", "--sandbox-id", "-Id") -and ($i + 1 -lt $rawArgs.Count)) {
            $sandboxId = $rawArgs[++$i]
        } else {
            $cmdParts.Add($arg)
        }
    }

    if ($cmdParts.Count -eq 0) {
        Write-Host "Usage: mxc-exec <command> [-SandboxId <id>]" -ForegroundColor Yellow
        Write-Host "Example: mxc-exec whoami"
        Write-Host "Example: mxc-exec powershell -Command `"Get-Process`""
        return
    }

    $id = Get-MxcActiveSandboxId -ExplicitId $sandboxId
    $cmdStr = $cmdParts -join ' '

    # Ensure dummy config file exists
    if (-not (Test-Path $Script:ExecJsonTemplate)) {
        @{
            version = "1.1.0-alpha"
            process = @{ commandLine = "hostname" }
        } | ConvertTo-Json -Depth 5 | Set-Content -Path $Script:ExecJsonTemplate -Encoding utf8
    }

    & $Script:ExecExe --experimental --operation exec --container-id $id $Script:ExecJsonTemplate -- $cmdStr
}
Set-Alias -Name mxc-exec -Value Invoke-MxcGuest -Scope Global

function Get-MxcStatus {
    param([string]$SandboxId)

    $vms = Get-VM "mxc-hv-*" -ErrorAction SilentlyContinue
    if (-not $vms) {
        Write-Host "No MXC Hyper-V VMs found on host." -ForegroundColor Yellow
        return
    }

    $results = foreach ($vm in $vms) {
        $token = $vm.Name -replace '^mxc-hv-', ''
        $sbId = "hv:$token"
        $recPath = Join-Path $Script:StateAwareRoot "$token\record.json"
        $baseImg = ""
        if (Test-Path $recPath) {
            $rec = Get-Content $recPath -Raw | ConvertFrom-Json
            $baseImg = [System.IO.Path]::GetFileName($rec.base_image_path)
        }

        $hb = (Get-VMIntegrationService -VMName $vm.Name -Name "Heartbeat" -ErrorAction SilentlyContinue).PrimaryStatusDescription
        $ip = ($vm.NetworkAdapters | Select-Object -ExpandProperty IPAddresses) -join ", "

        [PSCustomObject]@{
            SandboxId      = $sbId
            VMName         = $vm.Name
            State          = $vm.State
            MemoryMB       = [math]::Round($vm.MemoryAssigned / 1MB, 0)
            Heartbeat      = if ($hb) { $hb } else { "N/A" }
            IPAddresses    = if ($ip) { $ip } else { "PowerShell Direct" }
            BaseImage      = $baseImg
            Uptime         = $vm.Uptime
        }
    }

    $results | Format-Table -AutoSize
}
Set-Alias -Name mxc-status -Value Get-MxcStatus -Scope Global

function Suspend-MxcVM {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Suspending (saving state for) $id..." -ForegroundColor Cyan
    & $Script:ExecExe --experimental --hyperv-op pause --hyperv-sandbox-id $id
}
Set-Alias -Name mxc-pause -Value Suspend-MxcVM -Scope Global

function Resume-MxcVM {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Resuming $id..." -ForegroundColor Cyan
    & $Script:ExecExe --experimental --hyperv-op resume --hyperv-sandbox-id $id
}
Set-Alias -Name mxc-resume -Value Resume-MxcVM -Scope Global

function Checkpoint-MxcVM {
    param(
        [Parameter(Position = 0, Mandatory = $true)]
        [string]$Name,
        [string]$SandboxId
    )
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Creating checkpoint '$Name' for $id..." -ForegroundColor Cyan
    & $Script:ExecExe --experimental --hyperv-op checkpoint --hyperv-sandbox-id $id --hyperv-checkpoint-name $Name
}
Set-Alias -Name mxc-checkpoint -Value Checkpoint-MxcVM -Scope Global

function Restore-MxcVM {
    param(
        [Parameter(Position = 0, Mandatory = $true)]
        [string]$Name,
        [string]$SandboxId
    )
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Restoring checkpoint '$Name' for $id..." -ForegroundColor Yellow
    & $Script:ExecExe --experimental --hyperv-op restore --hyperv-sandbox-id $id --hyperv-checkpoint-name $Name
}
Set-Alias -Name mxc-restore -Value Restore-MxcVM -Scope Global

function Get-MxcCheckpoints {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    $raw = & $Script:ExecExe --experimental --hyperv-op list-checkpoints --hyperv-sandbox-id $id
    try {
        $json = $raw | ConvertFrom-Json
        $cps = $json.result.checkpoints
        if ($cps) {
            $cps | Select-Object name, creationTime | Format-Table -AutoSize
        } else {
            Write-Host "No checkpoints found for $id." -ForegroundColor Gray
        }
    } catch {
        Write-Host $raw
    }
}
Set-Alias -Name mxc-checkpoints -Value Get-MxcCheckpoints -Scope Global

function Start-MxcVM {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Starting $id..." -ForegroundColor Cyan
    & $Script:ExecExe --experimental --operation start --container-id $id
}
Set-Alias -Name mxc-start -Value Start-MxcVM -Scope Global

function Stop-MxcVM {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Stopping (saving) $id..." -ForegroundColor Cyan
    & $Script:ExecExe --experimental --operation stop --container-id $id
}
Set-Alias -Name mxc-stop -Value Stop-MxcVM -Scope Global

function Remove-MxcVM {
    param([string]$SandboxId)
    Ensure-MxcExecBinary
    $id = Get-MxcActiveSandboxId -ExplicitId $SandboxId
    Write-Host "Deprovisioning $id and cleaning up disk..." -ForegroundColor Red
    & $Script:ExecExe --experimental --operation deprovision --container-id $id
}
Set-Alias -Name mxc-deprovision -Value Remove-MxcVM -Scope Global

# --- Ultra-Short CLI Aliases ---
Set-Alias -Name mx   -Value mxc-exec -Scope Global
Set-Alias -Name mxs  -Value mxc-status -Scope Global
Set-Alias -Name mxp  -Value mxc-pause -Scope Global
Set-Alias -Name mxr  -Value mxc-resume -Scope Global
Set-Alias -Name mxc  -Value mxc-checkpoint -Scope Global
Set-Alias -Name mxcl -Value mxc-checkpoints -Scope Global

# Execute arbitrary PowerShell scriptblock inside the guest cleanly without quoting issues
function Invoke-MxcPowerShell {
    [CmdletBinding()]
    [Alias("mx-ps")]
    param(
        [Parameter(Position = 0, Mandatory = $true)]
        [string]$Script,

        [Parameter()]
        [string]$SandboxId
    )

    $bytes = [System.Text.Encoding]::Unicode.GetBytes($Script)
    $b64 = [Convert]::ToBase64String($bytes)
    mxc-exec powershell.exe -NoProfile -EncodedCommand $b64 -SandboxId $SandboxId
}

# --- Frequent Guest Commands ---

# Network & IP config inside the guest
function mxc-ip {
    mxc-exec ipconfig /all
}

# Running processes inside the guest
function mxc-ps {
    Invoke-MxcPowerShell "Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Id, ProcessName, CPU, WorkingSet"
}

# Check Hyper-V integration services inside the guest
function mxc-services {
    Invoke-MxcPowerShell "Get-Service vmic* | Select-Object Status, Name, DisplayName"
}

# Tail recent System/Application error events in the guest
function mxc-logs {
    Invoke-MxcPowerShell "Get-EventLog -LogName System -EntryType Error,Warning -Newest 15 | Format-Table TimeGenerated, Source, Message -AutoSize"
}

# Quick guest OS & uptime info
function mxc-info {
    Invoke-MxcPowerShell "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, LastBootUpTime, FreePhysicalMemory"
}

Write-Host "MXC Hyper-V helpers loaded. Available commands:" -ForegroundColor Green
Write-Host "  mxc-exec / mx <cmd>    Run command inside guest (e.g. mx whoami)"
Write-Host "  mxc-status / mxs       View active sandboxes & health"
Write-Host "  mxc-pause / mxp        Fast suspend (~5s)"
Write-Host "  mxc-resume / mxr       Fast resume (~4s)"
Write-Host "  mxc-checkpoint / mxc   Create named snapshot"
Write-Host "  mxc-checkpoints / mxcl List snapshots"
Write-Host "  mxc-ip                 Guest IP & network configuration"
Write-Host "  mxc-services           Guest Hyper-V integration services"
Write-Host "  mxc-ps                 Top CPU processes in guest"
Write-Host "  mxc-info               Guest OS and uptime information"
Write-Host "  mxc-logs               Recent system warnings and errors in guest"



