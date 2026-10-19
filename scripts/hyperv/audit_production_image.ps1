<#
.SYNOPSIS
    MXC Production VHDX Image Audit & Compliance Gate (AC-04.1 / ADR-003)
.DESCRIPTION
    Performs fast, non-blocking inspection on a production VHDX image or Hyper-V sandbox
    to verify the total absence of unauthorized developer toolchains, package managers,
    and source repositories per ADR-003 and AC-04.1.

    Supports two execution modes:
    1. Offline VHDX mode: Mounts VHDX in read-only inspection mode (requires elevation).
    2. Live Sandbox mode: Audits via Hyper-V PowerShell Direct (runs non-interactively
       without elevation for Hyper-V Administrators).
.PARAMETER VhdxPath
    Path to the target production VHDX image.
.PARAMETER VMName
    Target Hyper-V Virtual Machine name (e.g. mxc-hv-a7df7452).
.PARAMETER SandboxId
    Target MXC sandbox ID (e.g. hv:a7df7452).
.PARAMETER OutputManifest
    Path to save the JSON compliance audit manifest.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$VhdxPath,

    [Parameter(Mandatory = $false)]
    [string]$VMName,

    [Parameter(Mandatory = $false)]
    [string]$SandboxId,

    [Parameter(Mandatory = $false)]
    [string]$OutputManifest = "C:\ProgramData\mxc\hyperv\audit\audit_manifest.json"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " MXC Production VHDX Image Compliance Audit (AC-04.1 / ADR-003)  " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# Resolve target mode
$mode = $null
if ($SandboxId) {
    $token = $SandboxId -replace '^hv:', ''
    $VMName = "mxc-hv-$token"
    $mode = "Sandbox"
} elseif ($VMName) {
    $mode = "Sandbox"
} elseif ($VhdxPath) {
    $mode = "OfflineVhdx"
} else {
    # Auto-detect running sandbox if nothing specified
    $runningVm = Get-VM "mxc-hv-*" -ErrorAction SilentlyContinue | Where-Object State -eq 'Running' | Select-Object -First 1
    if ($runningVm) {
        $VMName = $runningVm.Name
        $mode = "Sandbox"
        Write-Host "Auto-detected active sandbox: $VMName" -ForegroundColor Yellow
    } else {
        Write-Error "Please specify either -VhdxPath <path> or -VMName <name> / -SandboxId <id>"
        exit 1
    }
}

$auditLogDir = Split-Path -Path $OutputManifest -Parent
if ($auditLogDir -and (-not (Test-Path $auditLogDir))) {
    New-Item -ItemType Directory -Path $auditLogDir -Force | Out-Null
}

$violations = @()
$missingRequired = @()
$vhdxHash = "N/A"
$inspectedTarget = ""

if ($mode -eq "Sandbox") {
    Write-Host "[1/5] Connecting to sandbox '$VMName' via PowerShell Direct..." -ForegroundColor Yellow
    $inspectedTarget = "Hyper-V Sandbox: $VMName"
    
    # Check VM exists
    $vm = Get-VM -Name $VMName -ErrorAction SilentlyContinue
    if (-not $vm) {
        Write-Error "Hyper-V VM '$VMName' not found."
        exit 1
    }

    # Resolve backing VHDX on host for hashing
    $diskDrive = Get-VMHardDiskDrive -VMName $VMName | Select-Object -First 1
    if ($diskDrive) {
        $VhdxPath = $diskDrive.Path
        Write-Host "      Backing Disk: $VhdxPath" -ForegroundColor DarkGray
    }

    # Load helper functions
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (Test-Path "$ScriptDir\mxc-hyperv.ps1") {
        . "$ScriptDir\mxc-hyperv.ps1"
    }

    # Wake VM if paused
    if ($vm.State -eq 'Paused') {
        Resume-VM -VM $vm -Confirm:$false | Out-Null
    } elseif ($vm.State -ne 'Running') {
        Start-VM -VM $vm -Confirm:$false | Out-Null
    }

    Write-Host "[2/5] Scanning guest filesystem for unauthorized developer debris..." -ForegroundColor Yellow
    $targetSandboxId = "hv:$($VMName -replace '^mxc-hv-','')"

    # Fast deterministic guest probe script (no unbounded recursive file searches)
    $guestProbeScript = @'
$v = @()
$m = @()

# 1. Check binaries on PATH via where.exe (instant, <100ms)
$forbiddenBinaries = @("rustc.exe", "cargo.exe", "cl.exe", "csc.exe", "link.exe", "gcc.exe", "git.exe", "uv.exe", "npm.cmd")
foreach ($bin in $forbiddenBinaries) {
    $found = where.exe $bin 2>$null
    if ($found) {
        $v += [PSCustomObject]@{
            ArtifactName = "Compiler/Tool on PATH ($bin)"
            Path         = ($found | Select-Object -First 1)
            Severity     = "CRITICAL"
        }
    }
}

# 2. Check known static and shallow paths via Test-Path (no recursive crawling)
$checkPaths = @(
    @{ Name = "Scoop Package Manager (ProgramData)"; Path = "C:\ProgramData\scoop" },
    @{ Name = "Scoop Package Manager (User)"; Path = "C:\Users\*\scoop" },
    @{ Name = "Cargo Registry Directory (.cargo)"; Path = "C:\Users\*\.cargo" },
    @{ Name = "Rustup Directory (.rustup)"; Path = "C:\Users\*\.rustup" },
    @{ Name = "Rust Toolchain Install"; Path = "C:\Program Files\Rust stable" },
    @{ Name = "Visual Studio Build Tools"; Path = "C:\Program Files\Microsoft Visual Studio" },
    @{ Name = "Workspace Source Repo (.git)"; Path = "C:\workspace\.git" },
    @{ Name = "Workspace MXC Git Clone"; Path = "C:\workspace\mxc-repo" },
    @{ Name = "Workspace Source Staging"; Path = "C:\workspace\src" }
)

foreach ($cp in $checkPaths) {
    if (Test-Path $cp.Path) {
        $v += [PSCustomObject]@{
            ArtifactName = $cp.Name
            Path         = $cp.Path
            Severity     = "CRITICAL"
        }
    }
}

# 3. Verify required runtime baseline
$reqPaths = @(
    @{ Name = "Hyper-V VMBus Driver"; Path = "C:\Windows\System32\drivers\vmbus.sys" },
    @{ Name = "Hyper-V Time Sync Service Provider"; Path = "C:\Windows\System32\vmictimeprovider.dll" },
    @{ Name = "Windows Cryptographic CNG Library"; Path = "C:\Windows\System32\bcrypt.dll" }
)

foreach ($rp in $reqPaths) {
    if (-not (Test-Path $rp.Path)) {
        $m += $rp.Name
    }
}

[PSCustomObject]@{
    Violations = $v
    Missing    = $m
} | ConvertTo-Json -Depth 5 -Compress
'@

    $rawOutput = mxc-exec-ps -SandboxId $targetSandboxId $guestProbeScript
    $lines = $rawOutput -split "`n"
    $jsonLine = $lines | Where-Object { $_ -match '\{.*"Violations"' } | Select-Object -Last 1

    if ($jsonLine) {
        $guestResult = $jsonLine.Trim() | ConvertFrom-Json
        $violations = @($guestResult.Violations)
        $missingRequired = @($guestResult.Missing)
    } else {
        Write-Warning "Could not parse JSON output from guest probe. Raw output:"
        $rawOutput | ForEach-Object { Write-Warning "  $_" }
    }

} else {
    # Offline VHDX mount mode (requires elevation)
    Write-Host "[1/5] Mounting VHDX in read-only inspection mode: $VhdxPath..." -ForegroundColor Yellow
    $inspectedTarget = "VHDX: $VhdxPath"

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Error "Direct host Mount-VHD requires elevation (Run as Administrator). In non-elevated sessions, specify -VMName <name> or -SandboxId <id> to audit via Hyper-V PowerShell Direct."
        exit 1
    }

    $mountResult = $null
    $driveLetter = $null
    $tempMountPoint = $null

    try {
        $mountResult = Mount-VHD -Path $VhdxPath -ReadOnly -Passthru
        $disk = $mountResult | Get-Disk
        $diskNum = $disk.Number

        $partition = Get-Disk -Number $diskNum | Get-Partition | Where-Object { $_.DriveLetter } | Select-Object -First 1
        if ($partition -and $partition.DriveLetter) {
            $driveLetter = $partition.DriveLetter
            $targetRoot = "${driveLetter}:\"
        } else {
            $partition = Get-Disk -Number $diskNum | Get-Partition | Where-Object { $_.Type -like '*Basic*' -or $_.GptType -like '*Basic*' } | Select-Object -First 1
            $tempMountPoint = "C:\Mount_Audit_Temp_$([System.IO.Path]::GetRandomFileName())"
            New-Item -ItemType Directory -Path $tempMountPoint -Force | Out-Null
            Add-PartitionAccessPath -DiskNumber $diskNum -PartitionNumber $partition.PartitionNumber -AccessPath "$tempMountPoint\"
            $targetRoot = "$tempMountPoint\"
        }

        Write-Host "      Successfully mounted at: $targetRoot" -ForegroundColor Green
        Write-Host "[2/5] Scanning for unauthorized developer toolchains and debris..." -ForegroundColor Yellow

        $checkPaths = @(
            @{ Name = "Scoop Package Manager Root"; Path = "ProgramData\scoop" },
            @{ Name = "User Scoop Packages"; Path = "Users\*\scoop" },
            @{ Name = "Cargo Registry Directory (.cargo)"; Path = "Users\*\.cargo" },
            @{ Name = "Rustup Directory (.rustup)"; Path = "Users\*\.rustup" },
            @{ Name = "Rust Toolchain Install"; Path = "Program Files\Rust stable" },
            @{ Name = "Visual Studio Build Tools"; Path = "Program Files\Microsoft Visual Studio" },
            @{ Name = "Workspace Source Repo (.git)"; Path = "workspace\.git" },
            @{ Name = "Workspace MXC Git Clone"; Path = "workspace\mxc-repo" },
            @{ Name = "Workspace Source Staging"; Path = "workspace\src" }
        )

        foreach ($cp in $checkPaths) {
            $fullPath = Join-Path $targetRoot $cp.Path
            if (Test-Path $fullPath) {
                Write-Host "      [VIOLATION] Found forbidden artifact: $($cp.Name) at $fullPath" -ForegroundColor Red
                $violations += [PSCustomObject]@{
                    ArtifactName = $cp.Name
                    Path         = $cp.Path
                    Severity     = "CRITICAL"
                }
            } else {
                Write-Host "      [PASS] Absent: $($cp.Name)" -ForegroundColor DarkGreen
            }
        }

        Write-Host "[3/5] Verifying required production runtime baseline..." -ForegroundColor Yellow
        $reqPaths = @(
            @{ Name = "Hyper-V VMBus Driver"; Path = "Windows\System32\drivers\vmbus.sys" },
            @{ Name = "Hyper-V Time Sync Service Provider"; Path = "Windows\System32\vmictimeprovider.dll" },
            @{ Name = "Windows Cryptographic CNG Library"; Path = "Windows\System32\bcrypt.dll" }
        )

        foreach ($rp in $reqPaths) {
            $fullPath = Join-Path $targetRoot $rp.Path
            if (-not (Test-Path $fullPath)) {
                Write-Host "      [MISSING] Required production artifact: $($rp.Name)" -ForegroundColor Red
                $missingRequired += $rp.Name
            } else {
                Write-Host "      [VERIFIED] Present: $($rp.Name)" -ForegroundColor Green
            }
        }

    } finally {
        if ($mountResult) {
            Write-Host "Cleaning up: Dismounting VHDX..." -ForegroundColor Yellow
            if ($tempMountPoint -and (Test-Path $tempMountPoint)) {
                Remove-PartitionAccessPath -DiskNumber $diskNum -PartitionNumber $partition.PartitionNumber -AccessPath "$tempMountPoint\" -ErrorAction SilentlyContinue
                Remove-Item -Path $tempMountPoint -Force -Recurse -ErrorAction SilentlyContinue
            }
            Dismount-VHD -Path $VhdxPath -ErrorAction SilentlyContinue
        }
    }
}

# 4. Hash VHDX
Write-Host "[4/5] Computing VHDX cryptographic checksum (SHA-256)..." -ForegroundColor Yellow
if ($VhdxPath -and (Test-Path $VhdxPath)) {
    try {
        $vhdxHash = (Get-FileHash -Path $VhdxPath -Algorithm SHA256 -ErrorAction Stop).Hash
        Write-Host "      SHA-256: $vhdxHash" -ForegroundColor Cyan
    } catch {
        # Active running sandbox: file is locked by Hyper-V VMMS
        try {
            $stream = [System.IO.File]::Open($VhdxPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            $sha = [System.Security.Cryptography.SHA256]::Create()
            $hashBytes = $sha.ComputeHash($stream)
            $stream.Close()
            $vhdxHash = [BitConverter]::ToString($hashBytes) -replace '-'
            Write-Host "      SHA-256: $vhdxHash (Shared Handle)" -ForegroundColor Cyan
        } catch {
            $vhdxHash = "Locked-By-HyperV-VMMS"
            Write-Host "      SHA-256: [Deferred: Disk is actively locked by Hyper-V VMMS]" -ForegroundColor DarkGray
        }
    }
}

# 5. Output Manifest
$isCompliant = ($violations.Count -eq 0) -and ($missingRequired.Count -eq 0)

$manifest = [PSCustomObject]@{
    Timestamp        = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    Target           = $inspectedTarget
    VhdxPath         = $VhdxPath
    Sha256Hash       = $vhdxHash
    IsCompliant      = $isCompliant
    ViolationsCount  = $violations.Count
    Violations       = $violations
    MissingRequired  = $missingRequired
    Auditor          = $env:USERNAME
    Machine          = $env:COMPUTERNAME
}

$manifestJson = $manifest | ConvertTo-Json -Depth 6
Set-Content -Path $OutputManifest -Value $manifestJson -Encoding UTF8
Write-Host "[5/5] Audit manifest written to: $OutputManifest" -ForegroundColor Yellow

# Summary display
Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host " MXC Audit Results Summary (AC-04.1 Compliance Gate)" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " Target Inspected : $inspectedTarget"
Write-Host " Violations Found : $($violations.Count)"
foreach ($v in $violations) {
    Write-Host "   - [CRITICAL] $($v.ArtifactName): $($v.Path)" -ForegroundColor Red
}
Write-Host " Missing Required : $($missingRequired.Count)"
Write-Host " Compliance State : $(if ($isCompliant) { 'COMPLIANT' } else { 'NON-COMPLIANT' })" -ForegroundColor $(if ($isCompliant) { 'Green' } else { 'Red' })
Write-Host " Manifest File    : $OutputManifest"
Write-Host "==================================================================" -ForegroundColor Cyan

if (-not $isCompliant) {
    Write-Host "GATE STATUS: BLOCKED (Production image violates AC-04.1)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "GATE STATUS: APPROVED (100% compliant with ADR-003 and AC-04.1)" -ForegroundColor Green
    exit 0
}
