import base64
import difflib
import os
import shutil
import subprocess
import tarfile
import tempfile

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


def _diff_file(rel_path: str, guest_bytes: bytes) -> str:
    """Generate a unified diff between host file and guest modified file."""
    if b"\x00" in guest_bytes[:4096]:
        return f"Binary file {rel_path} changed in guest.\n"

    host_file = os.path.join(REPO_ROOT, rel_path)
    guest_text = guest_bytes.decode("utf-8-sig", errors="replace").splitlines(keepends=True)

    if os.path.exists(host_file):
        with open(host_file, "r", encoding="utf-8-sig", errors="replace") as f:
            host_text = f.readlines()
        from_file = f"a/{rel_path}"
    else:
        host_text = []
        from_file = "/dev/null"

    to_file = f"b/{rel_path}"
    diff = list(difflib.unified_diff(host_text, guest_text, fromfile=from_file, tofile=to_file))
    return "".join(diff)



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
    """Restore the Hyper-V sandbox back to a named checkpoint to undo broken state."""
    return _run_wxc([
        "--hyperv-op", "restore",
        "--hyperv-sandbox-id", sandbox_id,
        "--hyperv-checkpoint-name", name
    ])


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
    Uses native tar.exe with exclusions (.git, target, node_modules, corpus) for sub-second packaging and transfer.
    Also creates a baseline .sync_time marker in the guest.
    """
    vm_name = _get_vm_name(sandbox_id)
    source_path = os.path.join(REPO_ROOT, source_subdir) if source_subdir else REPO_ROOT

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        archive_path = tmp.name

    try:
        # Use native tar.exe on Windows for ~400ms packaging excluding build output
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

        # Extract inside guest, stamp baseline sync time, and clean up archive
        ps_extract = (
            f"if (-not (Test-Path '{target_dir}')) {{ New-Item -ItemType Directory -Path '{target_dir}' -Force }}; "
            f"tar.exe -xzf '{guest_archive}' -C '{target_dir}'; "
            f"Set-Content -Path '{target_dir}\\.sync_time' -Value (Get-Date).ToUniversalTime().ToString('o'); "
            f"Remove-Item '{guest_archive}' -Force"
        )
        extract_res = execute_command(ps_extract, sandbox_id)
        return f"Successfully synchronized workspace to guest directory '{target_dir}'.\n{extract_res}"
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)


@mcp.tool()
def export_diff_from_guest(
    guest_dir: str = "C:\\workspace",
    sandbox_id: str = DEFAULT_SANDBOX_ID
) -> str:
    """Generate a clean unified git diff of all changes made inside the guest workspace compared to host workspace.
    Scans for files created or modified since sync_workspace_to_guest and returns standard unified diff format.
    """
    scan_script = (
        f"$syncFile = '{guest_dir}\\.sync_time'; "
        f"if (-not (Test-Path $syncFile)) {{ 'NO_SYNC_TIME'; exit }}; "
        f"$syncTime = [DateTime]::Parse((Get-Content $syncFile)); "
        f"$files = Get-ChildItem -Path '{guest_dir}' -Recurse -File | "
        f"  Where-Object {{ $_.Name -ne '.sync_time' -and "
        f"    $_.FullName -notmatch '\\\\(target|bin|obj|\\.git|node_modules)\\\\' -and "
        f"    $_.Extension -notin @('.dll', '.pdb', '.cache', '.exe', '.tar', '.gz') -and "
        f"    $_.LastWriteTimeUtc -gt $syncTime }}; "
        f"if (-not $files) {{ 'NO_CHANGES'; exit }}; "
        f"foreach ($f in $files) {{ "
        f"  $rel = $f.FullName.Substring('{guest_dir}'.Length).TrimStart('\\'); "
        f"  $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($f.FullName)); "
        f"  Write-Output ('===FILE:' + $rel); "
        f"  Write-Output $b64; "
        f"}}"
    )

    res = execute_command(scan_script, sandbox_id)
    if "NO_SYNC_TIME" in res:
        return "No sync baseline found. Please run sync_workspace_to_guest first before checking diffs."
    if "NO_CHANGES" in res:
        return "No differences between guest workspace and host workspace."

    lines = res.splitlines()
    diffs = []
    curr_rel = None
    curr_b64 = []

    for line in lines:
        line = line.strip()
        if line.startswith("===FILE:"):
            if curr_rel and curr_b64:
                try:
                    file_bytes = base64.b64decode("".join(curr_b64))
                    diff = _diff_file(curr_rel, file_bytes)
                    if diff:
                        diffs.append(diff)
                except Exception as e:
                    diffs.append(f"Error diffing {curr_rel}: {e}")
            curr_rel = line[len("===FILE:"):]
            curr_b64 = []
        elif curr_rel:
            if not line.startswith("[Exit Code:") and not line.startswith("{"):
                curr_b64.append(line)

    if curr_rel and curr_b64:
        try:
            file_bytes = base64.b64decode("".join(curr_b64))
            diff = _diff_file(curr_rel, file_bytes)
            if diff:
                diffs.append(diff)
        except Exception as e:
            diffs.append(f"Error diffing {curr_rel}: {e}")

    if not diffs:
        return "No file content differences detected."

    return "\n".join(diffs)


if __name__ == "__main__":
    mcp.run()
