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
WXC_BIN = os.path.join(REPO_ROOT, "src", "target", "debug", "wxc-exec.exe")
EXEC_JSON = os.path.join(REPO_ROOT, "exec.json")
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


@mcp.tool()
def execute_command(command: str, sandbox_id: str = DEFAULT_SANDBOX_ID) -> str:
    """Execute a shell or PowerShell command inside the isolated MXC Hyper-V guest VM."""
    return _run_wxc([
        "--operation", "exec",
        "--container-id", sandbox_id,
        EXEC_JSON,
        "--",
        "powershell", "-NoProfile", "-Command", command
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
    Excludes .git, target, node_modules, and corpus to ensure fast, lightweight transfer.
    """
    vm_name = _get_vm_name(sandbox_id)
    source_path = os.path.join(REPO_ROOT, source_subdir) if source_subdir else REPO_ROOT

    # Create temporary tar.gz excluding build artifacts and git
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        archive_path = tmp.name

    def _filter(tarinfo):
        name = tarinfo.name.replace("\\", "/")
        for ignore in [".git", "target", "node_modules", ".vscode", "corpus"]:
            if f"/{ignore}" in f"/{name}" or name == ignore:
                return None
        return tarinfo

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_path, arcname=".", filter=_filter)

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

        # Extract inside guest and clean up archive
        ps_extract = (
            f"if (-not (Test-Path '{target_dir}')) {{ New-Item -ItemType Directory -Path '{target_dir}' -Force }}; "
            f"tar.exe -xzf '{guest_archive}' -C '{target_dir}'; "
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
    """Generate a unified diff of modified files inside the guest workspace so changes can be inspected and applied back to the host."""
    # Run git diff if git repository exists, otherwise check modified files
    check_git = execute_command(f"if (Test-Path '{guest_dir}\\.git') {{ git -C '{guest_dir}' diff }} else {{ 'no-git' }}", sandbox_id)
    if "no-git" not in check_git:
        return check_git

    # Fallback if no git repo inside guest: list files modified in the last 2 hours
    ps_find = (
        f"Get-ChildItem -Path '{guest_dir}' -Recurse -File | "
        f"Where-Object {{ $_.LastWriteTime -gt (Get-Date).AddHours(-2) }} | "
        f"Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize"
    )
    return execute_command(ps_find, sandbox_id)


if __name__ == "__main__":
    mcp.run()
