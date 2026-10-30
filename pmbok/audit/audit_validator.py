"""
PMBOK Audit Validator.

Core validation engine for PMBOK compliance auditing.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from pmbok.models.audit import AuditFinding, AuditResult, AuditSeverity
from pmbok.models.pmbok import ProjectArtifact
from pmbok.process_registry import ProcessRegistry

from .audit_policy import PolicySet
from .audit_scoring import AuditScoringEngine


class PMBOKAuditValidator:
    """Validates artifacts against PMBOK standards and policies."""

    # Placeholder patterns that indicate incomplete content
    PLACEHOLDER_PATTERNS = [
        r"\$\[[^\]]+\]",  # Currency placeholders: requires brackets like $[amount] or $[1000]
        r"TBD|To Be Determined",
        r"TK|To Come",
        r"TODO|FIXME",
        r"\[PLACEHOLDER\]|\[DRAFT\]",
        r"[Xx]xx|xxx",
        r"###|~~~",
    ]

    MIN_FIELD_LENGTH = 3
    """Minimum character length for text fields."""

    def __init__(self, process_registry: Optional[ProcessRegistry] = None):
        """
        Initialize the validator.

        Args:
            process_registry: Optional ProcessRegistry for PMBOK process validation
        """
        self.process_registry = process_registry or ProcessRegistry()

    def validate_artifact(
        self,
        artifact: ProjectArtifact,
        policy: PolicySet,
    ) -> AuditResult:
        """
        Validate an artifact against a policy.

        Args:
            artifact: The artifact to validate
            policy: The policy set to validate against

        Returns:
            AuditResult with findings and scores
        """
        findings: List[AuditFinding] = []
        check_results: Dict[str, Tuple[int, int]] = {}

        # Initialize check counts for each criterion
        for criterion in policy.criteria:
            check_results[criterion.code] = (0, 0)

        # Run each criterion's checks
        for criterion in policy.criteria:
            criterion_findings, passed, total = self._validate_criterion(
                artifact, criterion, policy
            )
            findings.extend(criterion_findings)
            check_results[criterion.code] = (passed, total)

        # Calculate scores
        criterion_scores = AuditScoringEngine.calculate_criterion_scores_from_policy(
            policy, check_results
        )

        # Calculate overall compliance score
        compliance_score = AuditScoringEngine.calculate_weighted_compliance_score(
            criterion_scores
        )

        # Calculate confidence score
        total_checks = sum(total for _, total in check_results.values())
        total_passed = sum(passed for passed, _ in check_results.values())
        validation_pass_rate = (
            total_passed / total_checks if total_checks > 0 else 0.0
        )
        data_completeness = self._calculate_data_completeness(artifact)

        confidence_basis = AuditScoringEngine.build_confidence_basis(
            validation_pass_rate=validation_pass_rate,
            llm_confidence=0.85,  # Default; can be enhanced with LLM calls
            completeness_rate=data_completeness,
        )

        confidence_score = AuditScoringEngine.calculate_confidence_score(
            validation_pass_rate=validation_pass_rate,
            llm_confidence=0.85,
            completeness_rate=data_completeness,
        )

        # Determine compliance tier
        compliance_tier = AuditScoringEngine.get_compliance_tier(compliance_score)

        # Build result
        result = AuditResult(
            artifact_id=artifact.id,  # Use artifact.id, not artifact.artifact_id
            artifact_type=artifact.artifact_type,
            run_id=artifact.run_id,
            process_id=artifact.process_id,
            policy_set_applied=policy.name,
            compliance_score=compliance_score,
            confidence_score=confidence_score,
            compliance_tier=compliance_tier,
            findings=findings,
            criterion_scores=criterion_scores,
            confidence_basis=confidence_basis,
        )

        return result

    def _validate_criterion(
        self,
        artifact: ProjectArtifact,
        criterion: Any,  # AuditCriterion
        policy: PolicySet,
    ) -> Tuple[List[AuditFinding], int, int]:
        """
        Validate a single criterion against an artifact.

        Returns:
            (findings, checks_passed, checks_total)
        """
        findings: List[AuditFinding] = []
        checks_passed = 0
        checks_total = len(criterion.checks)

        for check in criterion.checks:
            check_finding = self._run_check(
                artifact, criterion, check, policy
            )
            if check_finding is None:
                # Check passed
                checks_passed += 1
            else:
                # Check failed
                findings.append(check_finding)

        return findings, checks_passed, checks_total

    def _run_check(
        self,
        artifact: ProjectArtifact,
        criterion: Any,
        check: Any,
        policy: PolicySet,
    ) -> Optional[AuditFinding]:
        """
        Run a single check. Returns None if passed, or AuditFinding if failed.
        """
        check_type = check.check_type.lower()

        if check_type == "schema":
            return self._check_schema(artifact, check, criterion)
        elif check_type == "content":
            return self._check_content(artifact, check, criterion)
        elif check_type == "semantic":
            return self._check_semantic(artifact, check, criterion)
        elif check_type == "format":
            return self._check_format(artifact, check, criterion)
        else:
            # Unknown check type
            return None

    def _check_schema(
        self,
        artifact: ProjectArtifact,
        check: Any,
        criterion: Any,
    ) -> Optional[AuditFinding]:
        """Check schema/structure requirements."""
        code = check.code
        params = check.parameters

        # Check required fields
        if "required_fields" in params:
            required_fields = params["required_fields"]
            missing_fields = []

            for field_name in required_fields:
                # Check envelope first, then content
                if hasattr(artifact, field_name) and getattr(artifact, field_name) is not None:
                    continue
                
                # If not in envelope, check content dict/object
                content = artifact.content
                if isinstance(content, dict):
                    if field_name not in content or content[field_name] is None:
                        missing_fields.append(field_name)
                else:
                    if not hasattr(content, field_name) or getattr(content, field_name) is None:
                        missing_fields.append(field_name)

            if missing_fields:
                return AuditFinding(
                    code=code,
                    severity=AuditSeverity(check.severity_if_failed),
                    message=f"Required fields missing in artifact: {', '.join(missing_fields)}",
                    affected_fields=missing_fields,
                    criterion=criterion.code,
                    remediation=f"Populate required fields: {', '.join(missing_fields)}",
                )

        return None

    def _check_content(
        self,
        artifact: ProjectArtifact,
        check: Any,
        criterion: Any,
    ) -> Optional[AuditFinding]:
        """Check content quality and completeness."""
        code = check.code
        params = check.parameters
        affected_fields = []

        # Check for placeholder text
        if params.get("no_placeholder_text", False):
            for placeholder_pattern in self.PLACEHOLDER_PATTERNS:
                for field_name, field_value in artifact.content.items():
                    if isinstance(field_value, str) and re.search(
                        placeholder_pattern, field_value, re.IGNORECASE
                    ):
                        affected_fields.append(field_name)

            if affected_fields:
                return AuditFinding(
                    code=code,
                    severity=AuditSeverity(check.severity_if_failed),
                    message=f"Placeholder or incomplete text found in fields: {', '.join(affected_fields)}",
                    affected_fields=affected_fields,
                    criterion=criterion.code,
                    remediation="Replace placeholder text with complete content",
                )

        # Check minimum field length
        if "min_field_length" in params:
            min_length = params["min_field_length"]
            short_fields = []

            for field_name, field_value in artifact.content.items():
                if isinstance(field_value, str) and len(field_value) < min_length:
                    short_fields.append(field_name)

            if short_fields:
                return AuditFinding(
                    code=code,
                    severity=AuditSeverity.WARNING,
                    message=f"Fields too short (minimum {min_length} chars): {', '.join(short_fields)}",
                    affected_fields=short_fields,
                    criterion=criterion.code,
                    remediation=f"Expand descriptions to at least {min_length} characters",
                )

        return None

    def _check_semantic(
        self,
        artifact: ProjectArtifact,
        check: Any,
        criterion: Any,
    ) -> Optional[AuditFinding]:
        """Check semantic/logical consistency."""
        code = check.code
        params = check.parameters

        # Check mapping to PMBOK process
        if params.get("valid_pmbok_process", False) and artifact.process_id:
            if not self.process_registry.get_process(artifact.process_id):
                return AuditFinding(
                    code=code,
                    severity=AuditSeverity.WARNING,
                    message=f"Process ID '{artifact.process_id}' not found in PMBOK registry",
                    affected_fields=["process_id"],
                    criterion=criterion.code,
                    remediation="Verify process ID matches PMBOK process registry",
                )

        # Check knowledge area consistency
        if "expected_knowledge_areas" in params:
            expected_kas = params["expected_knowledge_areas"]
            if criterion.knowledge_areas:
                missing_kas = [ka for ka in expected_kas if ka not in criterion.knowledge_areas]
                if missing_kas:
                    return AuditFinding(
                        code=code,
                        severity=AuditSeverity.INFO,
                        message=f"Expected knowledge areas not mapped: {', '.join(missing_kas)}",
                        affected_fields=["knowledge_area_mapping"],
                        criterion=criterion.code,
                        remediation=f"Map all expected knowledge areas: {', '.join(missing_kas)}",
                    )

        return None

    def _check_format(
        self,
        artifact: ProjectArtifact,
        check: Any,
        criterion: Any,
    ) -> Optional[AuditFinding]:
        """Check format compliance (dates, IDs, etc.)."""
        code = check.code
        params = check.parameters

        # Format-specific checks can be extended here
        # Example: check date formats, ID formats, etc.

        return None

    def _calculate_data_completeness(self, artifact: ProjectArtifact) -> float:
        """
        Calculate what percentage of artifact fields are populated.

        Returns:
            Ratio 0.0-1.0
        """
        if not hasattr(artifact, "content") or not artifact.content:
            return 0.0

        content_dict = (
            artifact.content.model_dump()
            if hasattr(artifact.content, "model_dump")
            else artifact.content
        )

        if not isinstance(content_dict, dict):
            return 0.0

        total_fields = len(content_dict)
        if total_fields == 0:
            return 0.0

        populated_fields = 0
        for value in content_dict.values():
            if value is not None and value != "" and value != []:
                populated_fields += 1

        return populated_fields / total_fields
