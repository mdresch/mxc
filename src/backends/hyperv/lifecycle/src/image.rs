// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! Base VHDX validation.
//!
//! MXC's job is provisioning a differencing disk off an operator-supplied
//! parent VHDX; building or authoring the golden image (sysprep, DISM,
//! Packer) is an operator prerequisite, not performed here. This only
//! confirms the supplied path looks like a usable, existing VHDX/VHD file —
//! deliberately simpler than WSLC's image resolution (no cache tier, no
//! registry pull).

use std::path::Path;

use wxc_common::mxc_error::MxcError;

const VALID_EXTENSIONS: &[&str] = &["vhdx", "vhd"];

pub fn validate_base_image_path(path: &str) -> Result<(), MxcError> {
    if path.trim().is_empty() {
        return Err(MxcError::policy_validation(
            "hyperv.provision.baseImagePath is required",
        ));
    }
    let p = Path::new(path);
    let ext_ok = p
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| VALID_EXTENSIONS.contains(&e.to_ascii_lowercase().as_str()))
        .unwrap_or(false);
    if !ext_ok {
        return Err(MxcError::policy_validation(format!(
            "hyperv.provision.baseImagePath must point to a .vhdx or .vhd file, got {path:?}"
        )));
    }
    if !p.is_file() {
        return Err(MxcError::policy_validation(format!(
            "hyperv.provision.baseImagePath {path:?} does not exist or is not a file"
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_empty_path() {
        let err = validate_base_image_path("").unwrap_err();
        assert!(err.message.contains("required"));
    }

    #[test]
    fn rejects_blank_path() {
        let err = validate_base_image_path("   ").unwrap_err();
        assert!(err.message.contains("required"));
    }

    #[test]
    fn rejects_wrong_extension() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("golden.iso");
        std::fs::write(&path, b"not a vhdx").unwrap();
        let err = validate_base_image_path(path.to_str().unwrap()).unwrap_err();
        assert!(err.message.contains("vhdx"));
    }

    #[test]
    fn rejects_missing_file() {
        let err = validate_base_image_path(r"C:\does\not\exist\golden.vhdx").unwrap_err();
        assert!(err.message.contains("does not exist"));
    }

    #[test]
    fn accepts_existing_vhdx() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("golden.vhdx");
        std::fs::write(&path, b"fake vhdx content").unwrap();
        assert!(validate_base_image_path(path.to_str().unwrap()).is_ok());
    }

    #[test]
    fn accepts_existing_vhd() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("golden.vhd");
        std::fs::write(&path, b"fake vhd content").unwrap();
        assert!(validate_base_image_path(path.to_str().unwrap()).is_ok());
    }

    #[test]
    fn extension_check_is_case_insensitive() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("golden.VHDX");
        std::fs::write(&path, b"fake vhdx content").unwrap();
        assert!(validate_base_image_path(path.to_str().unwrap()).is_ok());
    }
}
