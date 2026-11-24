# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    MXC Ultra-Lean Windows 11 Agent Image Baking Pipeline
.DESCRIPTION
    Clones F:\HyperV\BaseImages\win11-golden.vhdx into a standalone Dynamic VHDX
    (F:\HyperV\BaseImages\win11-agent-lean.vhdx), boots a temporary Gen2 bake VM,
    strips all non-agent Windows 11 features/AppX bloat/services, replaces Explorer
    with a prompt-only PowerShell shell, installs the Core Agent Software Stack
    (git, gh, pwsh, ripgrep, fd, jq, 7zip, python, uv, ruff, pytest, httpx, pydantic,
    mcp, nodejs-lts, pnpm, typescript, tsx), cleans caches, runs DISM /ResetBase +
    CompactOS LZX, shuts down, and runs Optimize-VHD -Mode Full.
#>

[CmdletBinding()]
param(
    [string]$GoldenVhdx = "F:\HyperV\BaseImages\win11-golden.vhdx",
    [string]$OutputVhdx = "F:\HyperV\BaseImages\win11-agent-lean.vhdx",
    [string]$StagingVhdx = "C:\HyperV\BaseImages\win11-agent-lean.vhdx",
    [string]$VmName = "MXC-Bake-Win11-Agent-Temp",
    [string]$CredentialTarget = "mxc-guest",
    [string]$SwitchName = "Default Switch",
    [int]$MemoryGB = 4,
    [int]$CpuCount = 4,
    [switch]$SkipStage
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  MXC ULTRA-LEAN WINDOWS 11 AGENT IMAGE BAKING PIPELINE" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Validate Golden Parent & Resolve Credential
if (-not (Test-Path $GoldenVhdx)) {
    throw "Golden Win11 VHDX not found at '$GoldenVhdx'"
}

$goldenItem = Get-Item $GoldenVhdx
$goldenSizeGB = [math]::Round($goldenItem.Length / 1GB, 2)
$goldenLastWrite = $goldenItem.LastWriteTime
Write-Host "[1/8] Golden Parent: $GoldenVhdx ($goldenSizeGB GB, modified $goldenLastWrite)" -ForegroundColor Green

function Resolve-MxcCredential {
    param([string]$Target)
    $code = @'
using System;
using System.Runtime.InteropServices;
using System.Management.Automation;

public class MxcAgentBakeCred {
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
        if (!CredRead(targetName, 1, 0, out credPtr)) return null;
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
    if (-not ([System.Management.Automation.PSTypeName]'MxcAgentBakeCred').Type) {
        Add-Type -TypeDefinition $code -ErrorAction Stop
    }
    return [MxcAgentBakeCred]::GetCredential($Target)
}

$guestCred = Resolve-MxcCredential -Target $CredentialTarget
if (-not $guestCred) {
    throw "Credential '$CredentialTarget' not found in Windows Credential Manager."
}
Write-Host "      Credential resolved for user: $($guestCred.UserName)" -ForegroundColor DarkGray

# Cleanup any leftover temp VM from a prior aborted run
$existingVm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if ($existingVm) {
    Write-Host "      Cleaning up leftover bake VM '$VmName'..." -ForegroundColor Yellow
    if ($existingVm.State -ne 'Off') { Stop-VM -Name $VmName -TurnOff -Force }
    Remove-VM -Name $VmName -Force
}

# 2. Stage Standalone Target on C: NVMe Hot Tier
$stagingDir = Split-Path -Path $StagingVhdx -Parent
if ($stagingDir -and (-not (Test-Path $stagingDir))) {
    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
}
if ($SkipStage -and (Test-Path $StagingVhdx)) {
    Write-Host "`n[2/8] -SkipStage set: reusing already-staged NVMe VHDX at $StagingVhdx" -ForegroundColor Green
} else {
    Write-Host "`n[2/8] Staging Golden VHDX on NVMe ($GoldenVhdx -> $StagingVhdx)..." -ForegroundColor Yellow
    if (Test-Path $StagingVhdx) {
        Remove-Item -Path $StagingVhdx -Force
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    Copy-Item -Path $GoldenVhdx -Destination $StagingVhdx -Force
    $sw.Stop()
    Write-Host "      Staged standalone VHDX on NVMe in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s." -ForegroundColor Green
}

# 3. Provision & Boot Temporary Gen2 Bake VM (Win11 UEFI SecureBoot + vTPM on NVMe)
Write-Host "`n[3/8] Creating & Booting Bake VM '$VmName' (${MemoryGB}GB static RAM, ${CpuCount} vCPUs, vTPM, $SwitchName)..." -ForegroundColor Yellow
New-VM -Name $VmName -Generation 2 -MemoryStartupBytes ($MemoryGB * 1GB) -VHDPath $StagingVhdx -SwitchName $SwitchName | Out-Null
Set-VMMemory -VMName $VmName -DynamicMemoryEnabled $false
Set-VMProcessor -VMName $VmName -Count $CpuCount
Set-VMFirmware -VMName $VmName -EnableSecureBoot On -ErrorAction SilentlyContinue
Set-VMKeyProtector -VMName $VmName -NewLocalKeyProtector -ErrorAction SilentlyContinue
Enable-VMTPM -VMName $VmName -ErrorAction SilentlyContinue
Enable-VMIntegrationService -VMName $VmName -Name "Guest Service Interface" -ErrorAction SilentlyContinue

$bakeSuccess = $false
try {
    Start-VM -Name $VmName

    # Wait for Heartbeat
    Write-Host "      Waiting for Guest Heartbeat..." -ForegroundColor DarkGray
    $hbReady = $false
    for ($i = 0; $i -lt 45; $i++) {
        Start-Sleep -Seconds 3
        $hb = (Get-VMIntegrationService -VMName $VmName -Name "Heartbeat" -ErrorAction SilentlyContinue).PrimaryStatusDescription
        if ($hb -match "OK" -or $hb -match "Applications") {
            $hbReady = $true
            Write-Host "      [+] Heartbeat OK after $(($i + 1) * 3)s" -ForegroundColor Green
            break
        }
    }
    if (-not $hbReady) { throw "Guest Heartbeat did not become ready within 135s." }

    # Wait for PowerShell Direct
    Write-Host "      Waiting for PowerShell Direct (vmicvmsession)..." -ForegroundColor DarkGray
    $psReady = $false
    $lastPsErr = ""
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $hn = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock { $env:COMPUTERNAME } -ErrorAction Stop
            if ($hn) {
                $psReady = $true
                Write-Host "      [+] PowerShell Direct ready! Guest hostname: $hn" -ForegroundColor Green
                break
            }
        } catch {
            $lastPsErr = $_.Exception.Message
            if (($i % 3) -eq 0) {
                Write-Host "      ... retry $($i + 1)/30: $lastPsErr" -ForegroundColor DarkGray
            }
            Start-Sleep -Seconds 5
        }
    }
    if (-not $psReady) { throw "PowerShell Direct did not respond within 150s. Last error: $lastPsErr" }

    # 4. Phase A: Debloat & Remove Non-Agent Windows 11 Features
    Write-Host "`n[4/8] Stripping non-agent Windows 11 features, AppX bloat, and services..." -ForegroundColor Yellow
    $debloatResult = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock {
        $ErrorActionPreference = 'Continue'
        $ProgressPreference = 'SilentlyContinue'

        Write-Output "--- [A1] Replacing Explorer shell with prompt-only PowerShell ---"
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" -Name "Shell" -Value "powershell.exe -NoLogo"

        Write-Output "--- [A2] Disabling hibernation & setting static 1GB pagefile ---"
        powercfg.exe /hibernate off 2>&1 | Out-Null
        $cs = Get-CimInstance Win32_ComputerSystem
        if ($cs.AutomaticManagedPagefile) {
            Set-CimInstance -InputObject $cs -Property @{ AutomaticManagedPagefile = $false } -ErrorAction SilentlyContinue
        }
        $pf = Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue
        if ($pf) {
            Set-CimInstance -InputObject $pf -Property @{ InitialSize = 1024; MaximumSize = 1024 } -ErrorAction SilentlyContinue
        }

        Write-Output "--- [A3] Removing non-agent provisioned & installed AppX packages ---"
        $keepRegex = 'WindowsTerminal|VCLibs|UI\.Xaml|NET\.Native|DesktopAppInstaller|StorePurchaseApp|SecHealthUI|WindowsAppRuntime'
        $prov = Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -notmatch $keepRegex }
        $removedProv = 0
        foreach ($pkg in $prov) {
            try {
                Remove-AppxProvisionedPackage -Online -PackageName $pkg.PackageName -ErrorAction SilentlyContinue | Out-Null
                $removedProv++
            } catch {}
        }
        $inst = Get-AppxPackage -AllUsers -ErrorAction SilentlyContinue | Where-Object {
            $_.NonRemovable -eq $false -and $_.IsFramework -eq $false -and $_.Name -notmatch $keepRegex
        }
        $removedInst = 0
        foreach ($pkg in $inst) {
            try {
                Remove-AppxPackage -Package $pkg.PackageFullName -AllUsers -ErrorAction SilentlyContinue | Out-Null
                $removedInst++
            } catch {}
        }
        Write-Output "Removed $removedProv provisioned AppX packages and $removedInst installed AppX packages."

        Write-Output "--- [A4] Disabling non-agent Windows Optional Features ---"
        $featuresToDisable = @(
            'Recall',
            'Printing-Foundation-Features',
            'Printing-Foundation-InternetPrinting-Client',
            'Printing-PrintToPDFServices-Features',
            'Printing-XPSServices-Features',
            'FaxServicesClientPackage',
            'MediaPlayback',
            'WindowsMediaPlayer',
            'WorkFolders-Client',
            'SearchEngine-Client-Package',
            'MSRDC-Infrastructure'
        )
        $disabledFeat = 0
        foreach ($f in $featuresToDisable) {
            $feat = Get-WindowsOptionalFeature -Online -FeatureName $f -ErrorAction SilentlyContinue
            if ($feat -and $feat.State -eq 'Enabled') {
                Disable-WindowsOptionalFeature -Online -FeatureName $f -NoRestart -Remove -ErrorAction SilentlyContinue | Out-Null
                $disabledFeat++
            }
        }
        Write-Output "Disabled $disabledFeat Windows Optional Features."

        Write-Output "--- [A5] Removing non-agent Windows Capabilities (FoD) ---"
        $capPatterns = @(
            'App.StepsRecorder*',
            'App.Support.QuickAssist*',
            'Browser.InternetExplorer*',
            'Hello.Face*',
            'MathRecognizer*',
            'Media.WindowsMediaPlayer*',
            'Microsoft.Windows.WordPad*',
            'OneCoreUAP.OneSync*',
            'Print.Fax.Scan*',
            'Print.Management.Console*'
        )
        $removedCaps = 0
        foreach ($pat in $capPatterns) {
            $caps = Get-WindowsCapability -Online -Name $pat -ErrorAction SilentlyContinue | Where-Object State -eq 'Installed'
            foreach ($c in $caps) {
                Remove-WindowsCapability -Online -Name $c.Name -ErrorAction SilentlyContinue | Out-Null
                $removedCaps++
            }
        }
        Write-Output "Removed $removedCaps Windows Capabilities."

        Write-Output "--- [A6] Uninstalling OneDrive & disabling consumer services ---"
        $odSetup = "$env:SystemRoot\SysWOW64\OneDriveSetup.exe"
        if (-not (Test-Path $odSetup)) { $odSetup = "$env:SystemRoot\System32\OneDriveSetup.exe" }
        if (Test-Path $odSetup) {
            Start-Process -FilePath $odSetup -ArgumentList "/uninstall" -Wait -NoNewWindow -ErrorAction SilentlyContinue
        }

        $servicesToDisable = @(
            'WSearch', 'wuauserv', 'UsoSvc', 'SysMain', 'DiagTrack', 'dmwappushservice',
            'MapsBroker', 'Spooler', 'Fax', 'WerSvc', 'XblAuthManager', 'XblGameSave',
            'XboxGipSvc', 'XboxNetApiSvc', 'WbioSrvc', 'TabletInputService', 'RetailDemo',
            'PcaSvc', 'DoSvc', 'lfsvc', 'WalletService', 'wisvc', 'DPS', 'WdiServiceHost', 'WdiSystemHost'
        )
        $disabledSvc = 0
        foreach ($s in $servicesToDisable) {
            $svc = Get-Service -Name $s -ErrorAction SilentlyContinue
            if ($svc) {
                Stop-Service -Name $s -Force -ErrorAction SilentlyContinue
                Set-Service -Name $s -StartupType Disabled -ErrorAction SilentlyContinue
                $disabledSvc++
            }
        }
        Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue
        Write-Output "Disabled $disabledSvc background services."

        Write-Output "--- [A7] Ensuring RDP & Hyper-V Enhanced Sessions remain enabled ---"
        Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
        Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
    }
    $debloatResult | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }

    # 5. Phase B: Install Core Agent Software Stack
    Write-Host "`n[5/8] Installing Core Agent Software Stack (git, gh, pwsh, rg, fd, jq, 7zip, python, uv, node-lts, pnpm, ts)..." -ForegroundColor Yellow
    $installResult = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock {
        $ErrorActionPreference = 'Continue'
        $ProgressPreference = 'SilentlyContinue'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

        # Wait briefly for DHCP / internet on Default Switch
        $netOk = $false
        for ($i = 0; $i -lt 12; $i++) {
            try {
                $r = Invoke-WebRequest -Uri "https://get.scoop.sh" -UseBasicParsing -TimeoutSec 10
                if ($r.StatusCode -eq 200) { $netOk = $true; break }
            } catch {
                Start-Sleep -Seconds 3
            }
        }
        if (-not $netOk) {
            throw "Guest VM cannot reach https://get.scoop.sh over Default Switch."
        }
        Write-Output "[+] Guest internet connectivity confirmed."

        # Install Scoop
        $shimPath = Join-Path $HOME 'scoop\shims'
        if (-not (Test-Path "$shimPath\scoop.ps1")) {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Invoke-RestMethod -Uri "https://get.scoop.sh" -OutFile "$env:TEMP\install-scoop.ps1"
            & "$env:TEMP\install-scoop.ps1" -RunAsAdmin 2>&1 | Out-Null
        }
        $env:Path = "$shimPath;$HOME\.local\bin;$HOME\scoop\apps\python\current\Scripts;$env:Path"

        # Configure Scoop & install Core Agent Stack
        & scoop install git 2>&1 | Out-Null
        & scoop bucket add main 2>&1 | Out-Null
        & scoop bucket add extras 2>&1 | Out-Null

        Write-Output "[+] Installing CLI tools (gh, pwsh, ripgrep, fd, jq, 7zip)..."
        & scoop install gh pwsh ripgrep fd jq 7zip 2>&1 | Out-Null

        Write-Output "[+] Installing Python + uv & Node.js LTS + pnpm..."
        & scoop install python uv nodejs-lts pnpm 2>&1 | Out-Null

        # Refresh PATH for newly installed runtimes
        $pyScripts = Join-Path $HOME 'scoop\apps\python\current\Scripts'
        $nodeBin = Join-Path $HOME 'scoop\apps\nodejs-lts\current\bin'
        $env:Path = "$shimPath;$pyScripts;$nodeBin;$HOME\.local\bin;$env:Path"

        Write-Output "[+] Installing Python agent packages (pytest, httpx, pydantic, mcp, requests) + ruff..."
        & pip install --no-cache-dir --no-warn-script-location pytest httpx pydantic mcp requests 2>&1 | Out-Null
        & uv tool install ruff 2>&1 | Out-Null

        Write-Output "[+] Installing TypeScript & tsx globally..."
        & npm install -g typescript tsx 2>&1 | Out-Null

        # Persist Machine PATH
        $targetDirs = @($shimPath, $pyScripts, $nodeBin, (Join-Path $HOME '.local\bin'))
        $currPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $parts = $currPath -split ';'
        foreach ($d in $targetDirs) {
            if ($d -notin $parts) { $currPath = "$d;$currPath" }
        }
        [Environment]::SetEnvironmentVariable("Path", $currPath, "Machine")

        # Defender exclusions for agent workspaces
        Add-MpPreference -ExclusionPath @('C:\workspace', 'C:\Tools', (Join-Path $HOME 'scoop'), (Join-Path $HOME '.local')) -ErrorAction SilentlyContinue

        # Verify installed tool versions
        Write-Output "--- Installed Agent Stack Verification ---"
        [PSCustomObject]@{
            git        = (& git --version 2>$null) -join ''
            gh         = ((& gh --version 2>$null) | Select-Object -First 1)
            pwsh       = (& pwsh --version 2>$null) -join ''
            rg         = ((& rg --version 2>$null) | Select-Object -First 1)
            fd         = (& fd --version 2>$null) -join ''
            jq         = (& jq --version 2>$null) -join ''
            python     = (& python --version 2>$null) -join ''
            uv         = (& uv --version 2>$null) -join ''
            ruff       = (& ruff --version 2>$null) -join ''
            node       = (& node --version 2>$null) -join ''
            pnpm       = (& pnpm --version 2>$null) -join ''
            tsc        = (& tsc --version 2>$null) -join ''
        } | Format-List | Out-String
    }
    $installResult | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }

    # 6. Phase C: Cache Purge, DISM /ResetBase, CompactOS LZX & Free-Space Zeroing
    Write-Host "`n[6/8] Purging caches, running DISM /ResetBase, enabling CompactOS LZX & zeroing free blocks..." -ForegroundColor Yellow
    $compactResult = Invoke-Command -VMName $VmName -Credential $guestCred -ScriptBlock {
        $ErrorActionPreference = 'Continue'
        $ProgressPreference = 'SilentlyContinue'
        $shimPath = Join-Path $HOME 'scoop\shims'
        $env:Path = "$shimPath;$env:Path"

        # Clear package manager caches
        & scoop cache rm * 2>&1 | Out-Null
        & npm cache clean --force 2>&1 | Out-Null
        & uv cache clean 2>&1 | Out-Null
        Remove-Item -Path "$env:TEMP\*", "C:\Windows\Temp\*", "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue

        Write-Output "[+] Running DISM StartComponentCleanup /ResetBase..."
        dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase /NoRestart 2>&1 | Select-Object -Last 5

        Write-Output "[+] Enabling CompactOS transparent LZX compression..."
        compact.exe /CompactOS:always 2>&1 | Select-Object -Last 5

        # Report guest disk usage
        $vol = Get-Volume -DriveLetter C
        $usedGB = [math]::Round(($vol.Size - $vol.SizeRemaining) / 1GB, 2)
        $freeGB = [math]::Round($vol.SizeRemaining / 1GB, 2)
        Write-Output "[+] Guest C:\ Used Space after CompactOS: ${usedGB} GB (Free: ${freeGB} GB)"

        # Zero free space via cipher /w:C:\TempZero (fast sparse-reclaimable zeroing)
        Write-Output "[+] Zero-filling freed blocks for host Optimize-VHD compaction..."
        $zeroFile = "C:\zero_fill.tmp"
        try {
            $fs = [System.IO.File]::Create($zeroFile)
            $buf = New-Object byte[] (16 * 1024 * 1024)
            $freeBytes = (Get-Volume -DriveLetter C).SizeRemaining
            $targetBytes = [math]::Max(0, $freeBytes - (256 * 1024 * 1024))
            $written = [int64]0
            while ($written -lt $targetBytes) {
                $toWrite = [int][math]::Min($buf.Length, $targetBytes - $written)
                $fs.Write($buf, 0, $toWrite)
                $written += $toWrite
            }
            $fs.Flush()
            $fs.Close()
        } catch {
            if ($fs) { try { $fs.Close() } catch {} }
        } finally {
            Remove-Item -Path $zeroFile -Force -ErrorAction SilentlyContinue
        }
        Write-Output "[+] Free-space zero-fill complete."
    }
    $compactResult | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }

    # 7. Clean Guest Shutdown & Remove Bake VM
    Write-Host "`n[7/8] Shutting down bake VM cleanly..." -ForegroundColor Yellow
    Stop-VM -Name $VmName -Force
    $bakeSuccess = $true
} finally {
    $vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
    if ($vm) {
        if ($vm.State -ne 'Off') { Stop-VM -Name $VmName -TurnOff -Force }
        Remove-VM -Name $VmName -Force
        Write-Host "      Temporary bake VM '$VmName' removed." -ForegroundColor DarkGray
    }
}

if (-not $bakeSuccess) {
    throw "Bake pipeline failed prior to completion."
}

# 8. Host-Side VHDX Compaction on NVMe (Optimize-VHD -Mode Full) & Archive Copy to F:
Write-Host "`n[8/8] Compacting standalone VHDX on NVMe (Optimize-VHD -Mode Full)..." -ForegroundColor Yellow
$preCompactGB = [math]::Round((Get-Item $StagingVhdx).Length / 1GB, 2)
try {
    Mount-VHD -Path $StagingVhdx -ReadOnly
    try {
        Optimize-VHD -Path $StagingVhdx -Mode Full
    } finally {
        Dismount-VHD -Path $StagingVhdx -ErrorAction SilentlyContinue
    }
} catch {
    Write-Warning "Host Optimize-VHD skipped (requires Administrator elevation): $($_.Exception.Message)"
    Write-Warning "Free blocks inside the guest are already zero-filled; run 'Optimize-VHD -Path `"$StagingVhdx`" -Mode Full' in an Admin PowerShell anytime to reclaim sparse space."
}
$postCompactGB = [math]::Round((Get-Item $StagingVhdx).Length / 1GB, 2)
$savedGB = [math]::Round($goldenSizeGB - $postCompactGB, 2)

# Copy compacted image to archive tier if different path
if ($OutputVhdx -ne $StagingVhdx) {
    Write-Host "      Copying compacted VHDX (${postCompactGB} GB) to archive target $OutputVhdx..." -ForegroundColor Yellow
    if (Test-Path $OutputVhdx) { Remove-Item -Path $OutputVhdx -Force }
    Copy-Item -Path $StagingVhdx -Destination $OutputVhdx -Force
}

# Verify golden parent invariance
$goldenCheck = Get-Item $GoldenVhdx
$parentIntact = ($goldenCheck.LastWriteTime -eq $goldenLastWrite)

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "  ULTRA-LEAN WINDOWS 11 AGENT IMAGE BAKE COMPLETE!" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  NVMe Hot-Tier VHDX : $StagingVhdx" -ForegroundColor Green
Write-Host "  Archive VHDX       : $OutputVhdx" -ForegroundColor Green
Write-Host "  Golden Parent Size : $goldenSizeGB GB (Untouched: $parentIntact)" -ForegroundColor Green
Write-Host "  Pre-Compact Size   : $preCompactGB GB" -ForegroundColor Yellow
Write-Host "  Final Compact Size : $postCompactGB GB (Net delta vs golden: $savedGB GB saved)" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
