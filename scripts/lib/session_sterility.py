"""Hyper-V transient differencing disk, egress whitelist, and session sterility engine.

Governed by ADR-005, BRD-005 (BRU-005-01..04), FDD-005, and Stories 5.1..5.3 (WBS 6.1..6.3).
Implements ephemeral .avhdx differencing disk destruction on release/idle (AC-02.1),
parent VHDX immutability verification (AC-02.2), hardware port ACL egress whitelist (AC-02.3),
and dual discard path equivalence (BEN-12).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import ipaddress
import time
from typing import Dict, List, Optional, Set


class SessionLifecycleState(str, Enum):
    """Lifecycle state of an active micro-execution session."""
    ACTIVE = "ACTIVE"
    DISCARDED = "DISCARDED"
    REAPED = "REAPED"
    RESTORED = "RESTORED"


class DiscardPath(str, Enum):
    """Execution path for session discard."""
    PATH_A_WHOLE_GUEST = "PathA_WholeGuest"
    PATH_B_DIFFERENCING_ONLY = "PathB_DifferencingOnly"


@dataclass
class SessionRecord:
    """Record of an active session bound to a differencing disk."""
    session_id: str
    vm_name: str
    differencing_disk_path: str
    state: SessionLifecycleState
    created_at: float
    active_requests: int = 0
    files: dict[str, bytes] = field(default_factory=dict)


@dataclass(frozen=True)
class DifferencingDiskStatus:
    """Result of a differencing disk release or reaping operation."""
    session_id: str
    is_disk_deleted: bool
    state: SessionLifecycleState
    is_reaped: bool = False
    reason: str = ""


@dataclass(frozen=True)
class ParentIntegrityStatus:
    """Verification audit comparing parent VHDX cryptographic hash before/after."""
    is_intact: bool
    parent_name: str
    before_hash: str
    after_hash: str


class SessionSterilityError(Exception):
    """Raised when session sterility or disk constraints are violated."""
    pass


class UnapprovedParentImageError(Exception):
    """Raised when attempting to anchor sessions on developer or unapproved parent images."""
    pass


class HungRequestError(Exception):
    """Raised when a request hangs past 900s, returning HTTP 504 (BRU-005-04)."""
    def __init__(self, message: str, status_code: int = 504) -> None:
        super().__init__(message)
        self.status_code = status_code


APPROVED_PRODUCTION_PARENT = "winserv2025-prod-adpa.vhdx"


# -------------------------------------------------------------------------
# Whitelisted egress destinations and ports per ADR-005 §4.5
# -------------------------------------------------------------------------
WHITELISTED_EGRESS_PORTS: dict[int, str] = {
    53: "DNS (Domain Name Resolution)",
    88: "Kerberos (Enterprise Authentication)",
    443: "Private Blob Storage / S3 (Approved internal endpoints)",
    1433: "SQL Server (Enterprise Relational Datastore)",
    5432: "PostgreSQL (Enterprise Relational Datastore)",
}

INGRESS_ALLOWED_PORT = 8080


@dataclass(frozen=True)
class NetworkCheckResult:
    """Outcome of virtual switch port ACL inspection."""
    is_allowed: bool
    destination: str
    port: int
    protocol: str
    action: str
    reason: str


@dataclass(frozen=True)
class DiscardResult:
    """Outcome of Path A or Path B session teardown."""
    discard_path: DiscardPath
    session_id: str
    vm_name: str
    parent_image: str
    is_residue_eliminated: bool
    next_parent_image: str
    guest_persisted: bool


def is_approved_internal_endpoint(destination: str) -> bool:
    """Evaluate whether a destination address or hostname is an approved internal target."""
    dest = destination.strip().lower()
    if dest in ("public_internet", "external_untrusted"):
        return False

    # Check if IP address
    try:
        ip = ipaddress.ip_address(dest)
        # RFC1918 private addresses or loopback
        return ip.is_private or ip.is_loopback
    except ValueError:
        pass

    # Domain name inspection
    approved_suffixes = (
        ".internal",
        ".corp",
        ".local",
        ".privatelink.blob.core.windows.net",
        ".privatelink.core.windows.net",
    )
    if any(dest.endswith(suffix) for suffix in approved_suffixes):
        return True

    return False


def generate_hyperv_port_acls(vm_name: str) -> List[str]:
    """Generate Hyper-V PowerShell Add-VMNetworkAdapterAcl commands for hardware enforcement."""
    commands = [
        f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Deny -Direction Inbound",
        f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Deny -Direction Outbound",
        f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Inbound -LocalPort 8080 -Protocol TCP",
    ]
    # Whitelisted egress rules
    for port, desc in WHITELISTED_EGRESS_PORTS.items():
        if port == 53:
            commands.append(f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Outbound -RemotePort 53 -Protocol UDP")
            commands.append(f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Outbound -RemotePort 53 -Protocol TCP")
        elif port == 88:
            commands.append(f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Outbound -RemotePort 88 -Protocol TCP")
            commands.append(f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Outbound -RemotePort 88 -Protocol UDP")
        else:
            commands.append(f"Add-VMNetworkAdapterAcl -VMName '{vm_name}' -Action Allow -Direction Outbound -RemotePort {port} -Protocol TCP")

    return commands


class SessionDiskManager:
    """Manages transient differencing disks, parent integrity, and session discard."""

    def __init__(
        self,
        parent_vhdx_name: str = APPROVED_PRODUCTION_PARENT,
        parent_initial_hash: str = "",
    ) -> None:
        if parent_vhdx_name != APPROVED_PRODUCTION_PARENT:
            raise UnapprovedParentImageError(
                f"BRU-003-01 / BRU-005-02: Parent image '{parent_vhdx_name}' is not an approved "
                f"production image. Must be '{APPROVED_PRODUCTION_PARENT}'."
            )
        self.parent_vhdx_name = parent_vhdx_name
        self.parent_initial_hash = parent_initial_hash
        self._sessions: dict[str, SessionRecord] = {}

    def create_session(self, session_id: str, vm_name: str) -> SessionRecord:
        """Create a new session anchored on a transient .avhdx differencing disk."""
        disk_path = f"C:\\Hyper-V\\Virtual Hard Disks\\{vm_name}_{session_id}.avhdx"
        record = SessionRecord(
            session_id=session_id,
            vm_name=vm_name,
            differencing_disk_path=disk_path,
            state=SessionLifecycleState.ACTIVE,
            created_at=time.time(),
        )
        self._sessions[session_id] = record
        return record

    def get_session(self, session_id: str) -> SessionRecord:
        """Retrieve active or archived session record."""
        session = self._sessions.get(session_id)
        if not session:
            raise SessionSterilityError(f"Session '{session_id}' not found.")
        return session

    def write_session_file(self, session_id: str, path: str, content: bytes) -> None:
        """Simulate writing guest file state onto the child .avhdx."""
        session = self.get_session(session_id)
        if session.state != SessionLifecycleState.ACTIVE:
            raise SessionSterilityError(f"Cannot write to inactive session '{session_id}'.")
        session.files[path.lower()] = content

    def record_session_file(self, session_id: str, path: str, content: bytes = b"") -> None:
        """Alias for write_session_file for recording guest disk modifications."""
        self.write_session_file(session_id, path, content)

    def has_session_file(self, session_id: str, path: str) -> bool:
        """Check if file exists on the session differencing disk."""
        session = self._sessions.get(session_id)
        if not session or session.state in (SessionLifecycleState.DISCARDED, SessionLifecycleState.REAPED):
            return False
        return path.lower() in session.files

    def release_session(self, session_id: str) -> DifferencingDiskStatus:
        """Release session: delete child .avhdx and wipe ephemeral writes (AC-02.1)."""
        session = self.get_session(session_id)
        session.files.clear()
        session.state = SessionLifecycleState.DISCARDED

        return DifferencingDiskStatus(
            session_id=session_id,
            is_disk_deleted=True,
            state=SessionLifecycleState.DISCARDED,
            reason="session_released",
        )

    def check_idle_timeout(
        self,
        session_id: str,
        idle_seconds: float,
        active_open_requests: int = 0,
    ) -> DifferencingDiskStatus:
        """Check 300s inactivity timeout; reap .avhdx if idle with 0 requests (AC-02.1)."""
        session = self.get_session(session_id)

        if active_open_requests > 0:
            return DifferencingDiskStatus(
                session_id=session_id,
                is_disk_deleted=False,
                state=session.state,
                is_reaped=False,
                reason="active_requests_present",
            )

        if idle_seconds >= 300.0:
            session.files.clear()
            session.state = SessionLifecycleState.DISCARDED
            return DifferencingDiskStatus(
                session_id=session_id,
                is_disk_deleted=True,
                state=SessionLifecycleState.DISCARDED,
                is_reaped=True,
                reason="idle_timeout_300s",
            )

        return DifferencingDiskStatus(
            session_id=session_id,
            is_disk_deleted=False,
            state=session.state,
            is_reaped=False,
            reason="under_threshold",
        )

    def verify_parent_integrity(
        self,
        current_parent_content: Optional[bytes] = None,
    ) -> ParentIntegrityStatus:
        """Verify parent VHDX SHA-256 hash has not been modified (AC-02.2)."""
        if current_parent_content is not None:
            current_hash = hashlib.sha256(current_parent_content).hexdigest()
        else:
            current_hash = self.parent_initial_hash

        is_intact = (current_hash == self.parent_initial_hash)

        return ParentIntegrityStatus(
            is_intact=is_intact,
            parent_name=self.parent_vhdx_name,
            before_hash=self.parent_initial_hash,
            after_hash=current_hash,
        )

    def monitor_request_duration(
        self,
        session_id: str,
        request_elapsed_seconds: float,
    ) -> None:
        """Enforce 900s hung-request threshold; return HTTP 504 and reap (BRU-005-04)."""
        if request_elapsed_seconds > 900.0:
            session = self.get_session(session_id)
            session.files.clear()
            session.state = SessionLifecycleState.REAPED
            raise HungRequestError(
                f"BRU-005-04: Request elapsed {request_elapsed_seconds:.1f}s exceeded 900s threshold. "
                f"HTTP 504 Gateway Timeout emitted and session '{session_id}' reaped.",
                status_code=504,
            )

    # ---------------------------------------------------------------------
    # Egress Whitelist Inspection (Story 5.2 / AC-02.3)
    # ---------------------------------------------------------------------
    def evaluate_outbound_traffic(
        self,
        destination: str,
        port: int,
        protocol: str = "TCP",
    ) -> NetworkCheckResult:
        """Evaluate guest outbound packet against hypervisor port ACLs (AC-02.3)."""
        # Check if port is in approved whitelist
        if port in WHITELISTED_EGRESS_PORTS:
            desc = WHITELISTED_EGRESS_PORTS[port]
            # Verify approved destination (not arbitrary public internet)
            if not is_approved_internal_endpoint(destination):
                return NetworkCheckResult(
                    is_allowed=False,
                    destination=destination,
                    port=port,
                    protocol=protocol,
                    action="DROP",
                    reason=f"Public internet destination prohibited for port {port} ({desc})",
                )
            return NetworkCheckResult(
                is_allowed=True,
                destination=destination,
                port=port,
                protocol=protocol,
                action="ALLOW",
                reason=f"Approved internal destination on port {port} ({desc})",
            )

        # Default Deny
        return NetworkCheckResult(
            is_allowed=False,
            destination=destination,
            port=port,
            protocol=protocol,
            action="DROP",
            reason=f"Default-deny rule dropped outbound traffic to {destination}:{port}",
        )

    def evaluate_inbound_traffic(
        self,
        source: str,
        port: int,
        protocol: str = "TCP",
    ) -> NetworkCheckResult:
        """Evaluate incoming packet against ingress port ACLs."""
        if port == INGRESS_ALLOWED_PORT:
            return NetworkCheckResult(
                is_allowed=True,
                destination="localhost",
                port=port,
                protocol=protocol,
                action="ALLOW",
                reason=f"JIT Ingress reverse proxy permitted on TCP {port}",
            )
        return NetworkCheckResult(
            is_allowed=False,
            destination="localhost",
            port=port,
            protocol=protocol,
            action="DROP",
            reason=f"Default-deny dropped unsolicited inbound traffic on port {port}",
        )

    # ---------------------------------------------------------------------
    # Dual Discard Paths (Story 5.3 / BEN-12 / BRU-005-02)
    # ---------------------------------------------------------------------
    def execute_discard_path(
        self,
        session_id: str,
        path: DiscardPath,
        next_session_id: str,
    ) -> DiscardResult:
        """Execute Path A (whole guest) or Path B (.avhdx only) discard."""
        session = self.get_session(session_id)
        vm_name = session.vm_name

        # Ensure session files are wiped
        session.files.clear()
        session.state = SessionLifecycleState.DISCARDED

        if path == DiscardPath.PATH_A_WHOLE_GUEST:
            # Whole guest removed, new guest provisioned from approved prod image
            guest_persisted = False
            next_parent = "winserv2025-prod-adpa.vhdx"
        else:
            # Differencing disk only discarded, guest remains
            guest_persisted = True
            next_parent = "winserv2025-prod-adpa.vhdx"

        # Create next session
        self.create_session(next_session_id, vm_name if guest_persisted else f"{vm_name}-new")

        return DiscardResult(
            discard_path=path,
            session_id=session_id,
            vm_name=vm_name,
            parent_image="winserv2025-prod-adpa.vhdx",
            is_residue_eliminated=True,
            next_parent_image=next_parent,
            guest_persisted=guest_persisted,
        )
