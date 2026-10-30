"""
PMBOK Audit System Package.

Provides comprehensive quality auditing for PMBOK project artifacts with
compliance scoring, confidence metrics, and detailed findings.
"""

from .audit_policy import AuditCheck, AuditCriterion, PolicyExtensibility, PolicySet
from .audit_scoring import AuditScoringEngine
from .audit_validator import PMBOKAuditValidator
from .policy_loader import PolicyLoader
from .regression_thresholds import (
    ArtifactType,
    RegressionThreshold,
    DEFAULT_THRESHOLDS,
    get_threshold,
    check_regression,
)
from .prompt_recommendations import (
    PromptEnhancementCategory,
    PromptImprovement,
    PromptImprovementPlan,
    PromptRecommendationEngine,
)
from .quality_control import quality_controller, ContentQualityController, QualityControlResult
from .prompt_optimizer import prompt_optimizer, PromptOptimizer, PromptOptimization

__all__ = [
    # Existing
    "AuditCheck",
    "AuditCriterion",
    "PolicyExtensibility",
    "PolicySet",
    "AuditScoringEngine",
    "PMBOKAuditValidator",
    "PolicyLoader",
    # New: Regression & Recommendations
    "ArtifactType",
    "RegressionThreshold",
    "DEFAULT_THRESHOLDS",
    "get_threshold",
    "check_regression",
    "PromptEnhancementCategory",
    "PromptImprovement",
    "PromptImprovementPlan",
    "PromptRecommendationEngine",
    "AuditAnalytics",
    "AuditComparison",
    # Quality Control
    "quality_controller",
    "ContentQualityController",
    "QualityControlResult",
    # Prompt Optimization
    "prompt_optimizer",
    "PromptOptimizer",
    "PromptOptimization"
]
