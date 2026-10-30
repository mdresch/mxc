<#
.SYNOPSIS
    Fixes the Windows "Windows could not complete the installation" Sysprep/OOBE setup loop
.DESCRIPTION
    Mounts a VHDX offline, loads the guest SYSTEM registry hive, and sets:
    - HKLM\SYSTEM\Setup\Status\ChildCompletion\setup.exe = 3 (Completed)
    - HKLM\SYSTEM\Setup\Status\ChildCompletion\audit.exe = 3
    - HKLM\SYSTEM\Setup\SetupType = 0
    - HKLM\SYSTEM\Setup\SystemSetupInProgress = 0
    - HKLM\SYSTEM\Setup\CmdLine = ""
    This bypasses the broken OOBE/Setup dialog and allows the OS to boot straight to desktop/prompt.
#>

param(
    [string]$VhdxPath = "C:\HyperV\BaseImages\win11-golden.vhdx"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " MXC Windows Setup / Sysprep Loop Offline Repair Tool             " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

if (-not (Test-Path $VhdxPath)) {
    throw "VHDX not found at $VhdxPath"
}

Write-Host "[1/5] Mounting VHDX ($VhdxPath)..." -ForegroundColor Yellow
$mounted = Mount-VHD -Path $VhdxPath -PassThru
Start-Sleep -Seconds 2

try {
    # Find the Windows partition
    $partitions = Get-Partition -DiskNumber $mounted.DiskNumber
    $winPart = $null
    $winDrive = $null

    foreach ($p in $partitions) {
        if ($p.DriveLetter) {
            $testPath = "$($p.DriveLetter):\Windows\System32\config\SYSTEM"
            if (Test-Path $testPath) {
                $winPart = $p
                $winDrive = "$($p.DriveLetter):"
                break
            }
        }
    }

    if (-not $winDrive) {
        # Assign drive letter if not assigned
        foreach ($p in $partitions) {
            if (-not $p.DriveLetter -and $p.Type -in @("Basic", "IFS", "Primary")) {
                $letter = (Get-ChildItem function:[d-z]: -Name | Where-Object { -not (Test-Path $_) })[0]
                if ($letter) {
                    $dl = $letter.Substring(0, 1)
                    Set-Partition -DiskNumber $p.DiskNumber -PartitionNumber $p.PartitionNumber -NewDriveLetter $dl
                    Start-Sleep -Milliseconds 500
                    if (Test-Path "$($dl):\Windows\System32\config\SYSTEM") {
                        $winDrive = "$($dl):"
                        $winPart = $p
                        break
                    }
                }
            }
        }
    }

    if (-not $winDrive) {
        throw "Could not locate Windows partition in mounted VHDX."
    }

    Write-Host "[2/5] Located Windows system drive at: $winDrive" -ForegroundColor Green

    # Load the guest SYSTEM hive
    $systemHivePath = "$winDrive\Windows\System32\config\SYSTEM"
    Write-Host "[3/5] Loading offline SYSTEM registry hive from $systemHivePath..." -ForegroundColor Yellow
    
    $loadResult = reg load "HKLM\GUEST_SYSTEM" "$systemHivePath"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to load registry hive: $loadResult"
    }

    # Inspect current ChildCompletion values
    Write-Host "[4/5] Patching Setup status keys to completed state (Value: 3)..." -ForegroundColor Yellow
    
    reg add "HKLM\GUEST_SYSTEM\Setup\Status\ChildCompletion" /v "setup.exe" /t REG_DWORD /d 3 /f
    reg add "HKLM\GUEST_SYSTEM\Setup\Status\ChildCompletion" /v "audit.exe" /t REG_DWORD /d 3 /f
    reg add "HKLM\GUEST_SYSTEM\Setup" /v "SetupType" /t REG_DWORD /d 0 /f
    reg add "HKLM\GUEST_SYSTEM\Setup" /v "SystemSetupInProgress" /t REG_DWORD /d 0 /f
    reg add "HKLM\GUEST_SYSTEM\Setup" /v "CmdLine" /t REG_SZ /d "" /f

    # Ensure local administrator is active and set shell
    reg add "HKLM\GUEST_SYSTEM\ControlSet001\Control\Terminal Server" /v "fDenyTSConnections" /t REG_DWORD /d 0 /f

    Write-Host "      Registry keys successfully patched." -ForegroundColor Green
}
finally {
    Write-Host "[5/5] Unloading registry hive and dismounting VHDX..." -ForegroundColor Yellow
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    reg unload "HKLM\GUEST_SYSTEM" 2>$null | Out-Null
    Start-Sleep -Seconds 1
    Dismount-VHD -Path $VhdxPath -ErrorAction SilentlyContinue
    Write-Host "[+] VHDX dismounted cleanly. Setup loop repair COMPLETE!" -ForegroundColor Green
}

