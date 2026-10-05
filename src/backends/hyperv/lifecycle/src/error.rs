// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Maps `hyperv_common` errors to the wire `MxcError` model.

use hyperv_common::credential::CredentialError;
use hyperv_common::error::PowerShellError;
use wxc_common::mxc_error::MxcError;

/// Map a PowerShell/cmdlet failure to a backend error, tagging it with the
/// operation that was in flight for diagnosability.
pub fn map_powershell_error(context: &str, e: PowerShellError) -> MxcError {
    MxcError::backend_error(format!("{context}: {e}"))
}

/// Map a Credential Manager lookup failure. A missing credential is a
/// configuration problem the operator can fix (register it and retry), so it
/// maps to `policy_validation` rather than an opaque backend error.
pub fn map_credential_error(e: CredentialError) -> MxcError {
    match e {
        CredentialError::NotFound { .. } => MxcError::policy_validation(e.to_string()),
        CredentialError::ReadFailed { .. } => MxcError::backend_error(e.to_string()),
    }
}

/// Map a Hyper-V host-availability probe failure.
pub fn map_unavailable(reason: String) -> MxcError {
    MxcError::backend_unavailable(reason)
}
