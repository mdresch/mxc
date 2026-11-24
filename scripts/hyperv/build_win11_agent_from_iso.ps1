# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Builds a clean, zero-OOBE, ultra-lean Windows 11 Agent VHDX directly from an ISO.
.DESCRIPTION
    1. Mounts the Windows 11 ISO (C:\HyperV\Windows11_Client_x64_en-us_26300_9457.iso).
    2. Creates a fresh 64 GB Dynamic GPT/UEFI VHDX at C:\HyperV\BaseImages\win11-agent-lean.vhdx.
    3. Applies the Windows 11 Enterprise/Pro WIM with /Compact (CompactOS LZX from boot 0).
    4. Installs UEFI boot files via bcdboot.
    5. Strips non-agent AppX packages & optional features OFFLINE before first boot.
    6. Injects a clean Unattend.xml + SetupComplete.cmd using the password from Windows
       Credential Manager target 'mxc-guest' (never hardcoded in this script) to skip OOBE,
       activate built-in Administrator, and enable PowerShell Direct + RDP.
    7. Hands off directly to bake_win11_agent_lean.ps1 -SkipStage to install the Core Agent
       Stack, switch to prompt-only PowerShell shell, compact via Optimize-VHD -Mode Full,
       and archive to F:\HyperV\BaseImages\win11-agent-lean.vhdx.
.NOTES
    Must be run from an elevated (Administrator) PowerShell prompt.
#>

[CmdletBinding()]
param(
    [string]$IsoPath = "C:\HyperV\Windows11_Client_x64_en-us_26300_9457.iso",
    [string]$StagingVhdx = "C:\HyperV\BaseImages\win11-agent-lean.vhdx",
    [string]$ArchiveVhdx = "F:\HyperV\BaseImages\win11-agent-lean.vhdx",
    [string]$CredentialTarget = "mxc-guest",
    [uint64]$VhdxSizeBytes = 64GB,
    [switch]$SkipApply,
    [switch]$SkipBake
)

$ErrorActionPreference = "Stop"

# Verify Administrator elevation
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "This script requires Administrator elevation (for Mount-DiskImage, Mount-VHD, DISM, bcdboot, and Optimize-VHD). Please run from an elevated PowerShell prompt."
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  MXC CLEAN WINDOWS 11 AGENT VHDX BUILDER (FROM ISO -> ULTRA-LEAN AGENT)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if (-not (Test-Path $IsoPath)) {
    throw "Windows 11 ISO not found at '$IsoPath'"
}

# Resolve mxc-guest password dynamically from Windows Credential Manager (never hardcoded)
$credCode = @'
using System;
using System.Runtime.InteropServices;

public class MxcIsoCredReader {
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

    public static string GetPassword(string targetName) {
        IntPtr credPtr;
        if (!CredRead(targetName, 1, 0, out credPtr)) return null;
        try {
            CREDENTIAL cred = (CREDENTIAL)Marshal.PtrToStructure(credPtr, typeof(CREDENTIAL));
            return Marshal.PtrToStringUni(cred.CredentialBlob, cred.CredentialBlobSize / 2);
        } finally {
            CredFree(credPtr);
        }
    }
}
'@
if (-not ([System.Management.Automation.PSTypeName]'MxcIsoCredReader').Type) {
    Add-Type -TypeDefinition $credCode -ErrorAction Stop
}
$adminPass = [MxcIsoCredReader]::GetPassword($CredentialTarget)
if (-not $adminPass) {
    throw "Credential '$CredentialTarget' not found in Windows Credential Manager."
}
# XML-escape password for Unattend.xml
$adminPassXml = [System.Security.SecurityElement]::Escape($adminPass)

$vhdxDir = Split-Path -Path $StagingVhdx -Parent
if ($vhdxDir -and (-not (Test-Path $vhdxDir))) {
    New-Item -ItemType Directory -Path $vhdxDir -Force | Out-Null
}

# Remove any leftover temp bake VM that might lock StagingVhdx
foreach ($oldVm in @("MXC-Bake-Win11-Agent-Temp", "MXC-Win11-Diag", "MXC-Win11-Probe")) {
    $v = Get-VM -Name $oldVm -ErrorAction SilentlyContinue
    if ($v) {
        if ($v.State -ne 'Off') { Stop-VM -Name $oldVm -TurnOff -Force }
        Remove-VM -Name $oldVm -Force
    }
}

$isoMounted = $false
$vhdMounted = $false

try {
    if ($SkipApply -and (Test-Path $StagingVhdx)) {
        Write-Host "`n[Step 1-4/6] -SkipApply set: mounting already-applied VHDX at $StagingVhdx ..." -ForegroundColor Green
        $vhd = Mount-VHD -Path $StagingVhdx -PassThru
        $vhdMounted = $true
        Start-Sleep -Seconds 2
        $parts = Get-Partition -DiskNumber $vhd.DiskNumber
        $winPart = $parts | Where-Object { $_.DriveLetter -and (Test-Path "$($_.DriveLetter):\Windows\System32") } | Select-Object -First 1
        if (-not $winPart) {
            $usedLetters = (Get-Volume | Where-Object DriveLetter).DriveLetter
            $freeLetter = [string]([char[]]([char]'Z'..[char]'K') | Where-Object { $_ -notin $usedLetters } | Select-Object -First 1)
            $winPart = $parts | Where-Object { $_.Type -eq 'Basic' } | Sort-Object Size -Descending | Select-Object -First 1
            Set-Partition -DiskNumber $vhd.DiskNumber -PartitionNumber $winPart.PartitionNumber -NewDriveLetter $freeLetter
            Start-Sleep -Seconds 1
            $winLetter = $freeLetter
        } else {
            $winLetter = [string]$winPart.DriveLetter
        }
        Write-Host "      Located Windows partition at ${winLetter}:" -ForegroundColor Green
    } else {
        # 1. Mount ISO and locate install.wim / install.esd
        Write-Host "`n[Step 1/6] Mounting ISO: $IsoPath" -ForegroundColor Yellow
        $isoObj = Mount-DiskImage -ImagePath $IsoPath -PassThru
        $isoMounted = $true
        Start-Sleep -Seconds 2
        $isoDrive = ($isoObj | Get-Volume).DriveLetter
        if (-not $isoDrive) { throw "Failed to obtain drive letter for mounted ISO." }

        $wimPath = "${isoDrive}:\sources\install.wim"
        if (-not (Test-Path $wimPath)) {
            $wimPath = "${isoDrive}:\sources\install.esd"
        }
        if (-not (Test-Path $wimPath)) {
            throw "Neither install.wim nor install.esd found on ${isoDrive}:\sources\"
        }

        $images = Get-WindowsImage -ImagePath $wimPath
        Write-Host "      Available editions in $(Split-Path -Leaf $wimPath):" -ForegroundColor DarkGray
        $images | ForEach-Object { Write-Host "        [$($_.ImageIndex)] $($_.ImageName)" -ForegroundColor DarkGray }

        # Prefer Windows 11 Enterprise, fallback to Pro, fallback to Index 1
        $selected = $images | Where-Object { $_.ImageName -match 'Windows 11 Enterprise$' } | Select-Object -First 1
        if (-not $selected) { $selected = $images | Where-Object { $_.ImageName -match 'Enterprise' } | Select-Object -First 1 }
        if (-not $selected) { $selected = $images | Where-Object { $_.ImageName -match 'Windows 11 Pro$' } | Select-Object -First 1 }
        if (-not $selected) { $selected = $images | Select-Object -First 1 }

        Write-Host "      Selected Edition: [$($selected.ImageIndex)] $($selected.ImageName)" -ForegroundColor Green

        # 2. Create & Partition Fresh GPT/UEFI VHDX on NVMe
        Write-Host "`n[Step 2/6] Creating fresh 64 GB Dynamic GPT/UEFI VHDX at $StagingVhdx ..." -ForegroundColor Yellow
        if (Test-Path $StagingVhdx) {
            Dismount-VHD -Path $StagingVhdx -ErrorAction SilentlyContinue
            Remove-Item -Path $StagingVhdx -Force
        }
        New-VHD -Path $StagingVhdx -SizeBytes $VhdxSizeBytes -Dynamic | Out-Null
        $vhd = Mount-VHD -Path $StagingVhdx -PassThru
        $vhdMounted = $true
        $diskNum = $vhd.DiskNumber
        Start-Sleep -Seconds 1

        Initialize-Disk -Number $diskNum -PartitionStyle GPT | Out-Null

        # Pick two free drive letters
        $usedLetters = (Get-Volume | Where-Object DriveLetter).DriveLetter
        $freeLetters = [char[]]([char]'Z'..[char]'K') | Where-Object { $_ -notin $usedLetters }
        $efiLetter = [string]$freeLetters[0]
        $winLetter = [string]$freeLetters[1]

        # EFI System Partition (260 MB FAT32)
        $efiPart = New-Partition -DiskNumber $diskNum -Size 260MB -GptType '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}' -DriveLetter $efiLetter
        Format-Volume -Partition $efiPart -FileSystem FAT32 -NewFileSystemLabel "System" -Confirm:$false | Out-Null

        # MSR Partition (16 MB)
        New-Partition -DiskNumber $diskNum -Size 16MB -GptType '{e3c9e316-0b5c-4db8-817d-f92df00215ae}' | Out-Null

        # Windows Primary Partition (remaining space, NTFS)
        $winPart = New-Partition -DiskNumber $diskNum -UseMaximumSize -DriveLetter $winLetter
        Format-Volume -Partition $winPart -FileSystem NTFS -NewFileSystemLabel "Windows" -Confirm:$false | Out-Null

        Write-Host "      Mounted partitions: EFI=${efiLetter}: | Windows=${winLetter}:" -ForegroundColor Green

        # 3. Apply Windows 11 Image with /Compact (CompactOS LZX from boot 0)
        Write-Host "`n[Step 3/6] Applying Windows 11 image via DISM (/Compact LZX)..." -ForegroundColor Yellow
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        & dism.exe /Apply-Image /ImageFile:"$wimPath" /Index:$($selected.ImageIndex) /ApplyDir:"${winLetter}:\" /Compact
        if ($LASTEXITCODE -ne 0) { throw "DISM /Apply-Image failed with exit code $LASTEXITCODE" }
        $sw.Stop()
        Write-Host "      [+] Image applied with CompactOS in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s." -ForegroundColor Green

        # 4. Install UEFI Bootloader
        Write-Host "`n[Step 4/6] Installing UEFI bootloader (bcdboot)..." -ForegroundColor Yellow
        & bcdboot.exe "${winLetter}:\Windows" /s "${efiLetter}:" /f UEFI
        if ($LASTEXITCODE -ne 0) { throw "bcdboot failed with exit code $LASTEXITCODE" }
        Write-Host "      [+] UEFI bootloader installed." -ForegroundColor Green
    }

    # 5. Offline Pre-Debloat (best-effort via dism.exe; online bake_win11_agent_lean.ps1 also enforces full strip)
    Write-Host "`n[Step 5/6] Stripping non-agent Optional Features offline via dism.exe..." -ForegroundColor Yellow
    $offlineFeatures = @(
        'Recall',
        'Printing-Foundation-Features',
        'Printing-Foundation-InternetPrinting-Client',
        'Printing-PrintToPDFServices-Features',
        'Printing-XPSServices-Features',
        'FaxServicesClientPackage',
        'MediaPlayback',
        'WindowsMediaPlayer',
        'WorkFolders-Client',
        'MSRDC-Infrastructure'
    )
    $disabledFeat = 0
    foreach ($feat in $offlineFeatures) {
        & dism.exe /Image:"${winLetter}:\" /Disable-Feature /FeatureName:$feat /Remove /Quiet /NoRestart 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $disabledFeat++ }
    }
    Write-Host "      [+] Disabled $disabledFeat non-agent Optional Features offline (AppX bloat will be stripped online inside guest)." -ForegroundColor Green

    # 6. Inject Zero-OOBE Unattend.xml + SetupComplete.cmd
    Write-Host "`n[Step 6/6] Injecting zero-OOBE Unattend.xml + SetupComplete.cmd (activating Administrator for '$CredentialTarget')..." -ForegroundColor Yellow
    $pantherDir = "${winLetter}:\Windows\Panther"
    $scriptsDir = "${winLetter}:\Windows\Setup\Scripts"
    New-Item -ItemType Directory -Path $pantherDir -Force | Out-Null
    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null

    $unattendXml = @"
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>MXC-WIN11-AGENT</ComputerName>
      <TimeZone>UTC</TimeZone>
    </component>
    <component name="Microsoft-Windows-TerminalServices-LocalSessionManager" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <fDenyTSConnections>false</fDenyTSConnections>
    </component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <InputLocale>en-US</InputLocale>
      <SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage>
      <UserLocale>en-US</UserLocale>
    </component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <OOBE>
        <HideEULAPage>true</HideEULAPage>
        <HideLocalAccountScreen>true</HideLocalAccountScreen>
        <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
        <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
        <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
        <ProtectYourPC>3</ProtectYourPC>
        <SkipMachineOOBE>true</SkipMachineOOBE>
        <SkipUserOOBE>true</SkipUserOOBE>
      </OOBE>
      <UserAccounts>
        <AdministratorPassword>
          <Value>$adminPassXml</Value>
          <PlainText>true</PlainText>
        </AdministratorPassword>
      </UserAccounts>
      <AutoLogon>
        <Password>
          <Value>$adminPassXml</Value>
          <PlainText>true</PlainText>
        </Password>
        <Enabled>true</Enabled>
        <LogonCount>1</LogonCount>
        <Username>Administrator</Username>
      </AutoLogon>
    </component>
  </settings>
</unattend>
"@
    [System.IO.File]::WriteAllText("$pantherDir\Unattend.xml", $unattendXml, [System.Text.UTF8Encoding]::new($false))

    # SetupComplete.cmd ensures built-in Administrator is active, RDP/VMBus ready, and scrubs Unattend.xml
    $setupComplete = @"
@echo off
net user Administrator /active:yes
wmic useraccount where "Name='Administrator'" set PasswordExpires=FALSE
sc config vmicvmsession start= auto
net start vmicvmsession
del /f /q C:\Windows\Panther\Unattend.xml 2>nul
"@
    [System.IO.File]::WriteAllText("$scriptsDir\SetupComplete.cmd", $setupComplete, [System.Text.Encoding]::ASCII)

    Write-Host "      [+] Unattend.xml and SetupComplete.cmd injected cleanly." -ForegroundColor Green
} finally {
    if ($vhdMounted) {
        Dismount-VHD -Path $StagingVhdx -ErrorAction SilentlyContinue
        Write-Host "      Dismounted VHDX: $StagingVhdx" -ForegroundColor DarkGray
    }
    if ($isoMounted) {
        Dismount-DiskImage -ImagePath $IsoPath -ErrorAction SilentlyContinue
        Write-Host "      Dismounted ISO:  $IsoPath" -ForegroundColor DarkGray
    }
}

$freshSizeGB = [math]::Round((Get-Item $StagingVhdx).Length / 1GB, 2)
Write-Host "`n[+] Clean Windows 11 Base VHDX ready at $StagingVhdx ($freshSizeGB GB)!" -ForegroundColor Green

if (-not $SkipBake) {
    Write-Host "`nHanding off to bake_win11_agent_lean.ps1 -SkipStage (Core Agent Stack + Prompt Shell + Optimize-VHD)..." -ForegroundColor Cyan
    $bakeScript = Join-Path $PSScriptRoot "bake_win11_agent_lean.ps1"
    & $bakeScript -GoldenVhdx $StagingVhdx -StagingVhdx $StagingVhdx -OutputVhdx $ArchiveVhdx -CredentialTarget $CredentialTarget -SkipStage
}
