// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Hyper-V containment backend: `StatefulSandboxBackend` over real,
//! standalone Hyper-V VMs with persistent state, pause/resume, and
//! checkpoint/rollback.
//!
//! State-aware only — see the backend doc for why this backend implements no
//! `ScriptRunner`.

pub mod backend_ops;
pub mod control_plane;
pub mod error;
pub mod image;
pub mod state_aware;

pub use state_aware::HypervProvisionMetadata;

pub struct HypervRunner;

impl HypervRunner {
    pub fn new() -> Self {
        Self
    }
}

impl Default for HypervRunner {
    fn default() -> Self {
        Self::new()
    }
}
