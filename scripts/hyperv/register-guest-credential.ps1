# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

<#
.SYNOPSIS
    Registers or manages a guest VM credential in the Windows Credential Manager for Hyper-V PowerShell Direct.

.DESCRIPTION
    The MXC Hyper-V backend uses PowerShell Direct to execute commands inside guest
    virtual machines over the Hyper-V VMBus without requiring a guest network connection.
    To authenticate against the guest VM, the JSON request provides a target name
    (via `hyperv.provision.guestCredentialTarget`). The actual secret is never placed
    in request payloads, logs, or command-line arguments. Instead, the runtime reads the
    generic credential directly from the Windows Credential Manager using the Win32
    CredReadW API.

    This script provides an operator-friendly helper to register, inspect, or delete
    the guest credential in the Windows Credential Manager using `cmdkey.exe`.

.PARAMETER Target
    The generic credential target name that matches the `guestCredentialTarget`
    field in the MXC Hyper-V provisioning configuration (e.g., "mxc-guest" or
    "mxc-hyperv-worker").

.PARAMETER Username
    The guest operating system account username (e.g., "Administrator" or "GuestAdmin").
    Required when adding or updating a credential.

.PARAMETER Password
    The plaintext password for the guest account. If omitted when adding a credential,
    the script securely prompts for the password using `Read-Host -AsSecureString`.

.PARAMETER Delete
    Removes the specified target credential from the Windows Credential Manager.

.PARAMETER Check
    Verifies whether a credential exists for the specified target.

.EXAMPLE
    .\register-guest-credential.ps1 -Target "mxc-guest" -Username "Administrator"
    Prompts interactively for the password and registers the generic credential.

.EXAMPLE
    .\register-guest-credential.ps1 -Target "mxc-guest" -Username "Administrator" -Password "SecretPass123!"
    Registers the generic credential non-interactively.

.EXAMPLE
    .\register-guest-credential.ps1 -Target "mxc-guest" -Check
    Checks if a credential for target "mxc-guest" is stored in the Credential Manager.

.EXAMPLE
    .\register-guest-credential.ps1 -Target "mxc-guest" -Delete
    Deletes the credential for target "mxc-guest".
#>

[CmdletBinding(DefaultParameterSetName = "Set")]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Target,

    [Parameter(Mandatory = $true, ParameterSetName = "Set", Position = 1)]
    [ValidateNotNullOrEmpty()]
    [string]$Username,

    [Parameter(Mandatory = $false, ParameterSetName = "Set")]
    [string]$Password,

    [Parameter(Mandatory = $true, ParameterSetName = "Delete")]
    [switch]$Delete,

    [Parameter(Mandatory = $true, ParameterSetName = "Check")]
    [switch]$Check
)

$ErrorActionPreference = "Stop"

if ($Check) {
    Write-Host "Checking Windows Credential Manager for target: $Target"
    & cmdkey.exe /list:$Target
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Credential found for target '$Target'." -ForegroundColor Green
    } else {
        Write-Warning "No credential found for target '$Target'."
    }
    exit $LASTEXITCODE
}

if ($Delete) {
    Write-Host "Deleting credential for target: $Target"
    & cmdkey.exe /delete:$Target
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Credential for target '$Target' successfully deleted." -ForegroundColor Green
    } else {
        Write-Error "Failed to delete credential for target '$Target'."
    }
    exit $LASTEXITCODE
}

# ParameterSetName is "Set"
$plainPassword = $Password
if ([string]::IsNullOrEmpty($plainPassword)) {
    $secPass = Read-Host -Prompt "Enter password for guest user '$Username'" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secPass)
    try {
        $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

Write-Host "Registering generic credential in Windows Credential Manager..."
Write-Host "  Target:   $Target"
Write-Host "  Username: $Username"

# Invoke cmdkey to store the generic credential
& cmdkey.exe /generic:$Target /user:$Username /pass:$plainPassword

if ($LASTEXITCODE -eq 0) {
    Write-Host "Credential registered successfully." -ForegroundColor Green
    Write-Host "You can now use '$Target' in 'hyperv.provision.guestCredentialTarget'."
} else {
    Write-Error "cmdkey.exe failed with exit code $LASTEXITCODE."
}
exit $LASTEXITCODE

