# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Configure an MXC Hyper-V guest VM as a Cursor Cloud Agent "My Machines" worker.

.DESCRIPTION
    Run on the Hyper-V host (elevated PowerShell). Targets VM mxc-hv-<token> by default
    (e.g. mxc-hv-6b34439e for sandbox hv:6b34439e). Ensures the VM is running, enables
    outbound network, syncs the mxc repository into the guest, provisions the Cursor CLI,
    and registers a guest scheduled task for `agent worker start`.

.PARAMETER VmToken
    Eight-character sandbox token (without hv: prefix). Default 6b34439e.

.PARAMETER SkipSync
    Skip host-to-guest workspace sync (use when C:\workspace is already current).

.PARAMETER GuestApiKey
    Optional personal Cursor user API key. Stored in guest Credential Manager as
    cursor-mxc-agent-api-key when -StoreApiKeyInGuest is set (default).

.PARAMETER StoreApiKeyInGuest
    Persist GuestApiKey in the guest Credential Manager for the scheduled worker.

.EXAMPLE
    .\scripts\hyperv\configure_cursor_my_machines.ps1 -VmToken 6b34439e

.EXAMPLE
    $env:CURSOR_API_KEY = 'key_...'
    .\scripts\hyperv\configure_cursor_my_machines.ps1 -GuestApiKey $env:CURSOR_API_KEY
#>
[CmdletBinding()]
param(
    [string]$VmToken = '6b34439e',

    [switch]$SkipSync,

    [string]$GuestApiKey,

    [switch]$StoreApiKeyInGuest = $true,

    [string]$SwitchName = 'Default Switch'
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\mxc-hyperv.ps1"

$SandboxId = "hv:$VmToken"
$VmName = "mxc-hv-$VmToken"
$WorkerName = $VmName
$global:MXC_DEFAULT_SANDBOX = $SandboxId

Write-Host '==================================================================' -ForegroundColor Cyan
Write-Host "  Cursor My Machines — Hyper-V guest $VmName" -ForegroundColor Cyan
Write-Host '==================================================================' -ForegroundColor Cyan

$vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if (-not $vm) {
    throw "Hyper-V VM '$VmName' was not found on this host. Create or lease the sandbox first (mxc-pool-lease / wxc-exec)."
}

switch ($vm.State) {
    'Paused' {
        Write-Host "Resuming paused VM $VmName..." -ForegroundColor Yellow
        Resume-VM -Name $VmName
    }
    'Off' {
        Write-Host "Starting VM $VmName..." -ForegroundColor Yellow
        Start-VM -Name $VmName
    }
    'Running' { Write-Host "VM $VmName is already running." -ForegroundColor Green }
    default { throw "VM $VmName is in state '$($vm.State)'; cannot configure worker." }
}

Start-Sleep -Seconds 3
mxc-net-enable -SandboxId $SandboxId -SwitchName $SwitchName

if (-not $SkipSync) {
    mxc-sync -SandboxId $SandboxId
}

if ($GuestApiKey -and $StoreApiKeyInGuest) {
    Write-Host 'Storing Cursor API key in guest Credential Manager...' -ForegroundColor Cyan
    mxc-exec-ps -SandboxId $SandboxId "cmdkey /generic:cursor-mxc-agent-api-key /user:cursor /pass:$GuestApiKey"
}

$repoRemote = git -C $Script:RepoRoot config --get remote.origin.url 2>$null
if (-not $repoRemote) {
    $repoRemote = 'https://github.com/mdresch/mxc.git'
    Write-Host "Host git remote not found; using default $repoRemote" -ForegroundColor Yellow
}

$guestScriptPath = 'C:\workspace\scripts\hyperv\guest_configure_cursor_worker.ps1'
Write-Host 'Running guest Cursor worker provisioning...' -ForegroundColor Cyan
$guestParams = @(
    '-SandboxId', $SandboxId,
    'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', $guestScriptPath,
    '-WorkerName', $WorkerName,
    '-RepoRemoteUrl', $repoRemote
)
if ($GuestApiKey) {
    $guestParams += @('-ApiKey', $GuestApiKey)
}
& Invoke-MxcGuest @guestParams

Write-Host ''
Write-Host 'Next steps:' -ForegroundColor Green
Write-Host "  1. On the guest (mxc-gui / VMConnect), run: agent login   # skip if you passed -GuestApiKey"
Write-Host "  2. Confirm: agent worker debug"
Write-Host "  3. In Cursor → Agents → pick My Machines → $WorkerName"
Write-Host "  4. Or trigger: @Cursor worker=$WorkerName <task>   (repo mdresch/mxc)"
Write-Host ''
Write-Host "Default sandbox for this host session: $SandboxId" -ForegroundColor Cyan