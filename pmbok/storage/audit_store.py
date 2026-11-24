"""
Audit Result Storage.

Provides versioned storage and retrieval of audit results, following the
same patterns as artifact_store for consistency.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pmbok.models.audit import AuditResult


class AuditStore:
    """Handles storage and retrieval of audit results."""

    def __init__(self, base_path: Path):
        """
        Initialize the audit store.

        Args:
            base_path: Base storage directory (typically runs/{run_id}/)
        """
        self.base_path = Path(base_path)
        self.audits_dir = self.base_path / "audits"

    def save(self, audit_result: AuditResult) -> str:
        """
        Save an audit result with versioning.

        Storage structure:
        {base_path}/audits/{artifact_id}/
        ├── v1_{timestamp}.json
        ├── v2_{timestamp}.json
        └── latest.json (atomic reference to highest version)

        Args:
            audit_result: AuditResult to save

        Returns:
            Path to saved audit file
        """
        # Create directories
        artifact_dir = self.audits_dir / audit_result.artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Determine next version
        version = self._get_next_version(artifact_dir)

        # Build versioned filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        versioned_filename = f"v{version}_{timestamp}.json"
        versioned_path = artifact_dir / versioned_filename

        # Write versioned file
        audit_dict = audit_result.to_dict()
        audit_dict["version"] = version

        with open(versioned_path, "w") as f:
            json.dump(audit_dict, f, indent=2, default=str)

        # Update latest.json (atomic reference)
        latest_path = artifact_dir / "latest.json"
        with open(latest_path, "w") as f:
            json.dump(audit_dict, f, indent=2, default=str)

        return str(versioned_path)

    def get(self, artifact_id: str) -> Optional[AuditResult]:
        """
        Get the latest audit result for an artifact.

        Args:
            artifact_id: ID of the artifact

        Returns:
            AuditResult or None if not found
        """
        artifact_dir = self.audits_dir / artifact_id
        latest_path = artifact_dir / "latest.json"

        if not latest_path.exists():
            return None

        with open(latest_path, "r") as f:
            data = json.load(f)

        return self._dict_to_audit_result(data)

    def get_version(self, artifact_id: str, version: int) -> Optional[AuditResult]:
        """
        Get a specific version of an audit result.

        Args:
            artifact_id: ID of the artifact
            version: Version number

        Returns:
            AuditResult or None if not found
        """
        artifact_dir = self.audits_dir / artifact_id

        # Find the file with this version
        for path in artifact_dir.glob(f"v{version}_*.json"):
            with open(path, "r") as f:
                data = json.load(f)
            return self._dict_to_audit_result(data)

        return None

    def get_history(self, artifact_id: str) -> List[AuditResult]:
        """
        Get all versions of audit results for an artifact.

        Args:
            artifact_id: ID of the artifact

        Returns:
            List of AuditResult objects, sorted by version ascending
        """
        artifact_dir = self.audits_dir / artifact_id

        if not artifact_dir.exists():
            return []

        results = []
        versioned_files = sorted(artifact_dir.glob("v*.json"))

        for path in versioned_files:
            with open(path, "r") as f:
                data = json.load(f)
            results.append(self._dict_to_audit_result(data))

        return results

    def list_artifacts(self) -> List[str]:
        """
        List all artifacts with audit results.

        Returns:
            List of artifact IDs
        """
        if not self.audits_dir.exists():
            return []

        return [d.name for d in self.audits_dir.iterdir() if d.is_dir()]

    def delete(self, artifact_id: str) -> bool:
        """
        Delete all audit results for an artifact.

        Args:
            artifact_id: ID of the artifact

        Returns:
            True if deleted, False if not found
        """
        artifact_dir = self.audits_dir / artifact_id

        if not artifact_dir.exists():
            return False

        import shutil

        shutil.rmtree(artifact_dir)
        return True

    def _get_next_version(self, artifact_dir: Path) -> int:
        """
        Determine the next version number.

        Args:
            artifact_dir: Directory containing audit files

        Returns:
            Next version number (1-indexed)
        """
        if not artifact_dir.exists():
            return 1

        version_numbers = []
        for path in artifact_dir.glob("v*_*.json"):
            # Extract version from v{version}_{timestamp}.json
            try:
                version_str = path.name.split("_")[0][1:]  # Remove 'v' prefix
                version_numbers.append(int(version_str))
            except (ValueError, IndexError):
                continue

        return max(version_numbers, default=0) + 1

    def _dict_to_audit_result(self, data: dict) -> AuditResult:
        """
        Convert dictionary to AuditResult.

        Args:
            data: Dictionary with audit result data

        Returns:
            AuditResult object
        """
        from pmbok.models.audit import AuditFinding, AuditSeverity, ComplianceTier

        findings = []
        for finding_data in data.get("findings", []):
            findings.append(
                AuditFinding(
                    code=finding_data["code"],
                    severity=AuditSeverity(finding_data["severity"]),
                    message=finding_data["message"],
                    affected_fields=finding_data.get("affected_fields", []),
                    criterion=finding_data.get("criterion"),
                    remediation=finding_data.get("remediation"),
                )
            )

        # Parse timestamp
        timestamp_str = data.get("audit_timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        return AuditResult(
            artifact_id=data["artifact_id"],
            artifact_type=data["artifact_type"],
            run_id=data["run_id"],
            process_id=data.get("process_id"),
            policy_set_applied=data.get("policy_set_applied", "pmbok_standard"),
            compliance_score=float(data.get("compliance_score", 0)),
            confidence_score=float(data.get("confidence_score", 0)),
            compliance_tier=ComplianceTier(data.get("compliance_tier", "POOR")),
            findings=findings,
            audit_timestamp=timestamp,
            confidence_basis=data.get("confidence_basis", {}),
        )
