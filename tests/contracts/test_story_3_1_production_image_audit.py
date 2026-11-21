"""Contract test for Story 3.1: Clean production VHDX image audit.

Governed by ADR-003, BRD-003 (BRU-003-01, BRU-003-02), FDD-003, and WBS 4.1.
Enforces AC-04.1:
- Given `winserv2025-prod-adpa.vhdx`, when audit runs, Scoop, uv, cargo, git,
  compilers (rustc, cl, csc, link, gcc), and source repos are absent.
- Production pool parent must be `winserv2025-prod-adpa.vhdx`, never developer
  image `winserv2025-mxc-dev.vhdx` (BRU-003-01).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.lib.production_image import (
    AuditMode,
    AuditSeverity,
    AuditStatus,
    AuditViolation,
    FORBIDDEN_BINARIES,
    FORBIDDEN_PATHS,
    ImageAuditResult,
    PoolRegistrationError,
    PoolRegistrationGuard,
    ProductionImageAuditEngine,
    REQUIRED_RUNTIME_PATHS,
)


@pytest.fixture
def clean_guest_filesystem() -> dict[str, bool]:
    """Clean production guest filesystem without developer debris."""
    fs: dict[str, bool] = {}
    # Populate required runtime baselines
    for req in REQUIRED_RUNTIME_PATHS:
        fs[req.path.lower()] = True
    return fs


class TestStory31CleanProductionImageAudit:
    """Acceptance contract suite for AC-04.1 / Story 3.1."""

    def test_audit_passes_on_clean_production_vhdx(self, clean_guest_filesystem: dict[str, bool]) -> None:
        """AC-04.1: Given clean winserv2025-prod-adpa.vhdx, audit passes with 0 violations."""
        engine = ProductionImageAuditEngine(mode=AuditMode.OFFLINE_VHDX)
        result = engine.audit_image(
            image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
            filesystem=clean_guest_filesystem,
            binaries_on_path=[],
        )

        assert result.status == AuditStatus.PASSED
        assert result.is_compliant is True
        assert len(result.violations) == 0
        assert len(result.missing_required) == 0
        assert "winserv2025-prod-adpa.vhdx" in result.image_name
        assert result.manifest_json is not None

        manifest = json.loads(result.manifest_json)
        assert manifest["compliance_status"] == "COMPLIANT"
        assert manifest["violations_count"] == 0

    @pytest.mark.parametrize(
        "forbidden_bin",
        ["rustc.exe", "cargo.exe", "cl.exe", "csc.exe", "link.exe", "gcc.exe", "git.exe", "uv.exe", "npm.cmd"],
    )
    def test_audit_fails_when_forbidden_compiler_or_tool_on_path(
        self,
        clean_guest_filesystem: dict[str, bool],
        forbidden_bin: str,
    ) -> None:
        """BRU-003-02 / AC-04.1: Audit detects and flags forbidden compilers/tools on PATH."""
        engine = ProductionImageAuditEngine(mode=AuditMode.LIVE_SANDBOX)
        result = engine.audit_image(
            image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
            filesystem=clean_guest_filesystem,
            binaries_on_path=[f"C:\\Tools\\{forbidden_bin}"],
        )

        assert result.status == AuditStatus.FAILED
        assert result.is_compliant is False
        assert len(result.violations) >= 1

        v = next(item for item in result.violations if forbidden_bin.lower() in item.path.lower())
        assert v.severity == AuditSeverity.CRITICAL
        assert "Compiler/Tool" in v.artifact_name or forbidden_bin in v.artifact_name

    @pytest.mark.parametrize(
        "forbidden_path",
        [
            "ProgramData\\scoop",
            "Users\\Administrator\\scoop",
            "Users\\Administrator\\.cargo",
            "Users\\Administrator\\.rustup",
            "Program Files\\Rust stable",
            "Program Files\\Microsoft Visual Studio",
            "workspace\\.git",
            "workspace\\mxc-repo",
            "workspace\\src",
        ],
    )
    def test_audit_fails_when_forbidden_path_present(
        self,
        clean_guest_filesystem: dict[str, bool],
        forbidden_path: str,
    ) -> None:
        """BRU-003-02 / AC-04.1: Audit flags Scoop, Cargo, Git, VS, and workspace paths."""
        dirty_fs = dict(clean_guest_filesystem)
        dirty_fs[forbidden_path.lower()] = True

        engine = ProductionImageAuditEngine(mode=AuditMode.OFFLINE_VHDX)
        result = engine.audit_image(
            image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
            filesystem=dirty_fs,
            binaries_on_path=[],
        )

        assert result.status == AuditStatus.FAILED
        assert result.is_compliant is False
        assert any(forbidden_path.lower() in v.path.lower() for v in result.violations)

    def test_audit_fails_when_runtime_baseline_missing(self) -> None:
        """FDD-003: Audit flags missing required Hyper-V drivers and CNG crypto baseline."""
        # Filesystem missing required vmbus.sys, vmictimeprovider.dll, bcrypt.dll
        empty_fs: dict[str, bool] = {}

        engine = ProductionImageAuditEngine(mode=AuditMode.OFFLINE_VHDX)
        result = engine.audit_image(
            image_path="winserv2025-prod-adpa.vhdx",
            filesystem=empty_fs,
            binaries_on_path=[],
        )

        assert result.status == AuditStatus.FAILED
        assert result.is_compliant is False
        assert len(result.missing_required) == len(REQUIRED_RUNTIME_PATHS)
        assert any("vmbus" in m.lower() for m in result.missing_required)

    def test_production_pool_registration_rejects_developer_image(self) -> None:
        """BRU-003-01: Reject pool registration if parent is winserv2025-mxc-dev.vhdx."""
        guard = PoolRegistrationGuard()

        with pytest.raises(PoolRegistrationError) as exc_info:
            guard.register_pool_parent(
                pool_id="prod-adpa-pool",
                image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-mxc-dev.vhdx",
                audit_result=ImageAuditResult(
                    image_name="winserv2025-mxc-dev.vhdx",
                    status=AuditStatus.PASSED,
                    violations=[],
                    missing_required=[],
                    manifest_json="{}",
                ),
            )

        assert "BRU-003-01" in str(exc_info.value)
        assert "developer image" in str(exc_info.value).lower()

    def test_production_pool_registration_requires_passed_audit(
        self,
        clean_guest_filesystem: dict[str, bool],
    ) -> None:
        """FDD-003 Error Handling: Failed audit blocks pool registration."""
        guard = PoolRegistrationGuard()

        failed_audit = ImageAuditResult(
            image_name="winserv2025-prod-adpa.vhdx",
            status=AuditStatus.FAILED,
            violations=[
                AuditViolation(
                    artifact_name="Compiler on PATH",
                    path="C:\\cargo\\bin\\rustc.exe",
                    severity=AuditSeverity.CRITICAL,
                )
            ],
            missing_required=[],
            manifest_json="{}",
        )

        with pytest.raises(PoolRegistrationError) as exc_info:
            guard.register_pool_parent(
                pool_id="prod-adpa-pool",
                image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
                audit_result=failed_audit,
            )

        assert "audit" in str(exc_info.value).lower()
        assert "failed" in str(exc_info.value).lower()

    def test_production_pool_registration_accepts_clean_prod_image(
        self,
        clean_guest_filesystem: dict[str, bool],
    ) -> None:
        """BRU-003-01 / AC-04.1: Clean audited winserv2025-prod-adpa.vhdx is accepted."""
        engine = ProductionImageAuditEngine(mode=AuditMode.OFFLINE_VHDX)
        audit_result = engine.audit_image(
            image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
            filesystem=clean_guest_filesystem,
            binaries_on_path=[],
        )

        guard = PoolRegistrationGuard()
        registration = guard.register_pool_parent(
            pool_id="prod-adpa-pool",
            image_path="C:\\Hyper-V\\Virtual Hard Disks\\winserv2025-prod-adpa.vhdx",
            audit_result=audit_result,
        )

        assert registration.pool_id == "prod-adpa-pool"
        assert registration.parent_image == "winserv2025-prod-adpa.vhdx"
        assert registration.is_active is True
