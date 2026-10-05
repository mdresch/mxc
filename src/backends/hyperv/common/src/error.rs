// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! PowerShell invocation errors. Independent of `MxcError` — mapping to the
//! wire error model happens in `hyperv_lifecycle`, which is the layer that
//! knows which phase/operation was in flight.

use std::fmt;

#[derive(Debug)]
pub enum PowerShellError {
    SpawnFailed(std::io::Error),
    NonZeroExit {
        exit_code: Option<i32>,
        stderr: String,
    },
    JsonDecode(serde_json::Error),
}

impl fmt::Display for PowerShellError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SpawnFailed(e) => write!(f, "failed to spawn powershell.exe: {e}"),
            Self::NonZeroExit { exit_code, stderr } => write!(
                f,
                "powershell.exe exited with {}: {}",
                exit_code
                    .map(|c| c.to_string())
                    .unwrap_or_else(|| "<unknown>".to_string()),
                stderr.trim()
            ),
            Self::JsonDecode(e) => write!(f, "failed to decode PowerShell JSON output: {e}"),
        }
    }
}

impl std::error::Error for PowerShellError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::SpawnFailed(e) => Some(e),
            Self::JsonDecode(e) => Some(e),
            Self::NonZeroExit { .. } => None,
        }
    }
}
