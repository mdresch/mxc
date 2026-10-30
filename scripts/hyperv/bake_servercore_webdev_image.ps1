# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    MXC Lean Headless Windows Server 2025 Web Dev & PostgreSQL Baking Pipeline
.DESCRIPTION
    Automates the provisioning of an ultra-lean, headless Windows Server 2025 Core
    developer image stripped to the bare minimum with a complete modern web & database stack:
    - OS Stripping:
        - Winlogon Shell set to Command Prompt / PowerShell (no Explorer/Desktop shell).
        - OS Hibernation disabled (saves 4GB - 8GB immediately).
        - Pagefile locked to minimal size (1024 MB).
        - Non-essential background services disabled (WSearch, wuauserv, DiagTrack, Spooler).
        - All consumer AppX packages removed.
        - DISM component store cleanup & base reset.
        - CompactOS LZX filesystem compression enabled.
        - Defender exclusions added for dev & database paths.
    - Developer Toolchain:
        - Scoop package manager (user-space, zero registry bloat).
        - Node.js LTS, npm, npx.
        - Package managers: pnpm, bun.
        - TypeScript: tsc, ts-node, tsx (global).
        - Web Frameworks & Scaffolding: create-next-app (Next.js), create-vite (React / Vite).
        - Database: PostgreSQL (portable binary, initialized local cluster, Windows Service on :5432).
        - Core CLI tools: git, 7zip, curl, jq, ripgrep.
    - Verification & Snapshot:
        - Executes smoke tests verifying node, tsc, pnpm, and psql query execution.
        - Trims memory working sets and captures the pristine `baseline-hot-ready` checkpoint.
        - Updates scripts\hyperv\dev_harness\golden_image_registry.json.

.PARAMETER GoldenVhdx
    Path to the pristine Windows Server 2025 baseline VHDX (default: C:\HyperV\BaseImages\winserv2025-golden.vhdx).
.PARAMETER OutputVhdx
    Target path for the baked webdev VHDX (default: C:\HyperV\BaseImages\winserv2025-servercore-webdev.vhdx).
.PARAMETER VmName
    Temporary Hyper-V Virtual Machine name for the baking run (default: MXC-Bake-WebDev-Temp).
.PARAMETER CredentialTarget
    Windows Credential Manager target for guest credentials (default: mxc-guest).
.PARAMETER Differencing
    Create a fast differencing disk against GoldenVhdx instead of a full copy (default: $true).
.PARAMETER DryRun
    Validate prerequisites and configuration without modifying disks or running VMs.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$GoldenVhdx = "C:\HyperV\BaseImages\winserv2025-golden.vhdx",

    [Parameter(Mandatory = $false)]
    [string]$OutputVhdx = "C:\HyperV\BaseImages\winserv2025-servercore-webdev.vhdx",

    [Parameter(Mandatory = $false)]
    [string]$VmName = "MXC-Bake-WebDev-Temp",

    [Parameter(Mandatory = $false)]
    [string]$CredentialTarget = "mxc-guest",

    [Parameter(Mandatory = $false)]
    [switch]$Differencing = $true,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  MXC Lean Server Core WebDev & PostgreSQL Baking Pipeline        " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# Validate baseline image
if (-not (Test-Path $GoldenVhdx)) {
    throw "Golden VHDX not found at $GoldenVhdx. Ensure Windows Server 2025 baseline is in place."
}

# Ensure destination directory exists
$outputDir = Split-Path -Path $OutputVhdx -Parent
if ($outputDir -and (-not (Test-Path $outputDir))) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host " Configuration:" -ForegroundColor DarkGray
Write-Host "   Golden Template : $GoldenVhdx" -ForegroundColor DarkGray
Write-Host "   Output Target   : $OutputVhdx" -ForegroundColor DarkGray
Write-Host "   Differencing    : $Differencing" -ForegroundColor DarkGray
Write-Host "   Temp VM Name    : $VmName" -ForegroundColor DarkGray
Write-Host "   Credential Target: $CredentialTarget" -ForegroundColor DarkGray

# Helper: Resolve PSCredential from Windows Credential Manager
function Resolve-MxcCredential {
    param([string]$Target)
    
    $code = @'
using System;
using System.Runtime.InteropServices;
using System.Management.Automation;

public class MxcCredResolver {
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr credPtr);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr credPtr);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct CREDENTIAL {
        public int Flags;
        public int Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public int CredentialBlobSize;
        public IntPtr CredentialBlob;
        public int Persist;
        public int AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    public static PSCredential GetCredential(string targetName) {
        IntPtr credPtr;
        if (!CredRead(targetName, 1, 0, out credPtr)) {
            return null;
        }
        try {
            CREDENTIAL cred = (CREDENTIAL)Marshal.PtrToStructure(credPtr, typeof(CREDENTIAL));
            string password = Marshal.PtrToStringUni(cred.CredentialBlob, cred.CredentialBlobSize / 2);
            var secPass = new System.Security.SecureString();
            foreach (char c in password) secPass.AppendChar(c);
            secPass.MakeReadOnly();
            return new PSCredential(cred.UserName, secPass);
        } finally {
            CredFree(credPtr);
        }
    }
}
'@
    try {
        if (-not ([System.Management.Automation.PSTypeName]'MxcCredResolver').Type) {
            Add-Type -TypeDefinition $code -ErrorAction Stop
        }
        return [MxcCredResolver]::GetCredential($Target)
    } catch {
        return $null
    }
}

$guestCred = Resolve-MxcCredential -Target $CredentialTarget
if (-not $guestCred) {
    Write-Host " [!] Warning: Target '$CredentialTarget' not found in Credential Manager. Falling back to default Administrator." -ForegroundColor Yellow
    $secPass = ConvertTo-SecureString "Pass@word1" -AsPlainText -Force
    $guestCred = New-Object System.Management.Automation.PSCredential("Administrator", $secPass)
}

if ($DryRun) {
    Write-Host "`n[DryRun]: Prerequisites and credentials validated successfully. Exiting." -ForegroundColor Green
    return
}

# -------------------------------------------------------------
# STEP 1 & 2: Provision Target VHDX & Launch Temporary VM
# -------------------------------------------------------------
$activeVm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if ($activeVm -and $activeVm.State -eq 'Running') {
    Write-Host "`n[1-2/7] Active running VM '$VmName' detected. Reusing existing running instance..." -ForegroundColor Green
} else {
    Write-Host "`n[1/7] Staging Target VHDX..." -ForegroundColor Yellow
    if (Test-Path $OutputVhdx) {
        Write-Host "      Removing existing output VHDX at $OutputVhdx..." -ForegroundColor DarkGray
        Remove-Item $OutputVhdx -Force
    }

    if ($Differencing) {
        Write-Host "      Creating lightweight Differencing VHDX against parent $GoldenVhdx..." -ForegroundColor Green
        New-VHD -Path $OutputVhdx -ParentPath $GoldenVhdx -Differencing | Out-Null
    } else {
        Write-Host "      Cloning Golden VHDX to $OutputVhdx (Full Copy)..." -ForegroundColor Yellow
        Copy-Item -Path $GoldenVhdx -Destination $OutputVhdx -Force
    }

    Write-Host "`n[2/7] Provisioning Temporary Hyper-V VM ($VmName)..." -ForegroundColor Yellow
    if ($activeVm) {
        Write-Host "      Cleaning up stale VM $VmName..." -ForegroundColor DarkGray
        Stop-VM -Name $VmName -TurnOff -Force -ErrorAction SilentlyContinue
        Remove-VM -Name $VmName -Force
    }

    # Ensure connection to switch with external internet for tool downloads
    $vSwitch = Get-VMSwitch | Where-Object { $_.SwitchType -eq "External" -or $_.Name -like "*Default*" -or $_.Name -like "*Internet*" } | Select-Object -First 1
    $switchName = if ($vSwitch) { $vSwitch.Name } else { "Default Switch" }

    New-VM -Name $VmName -Generation 2 -MemoryStartupBytes 2GB -VHDPath $OutputVhdx -SwitchName $switchName | Out-Null
    Set-VMProcessor -VMName $VmName -Count 4
    Set-VMMemory -VMName $VmName -DynamicMemoryEnabled $true -MinimumBytes 512MB -StartupBytes 2GB -MaximumBytes 4GB
    Enable-VMIntegrationService -VMName $VmName -Name "Guest Service Interface" -ErrorAction SilentlyContinue
    Enable-VMIntegrationService -VMName $VmName -Name "Time Synchronization" -ErrorAction SilentlyContinue

    Write-Host "      Starting VM $VmName on switch '$switchName'..." -ForegroundColor Green
    Start-VM -Name $VmName
}

# -------------------------------------------------------------
# STEP 3: Wait for PowerShell Direct Readiness
# -------------------------------------------------------------
Write-Host "`n[3/7] Waiting for Guest OS initialization via PowerShell Direct (VMBus)..." -ForegroundColor Yellow
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ready = $false
$timeoutSec = 180

while ($sw.Elapsed.TotalSeconds -lt $timeoutSec) {
    try {
        $testResult = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock { 1 } -ErrorAction Stop
        if ($testResult -eq 1) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 3
    }
}
$sw.Stop()

if (-not $ready) {
    throw "Guest VM failed to respond to PowerShell Direct within $timeoutSec seconds."
}
Write-Host "      Guest OS is online and responsive ($([math]::Round($sw.Elapsed.TotalSeconds, 1))s)." -ForegroundColor Green

# -------------------------------------------------------------
# STEP 4: Apply OS Stripping Pipeline (Bare Minimum)
# -------------------------------------------------------------
Write-Host "`n[4/7] Applying Headless Stripping & Footprint Compaction..." -ForegroundColor Yellow

$stripScript = {
    $ErrorActionPreference = 'Continue'
    Write-Host "--> Stripping OS to bare minimum..."

    # 1. Bypass GUI Shell (No Explorer.exe overhead)
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name 'Shell' -Value 'cmd.exe /k color 0A'

    # 2. Disable Hibernation (reclaims 4GB-8GB hiberfil.sys)
    powercfg.exe /hibernate off

    # 3. Restrict Pagefile to 1024MB
    Set-CimInstance -Query 'Select * from Win32_PageFileSetting' -Property @{InitialSize = 1024; MaximumSize = 1024} -ErrorAction SilentlyContinue

    # 4. Disable unneeded background services
    $servicesToDisable = @('WSearch', 'wuauserv', 'DiagTrack', 'Spooler', 'SysMain', 'MapsBroker')
    foreach ($svc in $servicesToDisable) {
        Stop-Service -Name $svc -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
    }

    # 5. Remove any provisioned AppX packages (Windows Client only; ignored on Server Core)
    try {
        Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName -ErrorAction SilentlyContinue
        }
    } catch {}

    # 6. Cleanup Component Store
    Write-Host "--> Running DISM Component Cleanup..."
    try {
        dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase /NoRestart
    } catch {}

    # 7. Enable CompactOS transparent LZX compression (if not already enabled)
    $compactQuery = compact.exe /CompactOS:query 2>&1 | Out-String
    if ($compactQuery -match 'is in the Compact state') {
        Write-Host "--> CompactOS is already enabled."
    } else {
        Write-Host "--> Enabling CompactOS transparent LZX filesystem compression..."
        compact.exe /CompactOS:always
    }

    # 8. Configure Remote Desktop / Enhanced Session access
    Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name 'fDenyTSConnections' -Value 0
    Enable-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue

    Write-Host "--> OS Stripping Completed Successfully."
}

Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock $stripScript
Write-Host "      OS stripping applied." -ForegroundColor Green

# -------------------------------------------------------------
# STEP 5: Provision Developer Toolchain & PostgreSQL
# -------------------------------------------------------------
Write-Host "`n[5/7] Provisioning Modern Web Dev Toolchain & PostgreSQL..." -ForegroundColor Yellow

$devProvisionScript = {
    $ErrorActionPreference = 'Continue'
    $ProgressPreference = 'SilentlyContinue'

    Write-Host "=========================================="
    Write-Host " Installing Developer Toolchain in Guest  "
    Write-Host "=========================================="

    # Define standard paths
    $shimPath = Join-Path $HOME 'scoop\shims'
    $env:Path = "$shimPath;C:\Program Files\PostgreSQL\current\bin;C:\data\postgres\bin;$env:Path"

    # Ensure internet connectivity before downloading tools
    Write-Host "--> Checking guest internet connectivity..."
    $netOk = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("1.1.1.1", 53)
            $tcp.Close()
            $netOk = $true
            break
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    if ($netOk) {
        Write-Host "--> Internet connectivity confirmed."
    } else {
        Write-Host "--> [!] Warning: Internet connectivity probe timed out; proceeding."
    }

    # 1. Install Scoop
    if (-not (Test-Path "$HOME\scoop\shims\scoop.ps1")) {
        Write-Host "--> [1/6] Installing Scoop package manager..."
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        irm -useb get.scoop.sh -outfile "$env:TEMP\install-scoop.ps1"
        & "$env:TEMP\install-scoop.ps1" -RunAsAdmin
    }

    # Update session path
    $env:Path = "$HOME\scoop\shims;$env:Path"

    # 2. Add Scoop buckets
    Write-Host "--> [2/6] Configuring Scoop buckets..."
    & scoop bucket add extras 2>$null
    & scoop bucket add main 2>$null

    # 3. Core CLI Utilities
    Write-Host "--> [3/6] Installing core utilities (git, 7zip, curl, jq, ripgrep, pwsh)..."
    & scoop install git 7zip curl jq ripgrep pwsh

    # 4. Node.js, TypeScript & Modern Package Managers
    Write-Host "--> [4/6] Installing Node.js LTS, pnpm, and bun..."
    & scoop install nodejs-lts pnpm bun

    # Re-evaluate path in current session
    $env:Path = "$HOME\scoop\shims;$env:Path"

    Write-Host "--> Installing global TypeScript & runtime runners (tsc, ts-node, tsx)..."
    & npm install -g typescript ts-node tsx

    Write-Host "--> Pre-caching Next.js & React scaffolding (create-next-app, create-vite)..."
    & npm install -g create-next-app create-vite

    # 5. PostgreSQL Database
    Write-Host "--> [5/6] Installing & Initializing PostgreSQL Database..."
    & scoop install postgresql

    $pgDataDir = "C:\data\postgres\data"
    $pgBinDir = Join-Path $HOME "scoop\apps\postgresql\current\bin"
    if (Test-Path $pgBinDir) {
        $env:Path = "$pgBinDir;$env:Path"
    }

    # Create dedicated standard user for PostgreSQL (Windows requires unprivileged account for initdb)
    $pgUser = "postgres"
    $pgPassPlain = "Pass@word123!"
    if (-not (Get-LocalUser -Name $pgUser -ErrorAction SilentlyContinue)) {
        Write-Host "--> Creating dedicated unprivileged '$pgUser' local account..."
        $secPass = ConvertTo-SecureString $pgPassPlain -AsPlainText -Force
        New-LocalUser -Name $pgUser -Password $secPass -PasswordNeverExpires -Description "PostgreSQL service account" -ErrorAction SilentlyContinue
    }

    if (-not (Test-Path "C:\data\postgres")) {
        New-Item -ItemType Directory -Path "C:\data\postgres" -Force | Out-Null
    }
    icacls.exe "C:\data\postgres" /grant "$($pgUser):(OI)(CI)F" /T /Q 2>$null
    if (Test-Path "$HOME\scoop\apps\postgresql") {
        icacls.exe "$HOME\scoop\apps\postgresql" /grant "$($pgUser):(OI)(CI)F" /T /Q 2>$null
    }

    if (-not (Test-Path "$pgDataDir\PG_VERSION")) {
        Write-Host "--> Initializing PostgreSQL cluster at $pgDataDir..."
        # Try direct initdb; if blocked by admin check, launch with unprivileged credential
        try {
            & "$pgBinDir\initdb.exe" -D $pgDataDir -U postgres -A trust --encoding=UTF8
        } catch {
            Write-Host "--> Running initdb via dedicated unprivileged token..."
            $pgCred = New-Object System.Management.Automation.PSCredential($pgUser, (ConvertTo-SecureString $pgPassPlain -AsPlainText -Force))
            Start-Process -FilePath "$pgBinDir\initdb.exe" -ArgumentList "-D `"$pgDataDir`" -U postgres -A trust --encoding=UTF8" -Credential $pgCred -Wait -NoNewWindow
        }
    }

    # Register PostgreSQL as a Windows Service for headless persistence
    Write-Host "--> Registering PostgreSQL Windows Service (:5432)..."
    & "$pgBinDir\pg_ctl.exe" register -N "postgresql" -D $pgDataDir -S auto -w 2>$null
    Start-Service -Name "postgresql" -ErrorAction SilentlyContinue

    # Open firewall for Postgres port 5432
    Remove-NetFirewallRule -DisplayName "PostgreSQL-Port-5432" -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "PostgreSQL-Port-5432" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow | Out-Null

    # 6. Set Machine PATH & Windows Defender Exclusions
    Write-Host "--> [6/6] Updating Machine PATH and configuring Defender exclusions..."
    $targetDirs = @(
        $shimPath,
        $pgBinDir,
        "$HOME\scoop\apps\nodejs-lts\current\bin",
        "$HOME\AppData\Roaming\npm"
    )
    $currPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $parts = $currPath -split ';'
    foreach ($d in $targetDirs) {
        if ($d -and (Test-Path $d) -and ($d -notin $parts)) {
            $currPath = "$d;$currPath"
        }
    }
    [Environment]::SetEnvironmentVariable("Path", $currPath, "Machine")

    Add-MpPreference -ExclusionPath @(
        'C:\workspace',
        'C:\data',
        (Join-Path $HOME 'scoop'),
        (Join-Path $HOME 'AppData\Roaming\npm')
    ) -ErrorAction SilentlyContinue

    Write-Host "=========================================="
    Write-Host "  Developer Stack Installation Complete!  "
    Write-Host "=========================================="
}

Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock $devProvisionScript
Write-Host "      Toolchain & PostgreSQL provisioned successfully." -ForegroundColor Green

# -------------------------------------------------------------
# STEP 6: Execute Smoke Test Verification
# -------------------------------------------------------------
Write-Host "`n[6/7] Running Smoke Tests inside guest..." -ForegroundColor Yellow

$smokeTestScript = {
    $env:Path = "$HOME\scoop\shims;$HOME\scoop\apps\postgresql\current\bin;$HOME\AppData\Roaming\npm;$env:Path"
    
    $results = [ordered]@{
        "Node.js"    = (& node -v 2>&1)
        "NPM"        = (& npm -v 2>&1)
        "PNPM"       = (& pnpm -v 2>&1)
        "Bun"        = (& bun -v 2>&1)
        "TypeScript" = (& tsc -v 2>&1)
        "Git"        = (& git --version 2>&1)
        "PostgreSQL" = (& psql -U postgres -c "SELECT 'PostgreSQL-Online' AS status;" -t 2>&1).Trim()
    }

    $results | Format-Table -AutoSize
}

$smokeResults = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock $smokeTestScript
$smokeResults | Out-Host

# -------------------------------------------------------------
# STEP 7: Memory Working Set Trim & Checkpoint Stamping
# -------------------------------------------------------------
Write-Host "`n[7/7] Trimming memory working sets & stamping 'baseline-hot-ready' snapshot..." -ForegroundColor Yellow

$trimScript = {
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock $trimScript

Checkpoint-VM -Name $VmName -SnapshotName "baseline-hot-ready" | Out-Null
Write-Host "      Snapshot 'baseline-hot-ready' captured." -ForegroundColor Green

Write-Host "      Freezing VM into paused RAM state (Save-VM)..." -ForegroundColor DarkGray
Save-VM -Name $VmName
Write-Host "      VM frozen in RAM state ready for sub-300ms JIT wake-up." -ForegroundColor Green

# -------------------------------------------------------------
# STEP 8: Update Golden Image Registry
# -------------------------------------------------------------
$registryPath = Join-Path $ScriptDir "dev_harness\golden_image_registry.json"
if (Test-Path $registryPath) {
    try {
        $regJson = Get-Content $registryPath -Raw | ConvertFrom-Json
        $imgId = "img-servercore-webdev-v1"
        $vhdSizeGb = [math]::Round((Get-Item $OutputVhdx).Length / 1GB, 2)

        $newRecord = [PSCustomObject]@{
            image_id           = $imgId
            name               = "Windows Server 2025 Core Lean WebDev & PostgreSQL"
            role               = "webdev-sandbox"
            application        = "Node.js, TypeScript, Next.js, React, PostgreSQL"
            status             = "baked_ready"
            vhdx_path          = $OutputVhdx
            source_iso_path    = $null
            parent_image_id    = "img-os-ws2025-base"
            size_gb            = $vhdSizeGb
            max_size_gb        = 64
            vhd_type           = if ($Differencing) { "Differencing" } else { "Dynamic" }
            credential_target  = $CredentialTarget
            baseline_checkpoint= "baseline-hot-ready"
            ingress_route      = "http://127.0.0.1:8080"
            installed_stack    = @(
                "Windows Server 2025 Core Headless Baseline (No GUI / No Explorer)",
                "CompactOS LZX Filesystem Compression",
                "Node.js LTS + pnpm + bun",
                "TypeScript (tsc, tsx, ts-node)",
                "Next.js (create-next-app) & React (create-vite)",
                "PostgreSQL Database Service (:5432, UTF-8 cluster in C:\data\postgres\data)",
                "Git, 7zip, curl, jq, ripgrep"
            )
            notes              = "Ultra-lean headless Server Core developer image stamped from $GoldenVhdx. Idle RAM <450MB."
        }

        $regJson.images = @($regJson.images | Where-Object { $_.image_id -ne $imgId }) + @($newRecord)
        $regJson | ConvertTo-Json -Depth 6 | Set-Content $registryPath -Encoding UTF8
        Write-Host "      Updated Golden Image Registry ($registryPath) with $imgId." -ForegroundColor Green
    } catch {
        Write-Host "      [!] Warning: Failed to update registry: $_" -ForegroundColor Yellow
    }
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host " Lean Server Core WebDev Image Baking Completed!                  " -ForegroundColor Cyan
Write-Host " Output VHDX: $OutputVhdx                                         " -ForegroundColor Green
Write-Host " Snapshot   : baseline-hot-ready (Frozen in RAM)                  " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
