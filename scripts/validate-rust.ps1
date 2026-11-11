# Rust validation for MXC. Run from anywhere.
#
# Default: fmt, clippy -D warnings, and the full workspace test suite.
# That suite is the regression check. A non-zero cargo test exit fails this script.
#
# -Coverage also runs cargo-llvm-cov and fails when line coverage is under
# the floor (default 100). Install once with: cargo install cargo-llvm-cov
# Use -Coverage for a new crate or a story module that can meet the floor.
# The repository CI jobs fail on cargo test, not on a workspace-wide percentage.

[CmdletBinding()]
param(
    [switch]$Coverage,
    [int]$FailUnder = 100
)

$ErrorActionPreference = 'Stop'
$SrcDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'src'

Push-Location $SrcDir
try {
    Write-Host '== cargo fmt =='
    cargo fmt --all -- --check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host '== cargo clippy =='
    cargo clippy --workspace --all-targets -- -D warnings
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host '== cargo test =='
    cargo test --workspace
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if ($Coverage) {
        if (-not (Get-Command cargo-llvm-cov -ErrorAction SilentlyContinue)) {
            Write-Error 'cargo-llvm-cov is not installed. Install it with: cargo install cargo-llvm-cov'
        }
        Write-Host "== cargo llvm-cov (fail under $FailUnder% lines) =="
        cargo llvm-cov --workspace --fail-under-lines $FailUnder
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}
finally {
    Pop-Location
}
