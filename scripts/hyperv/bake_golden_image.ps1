# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Automated host-side provisioner to install essential developer toolchains
    and optimizations into the active MXC Hyper-V VM for baking into the golden base image.

.DESCRIPTION
    Runs entirely from the host machine via PowerShell Direct:
    1. Temporarily connects the VM to the 'Default Switch' (mxc-net-enable).
    2. Verifies guest internet connectivity.
    3. Executes the full guest-side provisioner (guest_bake_tools.ps1) via Base64 EncodedCommand.
    4. Disconnects network back to strict airgap isolation (mxc-net-disable).

.EXAMPLE
    .\scripts\hyperv\bake_golden_image.ps1
#>

[CmdletBinding()]
param(
    [string]$SandboxId,
    [switch]$SkipAirgap
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\mxc-hyperv.ps1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    MXC Golden Image Toolchain Provisioner (Host-Driven)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Resolve Target Sandbox
$sbId = if ($SandboxId) { $SandboxId } else { Get-MxcActiveSandboxId }
Write-Host "[1/4] Target Sandbox: $sbId" -ForegroundColor Green

# 2. Enable Network Connectivity for Downloads
Write-Host "`n[2/4] Hot-plugging network adapter (Default Switch)..." -ForegroundColor Yellow
mxc-net-enable -SandboxId $sbId

# Verify Guest Internet Reachability with retry loop
Write-Host "Verifying guest internet connectivity..." -ForegroundColor Gray
$connected = $false
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 3
    $probe = mxc-exec-ps -SandboxId $sbId 'Test-NetConnection 1.1.1.1 -Port 53 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded'
    if ($probe -match "True") {
        $connected = $true
        break
    }
    Write-Host "  Waiting for network DHCP lease ($($i + 1)/10)..." -ForegroundColor Gray
}

if (-not $connected) {
    Write-Warning "Guest does not have active internet connection. Please verify host internet and Default Switch NAT."
} else {
    Write-Host "Guest internet confirmed (TCP 1.1.1.1:53 OK)." -ForegroundColor Green
}

# 3. Execute Guest Provisioning Script via EncodedCommand
Write-Host "`n[3/4] Executing guest-side toolchain provisioning..." -ForegroundColor Yellow
$guestScriptPath = Join-Path $ScriptDir "guest_bake_tools.ps1"
if (-not (Test-Path $guestScriptPath)) {
    throw "Guest provisioning script not found at $guestScriptPath"
}
$guestScriptText = Get-Content -Path $guestScriptPath -Raw
mxc-exec-ps -SandboxId $sbId $guestScriptText

# 4. Restore Airgap Isolation
if (-not $SkipAirgap) {
    Write-Host "`n[4/4] Restoring strict airgap isolation..." -ForegroundColor Yellow
    mxc-net-disable -SandboxId $sbId
    Write-Host "Sandbox network adapter disconnected." -ForegroundColor Green
} else {
    Write-Host "`n[4/4] Skipping airgap disconnect (-SkipAirgap specified)." -ForegroundColor Cyan
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "    Golden Image Provisioning Completed Successfully!     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "To freeze this state as your new golden base image:" -ForegroundColor Cyan
Write-Host "  1. Stop VM:          mxc-stop -SandboxId $sbId" -ForegroundColor White
Write-Host "  2. Clean Checkpoint: mxc-checkpoint -Name 'golden-tools-baked'" -ForegroundColor White
Write-Host "  3. Re-save/copy the child VHDX or merge as C:\HyperV\BaseImages\winserv2025-golden.vhdx" -ForegroundColor White
