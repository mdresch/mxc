// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! `StatefulSandboxBackend` impl for the Hyper-V backend.
//!
//! No daemon: a Hyper-V VM is a first-class object the host's own always-on
//! Virtual Machine Management Service holds open, addressable by any
//! process at any time — unlike Windows Sandbox (one host-wide VM slot a
//! daemon must hold) or WSLC (a session with its own idle-watchdog
//! lifecycle). Each phase call is a short-lived process; a per-token
//! [`crate::control_plane::TransitionLock`] serializes only concurrent calls
//! against the *same* sandbox.

use std::time::Duration;

use hyperv_common::credential::GuestCredential;
use serde::Serialize;
use wxc_common::id::mint_random_token;
use wxc_common::models::{ExecutionRequest, HypervProvisionConfig};
use wxc_common::mxc_error::MxcError;
use wxc_common::script_runner::get_timeout_milliseconds;
use wxc_common::state_aware_backend::{
    null_pipe_handle, unsupported_piped_exec, DeprovisionResult, ExecHandle, ExecOutcome,
    ExecStdio, ProvisionResult, StartResult, StatefulSandboxBackend, StopResult,
};
use wxc_common::validator::{validate_state_aware_network_policy_support, NetworkPolicySupport};

use crate::control_plane::{self, HypervSandboxRecord, HypervSandboxState, TransitionLock};
use crate::error::{map_credential_error, map_powershell_error, map_unavailable};
use crate::image;
use crate::HypervRunner;

const TRANSITION_LOCK_TIMEOUT: Duration = Duration::from_secs(120);

const DEFAULT_GENERATION: u8 = 2;
const DEFAULT_MEMORY_STARTUP_BYTES: u64 = 2 * 1024 * 1024 * 1024;
const DEFAULT_CPU_COUNT: u32 = 2;

const SANDBOX_TOKEN_LEN: usize = 8;

/// Provision-phase metadata: the Hyper-V VM name minted for this sandbox,
/// useful for operator-side `Get-VM` lookups.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HypervProvisionMetadata {
    pub vm_name: String,
}

/// Extract the strict 8-lowercase-hex token from `hv:<token>`.
pub(crate) fn extract_token(sandbox_id: &str) -> Result<&str, MxcError> {
    let prefix = <HypervRunner as StatefulSandboxBackend>::ID_PREFIX;
    let (p, rest) = sandbox_id.split_once(':').ok_or_else(|| {
        MxcError::malformed_id(format!("expected {}:<token>, got {:?}", prefix, sandbox_id))
    })?;
    if p != prefix {
        return Err(MxcError::malformed_id(format!(
            "expected {}:<token>, got {:?}",
            prefix, sandbox_id
        )));
    }
    if !is_valid_sandbox_token(rest) {
        return Err(MxcError::malformed_id(format!(
            "sandbox token must be exactly {SANDBOX_TOKEN_LEN} lowercase hex chars; got {:?}",
            rest
        )));
    }
    Ok(rest)
}

/// True iff `token` is exactly [`SANDBOX_TOKEN_LEN`] lowercase hex chars.
fn is_valid_sandbox_token(token: &str) -> bool {
    token.len() == SANDBOX_TOKEN_LEN
        && token
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

/// This backend supports neither filesystem nor network policy at any
/// phase: it has no mapped-folder primitive (unlike Windows Sandbox), and
/// PowerShell Direct needs no network path into the guest at all.
fn reject_filesystem_and_network_policy(request: &ExecutionRequest) -> Result<(), MxcError> {
    validate_state_aware_network_policy_support(request, NetworkPolicySupport::LEGACY)?;
    let p = &request.policy;
    if !p.readwrite_paths.is_empty() || !p.readonly_paths.is_empty() || !p.denied_paths.is_empty()
    {
        return Err(MxcError::policy_validation(
            "the Hyper-V backend supports no filesystem policy (it has no mapped-folder \
             primitive); omit filesystem.readwritePaths/readonlyPaths/deniedPaths",
        ));
    }
    // `network_specified` (not `network_egress`/`network_ingress` presence,
    // which `normalize_common_request_ir` always defaults to `Some(..)` when
    // no `network` field was supplied) is the correct "did the caller
    // actually supply a network block" signal — see its doc comment in
    // `wxc_common::models::ContainerPolicy`.
    if p.network_specified || !p.allowed_hosts.is_empty() || !p.blocked_hosts.is_empty() {
        return Err(MxcError::policy_validation(
            "the Hyper-V backend supports no network policy; PowerShell Direct needs no network \
             path into the guest. Omit the network field entirely.",
        ));
    }
    Ok(())
}

/// Best-effort teardown of whatever provisioning got through before a later
/// step failed, so a failed `provision` never leaks a VM or disk the caller
/// has no sandbox id to address. Cleanup failures are swallowed: the
/// original error is what the caller needs to see, and a leaked artifact
/// here is still reachable by an operator via `Get-VM`/the disk path logged
/// in the returned error context.
fn cleanup_partial_provision(vm_name: &str, child_disk_path: &std::path::Path, vm_created: bool) {
    if vm_created {
        let _ = hyperv_common::cmdlets::remove_vm(vm_name);
    }
    let _ = std::fs::remove_file(child_disk_path);
}

impl StatefulSandboxBackend for HypervRunner {
    const ID_PREFIX: &'static str = "hv";
    const BACKEND_KEY: &'static str = "hyperv";

    type ProvisionConfig = HypervProvisionConfig;
    type StartConfig = ();
    type ExecConfig = ();
    type StopConfig = ();
    type DeprovisionConfig = ();
    type ProvisionMetadata = HypervProvisionMetadata;
    type StartMetadata = ();
    type StopMetadata = ();
    type DeprovisionMetadata = ();

    fn provision(
        &mut self,
        request: &ExecutionRequest,
        config: Option<HypervProvisionConfig>,
    ) -> Result<ProvisionResult<HypervProvisionMetadata>, MxcError> {
        reject_filesystem_and_network_policy(request)?;

        let config = config.unwrap_or_default();
        let base_image_path = config
            .base_image_path
            .as_deref()
            .unwrap_or("")
            .trim()
            .to_string();
        image::validate_base_image_path(&base_image_path)?;

        hyperv_common::probe::hyperv_available().map_err(map_unavailable)?;

        let token = mint_random_token();
        let sandbox_id = format!("{}:{}", <Self as StatefulSandboxBackend>::ID_PREFIX, token);
        let vm_name = hyperv_common::vm_naming::vm_name_for_token(&token);

        control_plane::secure_record_root()
            .map_err(|e| MxcError::backend_error(format!("secure state-aware record root: {e}")))?;
        let dir = control_plane::sandbox_dir(&token);
        std::fs::create_dir_all(&dir)
            .map_err(|e| MxcError::backend_error(format!("create sandbox dir {dir:?}: {e}")))?;
        control_plane::os::set_owner_only_dir(&dir)
            .map_err(|e| MxcError::backend_error(format!("secure sandbox dir {dir:?}: {e:#}")))?;

        let child_disk_path = hyperv_common::vm_naming::child_disk_path(
            &control_plane::state_aware_root(),
            &token,
            &base_image_path,
        );

        let generation = config.generation.unwrap_or(DEFAULT_GENERATION);
        let memory_startup_bytes = config
            .memory_startup_bytes
            .unwrap_or(DEFAULT_MEMORY_STARTUP_BYTES);
        let cpu_count = config.cpu_count.unwrap_or(DEFAULT_CPU_COUNT);

        hyperv_common::cmdlets::new_differencing_disk(&base_image_path, &child_disk_path)
            .map_err(|e| map_powershell_error("create differencing disk", e))?;

        if let Err(e) = hyperv_common::cmdlets::new_vm(&vm_name, generation, memory_startup_bytes)
        {
            cleanup_partial_provision(&vm_name, &child_disk_path, false);
            return Err(map_powershell_error("create VM", e));
        }

        if let Err(e) = hyperv_common::cmdlets::add_hard_disk_drive(&vm_name, &child_disk_path) {
            cleanup_partial_provision(&vm_name, &child_disk_path, true);
            return Err(map_powershell_error("attach differencing disk", e));
        }

        if let Err(e) = hyperv_common::cmdlets::set_vm_processor(&vm_name, cpu_count) {
            cleanup_partial_provision(&vm_name, &child_disk_path, true);
            return Err(map_powershell_error("set VM processor count", e));
        }

        let record = HypervSandboxRecord::new_provisioned(
            sandbox_id.clone(),
            vm_name.clone(),
            base_image_path,
            child_disk_path.clone(),
            config.guest_credential_target,
        );
        if let Err(e) = control_plane::write_sandbox_record(&token, &record) {
            cleanup_partial_provision(&vm_name, &child_disk_path, true);
            return Err(MxcError::backend_error(format!(
                "write sandbox record: {e}"
            )));
        }

        Ok(ProvisionResult {
            sandbox_id,
            metadata: Some(HypervProvisionMetadata { vm_name }),
        })
    }

    fn start(
        &mut self,
        sandbox_id: &str,
        _request: &ExecutionRequest,
        _config: Option<()>,
    ) -> Result<StartResult<()>, MxcError> {
        let token = extract_token(sandbox_id)?;
        let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?;

        let mut record = control_plane::read_sandbox_record(token)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?
            .ok_or_else(|| {
                MxcError::not_provisioned(format!("sandbox {sandbox_id} is not provisioned"))
            })?;

        if record.state == HypervSandboxState::Started {
            return Err(MxcError::already_started(format!(
                "sandbox {sandbox_id} is already started"
            )));
        }

        hyperv_common::cmdlets::start_vm(&record.vm_name)
            .map_err(|e| map_powershell_error("start VM", e))?;

        record.state = HypervSandboxState::Started;
        control_plane::write_sandbox_record(token, &record)
            .map_err(|e| MxcError::backend_error(format!("update sandbox record: {e}")))?;

        Ok(StartResult { metadata: None })
    }

    fn exec(
        &mut self,
        sandbox_id: &str,
        request: &ExecutionRequest,
        _config: Option<()>,
        stdio: ExecStdio,
    ) -> Result<ExecHandle, MxcError> {
        // This backend relays guest output to the calling process's own
        // stdio; refuse Piped before any work, matching the Windows
        // Sandbox / WSLC precedent.
        if stdio == ExecStdio::Piped {
            return Err(unsupported_piped_exec("Hyper-V"));
        }
        reject_filesystem_and_network_policy(request)?;

        let token = extract_token(sandbox_id)?;
        let record = control_plane::read_sandbox_record(token)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?
            .ok_or_else(|| {
                MxcError::not_provisioned(format!("sandbox {sandbox_id} is not provisioned"))
            })?;
        if record.state != HypervSandboxState::Started {
            return Err(MxcError::not_started(format!(
                "sandbox {sandbox_id} is not started"
            )));
        }

        let target = record.guest_credential_target.as_deref().ok_or_else(|| {
            MxcError::policy_validation(
                "sandbox was provisioned with no guestCredentialTarget; exec requires one to \
                 authenticate PowerShell Direct into the guest",
            )
        })?;
        let credential: GuestCredential =
            hyperv_common::credential::resolve_guest_credential(target)
                .map_err(map_credential_error)?;

        let cwd = if request.working_directory.trim().is_empty() {
            None
        } else {
            Some(request.working_directory.as_str())
        };

        // `script_timeout` (0 == infinite) is accepted but not yet enforced
        // here: enforcing it would need the relayed call's child PID exposed
        // back to a host-side watchdog, which `invoke_command_in_vm` does
        // not yet surface. Tracked as a follow-up, not silently ignored —
        // see the backend doc.
        let _requested_timeout_ms = get_timeout_milliseconds(request.script_timeout);

        let exit_code =
            hyperv_common::cmdlets::invoke_command_in_vm(&record.vm_name, &credential, &request.script_code, cwd)
                .map_err(|e| map_powershell_error("exec via PowerShell Direct", e))?;

        Ok(ExecHandle {
            stdout: null_pipe_handle(),
            stderr: null_pipe_handle(),
            stdin: null_pipe_handle(),
            stdin_closer: None,
            // `Exited`, not `TimedOut`: this backend runs the workload to
            // completion inside `exec` and reports what the guest returned.
            waiter: Box::new(move || Ok(ExecOutcome::Exited(exit_code))),
            terminator: Box::new(|| Ok(())),
        })
    }

    fn stop(
        &mut self,
        sandbox_id: &str,
        _request: &ExecutionRequest,
        _config: Option<()>,
    ) -> Result<StopResult<()>, MxcError> {
        let token = extract_token(sandbox_id)?;
        let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?;

        let mut record = control_plane::read_sandbox_record(token)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?
            .ok_or_else(|| {
                MxcError::not_provisioned(format!("sandbox {sandbox_id} is not provisioned"))
            })?;

        match record.state {
            HypervSandboxState::Started => {
                hyperv_common::cmdlets::save_vm(&record.vm_name)
                    .map_err(|e| map_powershell_error("save VM", e))?;
            }
            HypervSandboxState::Stopped => {
                return Err(MxcError::already_stopped(format!(
                    "sandbox {sandbox_id} is already stopped"
                )));
            }
            HypervSandboxState::Provisioned => {
                return Err(MxcError::already_stopped(format!(
                    "sandbox {sandbox_id} is not started"
                )));
            }
        }

        record.state = HypervSandboxState::Stopped;
        control_plane::write_sandbox_record(token, &record)
            .map_err(|e| MxcError::backend_error(format!("update sandbox record: {e}")))?;

        Ok(StopResult { metadata: None })
    }

    fn deprovision(
        &mut self,
        sandbox_id: &str,
        _request: &ExecutionRequest,
        _config: Option<()>,
    ) -> Result<DeprovisionResult<()>, MxcError> {
        let token = extract_token(sandbox_id)?;
        let _lock = TransitionLock::acquire(token, TRANSITION_LOCK_TIMEOUT)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?;

        let record = control_plane::read_sandbox_record(token)
            .map_err(|e| MxcError::backend_error(format!("{e}")))?
            .ok_or_else(|| {
                MxcError::not_provisioned(format!("sandbox {sandbox_id} is not provisioned"))
            })?;

        if record.state == HypervSandboxState::Started {
            // Discard rather than save: the disk is about to be deleted, so
            // there is no point persisting state we are destroying anyway.
            hyperv_common::cmdlets::stop_vm_force_poweroff(&record.vm_name)
                .map_err(|e| map_powershell_error("power off VM before deprovision", e))?;
        }

        let snapshots = hyperv_common::cmdlets::list_vm_snapshots(&record.vm_name)
            .map_err(|e| map_powershell_error("list checkpoints before deprovision", e))?;
        for snapshot in snapshots {
            hyperv_common::cmdlets::remove_vm_snapshot(&record.vm_name, &snapshot.name).map_err(
                |e| map_powershell_error(&format!("remove checkpoint {:?}", snapshot.name), e),
            )?;
        }

        hyperv_common::cmdlets::remove_vm(&record.vm_name)
            .map_err(|e| map_powershell_error("remove VM", e))?;

        if let Err(e) = std::fs::remove_file(&record.child_disk_path) {
            if e.kind() != std::io::ErrorKind::NotFound {
                return Err(MxcError::backend_error(format!(
                    "remove differencing disk {:?}: {e}",
                    record.child_disk_path
                )));
            }
        }

        control_plane::remove_sandbox_dir(token).map_err(|e| {
            MxcError::backend_error(format!("remove sandbox dir for {sandbox_id}: {e}"))
        })?;

        Ok(DeprovisionResult { metadata: None })
    }

    fn validate_provision(
        &self,
        request: &ExecutionRequest,
        config: Option<&HypervProvisionConfig>,
    ) -> Result<(), MxcError> {
        reject_filesystem_and_network_policy(request)?;
        let base_image_path = config
            .and_then(|c| c.base_image_path.as_deref())
            .unwrap_or("")
            .trim();
        image::validate_base_image_path(base_image_path)
    }

    fn validate_start(
        &self,
        sandbox_id: &str,
        request: &ExecutionRequest,
        _config: Option<&()>,
    ) -> Result<(), MxcError> {
        extract_token(sandbox_id)?;
        reject_filesystem_and_network_policy(request)
    }

    fn validate_exec(
        &self,
        sandbox_id: &str,
        request: &ExecutionRequest,
        _config: Option<&()>,
    ) -> Result<(), MxcError> {
        extract_token(sandbox_id)?;
        reject_filesystem_and_network_policy(request)
    }

    fn validate_stop(
        &self,
        sandbox_id: &str,
        request: &ExecutionRequest,
        _config: Option<&()>,
    ) -> Result<(), MxcError> {
        extract_token(sandbox_id)?;
        reject_filesystem_and_network_policy(request)
    }

    fn validate_deprovision(
        &self,
        sandbox_id: &str,
        request: &ExecutionRequest,
        _config: Option<&()>,
    ) -> Result<(), MxcError> {
        extract_token(sandbox_id)?;
        reject_filesystem_and_network_policy(request)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use wxc_common::models::{ContainerPolicy, NetworkEgressPolicy};
    use wxc_common::mxc_error::MxcErrorCode;

    #[test]
    fn backend_key_matches_wire_format() {
        assert_eq!(
            <HypervRunner as StatefulSandboxBackend>::BACKEND_KEY,
            "hyperv"
        );
    }

    #[test]
    fn id_prefix_matches_wire_format() {
        assert_eq!(<HypervRunner as StatefulSandboxBackend>::ID_PREFIX, "hv");
    }

    #[test]
    fn extract_token_unwraps_hv_prefix() {
        assert_eq!(extract_token("hv:deadbeef").unwrap(), "deadbeef");
    }

    #[test]
    fn extract_token_rejects_other_prefix() {
        let err = extract_token("wsb:abcd1234").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);
    }

    #[test]
    fn extract_token_rejects_missing_colon() {
        let err = extract_token("hvabcd1234").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);
    }

    #[test]
    fn extract_token_rejects_wrong_length_hex() {
        for token in ["", "1", "dead", "deadbee", "deadbeefa", "deadbeefdeadbeef"] {
            let err = extract_token(&format!("hv:{token}")).unwrap_err();
            assert_eq!(err.code, MxcErrorCode::MalformedId, "token {token:?}");
        }
    }

    #[test]
    fn extract_token_rejects_uppercase_hex() {
        let err = extract_token("hv:DEADBEEF").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);
    }

    #[test]
    fn extract_token_rejects_path_traversal() {
        for s in ["hv:..", "hv:../../etc/passwd", "hv:C:\\Windows"] {
            let err = extract_token(s).unwrap_err();
            assert_eq!(err.code, MxcErrorCode::MalformedId, "input {s:?}");
        }
    }

    #[test]
    fn extract_token_accepts_exactly_8_lowercase_hex() {
        assert_eq!(extract_token("hv:00000000").unwrap(), "00000000");
        assert_eq!(extract_token("hv:deadbeef").unwrap(), "deadbeef");
        assert_eq!(extract_token("hv:ffffffff").unwrap(), "ffffffff");
    }

    #[test]
    fn reject_policy_accepts_default() {
        let req = ExecutionRequest::default();
        reject_filesystem_and_network_policy(&req).unwrap();
    }

    #[test]
    fn reject_policy_rejects_readwrite_paths() {
        let req = ExecutionRequest {
            policy: ContainerPolicy {
                readwrite_paths: vec!["C:\\work".into()],
                ..Default::default()
            },
            ..Default::default()
        };
        let err = reject_filesystem_and_network_policy(&req).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::PolicyValidation);
    }

    #[test]
    fn reject_policy_rejects_denied_paths() {
        let req = ExecutionRequest {
            policy: ContainerPolicy {
                denied_paths: vec!["C:\\secret".into()],
                ..Default::default()
            },
            ..Default::default()
        };
        let err = reject_filesystem_and_network_policy(&req).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::PolicyValidation);
    }

    #[test]
    fn reject_policy_rejects_allowed_hosts() {
        let req = ExecutionRequest {
            policy: ContainerPolicy {
                allowed_hosts: vec!["example.com".into()],
                ..Default::default()
            },
            ..Default::default()
        };
        let err = reject_filesystem_and_network_policy(&req).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::PolicyValidation);
    }

    #[test]
    fn reject_policy_rejects_directional_egress() {
        // `network_specified`, not `network_egress`/`network_ingress`
        // presence, is the real "caller supplied a network block" signal —
        // `normalize_common_request_ir` always defaults those two to
        // `Some(..)` even when no `network` field was supplied at all.
        let req = ExecutionRequest {
            policy: ContainerPolicy {
                network_specified: true,
                network_egress: Some(NetworkEgressPolicy::default()),
                ..Default::default()
            },
            ..Default::default()
        };
        let err = reject_filesystem_and_network_policy(&req).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::PolicyValidation);
    }

    #[test]
    fn reject_policy_accepts_default_directional_network_when_not_specified() {
        // Regression guard: the real-world shape of "no network field
        // supplied at all" is `network_specified: false` with
        // `network_egress`/`network_ingress` already defaulted to `Some`.
        // This must NOT be rejected.
        let req = ExecutionRequest {
            policy: ContainerPolicy {
                network_specified: false,
                network_egress: Some(NetworkEgressPolicy::default()),
                network_ingress: Some(Default::default()),
                ..Default::default()
            },
            ..Default::default()
        };
        reject_filesystem_and_network_policy(&req).unwrap();
    }

    #[test]
    fn validate_provision_requires_base_image_path() {
        let backend = HypervRunner::new();
        let req = ExecutionRequest::default();
        let err = backend.validate_provision(&req, None).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::PolicyValidation);
    }

    #[test]
    fn validate_start_rejects_malformed_id() {
        let backend = HypervRunner::new();
        let req = ExecutionRequest::default();
        let err = backend
            .validate_start("not-a-valid-id", &req, None)
            .unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);
    }

    #[test]
    fn a_piped_exec_is_refused_before_any_lookup() {
        let mut runner = HypervRunner::new();
        let err = runner
            .exec(
                "not-a-valid-sandbox-id",
                &ExecutionRequest::default(),
                None,
                ExecStdio::Piped,
            )
            .expect_err("a streams-consuming caller must be refused");
        assert!(
            err.message.contains("cannot return exec streams"),
            "expected the shared refusal ahead of id and record checks, got: {}",
            err.message
        );
    }

    #[test]
    fn start_on_unprovisioned_id_is_not_provisioned() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let mut runner = HypervRunner::new();
        let err = runner
            .start("hv:abcd1234", &ExecutionRequest::default(), None)
            .unwrap_err();
        assert_eq!(err.code, MxcErrorCode::NotProvisioned);

        control_plane::set_state_aware_root_for_test(None);
    }

    #[test]
    fn stop_on_unprovisioned_id_is_not_provisioned() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let mut runner = HypervRunner::new();
        let err = runner
            .stop("hv:cafef00d", &ExecutionRequest::default(), None)
            .unwrap_err();
        assert_eq!(err.code, MxcErrorCode::NotProvisioned);

        control_plane::set_state_aware_root_for_test(None);
    }

    #[test]
    fn stop_on_a_provisioned_but_never_started_sandbox_is_already_stopped() {
        let _guard = control_plane::STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        control_plane::set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let token = "beefcafe";
        let record = HypervSandboxRecord::new_provisioned(
            format!("hv:{token}"),
            "mxc-hv-beefcafe".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            control_plane::sandbox_dir(token).join("disk.avhdx"),
            None,
        );
        control_plane::write_sandbox_record(token, &record).unwrap();

        let mut runner = HypervRunner::new();
        let err = runner
            .stop(&format!("hv:{token}"), &ExecutionRequest::default(), None)
            .unwrap_err();
        assert_eq!(err.code, MxcErrorCode::AlreadyStopped);

        control_plane::set_state_aware_root_for_test(None);
    }

    #[test]
    fn provision_metadata_schema_version_matches_current() {
        // Sanity check that the record schema constant this module depends
        // on transitively (via control_plane) has not silently drifted.
        assert_eq!(control_plane::RECORD_SCHEMA_VERSION, 1);
    }
}
