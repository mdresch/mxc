# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Guest-side Cursor CLI + My Machines worker setup for MXC Hyper-V sandboxes.

.DESCRIPTION
    Installs the Cursor agent CLI, registers a logon/startup scheduled task that runs
    `agent worker start`, and runs `agent worker debug`. Interactive `agent login` is
    required once unless -ApiKey is supplied (store the key in Windows Credential Manager
    target "cursor-mxc-agent-api-key" via the host script instead).

.PARAMETER WorkerName
    Friendly My Machines name (must match the Hyper-V VM suffix, e.g. mxc-hv-6b34439e).

.PARAMETER WorkerDir
    Git checkout registered with the worker (default C:\workspace).

.PARAMETER ApiKey
    Optional personal user API key for non-interactive worker start.

.PARAMETER RepoRemoteUrl
    Git remote registered with the worker. Required when mxc-sync mirrored the tree
    without .git (sync excludes .git by design).

.PARAMETER SkipScheduledTask
    Install CLI only; do not register the worker scheduled task.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkerName,

    [string]$WorkerDir = 'C:\workspace',

    [string]$ApiKey,

    [string]$RepoRemoteUrl = 'https://github.com/mdresch/mxc.git',

    [switch]$SkipScheduledTask
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
. (Join-Path $PSScriptRoot 'guest_git_for_windows.ps1')

function Test-AgentCli {
    $cmd = Get-Command agent -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $localApp = Join-Path $env:LOCALAPPDATA 'Programs\cursor-agent\agent.exe'
    if (Test-Path $localApp) { return $localApp }
    return $null
}

function Ensure-AgentCli {
    $existing = Test-AgentCli
    if ($existing) {
        Write-Host "Cursor agent CLI already present: $existing"
        return $existing
    }

    Write-Host 'Installing Cursor agent CLI...'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $installScript = Join-Path $env:TEMP 'install-cursor-agent.ps1'
    Invoke-WebRequest -Uri 'https://cursor.com/install?win32=true' -OutFile $installScript -UseBasicParsing
    & $installScript
    Remove-Item $installScript -Force -ErrorAction SilentlyContinue

    $path = Test-AgentCli
    if (-not $path) {
        throw 'Cursor agent CLI install finished but agent.exe was not found on PATH.'
    }
    Write-Host "Installed agent at: $path"
    return $path
}

function Resolve-WorkerApiKey {
    param([string]$InlineKey)

    if ($InlineKey) { return $InlineKey }

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class MxcCursorCred {
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr credPtr);
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr credPtr);
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct CREDENTIAL {
        public int Flags; public int Type; public string TargetName; public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public int CredentialBlobSize; public IntPtr CredentialBlob;
        public int Persist; public int AttributeCount; public IntPtr Attributes;
        public string TargetAlias; public string UserName;
    }
    public static string ReadPassword(string target) {
        IntPtr credPtr;
        if (!CredRead(target, 1, 0, out credPtr)) return null;
        try {
            var cred = (CREDENTIAL)Marshal.PtrToStructure(credPtr, typeof(CREDENTIAL));
            return Marshal.PtrToStringUni(cred.CredentialBlob, cred.CredentialBlobSize / 2);
        } finally { CredFree(credPtr); }
    }
}
'@ -ErrorAction SilentlyContinue

    return [MxcCursorCred]::ReadPassword('cursor-mxc-agent-api-key')
}

function Ensure-GuestGitRepo {
    param(
        [string]$Dir,
        [string]$RemoteUrl
    )

    if (Test-Path (Join-Path $Dir '.git')) {
        $existing = git -C $Dir config --get remote.origin.url 2>$null
        if (-not $existing -and $RemoteUrl) {
            git -C $Dir remote add origin $RemoteUrl
        }
        return
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'git is not on PATH in the guest. Run guest_bake_tools.ps1 or scoop install git first.'
    }

    Write-Host "mxc-sync omits .git; bootstrapping guest repo at $Dir with remote $RemoteUrl"
    Push-Location $Dir
    try {
        & git init
        & git branch -M main 2>$null
        & git remote add origin $RemoteUrl
        & git add -A
        & git -c user.email='mxc-hyperv@guest.local' -c user.name='MXC Hyper-V Guest' commit -m 'mxc-sync baseline' 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'No commit created (empty tree or commit failed); remote.origin is still registered.' -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $WorkerDir)) {
    throw "Worker directory not found: $WorkerDir. Run mxc-sync from the Hyper-V host first."
}

Ensure-GuestGitRepo -Dir $WorkerDir -RemoteUrl $RepoRemoteUrl
Ensure-GitBashForWorker

$agentExe = Ensure-AgentCli

$resolvedKey = Resolve-WorkerApiKey -InlineKey $ApiKey
$authMode = if ($resolvedKey) { 'api-key' } else { 'interactive-login-required' }

if (-not $SkipScheduledTask) {
    $taskName = 'MXC-Cursor-MyMachines-Worker'
    $logDir = Join-Path $env:ProgramData 'mxc\cursor-worker'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $runnerPath = Join-Path $logDir 'start-cursor-worker.cmd'

    $workerArgs = "worker start --name `"$WorkerName`" --worker-dir `"$WorkerDir`""
    if ($resolvedKey) {
        $workerArgs += " --api-key `"$resolvedKey`""
    }

    $agentLine = if ($agentExe -like '*.ps1') {
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$agentExe`" $workerArgs"
    } else {
        "`"$agentExe`" $workerArgs"
    }

    @"
@echo off
setlocal
cd /d "$WorkerDir"
echo [%DATE% %TIME%] Starting Cursor My Machines worker ($WorkerName) >> "$logDir\worker.log"
$agentLine >> "$logDir\worker.log" 2>&1
"@ | Set-Content -Path $runnerPath -Encoding ASCII

    $action = New-ScheduledTaskAction -Execute $runnerPath
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn
    $triggerBoot = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($triggerLogon, $triggerBoot) `
        -Settings $settings -User $env:USERNAME -RunLevel Limited -Force | Out-Null

    Write-Host "Registered scheduled task '$taskName' (logs: $logDir\worker.log)"
    if (-not $resolvedKey) {
        Write-Host 'No API key found. Open VMConnect, sign in with: agent login' -ForegroundColor Yellow
        Write-Host 'Or store a personal API key in Credential Manager target cursor-mxc-agent-api-key' -ForegroundColor Yellow
    } else {
        Write-Host 'Starting worker now (background)...' -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $taskName
    }
}

Write-Host "`n=== agent worker debug ===" -ForegroundColor Cyan
& $agentExe worker debug
Write-Host "`nAuth mode: $authMode" -ForegroundColor Cyan