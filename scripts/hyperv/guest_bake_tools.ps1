# Guest-side toolchain provisioning script executed via PowerShell Direct
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$shimPath = Join-Path $HOME 'scoop\shims'
$cargoPath = Join-Path $HOME '.cargo\bin'
$localPath = Join-Path $HOME '.local\bin'
$env:Path = "$shimPath;$cargoPath;$localPath;$env:Path"

Write-Host "=========================================="
Write-Host "  Guest-Side Toolchain Baking Initiated   "
Write-Host "=========================================="

# 1. Verify Scoop
if (-not (Test-Path "$HOME\scoop\shims\scoop.ps1")) {
    Write-Host "[1/6] Installing Scoop package manager..."
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    irm -useb get.scoop.sh -outfile "$env:TEMP\install-scoop.ps1"
    & "$env:TEMP\install-scoop.ps1" -RunAsAdmin
} else {
    Write-Host "[1/6] Scoop is already installed."
}

# 2. Ensure Buckets
Write-Host "`n[2/6] Configuring Scoop buckets..."
& scoop bucket add extras 2>$null
& scoop bucket add main 2>$null

# 3. Core CLI utilities
Write-Host "`n[3/6] Installing core utilities..."
& scoop install git 7zip pwsh ripgrep fd jq

# 4. Language Toolchains
Write-Host "`n[4/6] Installing language runtimes & compilers..."
& scoop install nodejs-lts bun uv dotnet-sdk pnpm

# Rust toolchain configuration
if (Get-Command rustup -ErrorAction SilentlyContinue) {
    Write-Host "Configuring Rust MSVC toolchain..."
    & rustup default stable-x86_64-pc-windows-msvc
    Write-Host "Installing cargo-nextest..."
    & cargo install cargo-nextest
}

# 5. Global Tooling (linters & runners)
Write-Host "`n[5/6] Installing global JS & Python tooling..."
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Installing npm global packages (tsx, eslint, prettier)..."
    & npm install -g tsx eslint prettier
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Installing Python ruff via uv..."
    & uv tool install ruff
}

# 6. Machine PATH & Windows Defender Exclusions
Write-Host "`n[6/6] Configuring Machine PATH & Defender exclusions..."
$targetDirs = @(
    $shimPath,
    $cargoPath,
    $localPath,
    "C:\Program Files\dotnet"
)
$currPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$parts = $currPath -split ';'
foreach ($d in $targetDirs) {
    if ($d -notin $parts) {
        $currPath = "$d;$currPath"
    }
}
[Environment]::SetEnvironmentVariable("Path", $currPath, "Machine")

Add-MpPreference -ExclusionPath @(
    'C:\workspace',
    'C:\Tools',
    (Join-Path $HOME '.cargo'),
    (Join-Path $HOME '.pnpm-store'),
    (Join-Path $HOME 'scoop'),
    (Join-Path $HOME '.local')
) -ErrorAction SilentlyContinue

Write-Host "=========================================="
Write-Host "  Golden Image Provisioning Completed!    "
Write-Host "=========================================="

