"""
PMBOK Audit Scoring Engine.

Implements weighted scoring and confidence calculation for audit results.
"""

from typing import Dict, Tuple

from pmbok.models.audit import AuditResult, ComplianceTier, CriterionScore

from .audit_policy import AuditCriterion, PolicySet


class AuditScoringEngine:
    """Engine for calculating audit scores and confidence."""

    @staticmethod
    def calculate_criterion_score(
        criterion: AuditCriterion,
        checks_passed: int,
        checks_total: int,
        severity_weights: Dict[str, float] = None,
    ) -> float:
        """
        Calculate score for a single criterion based on checks.

        Args:
            criterion: The audit criterion
            checks_passed: Number of checks that passed
            checks_total: Total number of checks
            severity_weights: Optional weights for different severity levels

        Returns:
            Score 0-100
        """
        if checks_total == 0:
            return 100.0

        pass_rate = checks_passed / checks_total
        return pass_rate * 100.0

    @staticmethod
    def calculate_weighted_compliance_score(
        criterion_scores: list[CriterionScore],
    ) -> float:
        """
        Calculate overall weighted compliance score.

        Args:
            criterion_scores: List of per-criterion scores with weights

        Returns:
            Overall weighted score 0-100
        """
        if not criterion_scores:
            return 0.0

        total_weight = sum(cs.weight for cs in criterion_scores)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(cs.score * cs.weight for cs in criterion_scores)
        return weighted_sum / total_weight

    @staticmethod
    def calculate_confidence_score(
        validation_pass_rate: float,
        llm_confidence: float = 0.85,
        completeness_rate: float = 1.0,
        weights: Dict[str, float] = None,
    ) -> float:
        """
        Calculate confidence score from multiple sources.

        Confidence combines:
        - Validation pass rate (40% default): % of checks passed
        - LLM semantic assessment (30% default): Model confidence (0-1)
        - Data completeness (30% default): % of expected fields populated

        Args:
            validation_pass_rate: Percentage of validation checks passed (0-1)
            llm_confidence: LLM assessment confidence (0-1, default 0.85)
            completeness_rate: Percentage of fields populated (0-1)
            weights: Optional custom weights {'validation': 0.4, 'llm': 0.3, 'completeness': 0.3}

        Returns:
            Confidence score 0-100
        """
        if weights is None:
            weights = {
                "validation": 0.4,
                "llm": 0.3,
                "completeness": 0.3,
            }

        # Normalize inputs to 0-1 range
        val_rate = max(0.0, min(1.0, validation_pass_rate))
        llm_conf = max(0.0, min(1.0, llm_confidence))
        comp_rate = max(0.0, min(1.0, completeness_rate))

        # Calculate combined confidence
        confidence = (
            val_rate * weights.get("validation", 0.4)
            + llm_conf * weights.get("llm", 0.3)
            + comp_rate * weights.get("completeness", 0.3)
        )

        return min(100.0, confidence * 100.0)

    @staticmethod
    def get_compliance_tier(score: float) -> ComplianceTier:
        """
        Determine compliance tier from score.

        - EXCELLENT: 90-100%
        - GOOD: 70-89%
        - FAIR: 50-69%
        - POOR: <50%

        Args:
            score: Compliance score 0-100

        Returns:
            ComplianceTier enum value
        """
        if score >= 90:
            return ComplianceTier.EXCELLENT
        elif score >= 70:
            return ComplianceTier.GOOD
        elif score >= 50:
            return ComplianceTier.FAIR
        else:
            return ComplianceTier.POOR

    @staticmethod
    def calculate_criterion_scores_from_policy(
        policy: PolicySet,
        check_results: Dict[str, Tuple[int, int]],  # {criterion_code: (passed, total)}
    ) -> list[CriterionScore]:
        """
        Calculate per-criterion scores from check results and policy.

        Args:
            policy: The policy set defining criteria and weights
            check_results: Dict mapping criterion codes to (checks_passed, checks_total) tuples

        Returns:
            List of CriterionScore objects
        """
        criterion_scores = []

        for criterion in policy.criteria:
            passed, total = check_results.get(criterion.code, (0, 0))

            score = AuditScoringEngine.calculate_criterion_score(
                criterion, passed, total
            )

            criterion_scores.append(
                CriterionScore(
                    code=criterion.code,
                    name=criterion.name,
                    weight=criterion.weight,
                    score=score,
                    checks_passed=passed,
                    checks_total=total,
                    description=criterion.description,
                )
            )

        return criterion_scores

    @staticmethod
    def build_confidence_basis(
        validation_pass_rate: float,
        llm_confidence: float,
        completeness_rate: float,
        weights: Dict[str, float] = None,
    ) -> Dict[str, float]:
        """
        Build detailed breakdown of confidence calculation.

        Args:
            validation_pass_rate: Raw validation pass rate (0-1)
            llm_confidence: Raw LLM confidence (0-1)
            completeness_rate: Raw completeness rate (0-1)
            weights: Optional custom weights

        Returns:
            Dict with detailed confidence metrics
        """
        if weights is None:
            weights = {
                "validation": 0.4,
                "llm": 0.3,
                "completeness": 0.3,
            }

        val_rate = max(0.0, min(1.0, validation_pass_rate))
        llm_conf = max(0.0, min(1.0, llm_confidence))
        comp_rate = max(0.0, min(1.0, completeness_rate))

        return {
            "validation_pass_rate": val_rate,
            "llm_confidence": llm_conf,
            "data_completeness_rate": comp_rate,
            "weight_validation": weights.get("validation", 0.4),
            "weight_llm": weights.get("llm", 0.3),
            "weight_completeness": weights.get("completeness", 0.3),
            "validation_contribution": val_rate * weights.get("validation", 0.4) * 100,
            "llm_contribution": llm_conf * weights.get("llm", 0.3) * 100,
            "completeness_contribution": comp_rate * weights.get("completeness", 0.3) * 100,
        }
