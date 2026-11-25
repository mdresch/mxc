<#
.SYNOPSIS
    Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer (ADR-022, Epic 021).
.DESCRIPTION
    Zero-cloud single-host pilot installer wrapper for Windows 11 Pro and Windows Server 2025.
    Performs strictly offline preflight checks, SHA-256 manifest verification via
    Get-FileHash -Algorithm SHA256, golden parent VHDX digest verification, and gates completion
    on the unattended <= 15 minute 5-Act Hardware-in-the-Loop self-test
    (scripts/hyperv/demo_win11_agent_sandbox.ps1) with zero outbound internet calls.
.PARAMETER BundleDir
    Directory containing mxc-embed-manifest.json and all vendored offline pilot artifacts.
.PARAMETER GoldenVhdxPath
    Absolute path to the golden parent VHDX image referenced by golden_vhdx_sha256.
.PARAMETER DryRun
    Validate offline manifest, artifact SHA-256 digests, golden VHDX digest, and host preflight
    without modifying Hyper-V configuration or launching the 5-Act HIL VM self-test.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundleDir,

    [Parameter(Mandatory = $false)]
    [string]$GoldenVhdxPath = "C:\HyperV\BaseImages\win11-agent-lean.vhdx",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$MaxInstallMinutes = 15.0
$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

function Fail-Closed {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Message
    )
    Write-Error "[$Code] $Message"
    exit 1
}

function Assert-Sha256Format {
    param([string]$Digest)
    return ($null -ne $Digest) -and ($Digest -match '^[0-9a-fA-F]{64}$')
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  MXC EMBED SOVEREIGN OFFLINE PILOT INSTALLER (ADR-022 / ZERO-CLOUD)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Offline bundle directory and manifest presence
if (-not (Test-Path -LiteralPath $BundleDir -PathType Container)) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "BundleDir not found: '$BundleDir'."
}

$ManifestPath = Join-Path -Path $BundleDir -ChildPath "mxc-embed-manifest.json"
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Manifest not found: '$ManifestPath'."
}

try {
    $Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Failed to parse mxc-embed-manifest.json: $($_.Exception.Message)"
}

if ($Manifest.offline_only -ne $true) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Manifest must declare offline_only=true."
}

if ([string]::IsNullOrWhiteSpace($Manifest.bundle_version)) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Manifest bundle_version is missing or blank."
}

if (-not (Assert-Sha256Format -Digest $Manifest.golden_vhdx_sha256)) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Manifest golden_vhdx_sha256 is not a valid 64-hex SHA-256 digest."
}

# 2. Verify all vendored bundle artifacts via SHA-256 (zero network calls)
$ArtifactProps = @($Manifest.artifacts.PSObject.Properties)
if ($ArtifactProps.Count -eq 0) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Manifest artifacts map is empty."
}

$VerifiedCount = 0
foreach ($Prop in $ArtifactProps) {
    $RelPath = $Prop.Name
    $ExpectedHash = [string]$Prop.Value

    if ([string]::IsNullOrWhiteSpace($RelPath) -or $RelPath.Contains("..") -or [System.IO.Path]::IsPathRooted($RelPath)) {
        Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Unsafe relative artifact path in manifest: '$RelPath'."
    }
    if (-not (Assert-Sha256Format -Digest $ExpectedHash)) {
        Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Malformed SHA-256 digest in manifest for '$RelPath'."
    }

    $FullPath = Join-Path -Path $BundleDir -ChildPath $RelPath
    if (-not (Test-Path -LiteralPath $FullPath -PathType Leaf)) {
        Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Missing vendored bundle artifact: '$RelPath'."
    }

    $ActualHash = (Get-FileHash -LiteralPath $FullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHash.ToLowerInvariant()) {
        Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "SHA-256 mismatch for '$RelPath' (expected $($ExpectedHash.ToLowerInvariant()), got $ActualHash)."
    }
    $VerifiedCount++
}
Write-Host "[OK] Verified $VerifiedCount vendored offline bundle artifact(s) for version '$($Manifest.bundle_version)'." -ForegroundColor Green

# 3. Verify Golden Parent VHDX presence and SHA-256 digest
if (-not (Test-Path -LiteralPath $GoldenVhdxPath -PathType Leaf)) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Golden parent VHDX not found: '$GoldenVhdxPath'."
}

$ParentHashBefore = (Get-FileHash -LiteralPath $GoldenVhdxPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ParentHashBefore -ne $Manifest.golden_vhdx_sha256.ToLowerInvariant()) {
    Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "Golden VHDX SHA-256 mismatch (expected $($Manifest.golden_vhdx_sha256.ToLowerInvariant()), got $ParentHashBefore)."
}
Write-Host "[OK] Verified Golden Parent VHDX SHA-256: $ParentHashBefore" -ForegroundColor Green

# 4. Locate post-install 5-Act HIL self-test hook
$SelfTestScript = Join-Path -Path $PSScriptRoot -ChildPath "demo_win11_agent_sandbox.ps1"
if (-not (Test-Path -LiteralPath $SelfTestScript -PathType Leaf)) {
    $BundledSelfTest = Join-Path -Path $BundleDir -ChildPath "scripts\hyperv\demo_win11_agent_sandbox.ps1"
    if (Test-Path -LiteralPath $BundledSelfTest -PathType Leaf) {
        $SelfTestScript = $BundledSelfTest
    } else {
        Fail-Closed -Code "ERR_BUNDLE_INTEGRITY_FAILED" -Message "5-Act HIL self-test script not found."
    }
}

# 5. DryRun short-circuit (zero Hyper-V mutation, zero VM starts)
if ($DryRun) {
    $ElapsedMin = [math]::Round($Stopwatch.Elapsed.TotalMinutes, 2)
    if ($ElapsedMin -gt $MaxInstallMinutes) {
        Fail-Closed -Code "ERR_INSTALL_BUDGET_EXCEEDED" -Message "DryRun exceeded $MaxInstallMinutes min budget ($ElapsedMin min)."
    }
    Write-Host "[DRY-RUN] Zero-cloud preflight and SHA-256 verification passed in $ElapsedMin min." -ForegroundColor Yellow
    Write-Host "[DRY-RUN] Planned 5-Act HIL self-test command: & '$SelfTestScript' -BaseImagePath '$GoldenVhdxPath'" -ForegroundColor Yellow
    exit 0
}

# 6. Execute unattended 5-Act HIL Self-Test Gate (ADR-022)
Write-Host "[GATE] Executing unattended 5-Act HIL self-test via '$SelfTestScript'..." -ForegroundColor Cyan
& $SelfTestScript -BaseImagePath $GoldenVhdxPath
if ($LASTEXITCODE -ne 0) {
    Fail-Closed -Code "ERR_HIL_ACT_FAILED" -Message "5-Act HIL self-test exited with code $LASTEXITCODE."
}

# 7. Assert bit-for-bit Golden Parent VHDX SHA-256 invariance & <= 15 min SLA budget
$ParentHashAfter = (Get-FileHash -LiteralPath $GoldenVhdxPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ParentHashAfter -ne $ParentHashBefore) {
    Fail-Closed -Code "ERR_PARENT_HASH_DRIFT" -Message "Golden parent VHDX hash drifted during 5-Act HIL self-test."
}

$TotalMinutes = [math]::Round($Stopwatch.Elapsed.TotalMinutes, 2)
if ($TotalMinutes -gt $MaxInstallMinutes) {
    Fail-Closed -Code "ERR_INSTALL_BUDGET_EXCEEDED" -Message "Install + 5-Act HIL self-test exceeded $MaxInstallMinutes min SLA ($TotalMinutes min)."
}

Write-Host "[OK] MXC Embed offline pilot install & 5-Act HIL self-test PASSED in $TotalMinutes min (0 outbound internet calls)." -ForegroundColor Green
exit 0
