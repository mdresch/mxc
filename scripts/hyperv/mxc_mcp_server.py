import base64
import difflib
import os
import shutil
import subprocess
import tarfile
import tempfile
from typing import Dict, List, Tuple

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
def execute_command(command: str, sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """Execute a shell or PowerShell command inside the isolated MXC Hyper-V guest VM.
    Passes command via Base64 UTF-16LE EncodedCommand to eliminate quoting and pipe parsing issues.
    """
    b64 = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    return _run_wxc([
        "--operation", "exec",
        "--container-id", sandbox_id,
        EXEC_JSON,
        "--",
        "powershell.exe", "-NoProfile", "-EncodedCommand", b64
    ])


@mcp.tool()
def create_checkpoint(name: str, sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """Save a fast Hyper-V checkpoint before attempting risky refactors or package installs."""
    return _run_wxc([
        "--hyperv-op", "checkpoint",
        "--hyperv-sandbox-id", sandbox_id,
        "--hyperv-checkpoint-name", name
    ])


@mcp.tool()
def rollback_checkpoint(name: str, sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """Restore the Hyper-V sandbox back to a named checkpoint to undo broken state.
    Automatically resynchronizes VM guest clock with host time upon completion.
    """
    res = _run_wxc([
        "--hyperv-op", "restore",
        "--hyperv-sandbox-id", sandbox_id,
        "--hyperv-checkpoint-name", name
    ])
    # Force guest clock resync to prevent timestamp skew after rollback
    execute_command("Start-Service w32time -ErrorAction SilentlyContinue; w32tm /resync /force -ErrorAction SilentlyContinue", sandbox_id)
    return res


@mcp.tool()
def list_checkpoints(sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """List all available checkpoints for the active MXC Hyper-V sandbox."""
    return _run_wxc([
        "--hyperv-op", "list-checkpoints",
        "--hyperv-sandbox-id", sandbox_id
    ])


@mcp.tool()
def inspect_status(sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """View VM power state, assigned RAM, uptime, and integration heartbeat."""
    vm_name = _get_vm_name(sandbox_id)
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
    sandbox_id: str = DEFAULT_SANDBOX_ID
) -> str:
    """Synchronize host workspace files into the guest VM virtual disk (VHDX) via Hyper-V VMBus Copy-VMFile.
    Uses native tar.exe with exclusions (.git, target, bin, obj, node_modules) for sub-second packaging and transfer.
    Generates a full baseline file manifest (.sync_manifest.json) in the guest to track additions, modifications, and deletions.
    """
    vm_name = _get_vm_name(sandbox_id)
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

        # Ensure Guest Service Interface is enabled
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Enable-VMIntegrationService -VMName '{vm_name}' -Name 'Guest Service Interface' -ErrorAction SilentlyContinue"],
            capture_output=True
        )

        # Copy archive to guest via Copy-VMFile over VMBus
        ps_copy = (
            f"Copy-VMFile -VMName '{vm_name}' -SourcePath '{archive_path}' "
            f"-DestinationPath '{guest_archive}' -CreateFullPath -FileSource Host -Force"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_copy], capture_output=True, text=True)
        if res.returncode != 0:
            return f"[Error copying archive to guest]: {res.stderr.strip()}"

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
        extract_res = execute_command(ps_extract, sandbox_id)
        return f"Successfully synchronized workspace and generated baseline manifest in '{target_dir}'.\n{extract_res}"
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)


@mcp.tool()
def export_diff_from_guest(
    guest_dir: str = "C:\\workspace",
    sandbox_id: str = DEFAULT_SANDBOX_ID
) -> str:
    """Generate a clean unified git diff of all changes (additions, modifications, and deletions)
    made inside the guest workspace compared to host workspace. Uses the baseline manifest to prevent timestamp skew.
    """
    added, modified, deleted, err = _get_guest_changes(guest_dir, sandbox_id)
    if err:
        return err

    if not added and not modified and not deleted:
        return "No differences between guest workspace and host workspace."

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
    sandbox_id: str = DEFAULT_SANDBOX_ID,
    dry_run: bool = False
) -> str:
    """Apply verified changes from inside the guest workspace directly to the host workspace.
    Supports file additions, modifications, and deletions losslessly without CRLF/LF mismatch.
    Set dry_run=True to preview the file operations before applying.
    """
    added, modified, deleted, err = _get_guest_changes(guest_dir, sandbox_id)
    if err:
        return err

    if not added and not modified and not deleted:
        return "No guest changes to apply to host."

    report: List[str] = []
    prefix = "[Dry Run] Would apply:" if dry_run else "Successfully applied:"
    report.append(prefix)

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


if __name__ == "__main__":
    mcp.run()
