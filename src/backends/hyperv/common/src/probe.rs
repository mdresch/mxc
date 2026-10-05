// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Hyper-V host-availability probing.

/// Confirm the Hyper-V Virtual Machine Management service is installed and
/// running. `Err` carries a human-readable reason suitable for a
/// `backend_unavailable` message.
#[cfg(windows)]
pub fn hyperv_available() -> Result<(), String> {
    use crate::powershell::run_powershell;

    match run_powershell("(Get-Service -Name vmms -ErrorAction SilentlyContinue).Status") {
        Ok(status) if status.trim() == "Running" => Ok(()),
        Ok(status) if status.trim().is_empty() => Err(
            "the Hyper-V Virtual Machine Management service (vmms) was not found; install the \
             Hyper-V Windows feature and reboot"
                .to_string(),
        ),
        Ok(status) => Err(format!(
            "the Hyper-V Virtual Machine Management service (vmms) is not running (status: \
             {status})"
        )),
        Err(e) => Err(format!("could not query the Hyper-V service: {e}")),
    }
}

/// Non-Windows stub: Hyper-V does not exist on this platform.
#[cfg(not(windows))]
pub fn hyperv_available() -> Result<(), String> {
    Err("Hyper-V is only available on Windows".to_string())
}

#[cfg(test)]
mod tests {
    use super::hyperv_available;

    #[test]
    #[cfg(not(windows))]
    fn unavailable_off_windows() {
        assert!(hyperv_available().is_err());
    }

    #[test]
    #[cfg(windows)]
    fn does_not_panic_on_windows() {
        // Host-dependent (Hyper-V may or may not be installed on the test
        // machine), so this only asserts the probe completes and returns a
        // well-formed `Result` rather than panicking.
        let _ = hyperv_available();
    }
}
