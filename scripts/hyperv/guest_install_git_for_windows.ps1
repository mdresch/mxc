# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
<#
.SYNOPSIS
    Install Git for Windows (Git Bash) in an MXC Hyper-V guest for Cursor My Machines workers.
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'guest_git_for_windows.ps1')
Ensure-GitBashForWorker
Write-Host 'In the guest, run: agent worker start --name mxc-hv-6b34439e --worker-dir C:\workspace'