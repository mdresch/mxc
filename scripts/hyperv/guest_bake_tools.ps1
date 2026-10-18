# Guest-side toolchain provisioning script executed via PowerShell Direct
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$shimPath = Join-Path $HOME 'scoop\shims'
$cargoPath = Join-Path $HOME '.cargo\bin'
$localPath = Join-Path $HOME '.local\bin'
$pythonScripts = Join-Path $HOME 'scoop\apps\python\current\Scripts'
$env:Path = "$shimPath;$cargoPath;$localPath;$pythonScripts;$env:Path"

Write-Host "=========================================="
Write-Host "  Guest-Side Toolchain Baking Initiated   "
Write-Host "=========================================="

# 1. Verify Scoop
if (-not (Test-Path "$HOME\scoop\shims\scoop.ps1")) {
    Write-Host "[1/7] Installing Scoop package manager..."
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    irm -useb get.scoop.sh -outfile "$env:TEMP\install-scoop.ps1"
    & "$env:TEMP\install-scoop.ps1" -RunAsAdmin
} else {
    Write-Host "[1/7] Scoop is already installed."
}

# 2. Ensure Buckets
Write-Host "`n[2/7] Configuring Scoop buckets..."
& scoop bucket add extras 2>$null
& scoop bucket add main 2>$null

# 3. Core CLI utilities
Write-Host "`n[3/7] Installing core utilities (git, gh, 7zip, pwsh, ripgrep, fd, jq)..."
& scoop install git gh 7zip pwsh ripgrep fd jq

# 4. Language Toolchains
Write-Host "`n[4/7] Installing language runtimes (Node.js, Bun, Python, uv, .NET, pnpm)..."
& scoop install nodejs-lts bun python uv dotnet-sdk pnpm

# Rust toolchain configuration
if (Get-Command rustup -ErrorAction SilentlyContinue) {
    Write-Host "Configuring Rust MSVC toolchain..."
    & rustup default stable-x86_64-pc-windows-msvc
    Write-Host "Installing cargo-nextest..."
    & cargo install cargo-nextest
}

# 5. Global Tooling (TypeScript, linters & libraries)
Write-Host "`n[5/7] Installing global JS & Python tooling..."
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Installing npm global packages (typescript, ts-node, tsx, eslint, prettier)..."
    & npm install -g typescript ts-node tsx eslint prettier
}
if (Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Host "Installing core Python agent libraries (requests, pydantic, mcp, httpx)..."
    & pip install --no-warn-script-location requests pydantic mcp httpx
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "Installing Python ruff via uv..."
    & uv tool install ruff
}

# 6. Pre-cache Headless Browser Runtime (Playwright)
Write-Host "`n[6/7] Pre-installing Playwright Chromium runtime for UI tests..."
& npx playwright install chromium

# 7. Machine PATH & Windows Defender Exclusions
Write-Host "`n[7/7] Configuring Machine PATH & Defender exclusions..."
$targetDirs = @(
    $shimPath,
    $cargoPath,
    $localPath,
    $pythonScripts,
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
