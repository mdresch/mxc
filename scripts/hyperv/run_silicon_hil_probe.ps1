<#
.SYNOPSIS
    Read-only Hyper-V bare-metal host hardware capability probe (ADR-021, Story 20.1).
.DESCRIPTION
    Inspects local host hardware capabilities (Hyper-V host state, NUMA topology,
    partitionable GPU-P adapters, TPM / confidential computing indicators, and free RAM)
    and emits structured JSON to stdout. Strictly read-only: never creates, stops,
    suspends, or modifies any Hyper-V VM or VHDX file.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "SilentlyContinue"

$vmHost = Get-VMHost -ErrorAction SilentlyContinue
$hypervEnabled = $null -ne $vmHost

$numaNodes = @(Get-VMHostNumaNode -ErrorAction SilentlyContinue)
$numaNodeCount = if ($numaNodes.Count -gt 0) { [int]$numaNodes.Count } else { 0 }

$partitionableGpus = @(Get-VMHostPartitionableGpu -ErrorAction SilentlyContinue)
$gpupSupported = $partitionableGpus.Count -gt 0

$tpm = Get-Tpm -ErrorAction SilentlyContinue
$vtpmSupported = ($null -ne $tpm) -and ($tpm.TpmPresent -eq $true) -and ($tpm.TpmReady -eq $true)

# Conservative fail-closed check for hardware confidential VM enclaves (AMD SEV-SNP / Intel TDX).
$sevSnpOrTdxSupported = $false
if ($null -ne $vmHost) {
    $hostProps = $vmHost.PSObject.Properties.Name
    if ($hostProps -contains "ConfidentialComputingSupported" -and $vmHost.ConfidentialComputingSupported -eq $true) {
        $sevSnpOrTdxSupported = $true
    }
}

$ramdiskAvailableMb = 0
$osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($null -ne $osInfo -and $null -ne $osInfo.FreePhysicalMemory) {
    # FreePhysicalMemory is reported in KiB; reserve a conservative 25% cap for RAM-disk reporting.
    $freeMb = [math]::Floor(([double]$osInfo.FreePhysicalMemory) / 1024.0)
    $ramdiskAvailableMb = [int][math]::Max(0, [math]::Floor($freeMb * 0.25))
}

$payload = [ordered]@{
    hyperv_enabled           = [bool]$hypervEnabled
    numa_node_count          = [int]$numaNodeCount
    vtpm_supported           = [bool]$vtpmSupported
    sev_snp_or_tdx_supported = [bool]$sevSnpOrTdxSupported
    gpup_supported           = [bool]$gpupSupported
    ramdisk_available_mb     = [int]$ramdiskAvailableMb
    hostname                 = $env:COMPUTERNAME
    probed_at_utc            = (Get-Date).ToUniversalTime().ToString("o")
}

$payload | ConvertTo-Json -Depth 4
