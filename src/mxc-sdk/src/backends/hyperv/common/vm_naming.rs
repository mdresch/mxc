// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//! VM name and on-disk child-disk path derivation from a sandbox token.

use std::path::{Path, PathBuf};

/// Hyper-V VM name for a sandbox token (the tail of a `hv:<token>` sandbox id).
pub fn vm_name_for_token(token: &str) -> String {
    format!("mxc-hv-{token}")
}

/// Per-sandbox differencing disk path under `state_dir`.
///
/// Matches the file extension of `base_image_path` (`.vhdx` or `.vhd`)
/// because Hyper-V requires parent and differencing child disks to share the
/// same format.
pub fn child_disk_path(state_dir: &Path, token: &str, base_image_path: &str) -> PathBuf {
    let ext = Path::new(base_image_path)
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_ascii_lowercase())
        .unwrap_or_else(|| "vhdx".to_string());
    let filename = format!("disk.{ext}");
    state_dir.join(token).join(filename)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn vm_name_has_expected_prefix() {
        assert_eq!(vm_name_for_token("abcd1234"), "mxc-hv-abcd1234");
    }

    #[test]
    fn vm_name_is_distinct_per_token() {
        assert_ne!(vm_name_for_token("aaaaaaaa"), vm_name_for_token("bbbbbbbb"));
    }

    #[test]
    fn child_disk_path_is_nested_under_token_dir_and_matches_extension() {
        let root = Path::new(r"C:\mxc\hyperv\state-aware");
        let path_vhdx = child_disk_path(root, "abcd1234", r"C:\base\golden.vhdx");
        assert_eq!(path_vhdx, root.join("abcd1234").join("disk.vhdx"));

        let path_vhd = child_disk_path(root, "abcd1234", r"C:\base\golden.vhd");
        assert_eq!(path_vhd, root.join("abcd1234").join("disk.vhd"));
    }
}
