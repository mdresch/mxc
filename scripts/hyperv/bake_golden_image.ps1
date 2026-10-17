# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Automated host-side provisioner to install essential developer toolchains
    and optimizations into the active MXC Hyper-V VM for baking into the golden base image.

.DESCRIPTION
    Runs entirely from the host machine via PowerShell Direct (mxc-exec):
    1. Temporarily connects the VM to the 'Default Switch' (mxc-net-enable).
    2. Installs Scoop and core CLI utilities (pwsh, git, ripgrep, fd, jq, 7zip).
    3. Installs language runtimes (Node.js LTS, pnpm, bun, Python uv, Rust MSVC, .NET SDK).
    4. Configures cargo-nextest, ruff, tsx, eslint, and prettier.
    5. Configures Windows Defender exclusions (C:\workspace, C:\Tools, Scoop, Cargo).
    6. Disconnects network back to strict airgap isolation (mxc-net-disable).

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
Write-Host "[1/7] Target Sandbox: $sbId" -ForegroundColor Green

# 2. Enable Network Connectivity for Downloads
Write-Host "`n[2/7] Hot-plugging network adapter (Default Switch)..." -ForegroundColor Yellow
mxc-net-enable -SandboxId $sbId
Start-Sleep -Seconds 5

# Verify Guest Internet Reachability
Write-Host "Verifying guest internet connectivity..." -ForegroundColor Gray
$pingTest = mxc-exec -SandboxId $sbId powershell -Command "Test-NetConnection 1.1.1.1 -Port 53 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded"
if ($pingTest -notmatch "True") {
    Write-Warning "Guest does not have active internet connection. Please verify host internet and Default Switch NAT."
} else {
    Write-Host "Guest internet confirmed (TCP 1.1.1.1:53 OK)." -ForegroundColor Green
}

# 3. Install Scoop Package Manager inside Guest
Write-Host "`n[3/7] Installing Scoop package manager inside guest..." -ForegroundColor Yellow
mxc-exec -SandboxId $sbId powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) { irm get.scoop.sh | iex }; scoop bucket add extras; scoop bucket add main"

# 4. Install Core CLI Utilities & Search Tools
Write-Host "`n[4/7] Installing core CLI utilities (pwsh, git, ripgrep, fd, jq, 7zip)..." -ForegroundColor Yellow
mxc-exec -SandboxId $sbId powershell -Command "scoop install git pwsh ripgrep fd jq 7zip"

# 5. Install Language Toolchains & Compilers
Write-Host "`n[5/7] Installing language toolchains (Node.js, pnpm, bun, uv, rustup, dotnet-sdk)..." -ForegroundColor Yellow
mxc-exec -SandboxId $sbId powershell -Command "scoop install nodejs-lts pnpm bun uv rustup dotnet-sdk"

Write-Host "Configuring Rust MSVC toolchain & cargo-nextest..." -ForegroundColor Gray
mxc-exec -SandboxId $sbId powershell -Command "rustup default stable-x86_64-pc-windows-msvc; cargo install cargo-nextest"

Write-Host "Installing global JS & Python tooling (tsx, eslint, prettier, ruff)..." -ForegroundColor Gray
mxc-exec -SandboxId $sbId powershell -Command "npm install -g tsx eslint prettier; uv tool install ruff"

# 6. Apply Windows Defender Build Exclusions
Write-Host "`n[6/7] Applying Windows Defender performance exclusions..." -ForegroundColor Yellow
mxc-exec -SandboxId $sbId powershell -Command "Add-MpPreference -ExclusionPath 'C:\workspace', 'C:\Tools', 'C:\Users\Administrator\.cargo', 'C:\Users\Administrator\.pnpm-store', 'C:\Users\Administrator\scoop' -ErrorAction SilentlyContinue; 'Defender exclusions configured.'"

# 7. Restore Airgap Isolation
if (-not $SkipAirgap) {
    Write-Host "`n[7/7] Restoring strict airgap isolation..." -ForegroundColor Yellow
    mxc-net-disable -SandboxId $sbId
    Write-Host "Sandbox network adapter disconnected." -ForegroundColor Green
} else {
    Write-Host "`n[7/7] Skipping airgap disconnect (-SkipAirgap specified)." -ForegroundColor Cyan
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "    Golden Image Provisioning Completed Successfully!     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "To freeze this state as your new golden base image:" -ForegroundColor Cyan
Write-Host "  1. Stop VM:          mxc-stop -SandboxId $sbId" -ForegroundColor White
Write-Host "  2. Clean Checkpoint: mxc-checkpoint -Name 'golden-tools-baked'" -ForegroundColor White
Write-Host "  3. Re-save/copy the child VHDX or merge as C:\HyperV\BaseImages\winserv2025-golden.vhdx" -ForegroundColor White

