# MXC Hyper-V Sandbox Workflow

When executing shell commands, running tests, or installing packages, ALWAYS use the `mxc-hyperv` MCP tools instead of the host terminal:
1. Call `inspect_status` first to verify the guest VM is `Running`.
2. Call `sync_workspace_to_guest` to push the current host workspace into the guest VHDX.
3. Call `create_checkpoint` (e.g., `name="pre-test"`) before installing packages or making destructive edits.
4. Run all builds and tests inside the guest via `execute_command`.
5. If an experiment corrupts the environment, call `rollback_checkpoint` to reset in ~2 seconds.
6. Once tests pass inside the guest, call `export_diff_from_guest` to review or apply the clean changes back to the host.
