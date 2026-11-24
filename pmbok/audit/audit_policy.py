"""
PMBOK Audit Policy Definitions.

Defines the structure of audit policies, criteria, and checks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuditCheck:
    """Represents a single compliance check."""

    code: str
    """Unique check identifier (e.g., 'REQUIRED_INPUTS_PRESENT')."""

    description: str
    """Human-readable description of what this check validates."""

    check_type: str
    """Type of check: 'schema', 'content', 'semantic', 'format'."""

    parameters: Dict[str, Any] = field(default_factory=dict)
    """Parameters for the check (e.g., {'min_length': 3, 'required_fields': [...]})."""

    severity_if_failed: str = "WARNING"
    """Default severity if this check fails: CRITICAL, WARNING, INFO."""


@dataclass
class AuditCriterion:
    """Represents a compliance criterion (e.g., Process Completeness)."""

    code: str
    """Unique criterion identifier (e.g., 'PROCESS_COMPLETENESS')."""

    name: str
    """Human-readable name."""

    description: str
    """What this criterion measures."""

    weight: float
    """Weight in overall scoring (0.0-1.0)."""

    checks: List[AuditCheck] = field(default_factory=list)
    """List of checks that make up this criterion."""

    knowledge_areas: List[str] = field(default_factory=list)
    """PMBOK knowledge areas this criterion applies to."""

    process_groups: List[str] = field(default_factory=list)
    """PMBOK process groups this criterion applies to."""


@dataclass
class PolicyExtensibility:
    """Configuration for policy extensibility."""

    allow_custom_checks: bool = True
    """Whether custom checks can be added."""

    allow_custom_criteria: bool = True
    """Whether custom criteria can be added."""

    allow_override_weights: bool = True
    """Whether criterion weights can be overridden."""


@dataclass
class PolicySet:
    """Complete audit policy set."""

    name: str
    """Policy set name (e.g., 'PMBOK Standard')."""

    description: str
    """Policy set description."""

    version: str = "1.0.0"
    """Policy set version."""

    criteria: List[AuditCriterion] = field(default_factory=list)
    """List of compliance criteria."""

    scoring_method: str = "weighted_average"
    """Scoring method: 'weighted_average', 'checklist', 'hybrid'."""

    confidence_method: str = "combined"
    """Confidence calculation method: 'validation_only', 'llm_only', 'combined'."""

    iso_standards: List[str] = field(default_factory=list)
    """ISO standards this policy references (e.g., 'ISO 21500')."""

    extensibility: PolicyExtensibility = field(default_factory=PolicyExtensibility)
    """Extensibility configuration."""

    parent_policy: Optional[str] = None
    """Name of parent policy to inherit from (for policy hierarchy)."""

    def get_criterion(self, code: str) -> Optional[AuditCriterion]:
        """Get a criterion by code."""
        for criterion in self.criteria:
            if criterion.code == code:
                return criterion
        return None

    def get_check(self, criterion_code: str, check_code: str) -> Optional[AuditCheck]:
        """Get a check by criterion and check codes."""
        criterion = self.get_criterion(criterion_code)
        if criterion:
            for check in criterion.checks:
                if check.code == check_code:
                    return check
        return None

    def total_weight(self) -> float:
        """Get sum of all criterion weights."""
        return sum(c.weight for c in self.criteria)

    def normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0."""
        total = self.total_weight()
        if total > 0:
            for criterion in self.criteria:
                criterion.weight = criterion.weight / total
