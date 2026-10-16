# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

<#
.SYNOPSIS
    Capture a high-fidelity PNG screenshot of an MXC Hyper-V guest VM directly from the host.

.DESCRIPTION
    Leverages Hyper-V WMI (GetVirtualSystemThumbnailImage) to read the synthetic video
    head framebuffer (RGB 565) without requiring guest agents or guest network access.
    Supports auto-detecting native VM resolution, custom dimensions, and JSON/Base64 output.
#>

param(
    [string]$VmName = "mxc-hv-a7df7452",
    [int]$Width = 0,
    [int]$Height = 0,
    [string]$OutputPath = "",
    [switch]$IncludeBase64,
    [switch]$Open
)

# Normalize VM name from sandbox ID (e.g. hv:a7df7452 -> mxc-hv-a7df7452)
if ($VmName -like "hv:*") {
    $token = $VmName.Substring(3).Trim()
    $VmName = "mxc-hv-$token"
} elseif ($VmName -notlike "mxc-hv-*") {
    $VmName = "mxc-hv-$VmName"
}

$vm = Get-CimInstance -Namespace 'root\virtualization\v2' -ClassName Msvm_ComputerSystem | Where-Object ElementName -eq $VmName
if (-not $vm) {
    $errObj = @{ success = $false; error = "VM '$VmName' not found in Hyper-V" }
    $errObj | ConvertTo-Json -Compress
    exit 1
}

# Auto-detect resolution if not specified
$video = Get-CimAssociatedInstance -InputObject $vm -ResultClassName Msvm_VideoHead | Select-Object -First 1
$w = if ($Width -gt 0) { [uint16]$Width } elseif ($video -and $video.CurrentHorizontalResolution) { [uint16]$video.CurrentHorizontalResolution } else { [uint16]1024 }
$h = if ($Height -gt 0) { [uint16]$Height } elseif ($video -and $video.CurrentVerticalResolution) { [uint16]$video.CurrentVerticalResolution } else { [uint16]768 }

$settings = Get-CimAssociatedInstance -InputObject $vm -ResultClassName Msvm_VirtualSystemSettingData | Where-Object VirtualSystemType -like '*SubType*'
if (-not $settings) {
    $settings = Get-CimAssociatedInstance -InputObject $vm -ResultClassName Msvm_VirtualSystemSettingData | Select-Object -First 1
}

$svc = Get-CimInstance -Namespace 'root\virtualization\v2' -ClassName Msvm_VirtualSystemManagementService
$res = Invoke-CimMethod -InputObject $svc -MethodName GetVirtualSystemThumbnailImage -Arguments @{
    TargetSystem = $settings
    WidthPixels = $w
    HeightPixels = $h
}

if ($res.ReturnValue -ne 0 -or -not $res.ImageData) {
    $errObj = @{ success = $false; error = "GetVirtualSystemThumbnailImage failed with ReturnValue: $($res.ReturnValue)" }
    $errObj | ConvertTo-Json -Compress
    exit 1
}

Add-Type -AssemblyName System.Drawing

$rawBytes = $res.ImageData
$expectedPixelsBytes = [int]$w * [int]$h * 2
$offset = 0

# Account for the 4-byte resolution header present in Hyper-V WMI v2
if ($rawBytes.Length -ge ($expectedPixelsBytes + 4)) {
    $offset = 4
}

# Check for blank / power-save framebuffer
$isPowerSave = $video.Availability -eq 6

$intW = [int]$w
$intH = [int]$h
$bmp = New-Object System.Drawing.Bitmap($intW, $intH, [System.Drawing.Imaging.PixelFormat]::Format16bppRgb565)
$rect = New-Object System.Drawing.Rectangle(0, 0, $intW, $intH)
$bmpData = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadWrite, $bmp.PixelFormat)
[System.Runtime.InteropServices.Marshal]::Copy($rawBytes, $offset, $bmpData.Scan0, $expectedPixelsBytes)
$bmp.UnlockBits($bmpData)

# Determine output file path
if (-not $OutputPath) {
    $screenshotsDir = Join-Path $PSScriptRoot "screenshots"
    if (-not (Test-Path $screenshotsDir)) {
        New-Item -ItemType Directory -Path $screenshotsDir -Force | Out-Null
    }
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = Join-Path $screenshotsDir "screenshot_${VmName}_${timestamp}.png"
} else {
    $outDir = Split-Path -Parent $OutputPath
    if ($outDir -and -not (Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }
}

$bmp.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

$b64 = $null
if ($IncludeBase64) {
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    $b64 = [Convert]::ToBase64String($ms.ToArray())
    $ms.Dispose()
}

$bmp.Dispose()

$fileInfo = Get-Item $OutputPath

$result = [ordered]@{
    success = $true
    path = $OutputPath
    width = [int]$w
    height = [int]$h
    fileSizeBytes = $fileInfo.Length
    vmName = $VmName
    isPowerSave = $isPowerSave
}

if ($b64) {
    $result["base64"] = $b64
}

$result | ConvertTo-Json -Compress

if ($Open) {
    Start-Process $OutputPath
}
