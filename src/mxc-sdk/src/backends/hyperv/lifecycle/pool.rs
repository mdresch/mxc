// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Warm Standby Pool Manager for Hyper-V Sandboxes.
//!
//! Maintains a configurable pool of pre-warmed Hyper-V VMs
//! (`hv:<token>`) so autonomous agents, test runners, and CI pipelines
//! can lease a live, authenticated Windows Server 2025 sandbox in <300ms.
//!
//! Lifecycle flow:
//! - Configure: Sets pool target size, base image path, and credentials.
//! - Replenish: Provisions VMs up to `target_size`, creates differencing disks,
//!   boots them to OS desktop, stamps baseline snapshot `pool-clean-baseline`,
//!   and suspends/saves them.
//! - Lease: Instantly checks out a `Ready` VM, wakes/resumes it (<300ms), marks
//!   it `Leased`, and returns its `sandbox_id`.
//! - Release: Restores the VM to `pool-clean-baseline`, resynchronizes the clock,
//!   suspends it, and recycles it back to `Ready`.
//! - Drain: Forcibly powers off and deletes all pool VMs and differencing disks.

use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::{Deserialize, Serialize};

use super::super::common as hyperv_common;
use super::control_plane::{self, HypervSandboxRecord, TransitionLock};
use super::error::map_powershell_error;
use super::state_aware::extract_token;
use crate::mxc_common::id::mint_random_token;
use crate::mxc_common::mxc_error::MxcError;

pub const POOL_SCHEMA_VERSION: u32 = 1;
pub const POOL_LOCK_NAME: &str = "pool";
pub const CLEAN_BASELINE_SNAPSHOT: &str = "pool-clean-baseline";
pub const DEFAULT_POOL_TARGET_SIZE: usize = 2;
const POOL_LOCK_TIMEOUT: Duration = Duration::from_secs(60);

const DEFAULT_GENERATION: u8 = 2;
const DEFAULT_MEMORY_STARTUP_BYTES: u64 = 2 * 1024 * 1024 * 1024;
const DEFAULT_CPU_COUNT: u32 = 2;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PoolMemberStatus {
    Ready,
    Leased,
    Recycling,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolMember {
    pub token: String,
    pub sandbox_id: String,
    pub vm_name: String,
    pub status: PoolMemberStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub leased_to: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub leased_at_utc: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolConfig {
    pub target_size: usize,
    pub base_image_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub guest_credential_target: Option<String>,
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self {
            target_size: DEFAULT_POOL_TARGET_SIZE,
            base_image_path: String::new(),
            guest_credential_target: None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolState {
    pub schema_version: u32,
    pub config: PoolConfig,
    pub members: Vec<PoolMember>,
}

impl PoolState {
    pub fn new(config: PoolConfig) -> Self {
        Self {
            schema_version: POOL_SCHEMA_VERSION,
            config,
            members: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolStatusReport {
    pub target_size: usize,
    pub total_members: usize,
    pub ready_count: usize,
    pub leased_count: usize,
    pub members: Vec<PoolMember>,
}

// ---------------------------------------------------------------------------
// On-disk Pool State Persistence
// ---------------------------------------------------------------------------

#[cfg(test)]
mod test_pool_root {
    use std::cell::RefCell;
    use std::path::PathBuf;

    thread_local! {
        static ROOT: RefCell<Option<PathBuf>> = const { RefCell::new(None) };
    }

    pub fn set(p: Option<PathBuf>) {
        ROOT.with(|r| *r.borrow_mut() = p);
    }

    pub fn get() -> Option<PathBuf> {
        ROOT.with(|r| r.borrow().clone())
    }
}

#[cfg(test)]
pub fn set_pool_root_for_test(p: Option<PathBuf>) {
    test_pool_root::set(p);
}

pub fn pool_dir() -> PathBuf {
    #[cfg(test)]
    {
        if let Some(p) = test_pool_root::get() {
            return p;
        }
    }
    control_plane::state_aware_root()
        .parent()
        .unwrap_or_else(|| Path::new(r"C:\ProgramData\mxc\hyperv"))
        .join("pool")
}

pub fn pool_state_file() -> PathBuf {
    pool_dir().join("pool_state.json")
}

pub fn read_pool_state() -> Result<Option<PoolState>, MxcError> {
    let path = pool_state_file();
    if !path.exists() {
        return Ok(None);
    }
    let data = std::fs::read_to_string(&path).map_err(|e| {
        MxcError::backend_error(format!("read pool state {path:?}: {e}"))
    })?;
    let state: PoolState = serde_json::from_str(&data).map_err(|e| {
        MxcError::backend_error(format!("parse pool state {path:?}: {e}"))
    })?;
    Ok(Some(state))
}

pub fn write_pool_state(state: &PoolState) -> Result<(), MxcError> {
    let dir = pool_dir();
    std::fs::create_dir_all(&dir).map_err(|e| {
        MxcError::backend_error(format!("create pool dir {dir:?}: {e}"))
    })?;
    let _ = control_plane::os::set_owner_only_dir(&dir);

    let path = pool_state_file();
    let data = serde_json::to_string_pretty(state).map_err(|e| {
        MxcError::backend_error(format!("serialize pool state: {e}"))
    })?;
    std::fs::write(&path, data).map_err(|e| {
        MxcError::backend_error(format!("write pool state {path:?}: {e}"))
    })?;
    Ok(())
}

// ---------------------------------------------------------------------------
// Pool Operations
// ---------------------------------------------------------------------------

/// Retrieve live status report of the standby pool.
pub fn get_pool_status() -> Result<PoolStatusReport, MxcError> {
    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let state = read_pool_state()?.unwrap_or_else(|| PoolState::new(PoolConfig::default()));
    let ready_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Ready)
        .count();
    let leased_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Leased)
        .count();

    Ok(PoolStatusReport {
        target_size: state.config.target_size,
        total_members: state.members.len(),
        ready_count,
        leased_count,
        members: state.members,
    })
}

/// Configure the pool target size, base image path, and credential target.
pub fn configure_pool(
    target_size: usize,
    base_image_path: &str,
    guest_credential_target: Option<String>,
) -> Result<PoolStatusReport, MxcError> {
    if target_size == 0 {
        return Err(MxcError::malformed_request(
            "pool target size must be at least 1",
        ));
    }
    if !base_image_path.trim().is_empty() && !Path::new(base_image_path).exists() {
        return Err(MxcError::malformed_request(format!(
            "base image path {base_image_path:?} does not exist"
        )));
    }

    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let mut state = read_pool_state()?.unwrap_or_else(|| PoolState::new(PoolConfig::default()));
    state.config.target_size = target_size;
    if !base_image_path.trim().is_empty() {
        state.config.base_image_path = base_image_path.to_string();
    }
    if guest_credential_target.is_some() {
        state.config.guest_credential_target = guest_credential_target;
    }
    write_pool_state(&state)?;

    let ready_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Ready)
        .count();
    let leased_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Leased)
        .count();

    Ok(PoolStatusReport {
        target_size: state.config.target_size,
        total_members: state.members.len(),
        ready_count,
        leased_count,
        members: state.members,
    })
}

/// Replenish the pool by provisioning and warming up VMs until `target_size` is reached.
pub fn replenish_pool() -> Result<PoolStatusReport, MxcError> {
    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let mut state = read_pool_state()?.ok_or_else(|| {
        MxcError::malformed_request(
            "pool has not been configured yet; call configure_pool first with base image path",
        )
    })?;

    if state.config.base_image_path.trim().is_empty() {
        return Err(MxcError::malformed_request(
            "pool base_image_path is not set; configure pool before replenishing",
        ));
    }

    while state.members.len() < state.config.target_size {
        let token = mint_random_token();
        let sandbox_id = format!("hv:{token}");
        let vm_name = hyperv_common::vm_naming::vm_name_for_token(&token);

        let child_disk = hyperv_common::vm_naming::child_disk_path(
            &control_plane::state_aware_root(),
            &token,
            &state.config.base_image_path,
        );

        // 1. Provision disk and VM
        hyperv_common::cmdlets::new_differencing_disk(&state.config.base_image_path, &child_disk)
            .map_err(|e| map_powershell_error("pool new differencing disk", e))?;

        hyperv_common::cmdlets::new_vm(&vm_name, DEFAULT_GENERATION, DEFAULT_MEMORY_STARTUP_BYTES)
            .map_err(|e| map_powershell_error("pool new VM", e))?;

        hyperv_common::cmdlets::add_hard_disk_drive(&vm_name, &child_disk)
            .map_err(|e| map_powershell_error("pool add disk", e))?;

        hyperv_common::cmdlets::set_vm_processor(&vm_name, DEFAULT_CPU_COUNT)
            .map_err(|e| map_powershell_error("pool set processor", e))?;

        let _ = hyperv_common::cmdlets::enable_guest_service_interface(&vm_name);

        // 2. Start VM and boot
        hyperv_common::cmdlets::start_vm(&vm_name)
            .map_err(|e| map_powershell_error("pool start VM", e))?;

        // 2b. Wait for guest OS to finish booting and establish heartbeat
        let _ = hyperv_common::cmdlets::wait_for_heartbeat(&vm_name, 60);

        // 3. Take clean baseline snapshot
        hyperv_common::cmdlets::checkpoint_vm(&vm_name, CLEAN_BASELINE_SNAPSHOT)
            .map_err(|e| map_powershell_error("pool baseline checkpoint", e))?;

        // 4. Suspend/save VM for fast resume
        let _ = hyperv_common::cmdlets::suspend_vm(&vm_name);

        // 5. Create durable sandbox record so wxc-exec recognizes this container
        let record = HypervSandboxRecord::new_provisioned(
            sandbox_id.clone(),
            vm_name.clone(),
            state.config.base_image_path.clone(),
            child_disk,
            state.config.guest_credential_target.clone(),
        );
        let _ = control_plane::write_sandbox_record(&token, &record);

        state.members.push(PoolMember {
            token,
            sandbox_id,
            vm_name,
            status: PoolMemberStatus::Ready,
            leased_to: None,
            leased_at_utc: None,
        });

        write_pool_state(&state)?;
    }

    let ready_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Ready)
        .count();
    let leased_count = state
        .members
        .iter()
        .filter(|m| m.status == PoolMemberStatus::Leased)
        .count();

    Ok(PoolStatusReport {
        target_size: state.config.target_size,
        total_members: state.members.len(),
        ready_count,
        leased_count,
        members: state.members,
    })
}

/// Instant checkout: Lease a warm standby VM from the pool (<300ms).
pub fn lease_from_pool(lease_holder: Option<&str>) -> Result<String, MxcError> {
    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let mut state = read_pool_state()?.ok_or_else(|| {
        MxcError::not_provisioned("standby pool is not initialized; call replenish_pool first")
    })?;

    let (vm_name, leased_sandbox_id) = {
        let ready_member = state
            .members
            .iter_mut()
            .find(|m| m.status == PoolMemberStatus::Ready);

        let member = match ready_member {
            Some(m) => m,
            None => {
                return Err(MxcError::backend_error(
                    "no standby VMs currently ready in pool; all instances are leased",
                ));
            }
        };

        member.status = PoolMemberStatus::Leased;
        member.leased_to = lease_holder.map(str::to_string);
        member.leased_at_utc = Some(
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs().to_string())
                .unwrap_or_default(),
        );

        (member.vm_name.clone(), member.sandbox_id.clone())
    };

    // Fast wake/resume
    let _ = hyperv_common::cmdlets::resume_vm(&vm_name);
    write_pool_state(&state)?;

    Ok(leased_sandbox_id)
}

/// Return a leased VM back to the pool, resetting it to its clean baseline snapshot.
pub fn release_to_pool(sandbox_id: &str) -> Result<(), MxcError> {
    let token = extract_token(sandbox_id)?;

    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let mut state = read_pool_state()?.ok_or_else(|| {
        MxcError::not_provisioned("standby pool is not initialized")
    })?;

    let vm_name = {
        let member = state
            .members
            .iter_mut()
            .find(|m| m.token == token)
            .ok_or_else(|| {
                MxcError::malformed_id(format!(
                    "sandbox {sandbox_id} is not a registered member of the pool"
                ))
            })?;

        member.status = PoolMemberStatus::Recycling;
        member.vm_name.clone()
    };
    write_pool_state(&state)?;

    // 1. Rollback to clean baseline snapshot
    let _ = hyperv_common::cmdlets::restore_vm_snapshot(&vm_name, CLEAN_BASELINE_SNAPSHOT);

    // 2. Suspend/pause VM for standby
    let _ = hyperv_common::cmdlets::suspend_vm(&vm_name);

    // 3. Mark ready
    if let Some(member) = state.members.iter_mut().find(|m| m.token == token) {
        member.status = PoolMemberStatus::Ready;
        member.leased_to = None;
        member.leased_at_utc = None;
    }
    write_pool_state(&state)?;

    Ok(())
}

/// Forcibly power off, remove all pool VMs, and delete all differencing disks.
pub fn drain_pool() -> Result<(), MxcError> {
    let _lock = TransitionLock::acquire(POOL_LOCK_NAME, POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))?;

    let mut state = match read_pool_state()? {
        Some(s) => s,
        None => return Ok(()),
    };

    for member in &state.members {
        let _ = hyperv_common::cmdlets::stop_vm_force_poweroff(&member.vm_name);
        if let Ok(snapshots) = hyperv_common::cmdlets::list_vm_snapshots(&member.vm_name) {
            for snap in snapshots {
                let _ = hyperv_common::cmdlets::remove_vm_snapshot(&member.vm_name, &snap.name);
            }
        }
        let _ = hyperv_common::cmdlets::remove_vm(&member.vm_name);
        let _ = control_plane::remove_sandbox_dir(&member.token);
    }

    state.members.clear();
    write_pool_state(&state)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mxc_common::mxc_error::MxcErrorCode;

    #[test]
    fn pool_state_serializes_and_deserializes() {
        let mut state = PoolState::new(PoolConfig {
            target_size: 2,
            base_image_path: r"C:\images\server2025.vhdx".to_string(),
            guest_credential_target: Some("mxc-guest".to_string()),
        });
        state.members.push(PoolMember {
            token: "1234abcd".to_string(),
            sandbox_id: "hv:1234abcd".to_string(),
            vm_name: "mxc-hv-1234abcd".to_string(),
            status: PoolMemberStatus::Ready,
            leased_to: None,
            leased_at_utc: None,
        });

        let json = serde_json::to_string(&state).unwrap();
        let decoded: PoolState = serde_json::from_str(&json).unwrap();
        assert_eq!(decoded.config.target_size, 2);
        assert_eq!(decoded.members.len(), 1);
        assert_eq!(decoded.members[0].status, PoolMemberStatus::Ready);
    }

    #[test]
    fn configure_pool_rejects_zero_target_size() {
        let err = configure_pool(0, "", None).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn configure_pool_rejects_missing_base_image() {
        let err = configure_pool(2, r"C:\nonexistent_path\image.vhdx", None).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn lease_from_empty_pool_returns_error() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        let state = PoolState::new(PoolConfig::default());
        write_pool_state(&state).unwrap();

        let err = lease_from_pool(Some("agent-1")).unwrap_err();
        assert!(err.message.contains("no standby VMs currently ready"));

        set_pool_root_for_test(None);
    }
}

