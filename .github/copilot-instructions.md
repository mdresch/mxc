# MXC Hyper-V Sandbox Workflow

When executing shell commands, running tests, or installing packages, ALWAYS use the `mxc-hyperv` MCP tools instead of the host terminal:
1. Call `inspect_status` first to verify the guest VM is `Running`.
2. Call `sync_workspace_to_guest` to push the current host workspace into the guest VHDX and initialize a baseline manifest.
3. Call `create_checkpoint` (e.g., `name="pre-test"`) before installing packages or making destructive edits.
4. Run all builds, refactoring, and tests inside the guest via `execute_command`.
5. If an experiment corrupts the environment, call `rollback_checkpoint` to reset in ~2 seconds (clock is automatically resynced).
6. Once tests pass inside the guest, call `export_diff_from_guest` to review the verified unified git diff.
7. Call `apply_guest_changes_to_host` (with `dry_run=False`) to losslessly apply additions, modifications, and deletions directly to the host repository.

- **Ephemeral Execution**: For risky package installs, untrusted scripts, or experimental runs where you want guaranteed zero state pollution, pass `disposable=True` to `execute_command`. The sandbox automatically snapshots before running and rolls back state and cleans up the snapshot upon completion.
