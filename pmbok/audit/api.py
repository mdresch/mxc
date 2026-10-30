"""
PMBOK Audit API.

Public API functions for auditing artifacts and managing audit results.
"""

from pathlib import Path
from typing import List, Optional

from pmbok.models.audit import AuditResult
from pmbok.models.pmbok import ProjectArtifact
from pmbok.storage.audit_store import AuditStore

from .audit_validator import PMBOKAuditValidator
from .policy_loader import PolicyLoader


class AuditAPI:
    """Public API for PMBOK audit operations."""

    def __init__(
        self,
        base_storage_path: Path,
        policies_dir: Optional[Path] = None,
    ):
        """
        Initialize the audit API.

        Args:
            base_storage_path: Base directory for run artifacts/audits
            policies_dir: Directory containing policy YAML files
        """
        self.base_storage_path = Path(base_storage_path)
        self.policy_loader = PolicyLoader(policies_dir=policies_dir)
        self.validator = PMBOKAuditValidator()
        self.audit_store = AuditStore(self.base_storage_path)

    def audit_artifact(
        self,
        artifact: ProjectArtifact,
        policy_set_name: str = "pmbok_standard",
        department: Optional[str] = None,
        user_id: Optional[str] = None,
        save_result: bool = True,
    ) -> AuditResult:
        """
        Audit a single artifact against a policy.

        Args:
            artifact: The artifact to audit
            policy_set_name: Name of policy set to apply
            department: Optional department for policy overrides
            user_id: Optional user ID for policy overrides
            save_result: Whether to save result to audit store

        Returns:
            AuditResult with findings and scores
        """
        policy = self.policy_loader.load_policy_for_context(
            policy_name=policy_set_name,
            department=department,
            user_id=user_id,
        )

        result = self.validator.validate_artifact(artifact, policy)

        if save_result:
            self.audit_store.save(result)

        return result

    def run_batch_audit(
        self,
        artifacts: List[ProjectArtifact],
        policy_set_name: str = "pmbok_standard",
        department: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[AuditResult]:
        """
        Audit multiple artifacts.

        Args:
            artifacts: List of artifacts to audit
            policy_set_name: Name of policy set to apply
            department: Optional department for policy overrides
            user_id: Optional user ID for policy overrides

        Returns:
            List of AuditResult objects
        """
        results = []
        for artifact in artifacts:
            result = self.audit_artifact(
                artifact,
                policy_set_name=policy_set_name,
                department=department,
                user_id=user_id,
                save_result=True,
            )
            results.append(result)

        return results

    def get_audit_result(self, artifact_id: str) -> Optional[AuditResult]:
        """
        Get the latest audit result for an artifact.

        Args:
            artifact_id: ID of the artifact

        Returns:
            AuditResult or None if not found
        """
        return self.audit_store.get(artifact_id)

    def get_audit_history(self, artifact_id: str) -> List[AuditResult]:
        """
        Get all audit results for an artifact (versions).

        Args:
            artifact_id: ID of the artifact

        Returns:
            List of AuditResult objects, sorted by version
        """
        return self.audit_store.get_history(artifact_id)

    def get_audit_policy(self, policy_name: str):
        """
        Get a policy set by name.

        Args:
            policy_name: Name of policy

        Returns:
            PolicySet object
        """
        return self.policy_loader.load_policy(policy_name)

    def list_available_policies(self) -> List[str]:
        """
        List all available policy sets.

        Returns:
            List of policy names
        """
        return self.policy_loader.list_available_policies()

    def list_audited_artifacts(self) -> List[str]:
        """
        List all artifacts that have audit results.

        Returns:
            List of artifact IDs
        """
        return self.audit_store.list_artifacts()

    def delete_audit_results(self, artifact_id: str) -> bool:
        """
        Delete all audit results for an artifact.

        Args:
            artifact_id: ID of the artifact

        Returns:
            True if deleted, False if not found
        """
        return self.audit_store.delete(artifact_id)
