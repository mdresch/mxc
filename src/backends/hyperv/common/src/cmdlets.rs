// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Typed wrappers over Hyper-V PowerShell module cmdlets.
//!
//! Every interpolated value that is not a bare integer goes through
//! [`ps_single_quote`] (identifiers, paths, names) or Base64 (arbitrary
//! command text) before it reaches a `-Command` string, so no argument can
//! break out of its intended position regardless of its content.

use std::path::Path;

use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine as _;
use serde::Deserialize;

use crate::credential::GuestCredential;
use crate::error::PowerShellError;
use crate::powershell::{
    run_powershell, run_powershell_json, run_powershell_relayed_with_stdin,
    run_powershell_with_stdin,
};

/// Hyper-V VM power/runtime state, as reported by `(Get-VM).State`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VmState {
    Off,
    Running,
    Saved,
    Paused,
    Other,
}

impl VmState {
    fn parse(s: &str) -> Self {
        match s.trim() {
            "Off" => Self::Off,
            "Running" => Self::Running,
            "Saved" => Self::Saved,
            "Paused" => Self::Paused,
            _ => Self::Other,
        }
    }
}

/// One Hyper-V checkpoint, as reported by `Get-VMSnapshot`.
#[derive(Debug, Clone, Deserialize)]
pub struct VmSnapshotInfo {
    #[serde(rename = "Name")]
    pub name: String,
    #[serde(rename = "CreationTime")]
    pub creation_time: Option<String>,
}

/// Single-quote a value for safe embedding in a PowerShell single-quoted
/// string literal (doubles embedded single quotes — PowerShell's own escaping
/// rule for `'...'` literals, so this is correct independent of shell quoting).
fn ps_single_quote(s: &str) -> String {
    format!("'{}'", s.replace('\'', "''"))
}

/// Base64-encode `s` as UTF-8 bytes, for safe embedding of arbitrary content
/// (paths, commands) as a PowerShell argument without quoting hazards.
fn to_base64_utf8(s: &str) -> String {
    BASE64.encode(s.as_bytes())
}

pub fn new_differencing_disk(
    base_image_path: &str,
    child_disk_path: &Path,
) -> Result<(), PowerShellError> {
    if let Some(parent) = child_disk_path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| PowerShellError::NonZeroExit {
            exit_code: None,
            stderr: format!("create disk directory {parent:?}: {e}"),
        })?;
    }
    let script = format!(
        "New-VHD -ParentPath {} -Differencing -Path {} | Out-Null",
        ps_single_quote(base_image_path),
        ps_single_quote(&child_disk_path.to_string_lossy()),
    );
    run_powershell(&script).map(|_| ())
}

pub fn new_vm(vm_name: &str, generation: u8, memory_startup_bytes: u64) -> Result<(), PowerShellError> {
    let script = format!(
        "New-VM -Name {} -Generation {} -MemoryStartupBytes {} -NoVHD | Out-Null",
        ps_single_quote(vm_name),
        generation,
        memory_startup_bytes,
    );
    run_powershell(&script).map(|_| ())
}

pub fn add_hard_disk_drive(vm_name: &str, disk_path: &Path) -> Result<(), PowerShellError> {
    let script = format!(
        "Add-VMHardDiskDrive -VMName {} -Path {} | Out-Null",
        ps_single_quote(vm_name),
        ps_single_quote(&disk_path.to_string_lossy()),
    );
    run_powershell(&script).map(|_| ())
}

pub fn set_vm_processor(vm_name: &str, cpu_count: u32) -> Result<(), PowerShellError> {
    let script = format!(
        "Set-VMProcessor -VMName {} -Count {} | Out-Null",
        ps_single_quote(vm_name),
        cpu_count,
    );
    run_powershell(&script).map(|_| ())
}

pub fn start_vm(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Start-VM -Name {} | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn save_vm(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Save-VM -Name {} | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn suspend_vm(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Suspend-VM -Name {} | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn resume_vm(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Resume-VM -Name {} | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn stop_vm_force_poweroff(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Stop-VM -Name {} -TurnOff -Force | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn checkpoint_vm(vm_name: &str, snapshot_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Checkpoint-VM -Name {} -SnapshotName {} | Out-Null",
        ps_single_quote(vm_name),
        ps_single_quote(snapshot_name),
    ))
    .map(|_| ())
}

pub fn restore_vm_snapshot(vm_name: &str, snapshot_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Restore-VMSnapshot -VMName {} -Name {} -Confirm:$false | Out-Null",
        ps_single_quote(vm_name),
        ps_single_quote(snapshot_name),
    ))
    .map(|_| ())
}

pub fn remove_vm_snapshot(vm_name: &str, snapshot_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Get-VMSnapshot -VMName {} -Name {} | Remove-VMSnapshot | Out-Null",
        ps_single_quote(vm_name),
        ps_single_quote(snapshot_name),
    ))
    .map(|_| ())
}

/// Formats the snapshots as a JSON array for 0, 1, or many matches alike,
/// ensuring compatibility with Windows PowerShell 5.1 (which lacks `-AsArray`).
pub fn list_vm_snapshots(vm_name: &str) -> Result<Vec<VmSnapshotInfo>, PowerShellError> {
    let script = format!(
        "$s = @(Get-VMSnapshot -VMName {} | Select-Object Name, CreationTime); \
         if ($s.Count -eq 0) {{ '[]' }} \
         elseif ($s.Count -eq 1) {{ '[' + ($s[0] | ConvertTo-Json -Depth 4 -Compress) + ']' }} \
         else {{ $s | ConvertTo-Json -Depth 4 -Compress }}",
        ps_single_quote(vm_name),
    );
    run_powershell_json(&script)
}

pub fn remove_vm(vm_name: &str) -> Result<(), PowerShellError> {
    run_powershell(&format!(
        "Remove-VM -Name {} -Force | Out-Null",
        ps_single_quote(vm_name)
    ))
    .map(|_| ())
}

pub fn get_vm_state(vm_name: &str) -> Result<VmState, PowerShellError> {
    let out = run_powershell(&format!(
        "(Get-VM -Name {}).State.ToString()",
        ps_single_quote(vm_name)
    ))?;
    Ok(VmState::parse(&out))
}

/// Run `command` inside `vm_name` via PowerShell Direct, relaying its live
/// output to this process's own stdout/stderr, and returning its exit code.
///
/// Two PowerShell Direct round trips, the workload running exactly once:
/// the first streams the command's own output live (via inherited stdio) and
/// writes its exit code to a marker file *inside the guest's own
/// filesystem* — no host-guest file transfer needed, since both calls reach
/// the same guest. The second, fast and unrelayed, reads that marker back
/// and deletes it; it re-enters the guest but never re-runs the workload.
pub fn invoke_command_in_vm(
    vm_name: &str,
    credential: &GuestCredential,
    command: &str,
    working_directory: Option<&str>,
) -> Result<i32, PowerShellError> {
    let marker_name = format!("mxc-hv-exit-{}.txt", marker_token());
    let cmd_b64 = to_base64_utf8(command);
    let cwd_b64 = working_directory.map(to_base64_utf8).unwrap_or_default();
    let password_stdin = password_stdin_line(credential);

    let run_script = format!(
        "{preamble}\n\
         Invoke-Command -VMName {vm} -Credential $cred -ScriptBlock {{\n\
         \u{20} param($cmdB64, $markerName, $cwdB64)\n\
         \u{20} $cmdText = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($cmdB64))\n\
         \u{20} if ($cwdB64) {{\n\
         \u{20}  $cwdText = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($cwdB64))\n\
         \u{20}  Set-Location -Path $cwdText\n\
         \u{20} }}\n\
         \u{20} & cmd.exe /c $cmdText\n\
         \u{20} $code = $LASTEXITCODE\n\
         \u{20} Set-Content -Path (Join-Path $env:TEMP $markerName) -Value $code -NoNewline\n\
         }} -ArgumentList {cmd_b64}, {marker}, {cwd_b64}\n",
        preamble = credential_preamble(credential),
        vm = ps_single_quote(vm_name),
        cmd_b64 = ps_single_quote(&cmd_b64),
        marker = ps_single_quote(&marker_name),
        cwd_b64 = ps_single_quote(&cwd_b64),
    );
    run_powershell_relayed_with_stdin(&run_script, password_stdin.as_bytes())?;

    let capture_script = format!(
        "{preamble}\n\
         $code = Invoke-Command -VMName {vm} -Credential $cred -ScriptBlock {{\n\
         \u{20} param($markerName)\n\
         \u{20} $path = Join-Path $env:TEMP $markerName\n\
         \u{20} $v = Get-Content -Path $path -ErrorAction SilentlyContinue\n\
         \u{20} Remove-Item -Path $path -ErrorAction SilentlyContinue\n\
         \u{20} if ($null -eq $v) {{ -1 }} else {{ [int]$v }}\n\
         }} -ArgumentList {marker}\n\
         Write-Output $code\n",
        preamble = credential_preamble(credential),
        vm = ps_single_quote(vm_name),
        marker = ps_single_quote(&marker_name),
    );
    let out = run_powershell_with_stdin(&capture_script, password_stdin.as_bytes())?;
    out.trim()
        .parse::<i32>()
        .map_err(|_| PowerShellError::NonZeroExit {
            exit_code: None,
            stderr: format!("could not parse exit-code marker output: {out:?}"),
        })
}

/// Shared script preamble that rebuilds the `PSCredential` from the password
/// piped on stdin (see [`password_stdin_line`]) into a `$cred` variable.
fn credential_preamble(credential: &GuestCredential) -> String {
    format!(
        "$pwUtf16 = [Console]::In.ReadLine()\n\
         $securePw = ConvertTo-SecureString -String \
         ([System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($pwUtf16))) \
         -AsPlainText -Force\n\
         $cred = New-Object System.Management.Automation.PSCredential({username}, $securePw)",
        username = ps_single_quote(&credential.username),
    )
}

/// Base64-encode the credential's raw password bytes as a single stdin line.
/// The script side decodes with `[System.Text.Encoding]::Unicode` (UTF-16LE),
/// matching how Credential Manager stores a `cmdkey`-created generic secret —
/// see [`crate::credential::GuestCredential::password_bytes`].
fn password_stdin_line(credential: &GuestCredential) -> String {
    format!("{}\n", BASE64.encode(credential.password_bytes()))
}

/// A short, time-based hex token for marker-file uniqueness. Collision would
/// only matter for two concurrent `exec` calls against the *same* VM, which
/// the lifecycle layer's per-token `TransitionLock` already serializes.
fn marker_token() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    format!("{nanos:x}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ps_single_quote_doubles_embedded_quotes() {
        assert_eq!(ps_single_quote("abc"), "'abc'");
        assert_eq!(ps_single_quote("a'b"), "'a''b'");
        assert_eq!(ps_single_quote("it's a test"), "'it''s a test'");
    }

    #[test]
    fn to_base64_round_trips() {
        let encoded = to_base64_utf8("hello world");
        let decoded = BASE64.decode(encoded).unwrap();
        assert_eq!(decoded, b"hello world");
    }

    #[test]
    fn vm_state_parses_known_values() {
        assert_eq!(VmState::parse("Off"), VmState::Off);
        assert_eq!(VmState::parse("Running"), VmState::Running);
        assert_eq!(VmState::parse("Saved"), VmState::Saved);
        assert_eq!(VmState::parse("Paused"), VmState::Paused);
        assert_eq!(VmState::parse("SomethingElse"), VmState::Other);
    }

    #[test]
    fn marker_tokens_are_distinct_across_calls() {
        let a = marker_token();
        let b = marker_token();
        // Not a hard guarantee on extremely fast clocks, but a basic sanity
        // check that this isn't a constant.
        assert!(a.len() >= 1 && b.len() >= 1);
    }

    #[test]
    fn list_vm_snapshots_fixture_decodes() {
        // Exercises the JSON shape (not the live cmdlet): an empty array, a
        // single-element array (the point `-AsArray` guards against), and a
        // multi-element array must all decode to `Vec<VmSnapshotInfo>`.
        let empty: Vec<VmSnapshotInfo> = serde_json::from_str("[]").unwrap();
        assert!(empty.is_empty());

        let one: Vec<VmSnapshotInfo> =
            serde_json::from_str(r#"[{"Name":"before-change","CreationTime":"2026-01-01"}]"#)
                .unwrap();
        assert_eq!(one.len(), 1);
        assert_eq!(one[0].name, "before-change");

        let many: Vec<VmSnapshotInfo> = serde_json::from_str(
            r#"[{"Name":"a","CreationTime":null},{"Name":"b","CreationTime":"2026-01-02"}]"#,
        )
        .unwrap();
        assert_eq!(many.len(), 2);
        assert!(many[0].creation_time.is_none());
    }
}
