// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Guest credential resolution via the Windows Credential Manager.
//!
//! The JSON config carries only a free-form target name
//! (`hyperv.provision.guestCredentialTarget`); the operator registers the
//! actual secret once as an image-prep step via
//! `cmdkey /generic:<target> /user:<user> /pass:<pass>` (see
//! `scripts/hyperv/register-guest-credential.ps1`). The secret never appears
//! in a request, a log line, or a child process's command line — it is read
//! here via `CredReadW` and handed to callers only as owned, zeroize-on-drop
//! bytes.

use std::fmt;

/// A resolved guest credential.
///
/// `password_bytes()` returns the raw `CredentialBlob` as Credential Manager
/// stored it — for a `cmdkey`-created generic credential this is UTF-16LE,
/// which is why consumers that hand it to a PowerShell script decode it with
/// `[System.Text.Encoding]::Unicode.GetString(...)` rather than treating it
/// as UTF-8.
pub struct GuestCredential {
    pub username: String,
    password: Vec<u8>,
}

impl GuestCredential {
    pub fn password_bytes(&self) -> &[u8] {
        &self.password
    }
}

impl Drop for GuestCredential {
    fn drop(&mut self) {
        for b in self.password.iter_mut() {
            *b = 0;
        }
    }
}

impl fmt::Debug for GuestCredential {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("GuestCredential")
            .field("username", &self.username)
            .field("password", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub enum CredentialError {
    NotFound { target: String },
    ReadFailed { target: String, detail: String },
}

impl fmt::Display for CredentialError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound { target } => write!(
                f,
                "no stored credential found for target {target:?}; register it with `cmdkey \
                 /generic:{target} /user:<user> /pass:<pass>` (see the hyperv backend doc's \
                 image-prep prerequisites) before provisioning"
            ),
            Self::ReadFailed { target, detail } => {
                write!(
                    f,
                    "failed to read stored credential for target {target:?}: {detail}"
                )
            }
        }
    }
}

impl std::error::Error for CredentialError {}

#[cfg(windows)]
pub fn resolve_guest_credential(target: &str) -> Result<GuestCredential, CredentialError> {
    use windows::core::PCWSTR;
    use windows::Win32::Foundation::ERROR_NOT_FOUND;
    use windows::Win32::Security::Credentials::{
        CredFree, CredReadW, CREDENTIALW, CRED_TYPE_GENERIC,
    };

    let wide_target: Vec<u16> = target.encode_utf16().chain(std::iter::once(0)).collect();
    let mut raw: *mut CREDENTIALW = std::ptr::null_mut();

    // SAFETY: `wide_target` is a valid null-terminated UTF-16 buffer alive
    // for the duration of the call. `raw` is populated by `CredReadW` on
    // success and freed via `CredFree` before returning; the slice built from
    // `CredentialBlob`/`CredentialBlobSize` is copied into an owned `Vec`
    // before that free.
    unsafe {
        if let Err(e) = CredReadW(
            PCWSTR(wide_target.as_ptr()),
            CRED_TYPE_GENERIC,
            Some(0),
            &mut raw,
        ) {
            return Err(if e.code() == ERROR_NOT_FOUND.to_hresult() {
                CredentialError::NotFound {
                    target: target.to_string(),
                }
            } else {
                CredentialError::ReadFailed {
                    target: target.to_string(),
                    detail: e.to_string(),
                }
            });
        }

        let cred = &*raw;
        let username = if cred.UserName.is_null() {
            String::new()
        } else {
            cred.UserName.to_string().unwrap_or_default()
        };
        let password = if cred.CredentialBlob.is_null() || cred.CredentialBlobSize == 0 {
            Vec::new()
        } else {
            std::slice::from_raw_parts(cred.CredentialBlob, cred.CredentialBlobSize as usize)
                .to_vec()
        };

        CredFree(raw as *const _);

        Ok(GuestCredential { username, password })
    }
}

#[cfg(not(windows))]
pub fn resolve_guest_credential(target: &str) -> Result<GuestCredential, CredentialError> {
    Err(CredentialError::ReadFailed {
        target: target.to_string(),
        detail: "the Windows Credential Manager is only available on Windows".to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn debug_never_prints_the_password() {
        let cred = GuestCredential {
            username: "guestuser".to_string(),
            password: b"super-secret".to_vec(),
        };
        let rendered = format!("{cred:?}");
        assert!(rendered.contains("guestuser"));
        assert!(!rendered.contains("super-secret"));
        assert!(rendered.contains("<redacted>"));
    }

    #[test]
    #[cfg(not(windows))]
    fn unavailable_off_windows() {
        assert!(resolve_guest_credential("any-target").is_err());
    }

    #[test]
    fn not_found_error_mentions_cmdkey_remediation() {
        let err = CredentialError::NotFound {
            target: "mxc-hyperv:golden-image".to_string(),
        };
        let msg = err.to_string();
        assert!(msg.contains("cmdkey"));
        assert!(msg.contains("mxc-hyperv:golden-image"));
    }
}
