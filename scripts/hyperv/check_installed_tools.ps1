$ErrorActionPreference = 'Continue'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\mxc-hyperv.ps1"

$probeScript = @'
$shimPath = Join-Path $HOME 'scoop\shims'
$cargoPath = Join-Path $HOME '.cargo\bin'
$localPath = Join-Path $HOME '.local\bin'
$env:Path = "$shimPath;$cargoPath;$localPath;$env:Path"

Write-Host "=== Installed Toolchain Audit ==="
Write-Host "Node.js:   $(node -v 2>$null)"
Write-Host "Bun:       $(bun -v 2>$null)"
Write-Host "Git:       $(git --version 2>$null)"
Write-Host "Ripgrep:   $(rg --version 2>$null | Select-Object -First 1)"
Write-Host "Python uv: $(uv --version 2>$null)"
Write-Host "Ruff:      $(ruff --version 2>$null)"
Write-Host "Rustc:     $(rustc --version 2>$null)"
Write-Host "Cargo:     $(cargo --version 2>$null)"
Write-Host "Dotnet:    $(dotnet --version 2>$null)"
Write-Host "TSX:       $(tsx --version 2>$null)"
Write-Host "ESLint:    $(eslint -v 2>$null)"
Write-Host "Prettier:  $(prettier -v 2>$null)"
'@

$sb = Get-MxcActiveSandboxId
mxc-exec-ps -SandboxId $sb $probeScript
