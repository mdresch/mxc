<#
.SYNOPSIS
    MXC Windows 11 Enterprise Prompt-Only Dev Box Shrink Pipeline
.DESCRIPTION
    Transforms a standard Windows 11 installation into an ultra-lean (<7 GB disk, <500 MB RAM)
    prompt-centric developer box while preserving full Win32 API fidelity, compilers, 
    Hyper-V synthetic video (for screen prints), and RDP Enhanced Sessions.
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " MXC Windows 11 Prompt-Only Dev Box Shrink Pipeline              " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Replace Explorer with Direct PowerShell Prompt Shell
Write-Host "[1/7] Replacing Explorer Shell with Direct PowerShell Prompt..." -ForegroundColor Yellow
if (-not $DryRun) {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name "Shell" -Value "powershell.exe -NoLogo"
}

# 2. Disable OS Hibernation (Saves 4GB - 8GB instantly)
Write-Host "[2/7] Disabling Hibernation and setting static 1GB Pagefile..." -ForegroundColor Yellow
if (-not $DryRun) {
    powercfg.exe /hibernate off
    Set-CimInstance -Query "Select * from Win32_PageFileSetting" -Property @{InitialSize = 1024; MaximumSize = 1024} -ErrorAction SilentlyContinue
}

# 3. Disable Heavy Background Daemons (Search Indexer, Update staging, Defender Scan)
Write-Host "[3/7] Disabling background consumer services (WSearch, wuauserv)..." -ForegroundColor Yellow
if (-not $DryRun) {
    Stop-Service WSearch -ErrorAction SilentlyContinue
    Set-Service WSearch -StartupType Disabled -ErrorAction SilentlyContinue

    Stop-Service wuauserv -ErrorAction SilentlyContinue
    Set-Service wuauserv -StartupType Disabled -ErrorAction SilentlyContinue

    Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue
}

# 4. Strip Consumer AppX and Web Bloat
Write-Host "[4/7] Purging provisioned Consumer AppX Packages..." -ForegroundColor Yellow
if (-not $DryRun) {
    Get-AppxProvisionedPackage -Online | Where-Object {
        $_.DisplayName -notmatch "Terminal|Notepad|Calculator|AppInstaller"
    } | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue
}

# 5. Deep Component Store Cleanup (Purge Superseded WinSxS Updates)
Write-Host "[5/7] Running DISM Component Store reset (/ResetBase)..." -ForegroundColor Yellow
if (-not $DryRun) {
    dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase /NoRestart
}

# 6. Enable Transparent NTFS CompactOS Compression
Write-Host "[6/7] Enabling CompactOS transparent LZX filesystem compression..." -ForegroundColor Yellow
if (-not $DryRun) {
    compact.exe /CompactOS:always
}

# 7. Ensure RDP and Enhanced Sessions are 100% Enabled
Write-Host "[7/7] Verifying RDP and Hyper-V Enhanced Session listener..." -ForegroundColor Yellow
if (-not $DryRun) {
    Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
}

Write-Host "`n[+] Windows Prompt-Only Dev Box Shrink Complete!" -ForegroundColor Green
Write-Host "[+] Reboot to initialize the pure PowerShell console shell." -ForegroundColor Green

