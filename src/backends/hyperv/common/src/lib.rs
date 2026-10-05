// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Host-side Hyper-V automation primitives.
//!
//! Pure PowerShell/Hyper-V automation with no dependency on `wxc_common` — a
//! backend-neutral layer the `hyperv_lifecycle` crate builds its
//! `StatefulSandboxBackend` implementation on top of.

pub mod cmdlets;
pub mod credential;
pub mod error;
pub mod powershell;
pub mod probe;
pub mod vm_naming;
