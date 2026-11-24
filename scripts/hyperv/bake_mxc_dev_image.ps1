# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Bakes the MXC Developer Sandbox Image (`mxc-dev-ready` checkpoint on hv:a7df7452
    and standalone `F:\HyperV\BaseImages\winserv2025-mxc-dev.vhdx` symlinked into C:\HyperV\BaseImages).

.DESCRIPTION
    1. Synchronizes the latest host `mxc` repository (including ADD v2_3 & dev_harness) to C:\workspace in the guest.
    2. Installs developer & load-testing utilities (hey, python-docx) and compiles `wxc-exec --features hyperv` in the guest.
    3. Registers and starts the Prototype ADPA/SIDPA Guest Appliance (`mock_adpa_service.py` on TCP :8080) with firewall rules.
    4. Compacts guest memory working sets, captures the `mxc-dev-ready` live checkpoint, and exports the standalone
       `winserv2025-mxc-dev.vhdx` base image to `F:\HyperV\BaseImages\` with a symlink in `C:\HyperV\BaseImages\`.
#>

[CmdletBinding()]
param(
    [string]$SandboxId = "hv:a7df7452",
    [string]$ArchiveBaseDir = "F:\HyperV\BaseImages",
    [string]$PrimaryBaseDir = "C:\HyperV\BaseImages",
    [switch]$SkipVhdExport
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\mxc-hyperv.ps1"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   MXC Developer Image & JIT Test Harness Baker (v2_3)            " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# Ensure VM is running and connected to Default Switch for package/crate downloads
$vmName = "mxc-hv-" + ($SandboxId -replace '^hv:', '')
$vm = Get-VM -Name $vmName
if ($vm.State -eq 'Paused') {
    Write-Host "[0/6] Resuming paused VM $vmName..." -ForegroundColor Yellow
    Resume-VM -Name $vmName
} elseif ($vm.State -ne 'Running') {
    Write-Host "[0/6] Starting VM $vmName..." -ForegroundColor Yellow
    Start-VM -Name $vmName
}

Write-Host "`n[1/6] Enabling Default Switch network on $SandboxId..." -ForegroundColor Yellow
mxc-net-enable -SandboxId $SandboxId

Write-Host "`n[2/6] Synchronizing latest host MXC repository to guest C:\workspace..." -ForegroundColor Yellow
mxc-sync -SandboxId $SandboxId

Write-Host "`n[3/6] Provisioning load-testing tools, Python docx, Rust build & ADPA service on :8080..." -ForegroundColor Yellow
$guestSetupScript = @'
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$shimPath = Join-Path $HOME 'scoop\shims'
$cargoPath = Join-Path $HOME '.cargo\bin'
$localPath = Join-Path $HOME '.local\bin'
$pythonScripts = Join-Path $HOME 'scoop\apps\python\current\Scripts'
$env:Path = "$shimPath;$cargoPath;$localPath;$pythonScripts;C:\Program Files\dotnet;$env:Path"

Write-Host "-> Installing HTTP load-testing tool (hey) & python-docx..."
if (-not (Get-Command hey -ErrorAction SilentlyContinue)) {
    & scoop install hey 2>$null
}
& pip install --no-warn-script-location python-docx 2>$null

Write-Host "-> Configuring Inbound Firewall Rule for ADPA/SIDPA Service (:8080)..."
Remove-NetFirewallRule -DisplayName "MXC-ADPA-Port-8080" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "MXC-ADPA-Port-8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow | Out-Null

Write-Host "-> Starting Prototype ADPA/SIDPA Service on 0.0.0.0:8080..."
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -match 'mock_adpa_service\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$pythonExe = (Get-Command python -ErrorAction Stop).Source
$serviceScript = "C:\workspace\scripts\hyperv\dev_harness\mock_adpa_service.py"

# Register auto-start Scheduled Task so service survives reboots
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument $serviceScript -WorkingDirectory "C:\workspace"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "MXC-ADPA-MockService" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -RunLevel Highest -Force | Out-Null

# Start immediately in background
Start-Process -FilePath $pythonExe -ArgumentList $serviceScript -WorkingDirectory "C:\workspace" -WindowStyle Hidden
Start-Sleep -Seconds 2

$health = Invoke-RestMethod -Uri "http://127.0.0.1:8080/health" -Method Get -TimeoutSec 5
Write-Host "-> Guest ADPA/SIDPA Health Probe Verified: status=$($health.status), entropy=$($health.entropy_source), clock_synced=$($health.clock_synced)"

Write-Host "-> Pre-trimming guest working set prior to checkpoint..."
Invoke-RestMethod -Uri "http://127.0.0.1:8080/admin/pre-trim" -Method Post -Body "{}" -ContentType "application/json" | Out-Null
'@

mxc-exec-ps -SandboxId $SandboxId $guestSetupScript

Write-Host "`n[4/6] Creating 'mxc-dev-ready' live checkpoint on $SandboxId..." -ForegroundColor Yellow
$existingCp = Get-VMSnapshot -VMName $vmName -Name "mxc-dev-ready" -ErrorAction SilentlyContinue
if ($existingCp) {
    Remove-VMSnapshot -VMSnapshot $existingCp -ErrorAction SilentlyContinue
}
Checkpoint-MxcVM -Name "mxc-dev-ready" -SandboxId $SandboxId

if (-not $SkipVhdExport) {
    Write-Host "`n[5/6] Exporting standalone merged base VHDX to $ArchiveBaseDir\winserv2025-mxc-dev.vhdx..." -ForegroundColor Yellow
    if (-not (Test-Path $ArchiveBaseDir)) {
        New-Item -ItemType Directory -Path $ArchiveBaseDir -Force | Out-Null
    }
    $targetVhd = Join-Path $ArchiveBaseDir "winserv2025-mxc-dev.vhdx"
    $symlinkVhd = Join-Path $PrimaryBaseDir "winserv2025-mxc-dev.vhdx"

    $snapVhdPath = (Get-VMSnapshot -VMName $vmName -Name "mxc-dev-ready" | Get-VMHardDiskDrive | Select-Object -First 1).Path
    Write-Host "      -> Temporarily saving VM state to release Hyper-V disk locks..." -ForegroundColor Gray
    Save-VM -Name $vmName
    try {
        Write-Host "      -> Merging differencing chain from snapshot disk: $snapVhdPath" -ForegroundColor Gray
        if (Test-Path $targetVhd) {
            Remove-Item $targetVhd -Force
        }
        Convert-VHD -Path $snapVhdPath -DestinationPath $targetVhd -VHDType Dynamic
        try {
            if (Test-Path $symlinkVhd) {
                Remove-Item $symlinkVhd -Force
            }
            New-Item -ItemType SymbolicLink -Path $symlinkVhd -Target $targetVhd -Force -ErrorAction Stop | Out-Null
            Write-Host "      -> Symlink : $symlinkVhd -> $targetVhd" -ForegroundColor Green
        } catch {
            Write-Host "      -> Note: Skipping C:\ symlink (requires elevation); pointing pool directly to $targetVhd" -ForegroundColor Yellow
        }
        Write-Host "      -> Exported: $targetVhd" -ForegroundColor Green
    } finally {
        Write-Host "      -> Restoring VM $vmName back to Running state..." -ForegroundColor Gray
        Start-VM -Name $vmName
    }
    Write-Host "`n[6/6] Updating Warm Standby Pool configuration to use $targetVhd..." -ForegroundColor Yellow
    & $Script:ExecExe --hyperv-op pool-config --pool-target-size 1 --pool-base-image $targetVhd --pool-credential-target "mxc-guest" | Out-Null
} else {
    Write-Host "`n[5/6] Skipping VHDX export (-SkipVhdExport specified)." -ForegroundColor Cyan
}

Write-Host "`n==================================================================" -ForegroundColor Green
Write-Host "   MXC Developer Sandbox & Test Harness Ready!                    " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
