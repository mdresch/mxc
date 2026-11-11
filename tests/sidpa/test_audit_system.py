"""
Test PMBOK Audit System

Demonstrates the audit system functionality with sample artifacts and policies.
"""

import pytest
from pathlib import Path
from datetime import datetime

from pmbok.models.pmbok import ProjectArtifact
from pmbok.models.audit import AuditFinding, AuditSeverity, ComplianceTier
from pmbok.audit.audit_policy import AuditCheck, AuditCriterion, PolicySet
from pmbok.audit.audit_scoring import AuditScoringEngine
from pmbok.audit.audit_validator import PMBOKAuditValidator
from pmbok.audit.policy_loader import PolicyLoader


class TestAuditScoringEngine:
    """Test compliance scoring calculations."""

    def test_criterion_score_all_passed(self):
        """Test scoring when all checks pass."""
        score = AuditScoringEngine.calculate_criterion_score(
            criterion=None,
            checks_passed=5,
            checks_total=5,
        )
        assert score == 100.0

    def test_criterion_score_partial(self):
        """Test scoring with partial pass."""
        score = AuditScoringEngine.calculate_criterion_score(
            criterion=None,
            checks_passed=3,
            checks_total=5,
        )
        assert score == 60.0

    def test_criterion_score_none_passed(self):
        """Test scoring when no checks pass."""
        score = AuditScoringEngine.calculate_criterion_score(
            criterion=None,
            checks_passed=0,
            checks_total=5,
        )
        assert score == 0.0

    def test_confidence_score_calculation(self):
        """Test confidence score aggregation."""
        confidence = AuditScoringEngine.calculate_confidence_score(
            validation_pass_rate=0.8,  # 80% of validations passed
            llm_confidence=0.85,  # LLM is 85% confident
            completeness_rate=0.9,  # 90% of fields populated
        )
        # Expected: (0.8 * 0.4) + (0.85 * 0.3) + (0.9 * 0.3) = 0.32 + 0.255 + 0.27 = 0.845 → 84.5%
        assert 84 < confidence < 85

    def test_get_compliance_tier_excellent(self):
        """Test tier classification for excellent."""
        tier = AuditScoringEngine.get_compliance_tier(95)
        assert tier == ComplianceTier.EXCELLENT

    def test_get_compliance_tier_good(self):
        """Test tier classification for good."""
        tier = AuditScoringEngine.get_compliance_tier(75)
        assert tier == ComplianceTier.GOOD

    def test_get_compliance_tier_fair(self):
        """Test tier classification for fair."""
        tier = AuditScoringEngine.get_compliance_tier(60)
        assert tier == ComplianceTier.FAIR

    def test_get_compliance_tier_poor(self):
        """Test tier classification for poor."""
        tier = AuditScoringEngine.get_compliance_tier(30)
        assert tier == ComplianceTier.POOR


class TestPolicyLoader:
    """Test policy loading and merging."""

    def test_load_pmbok_standard_policy(self):
        """Test loading the built-in PMBOK standard policy."""
        loader = PolicyLoader()
        policy = loader.load_policy("pmbok_standard")
        
        assert policy.name == "PMBOK Standard"
        assert len(policy.criteria) > 0
        # Verify expected criteria
        criterion_codes = [c.code for c in policy.criteria]
        assert "PROCESS_COMPLETENESS" in criterion_codes
        assert "QUALITY_STANDARDS" in criterion_codes
        assert "ALIGNMENT" in criterion_codes

    def test_policy_weights_sum(self):
        """Test that policy weights are properly configured."""
        loader = PolicyLoader()
        policy = loader.load_policy("pmbok_standard")
        
        total_weight = policy.total_weight()
        assert 0.99 < total_weight < 1.01  # Allow for floating-point precision

    def test_list_available_policies(self):
        """Test listing available policies."""
        loader = PolicyLoader()
        policies = loader.list_available_policies()
        
        assert "pmbok_standard" in policies
        assert len(policies) > 0


class TestAuditValidator:
    """Test core validation logic."""

    def test_validate_artifact_with_good_content(self):
        """Test validating an artifact with good content."""
        # Create a test artifact with good content
        artifact = ProjectArtifact(
            id="test-artifact-1",
            run_id="test-run-1",
            process_id="4.1",  # Develop Project Charter
            artifact_type="ProjectArtifact",
            content={
                "project_charter": "This is a comprehensive project charter",
                "authorization": "Authorized by executive stakeholder",
                "description": "This project aims to deliver value",
            },
            produced_by="test-process",
        )

        # Load policy and validate
        loader = PolicyLoader()
        policy = loader.load_policy("pmbok_standard")
        
        validator = PMBOKAuditValidator()
        result = validator.validate_artifact(artifact, policy)

        # Should have reasonable compliance score
        assert result.compliance_score >= 0
        assert result.compliance_score <= 100
        assert result.confidence_score >= 0
        assert result.confidence_score <= 100
        assert result.artifact_id == artifact.id

    def test_validate_artifact_with_placeholders(self):
        """Test validating an artifact with placeholder text."""
        artifact = ProjectArtifact(
            id="test-artifact-2",
            run_id="test-run-1",
            process_id="4.1",
            artifact_type="ProjectArtifact",
            content={
                "project_charter": "TBD",  # Placeholder
                "authorization": "TK",  # Placeholder
                "description": "TODO: Fill this in",  # Placeholder
            },
            produced_by="test-process",
        )

        loader = PolicyLoader()
        policy = loader.load_policy("pmbok_standard")
        
        validator = PMBOKAuditValidator()
        result = validator.validate_artifact(artifact, policy)

        # Should detect placeholder findings
        placeholder_findings = [
            f for f in result.findings
            if f.code == "NO_PLACEHOLDER_TEXT"
        ]
        assert len(placeholder_findings) > 0

    def test_validate_artifact_completeness(self):
        """Test data completeness calculation."""
        # Partially populated artifact
        artifact = ProjectArtifact(
            id="test-artifact-3",
            run_id="test-run-1",
            process_id="4.1",
            artifact_type="ProjectArtifact",
            content={
                "project_charter": "Valid charter",
                "authorization": None,  # Missing
                "description": "",  # Empty
                "budget": "Complete budget information",
            },
            produced_by="test-process",
        )

        loader = PolicyLoader()
        policy = loader.load_policy("pmbok_standard")
        
        validator = PMBOKAuditValidator()
        result = validator.validate_artifact(artifact, policy)

        # Check that confidence basis includes completeness
        assert "data_completeness_rate" in result.confidence_basis


class TestAuditFindings:
    """Test audit finding models."""

    def test_create_finding(self):
        """Test creating an audit finding."""
        finding = AuditFinding(
            code="TEST_CHECK",
            severity=AuditSeverity.WARNING,
            message="Test warning message",
            affected_fields=["field1", "field2"],
            criterion="TEST_CRITERION",
            remediation="Fix the fields",
        )

        assert finding.code == "TEST_CHECK"
        assert finding.severity == AuditSeverity.WARNING
        assert len(finding.affected_fields) == 2

    def test_audit_result_properties(self):
        """Test AuditResult aggregation properties."""
        findings = [
            AuditFinding(
                code="CRIT1",
                severity=AuditSeverity.CRITICAL,
                message="Critical issue",
            ),
            AuditFinding(
                code="WARN1",
                severity=AuditSeverity.WARNING,
                message="Warning issue",
            ),
            AuditFinding(
                code="WARN2",
                severity=AuditSeverity.WARNING,
                message="Another warning",
            ),
            AuditFinding(
                code="INFO1",
                severity=AuditSeverity.INFO,
                message="Info",
            ),
        ]

        from pmbok.models.audit import AuditResult
        
        result = AuditResult(
            artifact_id="test",
            artifact_type="ProjectArtifact",
            run_id="test-run",
            findings=findings,
        )

        assert result.critical_count == 1
        assert result.warning_count == 2
        assert result.info_count == 1
        assert result.total_findings == 4


class TestAuditRendering:
    """Test audit result rendering to Markdown."""

    def test_render_audit_section(self):
        """Test rendering audit section to Markdown."""
        from pmbok.output.audit_renderer import AuditRenderer
        from pmbok.models.audit import AuditResult

        findings = [
            AuditFinding(
                code="TEST_WARN",
                severity=AuditSeverity.WARNING,
                message="Test warning",
                affected_fields=["field1"],
            ),
        ]

        result = AuditResult(
            artifact_id="test",
            artifact_type="ProjectArtifact",
            run_id="test-run",
            compliance_score=85.5,
            confidence_score=82.3,
            compliance_tier=ComplianceTier.GOOD,
            findings=findings,
            confidence_basis={
                "validation_pass_rate": 0.9,
                "llm_confidence": 0.85,
                "data_completeness_rate": 0.95,
            },
        )

        markdown = AuditRenderer.render_audit_section(result)

        # Verify markdown contains expected sections
        assert "Quality Audit Results" in markdown
        assert "Compliance Score" in markdown
        assert "85.5%" in markdown
        assert "GOOD" in markdown
        assert "Confidence Score" in markdown
        assert "82.3%" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
