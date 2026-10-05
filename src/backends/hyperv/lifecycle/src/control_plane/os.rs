// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Win32 DACL and named-mutex primitives for the Hyper-V control plane.
//!
//! Unlike Windows Sandbox's single fixed transition mutex (one host-wide VM
//! slot to serialize), Hyper-V has no such slot: many VMs can run
//! concurrently. [`TransitionLock`] is therefore named *per sandbox token*,
//! serializing only concurrent phase calls against the same sandbox.

use std::path::Path;

use anyhow::{Context, Result};

/// Per-session, per-token transition mutex name prefix. `Local\` (not
/// `Global\`): nothing here needs cross-session visibility, and an
/// unelevated caller may lack `SeCreateGlobalPrivilege`.
const TRANSITION_MUTEX_PREFIX: &str = r"Local\mxc-hyperv-transition-";

// ---------------------------------------------------------------------------
// Filesystem DACL helpers
// ---------------------------------------------------------------------------

/// Apply an inheritable owner-only DACL and reject directories owned by
/// another user, who would retain implicit `WRITE_DAC`.
#[cfg(windows)]
pub fn set_owner_only_dir(dir: &Path) -> Result<()> {
    wxc_common::filesystem_dacl::set_owner_only_dacl(dir, true)
        .map_err(|e| anyhow::Error::new(e).context(format!("secure dir {dir:?}")))?;
    let owned = wxc_common::filesystem_dacl::owner_is_self(dir)
        .map_err(|e| anyhow::Error::new(e).context(format!("read owner of {dir:?}")))?;
    if !owned {
        anyhow::bail!(
            "refusing to use {dir:?}: it is owned by another user (cross-user tampering risk on \
             a shared ProgramData directory). Remove it and retry."
        );
    }
    // Also grant NT VIRTUAL MACHINE\Virtual Machines (S-1-5-83-0) access so
    // Hyper-V's VM worker process (vmwp.exe) can access the differencing VHDX.
    let _ = std::process::Command::new("icacls.exe")
        .arg(dir)
        .arg("/grant")
        .arg("*S-1-5-83-0:(OI)(CI)F")
        .output();
    Ok(())
}

#[cfg(not(windows))]
pub fn set_owner_only_dir(_dir: &Path) -> Result<()> {
    Ok(())
}

/// Create and secure a directory before reading trusted state from it.
#[cfg(windows)]
pub fn ensure_secure_dir(dir: &Path) -> Result<()> {
    std::fs::create_dir_all(dir).with_context(|| format!("create dir {dir:?}"))?;
    set_owner_only_dir(dir)
}

#[cfg(not(windows))]
pub fn ensure_secure_dir(dir: &Path) -> Result<()> {
    std::fs::create_dir_all(dir).with_context(|| format!("create dir {dir:?}"))
}

/// Apply an owner-only DACL to an existing file.
#[cfg(windows)]
pub(crate) fn set_owner_only_file(path: &Path) -> Result<()> {
    wxc_common::filesystem_dacl::set_owner_only_dacl(path, false)
        .map_err(|e| anyhow::Error::new(e).context(format!("secure file {path:?}")))
}

#[cfg(not(windows))]
pub(crate) fn set_owner_only_file(_path: &Path) -> Result<()> {
    Ok(())
}

// ---------------------------------------------------------------------------
// Cross-process named mutex (per-token transition lock)
// ---------------------------------------------------------------------------

/// Try to acquire the named mutex, distinguishing contention from failure.
#[cfg(windows)]
fn named_mutex_try_acquire(
    name: &str,
    timeout: std::time::Duration,
) -> Result<Option<windows::Win32::Foundation::HANDLE>> {
    use windows::core::PCWSTR;
    use windows::Win32::Foundation::{WAIT_ABANDONED, WAIT_OBJECT_0, WAIT_TIMEOUT};
    use windows::Win32::System::Threading::{CreateMutexW, WaitForSingleObject};

    let wide: Vec<u16> = name.encode_utf16().chain(std::iter::once(0)).collect();

    // SAFETY: `wide` is a valid null-terminated UTF-16 buffer that outlives
    // the call; the returned handle is owned by the caller and closed on
    // every path (via `Drop`/explicit close below).
    let handle = unsafe { CreateMutexW(None, false, PCWSTR(wide.as_ptr())) }
        .context("create named mutex")?;

    let ms = timeout.as_millis().min(u32::MAX as u128) as u32;
    // SAFETY: `handle` is a valid mutex handle from `CreateMutexW`.
    let wait = unsafe { WaitForSingleObject(handle, ms) };
    if wait == WAIT_OBJECT_0 || wait == WAIT_ABANDONED {
        Ok(Some(handle))
    } else if wait == WAIT_TIMEOUT {
        // SAFETY: closing the handle we just created; we do not own the mutex.
        unsafe {
            let _ = windows::Win32::Foundation::CloseHandle(handle);
        }
        Ok(None)
    } else {
        // SAFETY: closing the handle we just created; we do not own the mutex.
        unsafe {
            let _ = windows::Win32::Foundation::CloseHandle(handle);
        }
        anyhow::bail!("waiting on named mutex {name:?} failed (wait result {wait:?})");
    }
}

#[cfg(windows)]
fn named_mutex_acquire(
    name: &str,
    timeout: std::time::Duration,
) -> Result<windows::Win32::Foundation::HANDLE> {
    match named_mutex_try_acquire(name, timeout)? {
        Some(handle) => Ok(handle),
        None => anyhow::bail!("timed out acquiring named mutex {name:?} after {timeout:?}"),
    }
}

#[cfg(windows)]
fn named_mutex_release(handle: windows::Win32::Foundation::HANDLE) {
    use windows::Win32::Foundation::CloseHandle;
    use windows::Win32::System::Threading::ReleaseMutex;
    // SAFETY: `handle` is a valid mutex handle owned by the caller.
    unsafe {
        let _ = ReleaseMutex(handle);
        let _ = CloseHandle(handle);
    }
}

/// RAII guard over a per-sandbox-token transition mutex. While held, no
/// other phase process can enter a transition for the *same* token — a
/// different token's lock is an entirely separate mutex, so concurrent
/// sandboxes never contend with each other. Released on drop.
#[cfg(windows)]
pub struct TransitionLock {
    handle: windows::Win32::Foundation::HANDLE,
}

#[cfg(windows)]
impl TransitionLock {
    pub fn acquire(token: &str, timeout: std::time::Duration) -> Result<Self> {
        let name = format!("{TRANSITION_MUTEX_PREFIX}{token}");
        let handle = named_mutex_acquire(&name, timeout)?;
        Ok(Self { handle })
    }
}

#[cfg(windows)]
impl Drop for TransitionLock {
    fn drop(&mut self) {
        named_mutex_release(self.handle);
    }
}

/// Non-Windows stub: named mutexes are a Windows-only concept. Hyper-V is
/// Windows-only, so this path is never reached in production — kept so the
/// crate compiles cross-platform for workspace-wide `cargo check`.
#[cfg(not(windows))]
pub struct TransitionLock;

#[cfg(not(windows))]
impl TransitionLock {
    pub fn acquire(_token: &str, _timeout: std::time::Duration) -> Result<Self> {
        Ok(Self)
    }
}

#[cfg(all(test, windows))]
mod tests {
    use super::*;

    #[test]
    fn same_token_serializes_different_tokens_do_not() {
        use std::sync::mpsc;
        use std::time::Duration;

        let suffix = format!("{:x}", std::process::id());
        let token_a = format!("test-a-{suffix}");
        let token_b = format!("test-b-{suffix}");

        // Holder thread takes token_a and holds it.
        let (held_tx, held_rx) = mpsc::channel::<()>();
        let (release_tx, release_rx) = mpsc::channel::<()>();
        let holder_token = token_a.clone();
        let holder = std::thread::spawn(move || {
            let _lock = TransitionLock::acquire(&holder_token, Duration::from_secs(5)).unwrap();
            held_tx.send(()).unwrap();
            release_rx.recv().ok();
        });
        held_rx.recv().unwrap();

        // Same token: must time out (contended).
        let contended = TransitionLock::acquire(&token_a, Duration::from_millis(100));
        assert!(contended.is_err(), "expected contention on the same token");

        // Different token: must succeed immediately even while token_a is held.
        let independent = TransitionLock::acquire(&token_b, Duration::from_secs(5));
        assert!(
            independent.is_ok(),
            "a different token must not contend with token_a's lock"
        );

        release_tx.send(()).unwrap();
        holder.join().unwrap();

        // Now that the holder released it, token_a must be acquirable again.
        let reacquired = TransitionLock::acquire(&token_a, Duration::from_secs(5));
        assert!(reacquired.is_ok());
    }
}
