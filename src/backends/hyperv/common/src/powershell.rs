// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Shells out to `powershell.exe` to drive the Hyper-V PowerShell module.
//!
//! No WMI v2 / HCS native bindings yet — see the backend doc's "future
//! optimization" note. Every call uses `-NoProfile -NonInteractive
//! -ExecutionPolicy Bypass` so host profile scripts and interactive prompts
//! can never affect or block a call.

use std::io::Write;
use std::process::{Command, Stdio};

use serde::de::DeserializeOwned;

use crate::error::PowerShellError;

fn base_command() -> Command {
    let mut cmd = Command::new("powershell.exe");
    cmd.args([
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
    ]);
    cmd
}

/// Run a PowerShell script, returning its trimmed stdout. A non-zero exit
/// code is reported as [`PowerShellError::NonZeroExit`] carrying stderr.
pub fn run_powershell(script: &str) -> Result<String, PowerShellError> {
    let mut cmd = base_command();
    cmd.arg(script);
    cmd.stdin(Stdio::null());
    let output = cmd.output().map_err(PowerShellError::SpawnFailed)?;
    if !output.status.success() {
        return Err(PowerShellError::NonZeroExit {
            exit_code: output.status.code(),
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        });
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// Run a PowerShell script and decode its stdout as JSON. The script itself
/// must pipe through `ConvertTo-Json` — callers choose `-Depth`/`-AsArray`
/// per their own single-vs-collection shape, so this function does not append
/// one.
pub fn run_powershell_json<T: DeserializeOwned>(script: &str) -> Result<T, PowerShellError> {
    let stdout = run_powershell(script)?;
    serde_json::from_str(&stdout).map_err(PowerShellError::JsonDecode)
}

/// Run a PowerShell script, writing `stdin_bytes` then closing stdin, with
/// stdout/stderr captured (not relayed). Used to hand a secret to a script
/// without ever placing it on the command line or in the script text.
pub fn run_powershell_with_stdin(
    script: &str,
    stdin_bytes: &[u8],
) -> Result<String, PowerShellError> {
    let mut cmd = base_command();
    cmd.arg(script);
    cmd.stdin(Stdio::piped());
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());
    let mut child = cmd.spawn().map_err(PowerShellError::SpawnFailed)?;
    {
        let mut stdin = child.stdin.take().expect("stdin was configured as piped");
        stdin
            .write_all(stdin_bytes)
            .map_err(PowerShellError::SpawnFailed)?;
    }
    let output = child
        .wait_with_output()
        .map_err(PowerShellError::SpawnFailed)?;
    if !output.status.success() {
        return Err(PowerShellError::NonZeroExit {
            exit_code: output.status.code(),
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        });
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// Run a PowerShell script with inherited stdout/stderr (the child writes
/// directly to this process's own console) after writing `stdin_bytes` and
/// closing stdin — the `ExecStdio::Relayed` exec path, so guest output
/// streams live without this process ever buffering or parsing it.
pub fn run_powershell_relayed_with_stdin(
    script: &str,
    stdin_bytes: &[u8],
) -> Result<i32, PowerShellError> {
    let mut cmd = base_command();
    cmd.arg(script);
    cmd.stdin(Stdio::piped());
    cmd.stdout(Stdio::inherit());
    cmd.stderr(Stdio::inherit());
    let mut child = cmd.spawn().map_err(PowerShellError::SpawnFailed)?;
    {
        let mut stdin = child.stdin.take().expect("stdin was configured as piped");
        stdin
            .write_all(stdin_bytes)
            .map_err(PowerShellError::SpawnFailed)?;
    }
    let status = child.wait().map_err(PowerShellError::SpawnFailed)?;
    Ok(status.code().unwrap_or(-1))
}

/// Kill a previously-spawned relayed call by PID — used by the exec timeout
/// watchdog. Best-effort: logged by the caller, never panics.
#[cfg(windows)]
pub fn kill_process(pid: u32) -> std::io::Result<()> {
    use std::process::Command as StdCommand;
    StdCommand::new("taskkill.exe")
        .args(["/PID", &pid.to_string(), "/T", "/F"])
        .output()
        .map(|_| ())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(windows)]
    fn run_powershell_captures_stdout() {
        let out = run_powershell("Write-Output 'hello'").expect("powershell should run");
        assert_eq!(out, "hello");
    }

    #[test]
    #[cfg(windows)]
    fn run_powershell_reports_nonzero_exit() {
        let err = run_powershell("exit 7").expect_err("exit 7 should be reported as an error");
        match err {
            PowerShellError::NonZeroExit { exit_code, .. } => assert_eq!(exit_code, Some(7)),
            other => panic!("expected NonZeroExit, got {other:?}"),
        }
    }

    #[test]
    #[cfg(windows)]
    fn run_powershell_json_decodes_output() {
        let v: serde_json::Value =
            run_powershell_json("@{ a = 1 } | ConvertTo-Json -Compress").unwrap();
        assert_eq!(v["a"], 1);
    }
}
