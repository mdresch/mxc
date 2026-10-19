// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Warm Standby Pool Manager for Hyper-V Sandboxes.
//!
//! Maintains one or more named pools of pre-warmed Hyper-V VMs
//! (`hv:<token>`) so autonomous agents, test runners, and CI pipelines
//! can lease a live, authenticated Windows Server 2025 sandbox in <300ms.
//!
//! Each pool is identified by a `pool_id` (e.g. `default`, `prod-adpa`,
//! `dev-mxc`) and owns its own base image, watermarks, state file
//! (`pool/<pool_id>/pool_state.json`) and transition lock (`pool-<pool_id>`),
//! so leasing or reaping in one pool never blocks another.
//!
//! Lifecycle flow:
//! - Configure: Sets pool target size, base image path, and credentials.
//! - Replenish / Warm: Provisions VMs until the pool has the requested number of
//!   `Ready` members (`target_size`, or an explicit `--count` capped at
//!   `max_ready_standby`), creates differencing disks, boots them to OS desktop,
//!   stamps baseline snapshot `pool-clean-baseline`, and suspends/saves them.
//! - Lease: Instantly checks out a `Ready` VM, wakes/resumes it (<300ms), marks
//!   it `Leased`, and returns its `sandbox_id`.
//! - Release: Restores the VM to `pool-clean-baseline`, resynchronizes the clock,
//!   suspends it, and recycles it back to `Ready`.
//! - Drain: Forcibly powers off and deletes all VMs and differencing disks of a pool.
//!
//! Legacy single-pool installs (`pool/pool_state.json`) are migrated in place
//! to the `default` pool on first access.

use std::path::{Path, PathBuf};
use std::time::Duration;

use serde::{Deserialize, Serialize};

use super::super::common as hyperv_common;
use super::control_plane::{self, HypervSandboxRecord, HypervSandboxState, TransitionLock};
use super::error::map_powershell_error;
use super::state_aware::extract_token;
use crate::mxc_common::id::mint_random_token;
use crate::mxc_common::mxc_error::MxcError;

pub const POOL_SCHEMA_VERSION: u32 = 1;
/// Pool used when no `--pool` is given, and the target of legacy-state migration.
pub const DEFAULT_POOL_ID: &str = "default";
pub const CLEAN_BASELINE_SNAPSHOT: &str = "pool-clean-baseline";
pub const DEFAULT_POOL_TARGET_SIZE: usize = 2;
/// Upper bound on ready standby VMs when a pool does not configure
/// `max_ready_standby` (matches the FDD example).
pub const DEFAULT_POOL_MAX_SIZE: usize = 5;
const POOL_LOCK_TIMEOUT: Duration = Duration::from_secs(60);
const POOL_STATE_FILE_NAME: &str = "pool_state.json";
const MAX_POOL_ID_LEN: usize = 63;

const DEFAULT_GENERATION: u8 = 2;
const DEFAULT_MEMORY_STARTUP_BYTES: u64 = 6 * 1024 * 1024 * 1024;
const DEFAULT_CPU_COUNT: u32 = 6;

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

fn default_pool_id() -> String {
    DEFAULT_POOL_ID.to_string()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolConfig {
    /// Identifier of the pool this config belongs to. Absent in legacy state
    /// files, which are always the `default` pool.
    #[serde(default = "default_pool_id")]
    pub pool_id: String,
    /// Minimum number of `Ready` standby VMs maintained by `replenish_pool`
    /// (`min_ready_standby` in the FDD; the alias keeps both spellings loadable).
    #[serde(alias = "min_ready_standby")]
    pub target_size: usize,
    /// Cap on `Ready` standby VMs for explicit pre-warming (`pool-warm --count`).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_ready_standby: Option<usize>,
    pub base_image_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub guest_credential_target: Option<String>,
}

impl PoolConfig {
    /// Effective ready-standby ceiling; never below `target_size`.
    pub fn effective_max_ready(&self) -> usize {
        self.max_ready_standby
            .unwrap_or(DEFAULT_POOL_MAX_SIZE)
            .max(self.target_size)
    }
}

impl Default for PoolConfig {
    fn default() -> Self {
        Self {
            pool_id: default_pool_id(),
            target_size: DEFAULT_POOL_TARGET_SIZE,
            max_ready_standby: None,
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

    fn count(&self, status: PoolMemberStatus) -> usize {
        self.members.iter().filter(|m| m.status == status).count()
    }

    fn into_report(self) -> PoolStatusReport {
        PoolStatusReport {
            pool_id: self.config.pool_id.clone(),
            target_size: self.config.target_size,
            max_ready_standby: self.config.effective_max_ready(),
            total_members: self.members.len(),
            ready_count: self.count(PoolMemberStatus::Ready),
            leased_count: self.count(PoolMemberStatus::Leased),
            members: self.members,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PoolStatusReport {
    pub pool_id: String,
    pub target_size: usize,
    pub max_ready_standby: usize,
    pub total_members: usize,
    pub ready_count: usize,
    pub leased_count: usize,
    pub members: Vec<PoolMember>,
}

// ---------------------------------------------------------------------------
// Pool identity
// ---------------------------------------------------------------------------

/// Pool ids become directory and mutex names, so they are restricted to
/// lowercase alphanumerics, `-` and `_`, starting with an alphanumeric.
pub fn validate_pool_id(pool_id: &str) -> Result<(), MxcError> {
    let valid = !pool_id.is_empty()
        && pool_id.len() <= MAX_POOL_ID_LEN
        && pool_id
            .chars()
            .next()
            .is_some_and(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
        && pool_id
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-' || c == '_');
    if valid {
        Ok(())
    } else {
        Err(MxcError::malformed_request(format!(
            "invalid pool id {pool_id:?}: use 1-{MAX_POOL_ID_LEN} lowercase letters, digits, '-' or '_', \
             starting with a letter or digit"
        )))
    }
}

fn pool_lock_name(pool_id: &str) -> String {
    format!("pool-{pool_id}")
}

fn pool_replenish_lock_name(pool_id: &str) -> String {
    format!("pool-replenish-{pool_id}")
}

fn acquire_pool_lock(pool_id: &str) -> Result<TransitionLock, MxcError> {
    TransitionLock::acquire(&pool_lock_name(pool_id), POOL_LOCK_TIMEOUT)
        .map_err(|e| MxcError::backend_error(format!("{e}")))
}

fn try_acquire_replenish_lock(pool_id: &str) -> Result<Option<TransitionLock>, MxcError> {
    TransitionLock::try_acquire(&pool_replenish_lock_name(pool_id), Duration::ZERO)
        .map_err(|e| MxcError::backend_error(format!("{e}")))
}

#[cfg(test)]
pub mod test_replenish_trigger {
    use std::collections::HashMap;
    use std::sync::Mutex;

    static TRIGGERS: Mutex<Option<HashMap<String, usize>>> = Mutex::new(None);

    pub fn record(pool_id: &str) {
        let mut guard = TRIGGERS.lock().unwrap();
        let map = guard.get_or_insert_with(HashMap::new);
        *map.entry(pool_id.to_string()).or_insert(0) += 1;
    }

    pub fn count_for(pool_id: &str) -> usize {
        let guard = TRIGGERS.lock().unwrap();
        guard
            .as_ref()
            .and_then(|map| map.get(pool_id).copied())
            .unwrap_or(0)
    }
}

/// Triggers non-blocking background replenishment of the given pool (AC-05.1).
pub fn trigger_background_replenish(pool_id: &str) {
    #[cfg(test)]
    {
        test_replenish_trigger::record(pool_id);
    }
    #[cfg(not(test))]
    {
        if let Ok(exe) = std::env::current_exe() {
            let _ = std::process::Command::new(exe)
                .args(&["--experimental", "--hyperv-op", "pool-replenish", "--pool", pool_id])
                .stdin(std::process::Stdio::null())
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn();
        }
    }
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

/// Directory holding every pool's subdirectory (and any legacy single-pool state).
pub fn pool_root_dir() -> PathBuf {
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

/// Directory of a single pool: `<root>/<pool_id>`.
pub fn pool_dir(pool_id: &str) -> PathBuf {
    pool_root_dir().join(pool_id)
}

pub fn pool_state_file(pool_id: &str) -> PathBuf {
    pool_dir(pool_id).join(POOL_STATE_FILE_NAME)
}

fn legacy_pool_state_file() -> PathBuf {
    pool_root_dir().join(POOL_STATE_FILE_NAME)
}

/// Move a pre-multi-pool `pool/pool_state.json` into `pool/default/`.
/// A no-op once the `default` pool has its own state file.
fn migrate_legacy_default_pool() -> Result<(), MxcError> {
    let legacy = legacy_pool_state_file();
    let target = pool_state_file(DEFAULT_POOL_ID);
    if !legacy.exists() || target.exists() {
        return Ok(());
    }
    let dir = pool_dir(DEFAULT_POOL_ID);
    std::fs::create_dir_all(&dir).map_err(|e| {
        MxcError::backend_error(format!("create pool dir {dir:?} for legacy migration: {e}"))
    })?;
    let _ = control_plane::os::set_owner_only_dir(&dir);
    std::fs::rename(&legacy, &target).map_err(|e| {
        MxcError::backend_error(format!(
            "migrate legacy pool state {legacy:?} -> {target:?}: {e}"
        ))
    })
}

/// Ids of every pool that has persisted state, including an un-migrated
/// legacy `default` pool.
pub fn list_pool_ids() -> Vec<String> {
    let mut ids = Vec::new();
    if let Ok(entries) = std::fs::read_dir(pool_root_dir()) {
        for entry in entries.flatten() {
            let path = entry.path();
            let Some(name) = entry.file_name().to_str().map(str::to_string) else {
                continue;
            };
            if path.is_dir()
                && validate_pool_id(&name).is_ok()
                && path.join(POOL_STATE_FILE_NAME).exists()
            {
                ids.push(name);
            }
        }
    }
    if legacy_pool_state_file().exists() && !ids.iter().any(|id| id == DEFAULT_POOL_ID) {
        ids.push(DEFAULT_POOL_ID.to_string());
    }
    ids.sort();
    ids
}

pub fn read_pool_state(pool_id: &str) -> Result<Option<PoolState>, MxcError> {
    validate_pool_id(pool_id)?;
    if pool_id == DEFAULT_POOL_ID {
        migrate_legacy_default_pool()?;
    }
    let path = pool_state_file(pool_id);
    if !path.exists() {
        return Ok(None);
    }
    let data = std::fs::read_to_string(&path)
        .map_err(|e| MxcError::backend_error(format!("read pool state {path:?}: {e}")))?;
    let mut state: PoolState = serde_json::from_str(&data)
        .map_err(|e| MxcError::backend_error(format!("parse pool state {path:?}: {e}")))?;
    // The directory is authoritative; keeps legacy files (no `pool_id`) coherent.
    state.config.pool_id = pool_id.to_string();
    Ok(Some(state))
}

pub fn write_pool_state(pool_id: &str, state: &PoolState) -> Result<(), MxcError> {
    validate_pool_id(pool_id)?;
    let dir = pool_dir(pool_id);
    std::fs::create_dir_all(&dir)
        .map_err(|e| MxcError::backend_error(format!("create pool dir {dir:?}: {e}")))?;
    let _ = control_plane::os::set_owner_only_dir(&dir);

    let path = pool_state_file(pool_id);
    let data = serde_json::to_string_pretty(state)
        .map_err(|e| MxcError::backend_error(format!("serialize pool state: {e}")))?;
    std::fs::write(&path, data)
        .map_err(|e| MxcError::backend_error(format!("write pool state {path:?}: {e}")))?;
    Ok(())
}

fn new_pool_state(pool_id: &str) -> PoolState {
    PoolState::new(PoolConfig {
        pool_id: pool_id.to_string(),
        ..PoolConfig::default()
    })
}

// ---------------------------------------------------------------------------
// Pool Operations
// ---------------------------------------------------------------------------

/// Retrieve live status report of a standby pool.
pub fn get_pool_status(pool_id: &str) -> Result<PoolStatusReport, MxcError> {
    validate_pool_id(pool_id)?;
    let _lock = acquire_pool_lock(pool_id)?;

    let state = read_pool_state(pool_id)?.unwrap_or_else(|| new_pool_state(pool_id));
    Ok(state.into_report())
}

/// Configure a pool's target size, ready-standby ceiling, base image path, and
/// credential target. Creates the pool if it does not exist yet.
pub fn configure_pool(
    pool_id: &str,
    target_size: usize,
    max_ready_standby: Option<usize>,
    base_image_path: &str,
    guest_credential_target: Option<String>,
) -> Result<PoolStatusReport, MxcError> {
    validate_pool_id(pool_id)?;
    if target_size == 0 {
        return Err(MxcError::malformed_request(
            "pool target size must be at least 1",
        ));
    }
    if let Some(max) = max_ready_standby {
        if max < target_size {
            return Err(MxcError::malformed_request(format!(
                "pool max size ({max}) must be at least the target size ({target_size})"
            )));
        }
    }
    if !base_image_path.trim().is_empty() && !Path::new(base_image_path).exists() {
        return Err(MxcError::malformed_request(format!(
            "base image path {base_image_path:?} does not exist"
        )));
    }

    let _lock = acquire_pool_lock(pool_id)?;

    let mut state = read_pool_state(pool_id)?.unwrap_or_else(|| new_pool_state(pool_id));
    state.config.target_size = target_size;
    if max_ready_standby.is_some() {
        state.config.max_ready_standby = max_ready_standby;
    }
    if !base_image_path.trim().is_empty() {
        state.config.base_image_path = base_image_path.to_string();
    }
    if guest_credential_target.is_some() {
        state.config.guest_credential_target = guest_credential_target;
    }
    write_pool_state(pool_id, &state)?;

    Ok(state.into_report())
}

/// Replenish a pool by provisioning and warming up VMs until it holds the
/// desired number of `Ready` standby members.
///
/// - `target_override == None` (`pool-replenish`): bring the pool up to its
///   configured `target_size` (`min_ready_standby`).
/// - `target_override == Some(n)` (`pool-warm --count n`): pre-warm up to `n`
///   ready members, clamped to the pool's `max_ready_standby`.
///
/// Leased members do not count towards the goal, so a replenish after a lease
/// provisions a replacement standby.
pub fn replenish_pool(
    pool_id: &str,
    target_override: Option<usize>,
) -> Result<PoolStatusReport, MxcError> {
    validate_pool_id(pool_id)?;

    // Serialize replenishment runs per pool so concurrent leases / replenish
    // requests don't stampede VM provisioning. If another replenishment is
    // actively running on this pool, return the current status report immediately.
    let _replenish_lock = match try_acquire_replenish_lock(pool_id)? {
        Some(lock) => lock,
        None => {
            let state = read_pool_state(pool_id)?.ok_or_else(|| {
                MxcError::malformed_request(format!("pool {pool_id:?} has not been configured yet"))
            })?;
            return Ok(state.into_report());
        }
    };

    loop {
        let (needed, base_image_path, guest_credential_target) = {
            let _lock = acquire_pool_lock(pool_id)?;
            let state = read_pool_state(pool_id)?.ok_or_else(|| {
                MxcError::malformed_request(format!(
                    "pool {pool_id:?} has not been configured yet; call configure_pool first with base image path"
                ))
            })?;

            if state.config.base_image_path.trim().is_empty() {
                return Err(MxcError::malformed_request(
                    "pool base_image_path is not set; configure pool before replenishing",
                ));
            }

            let goal = match target_override {
                Some(count) => count.min(state.config.effective_max_ready()),
                None => state.config.target_size,
            };

            let ready_count = state.count(PoolMemberStatus::Ready);
            (
                ready_count < goal,
                state.config.base_image_path.clone(),
                state.config.guest_credential_target.clone(),
            )
        };

        if !needed {
            break;
        }

        let token = mint_random_token();
        let sandbox_id = format!("hv:{token}");
        let vm_name = hyperv_common::vm_naming::vm_name_for_token(&token);

        let child_disk = hyperv_common::vm_naming::child_disk_path(
            &control_plane::state_aware_root(),
            &token,
            &base_image_path,
        );

        // 1. Provision disk and VM
        hyperv_common::cmdlets::new_differencing_disk(&base_image_path, &child_disk)
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

        // 2c. Wait for PowerShell Direct (vmicvmsession / WinRM) to accept connections
        // before capturing `pool-clean-baseline`, preventing mid-boot snapshots.
        if let Some(target) = guest_credential_target.as_deref() {
            if let Ok(cred) = hyperv_common::credential::resolve_guest_credential(target) {
                let deadline = std::time::Instant::now() + Duration::from_secs(60);
                while std::time::Instant::now() < deadline {
                    if hyperv_common::cmdlets::invoke_command_in_vm(&vm_name, &cred, "exit 0", None)
                        .is_ok()
                    {
                        break;
                    }
                    std::thread::sleep(Duration::from_secs(2));
                }
            }
        }

        // 3. Take clean baseline snapshot
        hyperv_common::cmdlets::checkpoint_vm(&vm_name, CLEAN_BASELINE_SNAPSHOT)
            .map_err(|e| map_powershell_error("pool baseline checkpoint", e))?;

        // 4. Suspend/save VM for fast resume
        let _ = hyperv_common::cmdlets::suspend_vm(&vm_name);

        // 5. Create durable sandbox record so wxc-exec recognizes this container
        let record = HypervSandboxRecord::new_provisioned(
            sandbox_id.clone(),
            vm_name.clone(),
            base_image_path.clone(),
            child_disk,
            guest_credential_target.clone(),
        );
        let _ = control_plane::write_sandbox_record(&token, &record);

        // Register the new member under pool lock
        {
            let _lock = acquire_pool_lock(pool_id)?;
            let mut state = read_pool_state(pool_id)?.ok_or_else(|| {
                MxcError::backend_error(format!("pool {pool_id:?} disappeared during replenish"))
            })?;
            state.members.push(PoolMember {
                token,
                sandbox_id,
                vm_name,
                status: PoolMemberStatus::Ready,
                leased_to: None,
                leased_at_utc: None,
            });
            write_pool_state(pool_id, &state)?;
        }
    }

    let _lock = acquire_pool_lock(pool_id)?;
    let state = read_pool_state(pool_id)?.ok_or_else(|| {
        MxcError::backend_error(format!("pool {pool_id:?} disappeared during replenish"))
    })?;
    Ok(state.into_report())
}

/// Instant checkout: Lease a warm standby VM from a pool (<300ms).
pub fn lease_from_pool(pool_id: &str, lease_holder: Option<&str>) -> Result<String, MxcError> {
    validate_pool_id(pool_id)?;
    let _lock = acquire_pool_lock(pool_id)?;

    let mut state = read_pool_state(pool_id)?.ok_or_else(|| {
        MxcError::not_provisioned(format!(
            "standby pool {pool_id:?} is not initialized; call replenish_pool first"
        ))
    })?;

    let (token, vm_name, leased_sandbox_id) = {
        let ready_member = state
            .members
            .iter_mut()
            .find(|m| m.status == PoolMemberStatus::Ready);

        let member = match ready_member {
            Some(m) => m,
            None => {
                return Err(MxcError::backend_error(format!(
                    "no standby VMs currently ready in pool {pool_id:?}; all instances are leased"
                )));
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

        (
            member.token.clone(),
            member.vm_name.clone(),
            member.sandbox_id.clone(),
        )
    };

    // Fast wake/resume
    let _ = hyperv_common::cmdlets::resume_vm(&vm_name);

    // Transition sandbox record to Started so wxc-exec accepts commands immediately
    if let Ok(Some(mut record)) = control_plane::read_sandbox_record(&token) {
        record.state = HypervSandboxState::Started;
        let _ = control_plane::write_sandbox_record(&token, &record);
    }

    write_pool_state(pool_id, &state)?;

    let ready_count = state.count(PoolMemberStatus::Ready);
    let target_size = state.config.target_size;

    // Drop the pool lock before spawning background replenishment
    drop(_lock);

    if ready_count < target_size {
        trigger_background_replenish(pool_id);
    }

    Ok(leased_sandbox_id)
}

/// Locate the pool that owns `token` by scanning every pool's state.
fn find_pool_for_token(token: &str) -> Result<String, MxcError> {
    for id in list_pool_ids() {
        if let Some(state) = read_pool_state(&id)? {
            if state.members.iter().any(|m| m.token == token) {
                return Ok(id);
            }
        }
    }
    Err(MxcError::malformed_id(format!(
        "sandbox hv:{token} is not a registered member of any pool"
    )))
}

/// Return a leased VM back to its pool, resetting it to its clean baseline snapshot.
///
/// `pool_id == None` finds the owning pool by scanning every pool for the
/// sandbox's token; pass `Some` to skip the scan.
pub fn release_to_pool(pool_id: Option<&str>, sandbox_id: &str) -> Result<(), MxcError> {
    let token = extract_token(sandbox_id)?;

    let pool_id = match pool_id {
        Some(id) => {
            validate_pool_id(id)?;
            id.to_string()
        }
        None => find_pool_for_token(token)?,
    };

    // The lock is taken only for the pool that owns the sandbox, and state is
    // re-read under it so a concurrent change during the scan cannot be lost.
    let _lock = acquire_pool_lock(&pool_id)?;

    let mut state = read_pool_state(&pool_id)?.ok_or_else(|| {
        MxcError::not_provisioned(format!("standby pool {pool_id:?} is not initialized"))
    })?;

    let vm_name = {
        let member = state
            .members
            .iter_mut()
            .find(|m| m.token == token)
            .ok_or_else(|| {
                MxcError::malformed_id(format!(
                    "sandbox {sandbox_id} is not a registered member of pool {pool_id:?}"
                ))
            })?;

        member.status = PoolMemberStatus::Recycling;
        member.vm_name.clone()
    };
    write_pool_state(&pool_id, &state)?;

    // 1. Rollback to clean baseline snapshot
    let _ = hyperv_common::cmdlets::restore_vm_snapshot(&vm_name, CLEAN_BASELINE_SNAPSHOT);

    // 2. Suspend/pause VM for standby
    let _ = hyperv_common::cmdlets::suspend_vm(&vm_name);

    // 3. Transition sandbox record back to Provisioned while unleased in standby
    if let Ok(Some(mut record)) = control_plane::read_sandbox_record(token) {
        record.state = HypervSandboxState::Provisioned;
        let _ = control_plane::write_sandbox_record(token, &record);
    }

    // 4. Mark ready
    if let Some(member) = state.members.iter_mut().find(|m| m.token == token) {
        member.status = PoolMemberStatus::Ready;
        member.leased_to = None;
        member.leased_at_utc = None;
    }
    write_pool_state(&pool_id, &state)?;

    Ok(())
}

/// Forcibly power off, remove all VMs of a pool, and delete their differencing disks.
pub fn drain_pool(pool_id: &str) -> Result<(), MxcError> {
    validate_pool_id(pool_id)?;
    let _lock = acquire_pool_lock(pool_id)?;

    let mut state = match read_pool_state(pool_id)? {
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
    write_pool_state(pool_id, &state)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mxc_common::mxc_error::MxcErrorCode;

    fn member(token: &str, status: PoolMemberStatus) -> PoolMember {
        PoolMember {
            token: token.to_string(),
            sandbox_id: format!("hv:{token}"),
            vm_name: format!("mxc-hv-{token}"),
            status,
            leased_to: None,
            leased_at_utc: None,
        }
    }

    fn state_with(pool_id: &str, members: Vec<PoolMember>) -> PoolState {
        let mut state = new_pool_state(pool_id);
        state.members = members;
        state
    }

    #[test]
    fn pool_state_serializes_and_deserializes() {
        let mut state = PoolState::new(PoolConfig {
            pool_id: "prod-adpa".to_string(),
            target_size: 2,
            max_ready_standby: Some(5),
            base_image_path: r"C:\images\server2025.vhdx".to_string(),
            guest_credential_target: Some("mxc-guest".to_string()),
        });
        state
            .members
            .push(member("1234abcd", PoolMemberStatus::Ready));

        let json = serde_json::to_string(&state).unwrap();
        let decoded: PoolState = serde_json::from_str(&json).unwrap();
        assert_eq!(decoded.config.pool_id, "prod-adpa");
        assert_eq!(decoded.config.target_size, 2);
        assert_eq!(decoded.config.max_ready_standby, Some(5));
        assert_eq!(decoded.members.len(), 1);
        assert_eq!(decoded.members[0].status, PoolMemberStatus::Ready);
    }

    #[test]
    fn legacy_config_without_pool_id_deserializes_as_default_pool() {
        let json = r#"{"target_size":3,"base_image_path":"C:\\a.vhdx"}"#;
        let config: PoolConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.pool_id, DEFAULT_POOL_ID);
        assert_eq!(config.target_size, 3);
        assert_eq!(config.max_ready_standby, None);
    }

    #[test]
    fn min_ready_standby_is_accepted_as_target_size_alias() {
        let json = r#"{"min_ready_standby":4,"base_image_path":""}"#;
        let config: PoolConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.target_size, 4);
    }

    #[test]
    fn effective_max_ready_defaults_and_never_drops_below_target() {
        let mut config = PoolConfig::default();
        assert_eq!(config.effective_max_ready(), DEFAULT_POOL_MAX_SIZE);
        config.target_size = 8;
        assert_eq!(config.effective_max_ready(), 8);
        config.max_ready_standby = Some(3);
        assert_eq!(config.effective_max_ready(), 8);
        config.target_size = 2;
        assert_eq!(config.effective_max_ready(), 3);
    }

    #[test]
    fn pool_ids_are_validated_before_they_reach_the_filesystem() {
        for ok in ["default", "prod-adpa", "dev_mxc", "a", "0pool", "p1-2_3"] {
            validate_pool_id(ok).unwrap_or_else(|e| panic!("{ok:?} rejected: {e:?}"));
        }
        let too_long = "a".repeat(MAX_POOL_ID_LEN + 1);
        for bad in [
            "",
            "..",
            "../x",
            "a/b",
            "a\\b",
            "Prod",
            "-lead",
            "_lead",
            "has space",
            "dot.ted",
            "pool_state.json",
            too_long.as_str(),
        ] {
            let err = validate_pool_id(bad).unwrap_err();
            assert_eq!(err.code, MxcErrorCode::MalformedRequest, "{bad:?}");
        }
    }

    #[test]
    fn invalid_pool_id_is_rejected_by_operations() {
        assert!(get_pool_status("../evil").is_err());
        assert!(lease_from_pool("Bad Id", None).is_err());
        assert!(replenish_pool("", None).is_err());
        assert!(drain_pool("a/b").is_err());
    }

    #[test]
    fn configure_pool_rejects_zero_target_size() {
        let err = configure_pool(DEFAULT_POOL_ID, 0, None, "", None).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn configure_pool_rejects_max_below_target() {
        let err = configure_pool(DEFAULT_POOL_ID, 3, Some(2), "", None).unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn configure_pool_rejects_missing_base_image() {
        let err = configure_pool(
            DEFAULT_POOL_ID,
            2,
            None,
            r"C:\nonexistent_path\image.vhdx",
            None,
        )
        .unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedRequest);
    }

    #[test]
    fn lease_from_empty_pool_returns_error() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        write_pool_state(DEFAULT_POOL_ID, &new_pool_state(DEFAULT_POOL_ID)).unwrap();

        let err = lease_from_pool(DEFAULT_POOL_ID, Some("agent-1")).unwrap_err();
        assert!(err.message.contains("no standby VMs currently ready"));

        set_pool_root_for_test(None);
    }

    #[test]
    fn pools_are_isolated_from_each_other() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        // `prod-adpa` has a ready VM; `dev-mxc` exists but is empty.
        write_pool_state(
            "prod-adpa",
            &state_with("prod-adpa", vec![member("aaaaaaaa", PoolMemberStatus::Ready)]),
        )
        .unwrap();
        write_pool_state("dev-mxc", &new_pool_state("dev-mxc")).unwrap();

        // Leasing from the empty pool must not hand out the other pool's VM.
        let err = lease_from_pool("dev-mxc", None).unwrap_err();
        assert!(err.message.contains("no standby VMs currently ready"));

        // And status reflects only that pool's members.
        let adpa = get_pool_status("prod-adpa").unwrap();
        assert_eq!(adpa.pool_id, "prod-adpa");
        assert_eq!((adpa.ready_count, adpa.total_members), (1, 1));
        let dev = get_pool_status("dev-mxc").unwrap();
        assert_eq!((dev.ready_count, dev.total_members), (0, 0));

        // Each pool has its own state file in its own directory.
        assert!(pool_state_file("prod-adpa").exists());
        assert!(pool_state_file("dev-mxc").exists());
        assert_ne!(pool_state_file("prod-adpa"), pool_state_file("dev-mxc"));

        set_pool_root_for_test(None);
    }

    #[test]
    fn list_pool_ids_reports_every_pool_with_state() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        assert!(list_pool_ids().is_empty());
        write_pool_state("prod-sidpa", &new_pool_state("prod-sidpa")).unwrap();
        write_pool_state("dev-mxc", &new_pool_state("dev-mxc")).unwrap();
        // A directory without state, and a junk name, are ignored.
        std::fs::create_dir_all(dir.path().join("empty-pool")).unwrap();
        std::fs::create_dir_all(dir.path().join("Not Valid")).unwrap();

        assert_eq!(list_pool_ids(), vec!["dev-mxc", "prod-sidpa"]);

        set_pool_root_for_test(None);
    }

    #[test]
    fn find_pool_for_token_scans_every_pool() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        write_pool_state(
            "dev-mxc",
            &state_with("dev-mxc", vec![member("11111111", PoolMemberStatus::Leased)]),
        )
        .unwrap();
        write_pool_state(
            "prod-adpa",
            &state_with("prod-adpa", vec![member("22222222", PoolMemberStatus::Leased)]),
        )
        .unwrap();

        assert_eq!(find_pool_for_token("22222222").unwrap(), "prod-adpa");
        assert_eq!(find_pool_for_token("11111111").unwrap(), "dev-mxc");
        let err = find_pool_for_token("33333333").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);

        set_pool_root_for_test(None);
    }

    #[test]
    fn release_rejects_a_sandbox_that_is_not_in_the_named_pool() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        write_pool_state(
            "dev-mxc",
            &state_with("dev-mxc", vec![member("11111111", PoolMemberStatus::Leased)]),
        )
        .unwrap();
        write_pool_state("prod-adpa", &new_pool_state("prod-adpa")).unwrap();

        let err = release_to_pool(Some("prod-adpa"), "hv:11111111").unwrap_err();
        assert_eq!(err.code, MxcErrorCode::MalformedId);
        // The wrongly-named pool's state is untouched.
        let dev = read_pool_state("dev-mxc").unwrap().unwrap();
        assert_eq!(dev.members[0].status, PoolMemberStatus::Leased);

        set_pool_root_for_test(None);
    }

    #[test]
    fn legacy_single_pool_state_migrates_to_the_default_pool() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        // A pre-multi-pool install: no pool_id, state directly under pool/.
        let legacy = r#"{
            "schema_version": 1,
            "config": {"target_size": 1, "base_image_path": "C:\\img.vhdx", "guest_credential_target": "mxc-guest"},
            "members": [{"token":"0b1e0d7e","sandbox_id":"hv:0b1e0d7e","vm_name":"mxc-hv-0b1e0d7e","status":"ready"}]
        }"#;
        std::fs::write(dir.path().join(POOL_STATE_FILE_NAME), legacy).unwrap();
        assert_eq!(list_pool_ids(), vec![DEFAULT_POOL_ID]);

        let state = read_pool_state(DEFAULT_POOL_ID).unwrap().unwrap();
        assert_eq!(state.config.pool_id, DEFAULT_POOL_ID);
        assert_eq!(state.members.len(), 1);
        assert_eq!(state.members[0].sandbox_id, "hv:0b1e0d7e");

        // The file moved; the legacy location no longer exists.
        assert!(pool_state_file(DEFAULT_POOL_ID).exists());
        assert!(!dir.path().join(POOL_STATE_FILE_NAME).exists());
        // And it is still found (once) after migration.
        assert_eq!(list_pool_ids(), vec![DEFAULT_POOL_ID]);

        set_pool_root_for_test(None);
    }

    #[test]
    fn migration_never_overwrites_an_existing_default_pool() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));

        write_pool_state(
            DEFAULT_POOL_ID,
            &state_with(DEFAULT_POOL_ID, vec![member("aaaaaaaa", PoolMemberStatus::Ready)]),
        )
        .unwrap();
        std::fs::write(
            dir.path().join(POOL_STATE_FILE_NAME),
            r#"{"schema_version":1,"config":{"target_size":9,"base_image_path":""},"members":[]}"#,
        )
        .unwrap();

        let state = read_pool_state(DEFAULT_POOL_ID).unwrap().unwrap();
        assert_eq!(state.members.len(), 1, "existing default pool must win");
        assert!(dir.path().join(POOL_STATE_FILE_NAME).exists());

        set_pool_root_for_test(None);
    }

    #[test]
    fn lease_triggers_background_replenish_when_below_target() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));
        let pool = "trig-below";

        let mut st = state_with(pool, vec![member("11111111", PoolMemberStatus::Ready)]);
        st.config.target_size = 1;
        write_pool_state(pool, &st).unwrap();

        assert_eq!(test_replenish_trigger::count_for(pool), 0);

        // Leasing the only ready member leaves ready_count = 0 < target_size (1)
        let leased = lease_from_pool(pool, Some("agent")).unwrap();
        assert_eq!(leased, "hv:11111111");

        // Background replenishment was triggered per AC-05.1
        assert_eq!(test_replenish_trigger::count_for(pool), 1);

        set_pool_root_for_test(None);
    }

    #[test]
    fn lease_does_not_trigger_replenish_when_buffer_satisfied() {
        let dir = tempfile::tempdir().unwrap();
        set_pool_root_for_test(Some(dir.path().to_path_buf()));
        let pool = "trig-satisfied";

        let mut st = state_with(
            pool,
            vec![
                member("11111111", PoolMemberStatus::Ready),
                member("22222222", PoolMemberStatus::Ready),
            ],
        );
        st.config.target_size = 1;
        write_pool_state(pool, &st).unwrap();

        assert_eq!(test_replenish_trigger::count_for(pool), 0);

        // Leasing 1 leaves ready_count = 1 >= target_size (1)
        let _ = lease_from_pool(pool, Some("agent")).unwrap();

        // Replenish was NOT triggered because ready buffer is still satisfied
        assert_eq!(test_replenish_trigger::count_for(pool), 0);

        set_pool_root_for_test(None);
    }

    #[test]
    fn replenish_lock_deduplicates_concurrent_replenishment() {
        use std::sync::mpsc;

        let pool_id = format!("dedup-{}", mint_random_token());
        let (held_tx, held_rx) = mpsc::channel::<()>();
        let (release_tx, release_rx) = mpsc::channel::<()>();

        let thread_pool = pool_id.clone();
        let holder = std::thread::spawn(move || {
            let _lock = TransitionLock::acquire(
                &pool_replenish_lock_name(&thread_pool),
                Duration::from_secs(5),
            )
            .expect("initial lock acquisition");
            held_tx.send(()).unwrap();
            release_rx.recv().ok();
        });
        held_rx.recv().unwrap();

        // From another thread, acquiring replenish lock non-blocking fails immediately
        let second = try_acquire_replenish_lock(&pool_id).unwrap();
        assert!(
            second.is_none(),
            "second acquire must return None while lock is held by another thread"
        );

        let _ = release_tx.send(());
        holder.join().unwrap();

        // Once released by holder thread, acquire succeeds
        let third = try_acquire_replenish_lock(&pool_id).unwrap();
        assert!(
            third.is_some(),
            "subsequent acquire must succeed once previous dropped"
        );
    }
}
