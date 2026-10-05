// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

use crate::dev::state_aware::provision::ProvisionPhase;
use crate::dev::Telemetry;
use crate::dev::{OptionalField, Version};
use serde::Deserialize;

string_marker! {
    /// The `hyperv` containment of the state-aware configuration contract.
    pub struct HypervContainment => "hyperv";
}

/// Hyper-V settings accepted during provisioning.
///
/// No `filesystem`/`network` fields exist anywhere on this root — the
/// backend supports neither (no mapped-folder primitive, PowerShell Direct
/// needs no network path into the guest), so supplying either is a
/// schema-level `deny_unknown_fields` rejection rather than a runtime policy
/// refusal.
#[derive(Debug, Deserialize)]
#[cfg_attr(feature = "schema-gen", derive(schemars::JsonSchema))]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct HypervProvision {
    /// Required path to the operator-supplied parent VHDX/VHD a per-sandbox
    /// differencing disk is provisioned from. Authoring the golden image
    /// (sysprep, DISM, Packer) is an operator prerequisite.
    pub base_image_path: String,
    /// Optional Windows Credential Manager target name to resolve the
    /// PowerShell Direct guest credential from. The secret itself never
    /// appears here or anywhere on the wire.
    #[serde(default)]
    pub guest_credential_target: OptionalField<String>,
    /// Optional VM generation (1 or 2). Defaults to 2 when absent.
    #[serde(default)]
    pub generation: OptionalField<u8>,
    /// Optional guest startup memory in bytes.
    #[serde(default)]
    pub memory_startup_bytes: OptionalField<u64>,
    /// Optional virtual processor count.
    #[serde(default)]
    pub cpu_count: OptionalField<u32>,
}

/// State-aware Hyper-V settings.
#[derive(Debug, Deserialize)]
#[cfg_attr(feature = "schema-gen", derive(schemars::JsonSchema))]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct StateAwareHyperv {
    /// Required provision-phase settings (`baseImagePath` is required).
    pub provision: HypervProvision,
}

/// A complete state-aware `provision` request for Hyper-V.
#[derive(Debug, Deserialize)]
#[cfg_attr(feature = "schema-gen", derive(schemars::JsonSchema))]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct HypervProvisionRequest {
    /// Optional JSON Schema reference for editor validation.
    #[serde(rename = "$schema", default)]
    pub schema: OptionalField<String>,
    /// Optional human-readable annotation ignored by the runtime.
    #[serde(rename = "_comment", default)]
    pub comment: OptionalField<serde_json::Value>,
    /// Exact development contract version.
    pub version: Version,
    /// Exact `provision` phase marker.
    pub phase: ProvisionPhase,
    /// Exact `hyperv` containment marker.
    pub containment: HypervContainment,
    /// Optional telemetry configuration.
    #[serde(default)]
    pub telemetry: OptionalField<Telemetry>,
    /// Required Hyper-V provision settings.
    pub hyperv: StateAwareHyperv,
}
