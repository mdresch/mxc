// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Backend-private pause/resume and checkpoint/rollback operations.
//!
//! These sit entirely outside the universal 5-phase lifecycle
//! (provision/start/exec/stop/deprovision): the state-aware design doc
//! defers snapshot/suspend/restore as "out of scope for v1" of the shared
//! contract but sanctions a backend exposing them privately under its own
//! section until universalised. Verified against the actual exact-contract
//! structs: `StopRequest`/`StartRequest` carry no backend-specific extension
//! point today, so there is no way to ride a `hyperv.stop.mode` field
//! through the shared `stop` phase without extending shared contract code
//! for one backend's feature — exactly the cost this escape hatch exists to
//! avoid. These operations are reachable only via dedicated `wxc-exec` CLI
//! flags and `mxc_ffi` functions (see `wxc::main` and `mxc_ffi::hyperv`),
//! never through `Phase`/`state_aware_dispatch`/`state_aware_binding`.

use std::time::Duration;

use hyperv_common::cmdlets::VmSnapshotInfo;
use wxc_common::mxc_error::MxcError;

use crate::control_plane::{self, HypervSandboxState, TransitionLock};
use crate::error::map_powershell_error;
use crate::state_aware::extract_token;

const TRANSITION_LOCK_TIMEOUT: Duration = Duration::from_secs(120);

fn read_record_or_not_provisioned(
    token: &str,
    sandbox_id: &str,
) -> Result<control_plane::HypervSandboxRecord, MxcError> {
    control_plane::read_sandbox_record(token)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?
        .ok_or_else(|| MxcError::not_provisioned(format!("sandbox {sandbox_id} is not provisioned")))
}

/// Pause a running VM in place (`Suspend-VM`) — a fast, memory-resident
/// pause distinct from `stop`'s `Save-VM`, which powers the VM off.
/// Requires the sandbox's own record to be `Started`.
pub fn pause(sandbox_id: &str) -> Result<(), MxcError> {
    let token = extract_token(sandbox_id)?;
    let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;
    let record = read_record_or_not_provisioned(token, sandbox_id)?;
    if record.state != HypervSandboxState::Started {
        return Err(MxcError::not_started(format!(
            "sandbox {sandbox_id} is not started; pause requires a running VM"
        )));
    }
    hyperv_common::cmdlets::suspend_vm(&record.vm_name)
        .map_err(|e| map_powershell_error("pause (Suspend-VM)", e))
}

/// Resume a paused VM (`Resume-VM`). Requires the sandbox's own record to be
/// `Started` — `pause`/`resume` do not change the record's `Started`/
/// `Stopped` state, since both leave the VM resident in memory.
pub fn resume(sandbox_id: &str) -> Result<(), MxcError> {
    let token = extract_token(sandbox_id)?;
    let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;
    let record = read_record_or_not_provisioned(token, sandbox_id)?;
    if record.state != HypervSandboxState::Started {
        return Err(MxcError::not_started(format!(
            "sandbox {sandbox_id} is not started; resume requires a paused, previously-started VM"
        )));
    }
    hyperv_common::cmdlets::resume_vm(&record.vm_name)
        .map_err(|e| map_powershell_error("resume (Resume-VM)", e))
}

/// Forcibly power the VM off, discarding any in-memory state (`Stop-VM
/// -TurnOff -Force`) — distinct from `stop`'s `Save-VM`, for an operator who
/// wants to discard rather than persist. Updates the record to `Stopped`.
pub fn force_poweroff(sandbox_id: &str) -> Result<(), MxcError> {
    let token = extract_token(sandbox_id)?;
    let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;
    let mut record = read_record_or_not_provisioned(token, sandbox_id)?;
    hyperv_common::cmdlets::stop_vm_force_poweroff(&record.vm_name)
        .map_err(|e| map_powershell_error("force-poweroff (Stop-VM -TurnOff)", e))?;
    record.state = HypervSandboxState::Stopped;
    control_plane::write_sandbox_record(token, &record)
        .map_err(|e| MxcError::backend_error(format!("update sandbox record: {e}")))?;
    Ok(())
}

/// Validate a checkpoint name: non-empty, no path separators or control
/// characters, since it ends up embedded in a PowerShell `-SnapshotName`
/// argument (quoted via `ps_single_quote` in `hyperv_common::cmdlets`, which
/// neutralises injection — this is an additional, user-facing sanity check,
/// not the injection defense).
fn validate_checkpoint_name(name: &str) -> Result<(), MxcError> {
    if name.trim().is_empty() {
        return Err(MxcError::malformed_request(
            "a checkpoint name is required and must not be blank",
        ));
    }
    if name
        .chars()
        .any(|c| c.is_control() || matches!(c, '/' | '\\'))
    {
        return Err(MxcError::malformed_request(format!(
            "checkpoint name {name:?} must not contain control characters or path separators"
        )));
    }
    Ok(())
}

/// Create a named checkpoint of the VM's current state (`Checkpoint-VM`).
/// Valid in any record state (`Provisioned`, `Started`, or `Stopped`) — a
/// Hyper-V checkpoint works whether the VM is off or running.
pub fn checkpoint(sandbox_id: &str, name: &str) -> Result<(), MxcError> {
    validate_checkpoint_name(name)?;
    let token = extract_token(sandbox_id)?;
    let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;
    let record = read_record_or_not_provisioned(token, sandbox_id)?;
    hyperv_common::cmdlets::checkpoint_vm(&record.vm_name, name)
        .map_err(|e| map_powershell_error("checkpoint (Checkpoint-VM)", e))
}

/// Roll the VM back to a previously-created checkpoint (`Restore-VMSnapshot`).
/// Valid in any record state, for the same reason as [`checkpoint`].
///
/// The record's own `Started`/`Stopped` bookkeeping is left untouched: a
/// restore changes the VM's disk/memory content, not whether this backend's
/// bookkeeping considers it started. An operator who restores a running VM
/// to an off-state checkpoint (or vice versa) should follow up with the
/// matching `start`/`stop`/`force-poweroff` call; querying the live state
/// directly (`hyperv_common::cmdlets::get_vm_state`) before doing so is
/// recommended but not enforced here.
pub fn restore(sandbox_id: &str, name: &str) -> Result<(), MxcError> {
    validate_checkpoint_name(name)?;
    let token = extract_token(sandbox_id)?;
    let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;
    let record = read_record_or_not_provisioned(token, sandbox_id)?;
    hyperv_common::cmdlets::restore_vm_snapshot(&record.vm_name, name)
        .map_err(|e| map_powershell_error("restore (Restore-VMSnapshot)", e))
}

/// List the VM's checkpoints (`Get-VMSnapshot`). Valid in any record state.
pub fn list_checkpoints(sandbox_id: &str) -> Result<Vec<VmSnapshotInfo>, MxcError> {
    let token = extract_token(sandbox_id)?;
    let record = read_record_or_not_provisioned(token, sandbox_id)?;
    hyperv_common::cmdlets::list_vm_snapshots(&record.vm_name)
        .map_err(|e| map_powershell_error("list-checkpoints (Get-VMSnapshot)", e))
}

#[cfg(test)]
mod tests {
    use super::*;
    use wxc_common::mxc_error::MxcErrorCode;

    #[test]
    fn validate_checkpoint_name_rejects_blank() {
        let err = validate_checkpoint_name("").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
        let err = validate_checkpoint_name("   ").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn validate_checkpoint_name_rejects_path_separators() {
        for name in ["a/b", "a\\b", "../escape"] {
            let err = validate_checkpoint_name(name).unwrap_err();
            assert_eq!(err.code, MxcErrorCode::MalformedRequest, "name {name:?}");
        }
    }

    #[test]
    fn validate_checkpoint_name_rejects_control_characters() {
        let err = validate_checkpoint_name("before\nchange").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn validate_checkpoint_name_accepts_ordinary_names() {
        for name in ["before-change", "snap_1", "milestone 2"] {
            validate_checkpoint_name(name).unwrap();
        }
    }

    #[test]
    fn pause_on_unprovisioned_id_is_not_provisioned() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let err = pause("hv:abcd1234").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::NotProvisioned);

        control_plane::set_state_aware_root_for_test(None);
    }

    #[test]
    fn checkpoint_rejects_malformed_name_before_touching_the_record() {
        // The record lookup would also fail (not provisioned), but the name
        // check must fire first so the error is about the actual mistake.
        let err = checkpoint("hv:abcd1234", "").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn restore_rejects_malformed_name_before_touching_the_record() {
        let err = restore("hv:abcd1234", "a/b").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn pause_on_a_provisioned_but_not_started_sandbox_is_not_started() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let token = "abcd1234";
        let record = control_plane::HypervSandboxRecord::new_provisioned(
            format!("hv:{token}"),
            "mxc-hv-abcd1234".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            control_plane::sandbox_dir(token).join("disk.avhdx"),
            None,
        );
        control_plane::write_sandbox_record(token, &record).unwrap();

        let err = pause(&format!("hv:{token}")).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::NotStarted);

        control_plane::set_state_aware_root_for_test(None);
    }

    #[test]
    fn resume_on_a_provisioned_but_not_started_sandbox_is_not_started() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let token = "beefcafe";
        let record = control_plane::HypervSandboxRecord::new_provisioned(
            format!("hv:{token}"),
            "mxc-hv-beefcafe".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            control_plane::sandbox_dir(token).join("disk.avhdx"),
            None,
        );
        control_plane::write_sandbox_record(token, &record).unwrap();

        let err = resume(&format!("hv:{token}")).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::NotStarted);

        control_plane::set_state_aware_root_for_test(None);
    }
}
