// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Durable per-sandbox records for the Hyper-V backend.
//!
//! Unlike Windows Sandbox, there is no daemon and no single-VM-slot
//! constraint: Hyper-V's own always-on Virtual Machine Management Service
//! holds every VM open, addressable by any process at any time via
//! `Get-VM`/`Start-VM`/etc. Each phase call is a short-lived process that
//! reads/writes this on-disk record; [`os::TransitionLock`] serializes
//! concurrent calls against the *same* sandbox token only.

use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

pub mod os;
pub use os::TransitionLock;

/// Current on-disk record schema. Bump when the record shape changes
/// incompatibly; readers reject mismatches via [`check_schema`].
pub const RECORD_SCHEMA_VERSION: u32 = 1;

/// Lifecycle state of a provisioned Hyper-V sandbox.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum HypervSandboxState {
    /// The VM and its differencing disk exist; the VM is off.
    Provisioned,
    /// The VM is running (or paused/suspended — see the backend-private
    /// pause/resume operations, which do not change this record state).
    Started,
    /// The VM has been saved to disk (`stop` always uses `Save-VM`); the
    /// record persists for a later `start`.
    Stopped,
}

/// Per-sandbox durable record (`<token>\record.json`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HypervSandboxRecord {
    pub schema_version: u32,
    pub sandbox_id: String,
    pub vm_name: String,
    pub base_image_path: String,
    pub child_disk_path: PathBuf,
    pub guest_credential_target: Option<String>,
    pub state: HypervSandboxState,
}

impl HypervSandboxRecord {
    /// Construct a freshly-provisioned record.
    pub fn new_provisioned(
        sandbox_id: String,
        vm_name: String,
        base_image_path: String,
        child_disk_path: PathBuf,
        guest_credential_target: Option<String>,
    ) -> Self {
        Self {
            schema_version: RECORD_SCHEMA_VERSION,
            sandbox_id,
            vm_name,
            base_image_path,
            child_disk_path,
            guest_credential_target,
            state: HypervSandboxState::Provisioned,
        }
    }
}

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

/// Root directory for state-aware records. `%ProgramData%`, not `%TEMP%`:
/// there is no daemon tying bookkeeping to one user's session, and Hyper-V
/// management itself already requires elevated / Hyper-V-Administrators
/// rights regardless of caller identity.
pub fn state_aware_root() -> PathBuf {
    #[cfg(test)]
    {
        if let Some(p) = test_root::get() {
            return p;
        }
    }
    program_data_dir()
        .join("mxc")
        .join("hyperv")
        .join("state-aware")
}

#[cfg(windows)]
fn program_data_dir() -> PathBuf {
    std::env::var_os("ProgramData")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(r"C:\ProgramData"))
}

#[cfg(not(windows))]
fn program_data_dir() -> PathBuf {
    std::env::temp_dir()
}

/// Create and secure the record root before reading trusted state from it.
pub fn secure_record_root() -> Result<()> {
    os::ensure_secure_dir(&state_aware_root())
}

/// Per-sandbox scratch directory: `<root>\<token>`. `token` is the tail of
/// `sandbox_id` (`hv:<token>`); callers pass the bare token so the path stays
/// free of the `:` separator.
pub fn sandbox_dir(token: &str) -> PathBuf {
    state_aware_root().join(token)
}

/// Per-sandbox record file: `<root>\<token>\record.json`.
pub fn sandbox_record_path(token: &str) -> PathBuf {
    sandbox_dir(token).join("record.json")
}

/// Serialise a JSON record through an atomic same-directory rename.
pub fn atomic_write_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let parent = path
        .parent()
        .context("record path has no parent directory")?;
    std::fs::create_dir_all(parent).with_context(|| format!("create record dir {:?}", parent))?;

    // Secure the directory before creating the temp file. A later DACL
    // change would not revoke an attacker's already-open handle to it.
    os::set_owner_only_dir(parent).with_context(|| format!("secure record dir {:?}", parent))?;

    let json = serde_json::to_vec_pretty(value).context("serialise record")?;
    let tmp = parent.join(format!("{}.tmp", temp_suffix()));
    std::fs::write(&tmp, &json).with_context(|| format!("write temp record {:?}", tmp))?;

    if let Err(e) = os::set_owner_only_file(&tmp) {
        let _ = std::fs::remove_file(&tmp);
        return Err(e).with_context(|| format!("secure record DACL {:?}", tmp));
    }

    if let Err(e) = std::fs::rename(&tmp, path) {
        let _ = std::fs::remove_file(&tmp);
        return Err(e).with_context(|| format!("rename {:?} -> {:?}", tmp, path));
    }
    Ok(())
}

/// A unique-enough suffix for a temp file in the same directory as the
/// target, without pulling in a UUID dependency for this one call site.
fn temp_suffix() -> String {
    use std::sync::atomic::{AtomicU64, Ordering};
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let n = COUNTER.fetch_add(1, Ordering::Relaxed);
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    format!("{}-{:x}-{n:x}", std::process::id(), nanos)
}

/// Read and deserialise a JSON record. `Ok(None)` if the file does not
/// exist; `Err` for a present-but-unreadable/unparseable file.
pub fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<Option<T>> {
    match std::fs::read_to_string(path) {
        Ok(s) => {
            let value =
                serde_json::from_str(&s).with_context(|| format!("parse record {:?}", path))?;
            Ok(Some(value))
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(e).with_context(|| format!("read record {:?}", path)),
    }
}

/// Reject a record whose schema does not match what this build understands.
pub fn check_schema(found: u32) -> Result<()> {
    if found != RECORD_SCHEMA_VERSION {
        anyhow::bail!(
            "sandbox record schema {} is incompatible with supported schema {}",
            found,
            RECORD_SCHEMA_VERSION
        );
    }
    Ok(())
}

/// Read the per-sandbox record for `token`, validating its schema. `Ok(None)`
/// if the record does not exist.
pub fn read_sandbox_record(token: &str) -> Result<Option<HypervSandboxRecord>> {
    let Some(record) = read_json::<HypervSandboxRecord>(&sandbox_record_path(token))? else {
        return Ok(None);
    };
    check_schema(record.schema_version)?;
    Ok(Some(record))
}

/// Atomically write the per-sandbox `record` for `token` to disk.
pub fn write_sandbox_record(token: &str, record: &HypervSandboxRecord) -> Result<()> {
    atomic_write_json(&sandbox_record_path(token), record)
}

/// Remove the per-sandbox directory, treating `NotFound` as success.
pub fn remove_sandbox_dir(token: &str) -> std::io::Result<()> {
    match std::fs::remove_dir_all(sandbox_dir(token)) {
        Ok(()) => Ok(()),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(e) => Err(e),
    }
}

#[cfg(test)]
mod test_root {
    use std::path::PathBuf;
    use std::sync::{Mutex, OnceLock};

    static OVERRIDE: OnceLock<Mutex<Option<PathBuf>>> = OnceLock::new();
    fn slot() -> &'static Mutex<Option<PathBuf>> {
        OVERRIDE.get_or_init(|| Mutex::new(None))
    }
    pub fn set(p: Option<PathBuf>) {
        *slot().lock().expect("test_root mutex poisoned") = p;
    }
    pub fn get() -> Option<PathBuf> {
        slot().lock().expect("test_root mutex poisoned").clone()
    }
}

/// Redirect [`state_aware_root`] for a test.
#[cfg(test)]
pub fn set_state_aware_root_for_test(path: Option<PathBuf>) {
    test_root::set(path);
}

/// Serialises tests that override [`state_aware_root`].
#[cfg(test)]
pub static STATE_AWARE_TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn paths_are_nested_under_root() {
        let _guard = STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let root = state_aware_root();
        assert_eq!(root, dir.path());
        assert_eq!(sandbox_dir("abc"), root.join("abc"));
        assert_eq!(
            sandbox_record_path("abc"),
            root.join("abc").join("record.json")
        );

        set_state_aware_root_for_test(None);
    }

    #[test]
    fn sandbox_record_roundtrips() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("record.json");
        let rec = HypervSandboxRecord::new_provisioned(
            "hv:deadbeef".to_string(),
            "mxc-hv-deadbeef".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            dir.path().join("deadbeef").join("disk.avhdx"),
            Some("mxc-hyperv:golden-image".to_string()),
        );
        atomic_write_json(&path, &rec).unwrap();
        let back: HypervSandboxRecord = read_json(&path).unwrap().unwrap();
        assert_eq!(back, rec);
        assert_eq!(back.state, HypervSandboxState::Provisioned);
    }

    #[test]
    fn atomic_write_overwrites_existing_and_leaves_no_temp_files() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("record.json");
        let mut rec = HypervSandboxRecord::new_provisioned(
            "hv:x".to_string(),
            "mxc-hv-x".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            dir.path().join("x").join("disk.avhdx"),
            None,
        );
        atomic_write_json(&path, &rec).unwrap();
        rec.state = HypervSandboxState::Started;
        atomic_write_json(&path, &rec).unwrap();
        let back: HypervSandboxRecord = read_json(&path).unwrap().unwrap();
        assert_eq!(back.state, HypervSandboxState::Started);

        let leftovers: Vec<_> = std::fs::read_dir(dir.path())
            .unwrap()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_name().to_string_lossy().ends_with(".tmp"))
            .collect();
        assert!(leftovers.is_empty(), "temp files leaked: {:?}", leftovers);
    }

    #[test]
    fn check_schema_rejects_mismatch() {
        assert!(check_schema(RECORD_SCHEMA_VERSION).is_ok());
        assert!(check_schema(RECORD_SCHEMA_VERSION + 1).is_err());
    }

    #[test]
    fn read_json_missing_is_none() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("nope.json");
        let back: Option<HypervSandboxRecord> = read_json(&path).unwrap();
        assert!(back.is_none());
    }

    #[test]
    fn read_sandbox_record_missing_is_none() {
        let _guard = STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        assert!(read_sandbox_record("nope").unwrap().is_none());

        set_state_aware_root_for_test(None);
    }

    #[test]
    fn write_then_read_then_remove_round_trips() {
        let _guard = STATE_AWARE_TEST_LOCK.lock().unwrap();
        let dir = tempfile::tempdir().unwrap();
        set_state_aware_root_for_test(Some(dir.path().to_path_buf()));

        let rec = HypervSandboxRecord::new_provisioned(
            "hv:cafef00d".to_string(),
            "mxc-hv-cafef00d".to_string(),
            r"C:\images\golden.vhdx".to_string(),
            sandbox_dir("cafef00d").join("disk.avhdx"),
            None,
        );
        write_sandbox_record("cafef00d", &rec).unwrap();
        let back = read_sandbox_record("cafef00d").unwrap().unwrap();
        assert_eq!(back, rec);

        remove_sandbox_dir("cafef00d").unwrap();
        assert!(read_sandbox_record("cafef00d").unwrap().is_none());

        set_state_aware_root_for_test(None);
    }
}
