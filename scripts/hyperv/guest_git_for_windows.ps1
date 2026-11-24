# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# Shared helpers: Git for Windows + Git Bash (required by Cursor My Machines worker).

function Get-GitBashPath {
    @(
        (Join-Path ${env:ProgramFiles} 'Git\bin\bash.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Git\bin\bash.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Git\bin\bash.exe')
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Install-GitForWindows {
    Write-Host 'Installing Git for Windows (required by Cursor worker)...' -ForegroundColor Cyan
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        $wingetArgs = @(
            'install', '--id', 'Git.Git', '-e',
            '--accept-source-agreements', '--accept-package-agreements',
            '--disable-interactivity'
        )
        & winget @wingetArgs
        if ($LASTEXITCODE -in 0, -1978335189) { return }
    }

    $installer = Join-Path $env:TEMP 'Git-64-bit.exe'
    $releaseUrl = 'https://api.github.com/repos/git-for-windows/git/releases/latest'
    try {
        $release = Invoke-RestMethod -Uri $releaseUrl -UseBasicParsing
        $asset = $release.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
        if (-not $asset) { throw 'No Git for Windows 64-bit installer asset found.' }
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installer -UseBasicParsing
    } catch {
        $fallback = 'https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/Git-2.47.1.2-64-bit.exe'
        Invoke-WebRequest -Uri $fallback -OutFile $installer -UseBasicParsing
    }

    $proc = Start-Process -FilePath $installer -ArgumentList '/VERYSILENT', '/NORESTART', '/NOCANCEL', '/SP-' -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "Git for Windows installer exited with code $($proc.ExitCode)."
    }
}

function Ensure-GitBashForWorker {
    $bash = Get-GitBashPath
    if ($bash) {
        Write-Host "Git Bash found: $bash"
        return
    }

    Install-GitForWindows

    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"

    $bash = Get-GitBashPath
    if (-not $bash) {
        throw 'Git Bash is still missing after install. Install Git for Windows from https://git-scm.com/download/win (include Git Bash), then retry agent worker start.'
    }
    Write-Host "Git Bash ready: $bash" -ForegroundColor Green
}