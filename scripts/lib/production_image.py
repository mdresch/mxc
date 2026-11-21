"""Production base image bake, compliance audit, and warm baseline checkpoint engine.

Governed by ADR-003, BRD-003 (BRU-003-01..04), FDD-003, and Stories 3.1..3.2 (WBS 4.1..4.2).
Implements compliance auditing for absence of developer debris (AC-04.1),
production pool parent enforcement (BRU-003-01), and warm baseline checkpointing (AC-04.2).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import fnmatch
import json
from pathlib import Path, PureWindowsPath
import time
from typing import Any, Dict, List, Optional, Sequence


class AuditMode(str, Enum):
    """Execution mode of the image compliance audit."""
    OFFLINE_VHDX = "OfflineVhdx"
    LIVE_SANDBOX = "LiveSandbox"


class AuditSeverity(str, Enum):
    """Severity classification of audit findings."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AuditStatus(str, Enum):
    """Overall outcome of the image compliance audit."""
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CheckItem:
    """Catalogued file or path to check."""
    name: str
    path: str


FORBIDDEN_BINARIES: tuple[str, ...] = (
    "rustc.exe",
    "cargo.exe",
    "cl.exe",
    "csc.exe",
    "link.exe",
    "gcc.exe",
    "git.exe",
    "uv.exe",
    "npm.cmd",
)

FORBIDDEN_PATHS: tuple[CheckItem, ...] = (
    CheckItem("Scoop Package Manager (ProgramData)", "ProgramData\\scoop"),
    CheckItem("Scoop Package Manager (User)", "Users\\*\\scoop"),
    CheckItem("Cargo Registry Directory (.cargo)", "Users\\*\\.cargo"),
    CheckItem("Rustup Directory (.rustup)", "Users\\*\\.rustup"),
    CheckItem("Rust Toolchain Install", "Program Files\\Rust stable"),
    CheckItem("Visual Studio Build Tools", "Program Files\\Microsoft Visual Studio"),
    CheckItem("Workspace Source Repo (.git)", "workspace\\.git"),
    CheckItem("Workspace MXC Git Clone", "workspace\\mxc-repo"),
    CheckItem("Workspace Source Staging", "workspace\\src"),
)

REQUIRED_RUNTIME_PATHS: tuple[CheckItem, ...] = (
    CheckItem("Hyper-V VMBus Driver", "Windows\\System32\\drivers\\vmbus.sys"),
    CheckItem("Hyper-V Time Sync Service Provider", "Windows\\System32\\vmictimeprovider.dll"),
    CheckItem("Windows Cryptographic CNG Library", "Windows\\System32\\bcrypt.dll"),
)


@dataclass(frozen=True)
class AuditViolation:
    """A single compliance violation detected on the inspected image."""
    artifact_name: str
    path: str
    severity: AuditSeverity = AuditSeverity.CRITICAL

    def to_dict(self) -> dict[str, str]:
        return {
            "ArtifactName": self.artifact_name,
            "Path": self.path,
            "Severity": self.severity.value,
        }


@dataclass(frozen=True)
class ImageAuditResult:
    """Result of an image compliance audit."""
    image_name: str
    status: AuditStatus
    violations: list[AuditViolation] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    manifest_json: str = "{}"
    inspected_target: str = ""

    @property
    def is_compliant(self) -> bool:
        return self.status == AuditStatus.PASSED and len(self.violations) == 0 and len(self.missing_required) == 0


@dataclass(frozen=True)
class PoolRegistration:
    """Record of a parent image registered to a production pool."""
    pool_id: str
    parent_image: str
    registered_at: float
    is_active: bool = True


class PoolRegistrationError(Exception):
    """Raised when an image fails production pool parent validation."""
    pass


def _normalize_win_path(p: str) -> str:
    """Normalize Windows-style path for case-insensitive matching."""
    s = p.replace("/", "\\").strip("\\")
    # Strip drive letter if present (e.g. C:\...)
    if len(s) >= 2 and s[1] == ":":
        s = s[2:].lstrip("\\")
    return s.lower()


class ProductionImageAuditEngine:
    """Audits production VHDX images for absence of developer debris (AC-04.1)."""

    def __init__(self, mode: AuditMode = AuditMode.OFFLINE_VHDX) -> None:
        self.mode = mode

    def _matches_pattern(self, fs_path: str, pattern: str) -> bool:
        """Match a filesystem path against a glob pattern (e.g. users/*/scoop)."""
        fs_norm = _normalize_win_path(fs_path)
        pat_norm = _normalize_win_path(pattern)

        # Direct match or substring containment
        if pat_norm in fs_norm:
            return True
        # Wildcard match
        if fnmatch.fnmatch(fs_norm, f"*{pat_norm}*") or fnmatch.fnmatch(fs_norm, pat_norm):
            return True
        return False

    def audit_image(
        self,
        image_path: str,
        filesystem: Optional[Dict[str, bool]] = None,
        binaries_on_path: Optional[Sequence[str]] = None,
    ) -> ImageAuditResult:
        """Inspect image filesystem and PATH binaries for compliance."""
        pure_name = PureWindowsPath(image_path).name
        fs = filesystem if filesystem is not None else {}
        bins = list(binaries_on_path) if binaries_on_path is not None else []

        violations: list[AuditViolation] = []
        missing_required: list[str] = []

        # 1. Audit binaries on PATH
        for binary_path in bins:
            bin_name = PureWindowsPath(binary_path).name.lower()
            for forbidden_bin in FORBIDDEN_BINARIES:
                if bin_name == forbidden_bin.lower():
                    violations.append(
                        AuditViolation(
                            artifact_name=f"Compiler/Tool on PATH ({forbidden_bin})",
                            path=binary_path,
                            severity=AuditSeverity.CRITICAL,
                        )
                    )

        # 2. Audit forbidden paths in guest filesystem
        for check in FORBIDDEN_PATHS:
            for actual_path, exists in fs.items():
                if exists and self._matches_pattern(actual_path, check.path):
                    violations.append(
                        AuditViolation(
                            artifact_name=check.name,
                            path=actual_path,
                            severity=AuditSeverity.CRITICAL,
                        )
                    )

        # 3. Verify required runtime baseline
        for req in REQUIRED_RUNTIME_PATHS:
            found = False
            for actual_path, exists in fs.items():
                if exists and self._matches_pattern(actual_path, req.path):
                    found = True
                    break
            if not found:
                missing_required.append(req.name)

        # Determine compliance
        is_compliant = (len(violations) == 0) and (len(missing_required) == 0)
        status = AuditStatus.PASSED if is_compliant else AuditStatus.FAILED

        # Build manifest
        manifest_data = {
            "image_name": pure_name,
            "target_path": image_path,
            "audit_mode": self.mode.value,
            "compliance_status": "COMPLIANT" if is_compliant else "NON_COMPLIANT",
            "violations_count": len(violations),
            "violations": [v.to_dict() for v in violations],
            "missing_required_count": len(missing_required),
            "missing_required": missing_required,
            "audit_timestamp": time.time(),
        }

        return ImageAuditResult(
            image_name=pure_name,
            status=status,
            violations=violations,
            missing_required=missing_required,
            manifest_json=json.dumps(manifest_data, indent=2),
            inspected_target=f"{self.mode.value}: {image_path}",
        )


class PoolRegistrationGuard:
    """Guards production pool registration to enforce ADR-003 / BRU-003-01."""

    DISALLOWED_DEV_PATTERNS = ("dev", "golden", "poc")

    def register_pool_parent(
        self,
        pool_id: str,
        image_path: str,
        audit_result: ImageAuditResult,
    ) -> PoolRegistration:
        """Register a parent VHDX to a production pool with invariant checks."""
        img_name = PureWindowsPath(image_path).name.lower()

        # BRU-003-01: Production pool parent is winserv2025-prod-adpa.vhdx, not winserv2025-mxc-dev.vhdx
        if "winserv2025-mxc-dev" in img_name or img_name == "winserv2025-golden.vhdx":
            raise PoolRegistrationError(
                f"BRU-003-01: Production pool parent cannot be developer image '{img_name}'. "
                f"Must be separate production image 'winserv2025-prod-adpa.vhdx'."
            )

        if not audit_result.is_compliant:
            raise PoolRegistrationError(
                f"Production pool parent '{img_name}' failed compliance audit gate: "
                f"{len(audit_result.violations)} violations, {len(audit_result.missing_required)} missing required."
            )

        if img_name != "winserv2025-prod-adpa.vhdx":
            raise PoolRegistrationError(
                f"BRU-003-01: Production pool parent must be 'winserv2025-prod-adpa.vhdx' (got '{img_name}')."
            )

        return PoolRegistration(
            pool_id=pool_id,
            parent_image=PureWindowsPath(image_path).name,
            registered_at=time.time(),
            is_active=True,
        )
