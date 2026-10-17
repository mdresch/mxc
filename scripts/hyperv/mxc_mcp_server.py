import argparse
import base64
import difflib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import uuid
from typing import Dict, List, Optional, Tuple

try:
    from mcp.server.fastmcp import FastMCP as MCPServer
except (ImportError, ModuleNotFoundError):
    from mcp.server import MCPServer

# Initialize FastMCP / MCPServer
mcp = MCPServer("mxc-hyperv-sandbox")

# Configure paths relative to this script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WXC_BIN = os.path.normpath(os.path.join(REPO_ROOT, "src", "target", "debug", "wxc-exec.exe"))
EXEC_JSON = os.path.normpath(os.path.join(REPO_ROOT, "exec.json"))
DEFAULT_SANDBOX_ID = os.environ.get("MXC_SANDBOX_ID", "hv:a7df7452")

# Active session sandbox ID (persists across multi-step agent actions until released)
_ACTIVE_SESSION_SANDBOX: Optional[str] = None


def _extract_json_payload(output: str) -> Optional[dict]:
    """Extract and parse JSON object from command output."""
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                pass
    try:
        start = output.find("{")
        end = output.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(output[start : end + 1])
    except Exception:
        pass
    return None


def _lease_from_pool(lease_holder: str = "mcp-agent") -> Tuple[Optional[str], str]:
    """Attempt to lease a VM from the standby pool in <300ms. Returns (sandbox_id, error_message)."""
    raw = _run_wxc(["--hyperv-op", "pool-lease", "--pool-lease-holder", lease_holder])
    if "[Exit Code: 0]" in raw:
        payload = _extract_json_payload(raw)
        if payload and "result" in payload and "sandboxId" in payload["result"]:
            return payload["result"]["sandboxId"], ""
    payload = _extract_json_payload(raw)
    err = "Unknown error leasing from pool"
    if payload and "error" in payload:
        err = payload["error"].get("message", err)
    return None, err


def _release_to_pool(sandbox_id: str) -> Tuple[bool, str]:
    """Release a leased VM back to the standby pool. Returns (success, message)."""
    raw = _run_wxc(["--hyperv-op", "pool-release", "--hyperv-sandbox-id", sandbox_id])
    return ("[Exit Code: 0]" in raw), raw


def _resolve_sandbox_id(requested_id: Optional[str] = "auto") -> str:
    """Resolve target sandbox ID:
    1. If explicit ID provided (not 'auto' or empty), use it.
    2. If an active session sandbox is bound, use it.
    3. Try auto-leasing a pre-warmed VM from the pool.
    4. Fall back to DEFAULT_SANDBOX_ID.
    """
    global _ACTIVE_SESSION_SANDBOX
    if requested_id and requested_id != "auto":
        return requested_id

    if _ACTIVE_SESSION_SANDBOX:
        return _ACTIVE_SESSION_SANDBOX

    # Attempt auto-lease from standby pool
    leased_id, _ = _lease_from_pool("mcp-auto-session")
    if leased_id:
        _ACTIVE_SESSION_SANDBOX = leased_id
        return leased_id

    return DEFAULT_SANDBOX_ID


def _run_wxc(args: list[str], timeout: int = 120) -> str:
    """Helper to invoke wxc-exec and capture combined output + exit code."""
    cmd = [WXC_BIN, "--experimental"] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        combined = "\n".join(filter(None, [output, err]))
        return f"[Exit Code: {result.returncode}]\n{combined}"
    except subprocess.TimeoutExpired:
        return f"[Error] Command timed out after {timeout} seconds."
    except Exception as e:
        return f"[Error] Failed to run wxc-exec: {str(e)}"


def _get_vm_name(sandbox_id: str) -> str:
    token = sandbox_id.replace("hv:", "").strip()
    return f"mxc-hv-{token}"


def _diff_file(rel_path: str, guest_bytes: bytes, is_new: bool = False) -> str:
    """Generate a unified diff between host file and guest modified file."""
    if b"\x00" in guest_bytes[:4096]:
        return f"Binary file {rel_path} changed in guest.\n"

    host_file = os.path.join(REPO_ROOT, rel_path)
    guest_text = guest_bytes.decode("utf-8-sig", errors="replace").splitlines(keepends=True)

    if not is_new and os.path.exists(host_file):
        with open(host_file, "r", encoding="utf-8-sig", errors="replace") as f:
            host_text = f.readlines()
        from_file = f"a/{rel_path}"
    else:
        host_text = []
        from_file = "/dev/null"

    to_file = f"b/{rel_path}"
    diff = list(difflib.unified_diff(host_text, guest_text, fromfile=from_file, tofile=to_file))
    return "".join(diff)


def _diff_deleted_file(rel_path: str) -> str:
    """Generate a unified diff representing a deleted file."""
    host_file = os.path.join(REPO_ROOT, rel_path)
    if not os.path.exists(host_file):
        return ""
    with open(host_file, "r", encoding="utf-8-sig", errors="replace") as f:
        host_text = f.readlines()
    from_file = f"a/{rel_path}"
    to_file = "/dev/null"
    diff = list(difflib.unified_diff(host_text, [], fromfile=from_file, tofile=to_file))
    return "".join(diff)


def _get_guest_changes(guest_dir: str, sandbox_id: str) -> Tuple[Dict[str, bytes], Dict[str, bytes], List[str], str]:
    """Scan guest workspace against .sync_manifest.json and return (added, modified, deleted, error)."""
    scan_script = (
        f"$target_dir = '{guest_dir}'; "
        f"$manifest_path = \"$target_dir\\.sync_manifest.json\"; "
        f"if (-not (Test-Path $manifest_path)) {{ 'NO_MANIFEST'; exit }}; "
        f"$manifest = Get-Content $manifest_path -Raw | ConvertFrom-Json; "
        f"$current = @{{}}; "
        f"Get-ChildItem -Path $target_dir -Recurse -File | Where-Object {{ "
        f"    $_.FullName -notmatch '\\\\(target|bin|obj|\\.git|node_modules)\\\\' -and "
        f"    $_.Extension -notin @('.dll', '.pdb', '.cache', '.exe', '.tar', '.gz') -and "
        f"    $_.Name -ne '.sync_manifest.json' "
        f"}} | ForEach-Object {{ "
        f"    $rel = $_.FullName.Substring($target_dir.Length).TrimStart('\\'); "
        f"    $current[$rel] = $_ "
        f"}}; "
        f"foreach ($rel in $current.Keys) {{ "
        f"    $f = $current[$rel]; "
        f"    $m = $manifest.$rel; "
        f"    if ($null -eq $m) {{ "
        f"        $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($f.FullName)); "
        f"        Write-Output ('===ADDED:' + $rel); "
        f"        Write-Output $b64; "
        f"    }} elseif ($f.Length -ne $m.l -or $f.LastWriteTimeUtc.Ticks -ne $m.t) {{ "
        f"        $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($f.FullName)); "
        f"        Write-Output ('===MODIFIED:' + $rel); "
        f"        Write-Output $b64; "
        f"    }} "
        f"}}; "
        f"foreach ($prop in $manifest.PSObject.Properties) {{ "
        f"    $rel = $prop.Name; "
        f"    if (-not $current.ContainsKey($rel)) {{ "
        f"        Write-Output ('===DELETED:' + $rel); "
        f"    }} "
        f"}}"
    )

    res = execute_command(scan_script, sandbox_id)
    if "NO_MANIFEST" in res:
        return {}, {}, [], "No sync baseline found. Please run sync_workspace_to_guest first."

    added: Dict[str, bytes] = {}
    modified: Dict[str, bytes] = {}
    deleted: List[str] = []

    lines = res.splitlines()
    curr_action = None
    curr_rel = None
    curr_b64: List[str] = []

    def _flush():
        nonlocal curr_action, curr_rel, curr_b64
        if curr_action and curr_rel:
            if curr_action in ("ADDED", "MODIFIED"):
                try:
                    payload = base64.b64decode("".join(curr_b64))
                    if curr_action == "ADDED":
                        added[curr_rel] = payload
                    else:
                        modified[curr_rel] = payload
                except Exception as e:
                    pass
            elif curr_action == "DELETED":
                deleted.append(curr_rel)
        curr_action = None
        curr_rel = None
        curr_b64 = []

    for line in lines:
        line = line.strip()
        if line.startswith("===ADDED:"):
            _flush()
            curr_action = "ADDED"
            curr_rel = line[len("===ADDED:"):]
        elif line.startswith("===MODIFIED:"):
            _flush()
            curr_action = "MODIFIED"
            curr_rel = line[len("===MODIFIED:"):]
        elif line.startswith("===DELETED:"):
            _flush()
            deleted.append(line[len("===DELETED:"):])
        elif curr_action in ("ADDED", "MODIFIED"):
            if not line.startswith("[Exit Code:") and not line.startswith("{"):
                curr_b64.append(line)

    _flush()
    return added, modified, deleted, ""


@mcp.tool()
def execute_command(
    command: str,
    sandbox_id: str = "auto",
    disposable: bool = False
) -> str:
    """Execute a shell or PowerShell command inside the isolated MXC Hyper-V guest VM.
    Passes command via Base64 UTF-16LE EncodedCommand to eliminate quoting and pipe parsing issues.

    Args:
        command: The command or script to execute inside the guest VM.
        sandbox_id: Target MXC Hyper-V sandbox ID (defaults to 'auto', which binds to active session or pool).
        disposable: If True, provides zero-residue execution. If a pool VM is available, leases it on-the-fly
                    and recycles it in a finally block; otherwise creates an ephemeral checkpoint and rolls back.
    """
    # If disposable mode with 'auto' sandbox, try on-the-fly pool lease with guaranteed recycle
    if disposable and (sandbox_id == "auto" or not sandbox_id):
        disp_id, _ = _lease_from_pool("mcp-disposable")
        if disp_id:
            try:
                b64 = base64.b64encode(command.encode("utf-16le")).decode("ascii")
                return _run_wxc([
                    "--operation", "exec",
                    "--container-id", disp_id,
                    EXEC_JSON,
                    "--",
                    "powershell.exe", "-NoProfile", "-EncodedCommand", b64
                ])
            finally:
                _release_to_pool(disp_id)

    # Standard execution path (or fallback for disposable on fixed sandbox)
    target_sb = _resolve_sandbox_id(sandbox_id)
    disp_checkpoint = None
    if disposable:
        disp_checkpoint = f"mxc-disp-{uuid.uuid4().hex[:8]}"
        ckpt_res = create_checkpoint(disp_checkpoint, target_sb)
        if "[Exit Code: 0]" not in ckpt_res:
            return f"[Error creating disposable checkpoint]: {ckpt_res}"

    try:
        b64 = base64.b64encode(command.encode("utf-16le")).decode("ascii")
        return _run_wxc([
            "--operation", "exec",
            "--container-id", target_sb,
            EXEC_JSON,
            "--",
            "powershell.exe", "-NoProfile", "-EncodedCommand", b64
        ])
    finally:
        if disp_checkpoint:
            rollback_checkpoint(disp_checkpoint, target_sb)
            vm_name = _get_vm_name(target_sb)
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-VMSnapshot -VMName '{vm_name}' -Name '{disp_checkpoint}' -ErrorAction SilentlyContinue | Remove-VMSnapshot -Confirm:$false",
                ],
                capture_output=True,
            )


@mcp.tool()
def create_checkpoint(name: str, sandbox_id: str = "auto") -> str:
    """Save a fast Hyper-V checkpoint before attempting risky refactors or package installs."""
    target_sb = _resolve_sandbox_id(sandbox_id)
    return _run_wxc([
        "--hyperv-op", "checkpoint",
        "--hyperv-sandbox-id", target_sb,
        "--hyperv-checkpoint-name", name
    ])


@mcp.tool()
def rollback_checkpoint(name: str, sandbox_id: str = "auto") -> str:
    """Restore the Hyper-V sandbox back to a named checkpoint to undo broken state.
    Automatically resynchronizes VM guest clock with host time upon completion.
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    res = _run_wxc([
        "--hyperv-op", "restore",
        "--hyperv-sandbox-id", target_sb,
        "--hyperv-checkpoint-name", name
    ])
    # Force guest clock resync to prevent timestamp skew after rollback
    execute_command("Start-Service w32time -ErrorAction SilentlyContinue; w32tm /resync /force -ErrorAction SilentlyContinue", target_sb)
    return res


@mcp.tool()
def list_checkpoints(sandbox_id: str = "auto") -> str:
    """List all available checkpoints for the active MXC Hyper-V sandbox."""
    target_sb = _resolve_sandbox_id(sandbox_id)
    return _run_wxc([
        "--hyperv-op", "list-checkpoints",
        "--hyperv-sandbox-id", target_sb
    ])


@mcp.tool()
def inspect_status(sandbox_id: str = "auto") -> str:
    """View VM power state, assigned RAM, uptime, and integration heartbeat."""
    target_sb = _resolve_sandbox_id(sandbox_id)
    vm_name = _get_vm_name(target_sb)
    ps_cmd = (
        f"Get-VM '{vm_name}' | Select-Object Name, State, "
        f"@{{N='MemoryMB';E={{[math]::Round($_.MemoryAssigned/1MB,0)}}}}, Uptime | Format-List; "
        f"Get-VMIntegrationService -VMName '{vm_name}' -Name Heartbeat | Select-Object Name, PrimaryStatusDescription | Format-List"
    )
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    return res.stdout.strip()


@mcp.tool()
def sync_workspace_to_guest(
    source_subdir: str = "",
    target_dir: str = "C:\\workspace",
    sandbox_id: str = "auto"
) -> str:
    """Synchronize host workspace files into the guest VM virtual disk (VHDX) via Hyper-V VMBus Copy-VMFile.
    Uses native tar.exe with exclusions (.git, target, bin, obj, node_modules) for sub-second packaging and transfer.
    Generates a full baseline file manifest (.sync_manifest.json) in the guest to track additions, modifications, and deletions.
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    vm_name = _get_vm_name(target_sb)
    source_path = os.path.join(REPO_ROOT, source_subdir) if source_subdir else REPO_ROOT

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        archive_path = tmp.name

    try:
        # Use native tar.exe on Windows for fast packaging excluding build output
        tar_cmd = [
            "tar.exe",
            "--exclude=target",
            "--exclude=.git",
            "--exclude=node_modules",
            "--exclude=.vscode",
            "--exclude=corpus",
            "--exclude=bin",
            "--exclude=obj",
            "--exclude=*.dll",
            "--exclude=*.pdb",
            "--exclude=*.cache",
            "--exclude=__pycache__",
            "-czf", archive_path,
            "-C", source_path,
            "."
        ]
        tar_res = subprocess.run(tar_cmd, capture_output=True, text=True)
        if tar_res.returncode != 0:
            return f"[Error creating archive on host]: {tar_res.stderr.strip()}"

        guest_archive = "C:\\transfer_workspace.tar.gz"

        # Copy archive to guest via native wxc-exec Rust backend operation
        copy_res = _run_wxc([
            "--hyperv-op", "copy-file",
            "--hyperv-sandbox-id", target_sb,
            "--hyperv-source-path", archive_path,
            "--hyperv-dest-path", guest_archive,
        ])
        if "[Exit Code: 0]" not in copy_res:
            return f"[Error copying archive to guest via wxc-exec]: {copy_res}"

        # Extract inside guest, clean up archive, and generate baseline .sync_manifest.json
        ps_extract = (
            f"$target_dir = '{target_dir}'; "
            f"if (-not (Test-Path $target_dir)) {{ New-Item -ItemType Directory -Path $target_dir -Force }}; "
            f"tar.exe -xzf '{guest_archive}' -C $target_dir; "
            f"Remove-Item '{guest_archive}' -Force; "
            f"$manifest = @{{}}; "
            f"Get-ChildItem -Path $target_dir -Recurse -File | Where-Object {{ "
            f"    $_.FullName -notmatch '\\\\(target|bin|obj|\\.git|node_modules)\\\\' -and "
            f"    $_.Extension -notin @('.dll', '.pdb', '.cache', '.exe', '.tar', '.gz') -and "
            f"    $_.Name -ne '.sync_manifest.json' "
            f"}} | ForEach-Object {{ "
            f"    $rel = $_.FullName.Substring($target_dir.Length).TrimStart('\\'); "
            f"    $manifest[$rel] = @{{ l = $_.Length; t = $_.LastWriteTimeUtc.Ticks }} "
            f"}}; "
            f"$manifest | ConvertTo-Json -Compress | Set-Content -Path \"$target_dir\\.sync_manifest.json\" -Encoding utf8"
        )
        extract_res = execute_command(ps_extract, target_sb)
        return f"Successfully synchronized workspace and generated baseline manifest in '{target_dir}' (sandbox: {target_sb}).\n{extract_res}"
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)


@mcp.tool()
def export_diff_from_guest(
    guest_dir: str = "C:\\workspace",
    sandbox_id: str = "auto"
) -> str:
    """Generate a clean unified git diff of all changes (additions, modifications, and deletions)
    made inside the guest workspace compared to host workspace. Uses the baseline manifest to prevent timestamp skew.
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    added, modified, deleted, err = _get_guest_changes(guest_dir, target_sb)
    if err:
        return err

    if not added and not modified and not deleted:
        return f"No differences between guest workspace ({target_sb}) and host workspace."

    diffs: List[str] = []

    for rel, b in added.items():
        diff = _diff_file(rel, b, is_new=True)
        if diff:
            diffs.append(diff)

    for rel, b in modified.items():
        diff = _diff_file(rel, b, is_new=False)
        if diff:
            diffs.append(diff)

    for rel in deleted:
        diff = _diff_deleted_file(rel)
        if diff:
            diffs.append(diff)

    if not diffs:
        return "No text content differences detected."

    return "".join(diffs)


@mcp.tool()
def apply_guest_changes_to_host(
    guest_dir: str = "C:\\workspace",
    sandbox_id: str = "auto",
    dry_run: bool = False
) -> str:
    """Apply verified changes from inside the guest workspace directly to the host workspace.
    Supports file additions, modifications, and deletions losslessly without CRLF/LF mismatch.
    Set dry_run=True to preview the file operations before applying.
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    added, modified, deleted, err = _get_guest_changes(guest_dir, target_sb)
    if err:
        return err

    if not added and not modified and not deleted:
        return f"No guest changes in {target_sb} to apply to host."

    report: List[str] = []
    prefix = "[Dry Run] Would apply:" if dry_run else "Successfully applied:"
    report.append(f"{prefix} (source: {target_sb})")

    # Process Additions
    for rel, content in added.items():
        target_path = os.path.join(REPO_ROOT, rel)
        if not dry_run:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
        report.append(f"  + Added:    {rel} ({len(content)} bytes)")

    # Process Modifications
    for rel, content in modified.items():
        target_path = os.path.join(REPO_ROOT, rel)
        if not dry_run:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
        report.append(f"  ~ Modified: {rel} ({len(content)} bytes)")

    # Process Deletions
    for rel in deleted:
        target_path = os.path.join(REPO_ROOT, rel)
        if not dry_run and os.path.exists(target_path):
            os.remove(target_path)
        report.append(f"  - Deleted:  {rel}")

    summary = f"\nTotal: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted."
    report.append(summary)
    return "\n".join(report)


@mcp.tool()
def pool_status() -> str:
    """View the live status of the warm standby VM pool (ready, leased, target size, members)."""
    return _run_wxc(["--hyperv-op", "pool-status"])


@mcp.tool()
def pool_lease(lease_holder: str = "agent") -> str:
    """Instantly lease a pre-warmed Hyper-V sandbox VM from the standby pool in <300ms.
    Sets it as the active session sandbox and returns the leased sandbox ID (e.g. hv:p1a2b3c4).
    """
    global _ACTIVE_SESSION_SANDBOX
    leased_id, err = _lease_from_pool(lease_holder)
    if leased_id:
        _ACTIVE_SESSION_SANDBOX = leased_id
        return f"Successfully leased sandbox '{leased_id}' in <300ms. Set as active session sandbox."
    return f"[Error leasing from pool]: {err}"


@mcp.tool()
def pool_release(sandbox_id: str = "auto") -> str:
    """Return a leased sandbox VM back to the standby pool.
    Instantly restores it to clean baseline snapshot, suspends it, and marks it Ready.
    If sandbox_id is 'auto', releases the active session sandbox.
    """
    global _ACTIVE_SESSION_SANDBOX
    target_id = _ACTIVE_SESSION_SANDBOX if (sandbox_id == "auto" or not sandbox_id) else sandbox_id
    if not target_id:
        return "No sandbox ID specified and no active session sandbox to release."

    success, raw = _release_to_pool(target_id)
    if success and _ACTIVE_SESSION_SANDBOX == target_id:
        _ACTIVE_SESSION_SANDBOX = None
        return f"Successfully returned '{target_id}' to standby pool and cleared active session."
    return raw


@mcp.tool()
def pool_replenish() -> str:
    """Replenish the standby pool by provisioning and warming up VMs up to the configured target size."""
    return _run_wxc(["--hyperv-op", "pool-replenish"])


@mcp.tool()
def session_acquire(lease_holder: str = "agent") -> str:
    """Acquire an isolated Hyper-V sandbox session from the warm pool.
    Subsequent commands will automatically run inside this session until session_release() is called.
    """
    return pool_lease(lease_holder)


@mcp.tool()
def session_release() -> str:
    """Release the current active session sandbox back to the pool (cleans state and suspends)."""
    return pool_release("auto")


@mcp.tool()
def session_status() -> str:
    """Check the currently bound session sandbox and pool availability."""
    global _ACTIVE_SESSION_SANDBOX
    status_raw = pool_status()
    active_str = f"Active session sandbox: {_ACTIVE_SESSION_SANDBOX or f'None (fallback: {DEFAULT_SANDBOX_ID})'}"
    return f"{active_str}\n\nPool Status:\n{status_raw}"


@mcp.tool()
def capture_screenshot(
    sandbox_id: str = "auto",
    width: Optional[int] = None,
    height: Optional[int] = None,
    save_path: Optional[str] = None
) -> str:
    """Capture a live PNG screenshot of the Hyper-V guest desktop buffer.
    Reads directly from the host-side Hyper-V synthetic video framebuffer via WMI
    without requiring any network connection or guest-side agents.

    Args:
        sandbox_id: Target MXC Hyper-V sandbox ID (defaults to 'auto', which uses active session or fallback).
        width: Optional custom width in pixels (defaults to guest native resolution, e.g. 1024).
        height: Optional custom height in pixels (defaults to guest native resolution, e.g. 768).
        save_path: Optional host path to save PNG image. If omitted, saves to a timestamped file
                   in scripts/hyperv/screenshots/ and returns the absolute file path and resolution metadata.
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    vm_name = _get_vm_name(target_sb)
    script_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "capture_screenshot.ps1"))

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", script_path,
        "-VmName", vm_name,
    ]
    if width:
        cmd.extend(["-Width", str(width)])
    if height:
        cmd.extend(["-Height", str(height)])
    if save_path:
        cmd.extend(["-OutputPath", save_path])

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return f"[Error capturing screenshot]: {res.stderr.strip() or res.stdout.strip()}"

    output = res.stdout.strip()
    payload = _extract_json_payload(output)
    if payload and payload.get("success"):
        path = payload.get("path")
        w = payload.get("width")
        h = payload.get("height")
        size = payload.get("fileSizeBytes")
        power_save = payload.get("isPowerSave")
        note = ""
        if power_save:
            note = "\n[Notice]: VM video adapter is in power-saving/disconnected mode (Enhanced Session in vmconnect may blank synthetic framebuffer)."
        return f"Successfully captured screenshot ({w}x{h}, {size} bytes):\nPath: {path}{note}"
    return output


@mcp.tool()
def set_network(
    enabled: bool = True,
    switch_name: str = "Default Switch",
    sandbox_id: str = "auto"
) -> str:
    """Connect or disconnect the guest VM virtual network adapter.
    Enables internet/LAN access via 'Default Switch' (or custom switch), or isolates the VM in airgap mode.

    Args:
        enabled: True to connect network (internet enabled), False to disconnect (airgap mode).
        switch_name: Virtual switch name to connect to (defaults to 'Default Switch').
        sandbox_id: Target MXC Hyper-V sandbox ID (defaults to 'auto', which uses active session or fallback).
    """
    target_sb = _resolve_sandbox_id(sandbox_id)
    vm_name = _get_vm_name(target_sb)

    if enabled:
        ps_cmd = (
            f"Connect-VMNetworkAdapter -VMName '{vm_name}' -SwitchName '{switch_name}'; "
            f"Start-Sleep -Seconds 2; "
            f"$a = Get-VMNetworkAdapter -VMName '{vm_name}'; "
            f"$ips = ($a.IPAddresses | Where-Object {{ $_ -notlike '*:*' -and $_ -notlike '169.254.*' }}) -join ', '; "
            f"[PSCustomObject]@{{ VMName = '{vm_name}'; Connected = $true; Switch = '{switch_name}'; IPv4 = $ips }} | ConvertTo-Json -Compress"
        )
    else:
        ps_cmd = (
            f"Disconnect-VMNetworkAdapter -VMName '{vm_name}'; "
            f"[PSCustomObject]@{{ VMName = '{vm_name}'; Connected = $false; Switch = $null; Airgapped = $true }} | ConvertTo-Json -Compress"
        )

    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode != 0:
        return f"[Error setting network state]: {res.stderr.strip() or res.stdout.strip()}"
    return res.stdout.strip()


@mcp.tool()
def get_network_status(sandbox_id: str = "auto") -> str:
    """Check the live network connectivity, virtual switch, MAC address, and assigned IP of the guest VM."""
    target_sb = _resolve_sandbox_id(sandbox_id)
    vm_name = _get_vm_name(target_sb)
    ps_cmd = (
        f"$a = Get-VMNetworkAdapter -VMName '{vm_name}'; "
        f"[PSCustomObject]@{{ "
        f"    VMName = '{vm_name}'; "
        f"    Connected = $a.Connected; "
        f"    Switch = if ($a.SwitchName) {{ $a.SwitchName }} else {{ 'None (Airgapped)' }}; "
        f"    MacAddress = $a.MacAddress; "
        f"    IPv4 = ($a.IPAddresses | Where-Object {{ $_ -notlike '*:*' -and $_ -notlike '169.254.*' }}) -join ', '; "
        f"    AllIPs = $a.IPAddresses -join ', ' "
        f"}} | ConvertTo-Json -Compress"
    )
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if res.returncode != 0:
        return f"[Error getting network status]: {res.stderr.strip() or res.stdout.strip()}"
    return res.stdout.strip()


try:
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "active_sandbox": _ACTIVE_SESSION_SANDBOX})

    @mcp.custom_route("/call", methods=["POST"])
    async def direct_tool_call(request: Request) -> JSONResponse:
        try:
            body = await request.json()
            tool_name = body.get("name")
            tool_args = body.get("arguments", {})
            res = await mcp.call_tool(tool_name, tool_args)
            content_list = []
            for c in (res.content if hasattr(res, "content") else []):
                if hasattr(c, "text"):
                    content_list.append({"type": "text", "text": c.text})
            return JSONResponse({"content": content_list})
        except Exception as e:
            return JSONResponse(
                {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}]},
                status_code=500,
            )
except Exception:
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MXC Hyper-V MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport mode: stdio (default), sse, or streamable-http",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host IP to bind for network transports (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for network transports (default: 8000)",
    )
    parser.add_argument(
        "--sse-path",
        default="/sse",
        help="SSE endpoint path (default: /sse)",
    )
    parser.add_argument(
        "--message-path",
        default="/messages/",
        help="SSE messages endpoint path (default: /messages/)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run("stdio")
    elif args.transport == "sse":
        print(f"[*] Starting MXC Hyper-V MCP Server on http://{args.host}:{args.port}{args.sse_path}")
        print(f"[*] SSE Message endpoint: http://{args.host}:{args.port}{args.message_path}")
        mcp.run("sse", host=args.host, port=args.port, sse_path=args.sse_path, message_path=args.message_path)
    elif args.transport == "streamable-http":
        print(f"[*] Starting MXC Hyper-V MCP Server on http://{args.host}:{args.port} (streamable-http)")
        mcp.run("streamable-http", host=args.host, port=args.port)

