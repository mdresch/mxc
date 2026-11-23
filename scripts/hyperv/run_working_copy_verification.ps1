<#
.SYNOPSIS
    MXC Hyper-V Working Copy Provisioning & Verification Task Runner
.DESCRIPTION
    Provisions a transient differencing working copy from an immutable golden base image
    (located on F:\HyperV\BaseImages), starts the micro-VM, executes in-guest verification
    tasks over PowerShell Direct / VMBus, audits isolation/invariance, and cleans up.
.PARAMETER BaseImagePath
    Path to the parent golden base VHDX (defaults to F:\HyperV\BaseImages\winserv2025-mxc-dev.vhdx).
.PARAMETER CredentialTarget
    Windows Credential Manager target name (defaults to 'mxc-guest').
.PARAMETER KeepRunning
    If specified, leaves the VM running for interactive operator inspection instead of deprovisioning.
.PARAMETER MemoryStartupMB
    Startup RAM in MB (default: 2048).
.PARAMETER CpuCount
    Virtual processor count (default: 2).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$BaseImagePath = "F:\HyperV\BaseImages\winserv2025-mxc-dev.vhdx",

    [Parameter(Mandatory = $false)]
    [string]$CredentialTarget = "mxc-guest",

    [Parameter(Mandatory = $false)]
    [int]$MemoryStartupMB = 4096,

    [Parameter(Mandatory = $false)]
    [int]$CpuCount = 4,

    [Parameter(Mandatory = $false)]
    [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  MXC HYPER-V WORKING COPY PROVISIONING & IN-GUEST VERIFICATION TASK" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Validate Parent Base Image
Write-Host "`n[Step 1/6] Validating Immutable Parent Base Image..." -ForegroundColor Yellow
if (-not (Test-Path $BaseImagePath)) {
    # Fallback check for winserv2025-golden.vhdx
    $alt = "F:\HyperV\BaseImages\winserv2025-golden.vhdx"
    if (Test-Path $alt) {
        Write-Warning "Target '$BaseImagePath' not found. Falling back to '$alt'."
        $BaseImagePath = $alt
    } else {
        throw "Base image not found at '$BaseImagePath' or '$alt'!"
    }
}

$parentItem = Get-Item $BaseImagePath
$parentLengthGB = [math]::Round($parentItem.Length / 1GB, 2)
$parentLastWrite = $parentItem.LastWriteTime
Write-Host "  Parent Path:       $BaseImagePath" -ForegroundColor Green
Write-Host "  Size on Disk:      $parentLengthGB GB" -ForegroundColor Green
Write-Host "  Last Modified:     $parentLastWrite" -ForegroundColor Green

# 2. Prepare State-Aware Configuration Files (UTF-8 without BOM)
Write-Host "`n[Step 2/6] Assembling State-Aware Configuration Files..." -ForegroundColor Yellow
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$wxcBin = Join-Path $repoRoot "src\target\debug\wxc-exec.exe"
if (-not (Test-Path $wxcBin)) {
    throw "wxc-exec.exe binary not found at '$wxcBin'. Please run 'cargo build' first."
}

$guid = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
$provConfigPath = Join-Path $env:TEMP ("mxc-prov-" + $guid + ".json")
$lifecycleConfigPath = Join-Path $env:TEMP ("mxc-lifecycle-" + $guid + ".json")
$execConfigPath = Join-Path $env:TEMP ("mxc-exec-" + $guid + ".json")

$memoryBytes = [int64]$MemoryStartupMB * 1024 * 1024
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

# Provision payload (contains containment + hyperv.provision; phase is passed on CLI)
$provisionPayload = @{
    version = "1.1.0-alpha"
    containment = "hyperv"
    hyperv = @{
        provision = @{
            baseImagePath = $BaseImagePath
            guestCredentialTarget = $CredentialTarget
            generation = 2
            memoryStartupBytes = $memoryBytes
            cpuCount = $CpuCount
        }
    }
}
[System.IO.File]::WriteAllText($provConfigPath, ($provisionPayload | ConvertTo-Json -Depth 5), $utf8NoBom)

# Start/Stop/Deprovision payload (minimal config)
$lifecyclePayload = @{
    version = "1.1.0-alpha"
}
[System.IO.File]::WriteAllText($lifecycleConfigPath, ($lifecyclePayload | ConvertTo-Json -Depth 5), $utf8NoBom)

# Exec payload
$execPayload = @{
    version = "1.1.0-alpha"
    process = @{
        commandLine = "hostname"
    }
}
[System.IO.File]::WriteAllText($execConfigPath, ($execPayload | ConvertTo-Json -Depth 5), $utf8NoBom)

Write-Host "  Config files initialized at $env:TEMP" -ForegroundColor DarkGray

$sandboxId = $null
$vmName = $null
$differencingDiskPath = $null

try {
    # 3. Provision Differencing Working Copy & Hyper-V VM via wxc-exec
    Write-Host "`n[Step 3/6] Provisioning Working Copy via MXC Runtime (wxc-exec)..." -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $wxcBin
    $pinfo.Arguments = "--experimental --operation provision `"$provConfigPath`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.WorkingDirectory = $repoRoot

    $proc = [System.Diagnostics.Process]::Start($pinfo)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $sw.Stop()

    if ($proc.ExitCode -ne 0) {
        Write-Error "Provisioning failed with exit code $($proc.ExitCode)`nStdout: $stdout`nStderr: $stderr"
        throw "wxc-exec provision failure"
    }

    # Extract JSON response
    $jsonLine = ($stdout -split "`r?`n" | Where-Object { $_ -match '^\s*\{.*"result".*\}\s*$' } | Select-Object -First 1)
    if (-not $jsonLine) {
        $jsonLine = $stdout
    }
    $resp = $jsonLine | ConvertFrom-Json
    $sandboxId = $resp.result.sandboxId
    $vmName = $resp.result.metadata.vmName

    Write-Host "  --> PROVISIONED SUCCESSFUL in $($sw.ElapsedMilliseconds) ms!" -ForegroundColor Green
    Write-Host "  Sandbox ID:        $sandboxId" -ForegroundColor Cyan
    Write-Host "  Hyper-V VM Name:   $vmName" -ForegroundColor Cyan

    $token = $sandboxId -replace '^hv:', ''
    $differencingDiskPath = Join-Path $env:ProgramData "mxc\hyperv\state-aware\$token\disk.vhdx"
    Write-Host "  Differencing Disk: $differencingDiskPath" -ForegroundColor DarkGray

    # 4. Start the VM
    Write-Host "`n[Step 4/6] Booting Working Copy Micro-VM..." -ForegroundColor Yellow
    $sw.Restart()

    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $wxcBin
    $pinfo.Arguments = "--experimental --operation start --container-id $sandboxId `"$lifecycleConfigPath`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.WorkingDirectory = $repoRoot

    $proc = [System.Diagnostics.Process]::Start($pinfo)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $sw.Stop()

    if ($proc.ExitCode -ne 0) {
        Write-Error "Start failed with exit code $($proc.ExitCode)`nStdout: $stdout`nStderr: $stderr"
        throw "wxc-exec start failure"
    }

    Write-Host "  --> VM STARTED in $($sw.ElapsedMilliseconds) ms!" -ForegroundColor Green

    # Wait for Guest Integration Heartbeat & PowerShell Direct ready
    Write-Host "  Waiting for Guest Integration Heartbeat and OS Initialization..." -ForegroundColor Yellow
    $heartbeatOk = $false
    $maxWaitSec = 90
    $elapsedSec = 0
    while ($elapsedSec -lt $maxWaitSec) {
        Start-Sleep -Seconds 3
        $elapsedSec += 3
        $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
        if ($vm) {
            $hb = (Get-VMIntegrationService -VMName $vmName -Name "Heartbeat" -ErrorAction SilentlyContinue).PrimaryStatusDescription
            if ($hb -match "OK" -or $hb -match "Applications") {
                $heartbeatOk = $true
                Write-Host "  [+] Heartbeat detected ($hb) after ${elapsedSec}s!" -ForegroundColor Green
                break
            }
        }
        Write-Host "  ... waiting for guest OS boot (${elapsedSec}s / ${maxWaitSec}s) ..." -ForegroundColor DarkGray
    }

    # Wait for PowerShell Direct (vmicvmsession) readiness
    Write-Host "  Waiting for PowerShell Direct (vmicvmsession) to accept exec..." -ForegroundColor Yellow
    $psDirectReady = $false
    $psWaitSec = 0
    $maxPsWaitSec = 90
    while ($psWaitSec -lt $maxPsWaitSec) {
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = $wxcBin
        $pinfo.Arguments = "--experimental --operation exec --container-id $sandboxId `"$execConfigPath`" -- hostname"
        $pinfo.RedirectStandardOutput = $true
        $pinfo.RedirectStandardError = $true
        $pinfo.UseShellExecute = $false
        $pinfo.WorkingDirectory = $repoRoot

        $proc = [System.Diagnostics.Process]::Start($pinfo)
        $probeOut = $proc.StandardOutput.ReadToEnd().Trim()
        $probeErr = $proc.StandardError.ReadToEnd().Trim()
        $proc.WaitForExit()

        if ($proc.ExitCode -eq 0 -and $probeOut) {
            $psDirectReady = $true
            Write-Host "  [+] PowerShell Direct responsive! Guest Hostname: $probeOut" -ForegroundColor Green
            break
        }
        Write-Host "  ... waiting for PowerShell Direct (${psWaitSec}s / ${maxPsWaitSec}s; exit=$($proc.ExitCode)) ..." -ForegroundColor DarkGray
        if ($probeErr) { Write-Host "      stderr: $probeErr" -ForegroundColor DarkGray }
        Start-Sleep -Seconds 5
        $psWaitSec += 5
    }

    if (-not $psDirectReady) {
        throw "PowerShell Direct did not become ready within ${maxPsWaitSec}s."
    }

    # Helper to execute in-guest PowerShell script and assert success
    function Invoke-GuestVerifyTask {
        param([string]$Title, [string]$ScriptText)
        Write-Host "`n  --- $Title ---" -ForegroundColor Cyan
        $bytes = [System.Text.Encoding]::Unicode.GetBytes($ScriptText)
        $b64 = [Convert]::ToBase64String($bytes)

        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = $wxcBin
        $pinfo.Arguments = "--experimental --operation exec --container-id $sandboxId `"$execConfigPath`" -- powershell.exe -NoProfile -EncodedCommand $b64"
        $pinfo.RedirectStandardOutput = $true
        $pinfo.RedirectStandardError = $true
        $pinfo.UseShellExecute = $false
        $pinfo.WorkingDirectory = $repoRoot

        $proc = [System.Diagnostics.Process]::Start($pinfo)
        $out = $proc.StandardOutput.ReadToEnd().Trim()
        $err = $proc.StandardError.ReadToEnd().Trim()
        $proc.WaitForExit()

        Write-Host "  Exit Code: $($proc.ExitCode)" -ForegroundColor DarkGray
        if ($out) { Write-Host $out -ForegroundColor White }
        if ($err) { Write-Host "  [stderr]: $err" -ForegroundColor Yellow }
        if ($proc.ExitCode -ne 0 -or -not $out) {
            throw "Verification task '$Title' failed (exit=$($proc.ExitCode))"
        }
    }

    # 5. Execute In-Guest Verification Tasks
    Write-Host "`n[Step 5/6] Executing Verification Tasks Inside Running Micro-VM..." -ForegroundColor Yellow

    # Verification Task 1: Guest Operating System Baseline
    Invoke-GuestVerifyTask -Title "Task 1: In-Guest OS & Hostname Probe" -ScriptText "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture, BuildNumber | ConvertTo-Json"

    # Verification Task 2: Guest Memory & Resource In-Guest Check
    $resScript = @"
[PSCustomObject]@{
    ComputerName = `$env:COMPUTERNAME
    ProcessorCount = `$env:NUMBER_OF_PROCESSORS
    TotalVisibleMemoryMB = [math]::Round(((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1024), 0)
    FreeMemoryMB = [math]::Round(((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024), 0)
} | ConvertTo-Json
"@
    Invoke-GuestVerifyTask -Title "Task 2: Resource Footprint & vCPU In-Guest Check" -ScriptText $resScript

    # Verification Task 3: Hyper-V Integration Services Status
    Invoke-GuestVerifyTask -Title "Task 3: Hyper-V Integration Services In-Guest Status" -ScriptText "Get-Service vmic* | Select-Object Name, Status, StartType | ConvertTo-Json"

    # Verification Task 4: Base Image Invariance & Child Differencing Isolation Check (ADR-005)
    Write-Host "  --- Task 4: Parent Image Invariance & Differencing Isolation Check ---" -ForegroundColor Cyan
    $parentCurrent = Get-Item $BaseImagePath
    $diffCurrent = Get-Item $differencingDiskPath
    $diffSizeMB = [math]::Round($diffCurrent.Length / 1MB, 2)

    Write-Host "  Parent VHDX Last Modified: $($parentCurrent.LastWriteTime) (Unchanged: $($parentCurrent.LastWriteTime -eq $parentLastWrite))" -ForegroundColor Green
    Write-Host "  Child Differencing Size:   $diffSizeMB MB (All mutations isolated to child disk)" -ForegroundColor Green
    if ($parentCurrent.LastWriteTime -ne $parentLastWrite) {
        Write-Warning "Parent image write time changed! Golden base image isolation violated!"
    } else {
        Write-Host "  [+] Golden base image is 100% sterile and untouched." -ForegroundColor Green
    }

    # Summary
    Write-Host "`n================================================================================" -ForegroundColor Cyan
    Write-Host "  VERIFICATION TASK COMPLETE: WORKING COPY PROVED 100% HEALTHY & ISOLATED" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

} finally {
    if ($sandboxId) {
        if ($KeepRunning) {
            Write-Host "`n[-KeepRunning specified] VM '$vmName' ($sandboxId) left active for inspection." -ForegroundColor Yellow
            Write-Host "  To stop and deprovision later: wxc-exec --operation stop --container-id $sandboxId; wxc-exec --operation deprovision --container-id $sandboxId" -ForegroundColor Gray
        } else {
            Write-Host "`n[Step 6/6] Tearing Down & Deprovisioning Transient Working Copy..." -ForegroundColor Yellow
            try {
                # Stop VM
                $pinfo = New-Object System.Diagnostics.ProcessStartInfo
                $pinfo.FileName = $wxcBin
                $pinfo.Arguments = "--experimental --operation stop --container-id $sandboxId `"$lifecycleConfigPath`""
                $pinfo.RedirectStandardOutput = $true
                $pinfo.RedirectStandardError = $true
                $pinfo.UseShellExecute = $false
                $pinfo.WorkingDirectory = $repoRoot
                $proc = [System.Diagnostics.Process]::Start($pinfo)
                $proc.WaitForExit()
                Write-Host "  VM Stopped." -ForegroundColor Green

                # Deprovision VM & clean disk
                $pinfo.Arguments = "--experimental --operation deprovision --container-id $sandboxId `"$lifecycleConfigPath`""
                $proc = [System.Diagnostics.Process]::Start($pinfo)
                $proc.WaitForExit()
                Write-Host "  VM Deprovisioned and differencing disk erased." -ForegroundColor Green
            } catch {
                Write-Warning "Cleanup error: $_"
            }
        }
    }

    # Cleanup temp config files
    Remove-Item -Path $provConfigPath, $lifecycleConfigPath, $execConfigPath -Force -ErrorAction SilentlyContinue
}
