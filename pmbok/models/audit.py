"""
PMBOK Quality Audit Models.

Defines audit findings, results, and compliance scoring structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class AuditSeverity(str, Enum):
    """Severity levels for audit findings."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ComplianceTier(str, Enum):
    """Compliance score tier classification."""

    EXCELLENT = "EXCELLENT"  # 90-100%
    GOOD = "GOOD"  # 70-89%
    FAIR = "FAIR"  # 50-69%
    POOR = "POOR"  # <50%


@dataclass
class AuditFinding:
    """Represents a single audit finding."""

    code: str
    """Unique code identifying the finding type (e.g., 'REQ_INPUT_MISSING')."""

    severity: AuditSeverity
    """Severity of the finding."""

    message: str
    """Human-readable description of the finding."""

    affected_fields: List[str] = field(default_factory=list)
    """List of artifact fields affected by this finding."""

    criterion: Optional[str] = None
    """The compliance criterion this finding relates to."""

    remediation: Optional[str] = None
    """Suggested remediation for this finding."""


@dataclass
class CriterionScore:
    """Score for an individual compliance criterion."""

    code: str
    """Criterion code (e.g., 'PROCESS_COMPLETENESS')."""

    name: str
    """Human-readable name."""

    weight: float
    """Weight in the overall score (0.0-1.0)."""

    score: float
    """Score for this criterion (0-100)."""

    checks_passed: int = 0
    """Number of checks passed."""

    checks_total: int = 0
    """Total number of checks."""

    description: Optional[str] = None
    """Description of what this criterion measures."""


@dataclass
class AuditResult:
    """Result of a PMBOK quality audit."""

    artifact_id: str
    """ID of the audited artifact."""

    artifact_type: str
    """Type of artifact (e.g., 'ProjectArtifact')."""

    run_id: str
    """ID of the project run."""

    process_id: Optional[str] = None
    """ID of the PMBOK process that produced this artifact."""

    policy_set_applied: str = "pmbok_standard"
    """Name of the policy set applied."""

    compliance_score: float = 0.0
    """Overall compliance score (0-100)."""

    confidence_score: float = 0.0
    """Confidence in the audit (0-100)."""

    compliance_tier: ComplianceTier = ComplianceTier.POOR
    """Tier classification of compliance score."""

    findings: List[AuditFinding] = field(default_factory=list)
    """List of audit findings."""

    criterion_scores: List[CriterionScore] = field(default_factory=list)
    """Detailed scores per compliance criterion."""

    audit_timestamp: datetime = field(default_factory=datetime.utcnow)
    """When the audit was performed."""

    confidence_basis: Dict[str, float] = field(default_factory=dict)
    """Breakdown of confidence calculation (e.g., {'validation_pass_rate': 0.85, ...})."""

    # Aggregated findings counts
    @property
    def critical_count(self) -> int:
        """Count of critical findings."""
        return len([f for f in self.findings if f.severity == AuditSeverity.CRITICAL])

    @property
    def warning_count(self) -> int:
        """Count of warning findings."""
        return len([f for f in self.findings if f.severity == AuditSeverity.WARNING])

    @property
    def info_count(self) -> int:
        """Count of info findings."""
        return len([f for f in self.findings if f.severity == AuditSeverity.INFO])

    @property
    def total_findings(self) -> int:
        """Total count of findings."""
        return len(self.findings)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "run_id": self.run_id,
            "process_id": self.process_id,
            "policy_set_applied": self.policy_set_applied,
            "compliance_score": round(self.compliance_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "compliance_tier": self.compliance_tier.value,
            "audit_timestamp": self.audit_timestamp.isoformat(),
            "critical_findings": self.critical_count,
            "warning_findings": self.warning_count,
            "info_findings": self.info_count,
            "total_findings": self.total_findings,
            "findings": [
                {
                    "code": f.code,
                    "severity": f.severity.value,
                    "message": f.message,
                    "affected_fields": f.affected_fields,
                    "criterion": f.criterion,
                    "remediation": f.remediation,
                }
                for f in self.findings
            ],
            "criterion_scores": [
                {
                    "code": cs.code,
                    "name": cs.name,
                    "weight": cs.weight,
                    "score": round(cs.score, 2),
                    "checks_passed": cs.checks_passed,
                    "checks_total": cs.checks_total,
                    "description": cs.description,
                }
                for cs in self.criterion_scores
            ],
            "confidence_basis": {k: round(v, 3) for k, v in self.confidence_basis.items()},
        }
