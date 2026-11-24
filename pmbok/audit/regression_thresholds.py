"""
Audit Regression Threshold Configuration

Defines minimum compliance score thresholds per artifact type
to detect quality regressions and trigger regeneration.
"""

from dataclasses import dataclass, field
from typing import Dict
from enum import Enum


class ArtifactType(str, Enum):
    """Supported artifact types with regression thresholds."""
    PROJECT_CHARTER = "PROJECT_CHARTER"
    SCOPE_STATEMENT = "SCOPE_STATEMENT"
    WBS = "WBS"
    SCHEDULE = "SCHEDULE"
    BUDGET = "BUDGET"
    RISK_REGISTER = "RISK_REGISTER"
    STAKEHOLDER_REGISTER = "STAKEHOLDER_REGISTER"
    COMMUNICATION_PLAN = "COMMUNICATION_PLAN"
    QUALITY_PLAN = "QUALITY_PLAN"
    LESSONS_LEARNED = "LESSONS_LEARNED"
    STATUS_REPORT = "STATUS_REPORT"
    CHANGE_REQUEST = "CHANGE_REQUEST"


@dataclass
class RegressionThreshold:
    """Per-artifact-type regression detection configuration."""
    
    artifact_type: str
    """Artifact type identifier."""
    
    minimum_compliance_score: float = 70.0
    """Minimum acceptable compliance score (0-100). Below this triggers regression."""
    
    minimum_confidence_score: float = 75.0
    """Minimum acceptable confidence score (0-100)."""
    
    critical_finding_threshold: int = 0
    """Maximum allowed critical findings (0 = none allowed)."""
    
    warning_finding_threshold: int = 2
    """Maximum allowed warning findings (regenerate if exceeded)."""
    
    auto_regenerate: bool = False
    """Auto-regenerate if score falls below threshold."""
    
    alert_on_regression: bool = True
    """Alert if score drops > 5% from previous version."""
    
    description: str = ""
    """Description of this artifact type and its quality expectations."""


# Default regression thresholds by artifact type
DEFAULT_THRESHOLDS: Dict[str, RegressionThreshold] = {
    ArtifactType.PROJECT_CHARTER: RegressionThreshold(
        artifact_type=ArtifactType.PROJECT_CHARTER,
        minimum_compliance_score=90.0,
        minimum_confidence_score=80.0,
        critical_finding_threshold=0,
        warning_finding_threshold=1,
        auto_regenerate=True,
        description="Project Charter - Foundation document, requires highest quality"
    ),
    ArtifactType.SCOPE_STATEMENT: RegressionThreshold(
        artifact_type=ArtifactType.SCOPE_STATEMENT,
        minimum_compliance_score=75.0,
        minimum_confidence_score=75.0,
        critical_finding_threshold=0,
        warning_finding_threshold=2,
        auto_regenerate=True,
        description="Scope Statement - Requires clear, complete scope definition"
    ),
    ArtifactType.SCHEDULE: RegressionThreshold(
        artifact_type=ArtifactType.SCHEDULE,
        minimum_compliance_score=75.0,
        minimum_confidence_score=75.0,
        critical_finding_threshold=0,
        warning_finding_threshold=2,
        auto_regenerate=False,
        description="Schedule Plan - Complex, may have valid deviations"
    ),
    ArtifactType.BUDGET: RegressionThreshold(
        artifact_type=ArtifactType.BUDGET,
        minimum_compliance_score=80.0,
        minimum_confidence_score=85.0,
        critical_finding_threshold=0,
        warning_finding_threshold=1,
        auto_regenerate=True,
        description="Budget Plan - Critical for financial control, needs precision"
    ),
    ArtifactType.RISK_REGISTER: RegressionThreshold(
        artifact_type=ArtifactType.RISK_REGISTER,
        minimum_compliance_score=75.0,
        minimum_confidence_score=78.0,
        critical_finding_threshold=0,
        warning_finding_threshold=3,
        auto_regenerate=False,
        description="Risk Register - Comprehensive, multiple risks acceptable"
    ),
    ArtifactType.QUALITY_PLAN: RegressionThreshold(
        artifact_type=ArtifactType.QUALITY_PLAN,
        minimum_compliance_score=72.0,
        minimum_confidence_score=75.0,
        critical_finding_threshold=1,
        warning_finding_threshold=3,
        auto_regenerate=False,
        description="Quality Plan - Operational document, some flexibility"
    ),
    ArtifactType.LESSONS_LEARNED: RegressionThreshold(
        artifact_type=ArtifactType.LESSONS_LEARNED,
        minimum_compliance_score=70.0,
        minimum_confidence_score=73.0,
        critical_finding_threshold=2,
        warning_finding_threshold=4,
        auto_regenerate=False,
        description="Lessons Learned - Retrospective, more subjective/flexible"
    ),
}


def get_threshold(artifact_type: str) -> RegressionThreshold:
    """Get regression threshold for artifact type."""
    # Normalize: "Project Charter" -> "PROJECT_CHARTER"
    normalized = artifact_type.upper().replace(" ", "_")
    
    # Try direct lookup
    if normalized in DEFAULT_THRESHOLDS:
        return DEFAULT_THRESHOLDS[normalized]
        
    # Try looking by enum values
    for t_key, threshold in DEFAULT_THRESHOLDS.items():
        if normalized == t_key or normalized == threshold.artifact_type:
            return threshold

    # Fallback to default
    return RegressionThreshold(
        artifact_type=artifact_type,
        minimum_compliance_score=70.0,
        minimum_confidence_score=75.0,
    )


def check_regression(artifact_type: str, current_score: float, previous_score: float = None) -> Dict[str, any]:
    """
    Check if artifact score represents a regression.
    
    Args:
        artifact_type: Type of artifact
        current_score: Current compliance score
        previous_score: Previous compliance score (optional, for trend analysis)
    
    Returns:
        Dict with regression status and details
    """
    threshold = get_threshold(artifact_type)
    
    result = {
        "artifact_type": artifact_type,
        "current_score": current_score,
        "threshold_minimum": threshold.minimum_compliance_score,
        "is_regression_absolute": current_score < threshold.minimum_compliance_score,
        "is_regression_relative": False,
        "trend_drop_percent": 0.0,
        "recommendation": "OK",
        "severity": "INFO",
    }
    
    # Check absolute threshold
    if current_score < threshold.minimum_compliance_score:
        result["severity"] = "CRITICAL" if current_score < threshold.minimum_compliance_score - 10 else "WARNING"
        result["recommendation"] = "REGENERATE_REQUIRED"
    
    # Check relative trend
    if previous_score is not None:
        trend_drop = previous_score - current_score
        result["trend_drop_percent"] = trend_drop
        result["is_regression_relative"] = trend_drop > 5.0
        
        if trend_drop > 5.0 and threshold.alert_on_regression:
            result["severity"] = "WARNING"
            result["recommendation"] = "REGENERATE_RECOMMENDED"
    
    return result
