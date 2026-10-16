# MXC Autonomous Engineering & Sandbox Protocol
# Harmonized with ECC (Everything Claude Code) Cognitive Guardrails

## Core Engineering Principles
1. **Plan Before Modifying**: Never edit code or invoke commands without first stating a clear hypothesis, risk assessment, and step-by-step implementation plan.
2. **Test-Driven Discipline (TDD)**: Write or update unit/integration tests before writing implementation code. Verify failures before implementing fixes.
3. **Mandatory Sandboxed Execution**: NEVER run untrusted scripts, heavy cargo builds, test suites, or package installations directly on the host machine. Route all execution through the isolated MXC Hyper-V sandbox via MCP tools or PowerShell Direct.
4. **Autonomous Self-Healing**: When a test fails in the sandbox, analyze compiler errors and diagnostics autonomously, adjust code, and re-run without asking the user for trivial permissions.

---

## MXC Hyper-V Sandbox Workflow

When executing commands, testing, or building:
1. **Inspect / Auto-Lease**:
   - MCP tools default to `sandbox_id="auto"`, which automatically checks out a pre-warmed VM from the warm standby pool in `<300ms` or uses the active session.
   - Call `inspect_status` or `session_status` to verify VM health and readiness.
2. **Synchronize Workspace**:
   - Call `sync_workspace_to_guest` to push host workspace state into `C:\workspace` in the guest VHDX via fast VMBus transfer. This automatically creates `.sync_manifest.json` as a baseline tracker.
3. **Defensive Checkpoints & Disposable Mode**:
   - For complex multi-step refactors, call `create_checkpoint(name="pre-refactor")`.
   - For risky installs or speculative one-shot checks, pass `disposable=True` to `execute_command`. This automatically creates an ephemeral checkpoint (or leases a clean pool VM) and rolls back cleanly in a `finally` block, leaving absolute zero state residue.
4. **Isolated Build & Test**:
   - Execute builds and tests inside the VM via `execute_command`.
   - If network access is required (e.g. downloading crates or packages), call `set_network(enabled=True)` (or `mxnet`), execute the build, and immediately restore airgap isolation via `set_network(enabled=False)` (or `mxair`).
5. **Multimodal Visual Inspection**:
   - If testing GUI apps, installers, web dashboards, or Windows console states, call `capture_screenshot` to retrieve a crystal-clear PNG frame from the Hyper-V synthetic video buffer without needing any guest-side agent.
6. **Self-Healing Rollback**:
   - If an experimental refactor fails or corrupts the environment, call `rollback_checkpoint` to restore clean state in ~2 seconds (guest clock is automatically resynchronized).
7. **Lossless Diff Review & Host Application**:
   - Call `export_diff_from_guest` to inspect the exact unified git diff (including additions, modifications, and deletions) tracked against the baseline manifest.
   - Call `apply_guest_changes_to_host(dry_run=True)` to preview changes, then `apply_guest_changes_to_host(dry_run=False)` to losslessly apply verified changes directly back to your host repository.
8. **Release Session**:
   - When finished with a task session, call `session_release()` (or `mxc-pool-release`) to reset the VM back to its clean baseline snapshot and return it to the ready pool.

