"""
Pydantic data models for PMBOK 8 Stage 18: Intent Refinement.
Grounded in ADR-009, PMBOK Process 4.7 (Close Project or Phase), and double-loop cybernetic feedback.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Sequence
from pydantic import AliasChoices, BaseModel, Field, model_validator


class HypothesisTerminalStatus(str, Enum):
    VALIDATED = "validated"
    REFUTED = "refuted"
    REFINED = "refined"


class MeasurementHorizon(str, Enum):
    IMMEDIATE = "immediate"       # Observed directly via telemetry at phase cutoff
    PROVISIONAL = "provisional"   # Early directional signal; final outcome pending
    DEFERRED = "deferred"         # Long-term lagging indicator (requires operational soak)


class OutcomeDeltaItem(BaseModel):
    objective_id: str
    target_metric_stage_4: str
    actual_metric_stage_12: str
    variance_percentage: float
    measurement_horizon: MeasurementHorizon
    deferred_audit_due_date: Optional[str] = None
    causal_factors: List[str]
    strategic_directive: str


class HypothesisResolutionItem(BaseModel):
    hypothesis_id: str
    statement: str
    terminal_status: HypothesisTerminalStatus
    recurrence_depth: int = Field(default=0, ge=0, le=2)
    bayes_factor: Optional[float] = None
    evidence_references: List[str]
    promotion_target: Optional[str] = None  # e.g., "Architecture Invariant #7" or "HYP-001.1"
    rationale: str

    @model_validator(mode="after")
    def validate_exhaustion_collapse(self) -> "HypothesisResolutionItem":
        # Invariant 11: on the 3rd cycle (d=2), REFINED is prohibited
        if self.recurrence_depth >= 2 and self.terminal_status == HypothesisTerminalStatus.REFINED:
            raise ValueError(
                f"Hypothesis '{self.hypothesis_id}' reached recurrence depth {self.recurrence_depth}. "
                "At d_max=2, REFINED is prohibited: must collapse to VALIDATED (BF10 >= 10) "
                "or default to REFUTED (BF10 < 10)."
            )
        return self


class SparkDirectiveItem(BaseModel):
    directive_id: str
    title: str
    action_type: str  # "expand_capability" | "retire_component" | "pivot_architecture"
    target_stage_1_spark: str


class CumulativeLineageKernel(BaseModel):
    root_spark: str
    parent_refinement: Optional[str] = None
    generational_index: int = Field(..., ge=1)
    immutable_core_invariants: List[str]
    accumulated_knowledge_hash: str


class IntentRefinementProposalPayload(BaseModel):
    refinement_id: str = Field(..., pattern=r"^IR-PROP-v\d+\.\d+\.\d+$")
    pmp_baseline: str = Field(
        ...,
        pattern=r"^PMP-BL-v\d+\.\d+\.\d+$",
        validation_alias=AliasChoices("pmp_baseline", "pmp_baseline_id"),
    )
    readiness_audit_ref: str
    disposition_type: Literal["phase_handoff", "project_termination"] = "phase_handoff"
    lifecycle_stage: str = "Stage 18 (Intent Refinement)"
    governance_policy: str = "approve-intent-refinement"
    executive_summary: str
    outcome_deltas: List[OutcomeDeltaItem]
    hypothesis_resolutions: List[HypothesisResolutionItem]
    strategic_pivots: List[str]
    phase_next_spark_directives: List[SparkDirectiveItem] = Field(default_factory=list)
    lineage: CumulativeLineageKernel
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_disposition_directives(self) -> "IntentRefinementProposalPayload":
        if self.disposition_type == "phase_handoff" and not self.phase_next_spark_directives:
            raise ValueError(
                "phase_next_spark_directives must be non-empty when disposition_type is 'phase_handoff'."
            )
        if self.disposition_type == "project_termination" and self.phase_next_spark_directives:
            raise ValueError(
                "phase_next_spark_directives must be empty when disposition_type is 'project_termination'."
            )
        return self


class ReadinessPreconditionError(Exception):
    """Raised when Stage 18 Intent Refinement entry preconditions fail."""
    pass


class ReadinessAuditResult(BaseModel):
    audit_ref: str
    is_ready: bool
    verified_at: str
    deliverables_accepted: int
    open_findings_count: int
    crystallized_lessons_count: int


def evaluate_phase_close_readiness(
    deliverables: List[Dict[str, Any]],
    audit_records: List[Dict[str, Any]],
    lessons_learned: List[Dict[str, Any]],
) -> ReadinessAuditResult:
    """
    Validates preconditions for entering Stage 18 Intent Refinement under PMBOK 8 Process 4.7.
    - All Stage 9 deliverables must be accepted.
    - Stage 11 audit records must have zero unresolved non-conformances.
    - Stage 15 lessons learned must be crystallized.
    """
    import hashlib
    from datetime import datetime, timezone

    unaccepted = [
        d.get("deliverable_id", d.get("name", "unknown"))
        for d in deliverables
        if d.get("status") != "accepted"
    ]
    if unaccepted:
        raise ReadinessPreconditionError(
            f"Stage 9 deliverables incomplete: {', '.join(unaccepted)} are not accepted."
        )

    open_findings = sum(
        rec.get("non_conformance_count", 0)
        for rec in audit_records
        if rec.get("status") != "cleared" or rec.get("non_conformance_count", 0) > 0
    )
    if open_findings > 0:
        raise ReadinessPreconditionError(
            f"Stage 11 audit has unresolved non-conformances: {open_findings} finding(s) pending."
        )

    if not lessons_learned or any(not l.get("crystallized", False) for l in lessons_learned):
        raise ReadinessPreconditionError(
            "Stage 15 lessons learned uncrystallized: all lessons must be marked crystallized before phase close."
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_hash = hashlib.sha256(f"{now_iso}-{len(deliverables)}".encode()).hexdigest()[:8]
    audit_ref = f"AUD-CLOSE-{audit_hash.upper()}"

    return ReadinessAuditResult(
        audit_ref=audit_ref,
        is_ready=True,
        verified_at=now_iso,
        deliverables_accepted=len(deliverables),
        open_findings_count=0,
        crystallized_lessons_count=len(lessons_learned),
    )



class HypothesisTerminalityError(Exception):
    """Raised when active Stage 3 hypotheses fail to resolve to valid terminal states."""
    pass


def resolve_hypothesis(
    hypothesis_id: str,
    statement: str,
    bayes_factor: float,
    recurrence_depth: int = 0,
    evidence_references: Optional[List[str]] = None,
    rationale: str = "",
) -> HypothesisResolutionItem:
    """
    Adjudicates a single hypothesis into a terminal state based on empirical Bayes factor (BF10)
    and recurrence depth (d_max=2). Grounded in ADR-009 Invariant 11.
    """
    evidence = evidence_references or []
    
    if bayes_factor >= 10.0:
        return HypothesisResolutionItem(
            hypothesis_id=hypothesis_id,
            statement=statement,
            terminal_status=HypothesisTerminalStatus.VALIDATED,
            recurrence_depth=recurrence_depth,
            bayes_factor=bayes_factor,
            evidence_references=evidence,
            promotion_target=f"Architecture Invariant #{hypothesis_id}",
            rationale=rationale or f"Empirical Bayes factor BF10={bayes_factor:.2f} >= 10.0: Graduated to permanent architecture invariant.",
        )
    elif bayes_factor <= 0.1:
        return HypothesisResolutionItem(
            hypothesis_id=hypothesis_id,
            statement=statement,
            terminal_status=HypothesisTerminalStatus.REFUTED,
            recurrence_depth=recurrence_depth,
            bayes_factor=bayes_factor,
            evidence_references=evidence,
            promotion_target=None,
            rationale=rationale or f"Empirical Bayes factor BF10={bayes_factor:.2f} <= 0.10: Refuted with negative reinforcement penalty.",
        )
    else:
        # Inconclusive (0.1 < BF10 < 10)
        if recurrence_depth < 2:
            child_target = f"{hypothesis_id}.1"
            return HypothesisResolutionItem(
                hypothesis_id=hypothesis_id,
                statement=statement,
                terminal_status=HypothesisTerminalStatus.REFINED,
                recurrence_depth=recurrence_depth,
                bayes_factor=bayes_factor,
                evidence_references=evidence,
                promotion_target=child_target,
                rationale=rationale or f"Inconclusive Bayes factor BF10={bayes_factor:.2f} (0.1 < BF10 < 10): Refined to child hypothesis {child_target} (depth {recurrence_depth}).",
            )
        else:
            # Recurrence exhaustion at d_max=2: collapse to REFUTED
            return HypothesisResolutionItem(
                hypothesis_id=hypothesis_id,
                statement=statement,
                terminal_status=HypothesisTerminalStatus.REFUTED,
                recurrence_depth=recurrence_depth,
                bayes_factor=bayes_factor,
                evidence_references=evidence,
                promotion_target=None,
                rationale=rationale or f"Inconclusive Bayes factor BF10={bayes_factor:.2f} at d_max=2: Collapsed to REFUTED due to budget exhaustion under Invariant 11.",
            )


def adjudicate_hypothesis_batch(
    hypotheses: List[Dict[str, Any] | HypothesisResolutionItem],
) -> List[HypothesisResolutionItem]:
    """
    Adjudicates a batch of Stage 3 hypotheses, asserting 100% terminal resolution.
    Raises HypothesisTerminalityError if any hypothesis lacks a valid Bayes factor or terminal state.
    """
    results: List[HypothesisResolutionItem] = []
    for item in hypotheses:
        if isinstance(item, HypothesisResolutionItem):
            results.append(item)
            continue
        
        hyp_id = item.get("hypothesis_id", "unknown")
        statement = item.get("statement", "")
        bf = item.get("bayes_factor")
        depth = item.get("recurrence_depth", 0)
        evidence = item.get("evidence_references", [])
        rat = item.get("rationale", "")

        if bf is None:
            raise HypothesisTerminalityError(
                f"Hypothesis '{hyp_id}' lacks empirical Bayes factor (BF10); cannot close phase with unadjudicated hypotheses."
            )

        resolved = resolve_hypothesis(
            hypothesis_id=hyp_id,
            statement=statement,
            bayes_factor=float(bf),
            recurrence_depth=depth,
            evidence_references=evidence,
            rationale=rat,
        )
        results.append(resolved)

    return results


class StrategicWhiplashError(Exception):
    """Raised when proposed strategic pivots exceed homeostatic adaptation capacity (S3-S4 balance)."""
    pass


class LowPassOutcomeDampingFilter:
    """
    Exponential Moving Average (EMA) low-pass filter for outcome deltas.
    Stabilizes strategic replanning against single-phase high-frequency noise.
    Grounded in ADR-009 Section 3.1: Theta_{N+1} = beta * Theta_N + (1 - beta) * grad(L).
    """

    def __init__(self, beta: float = 0.75) -> None:
        if not (0.6 <= beta <= 0.85):
            raise ValueError(f"Momentum beta must be in [0.6, 0.85], got {beta}")
        self.beta = beta

    def filter_series(
        self,
        deltas: Sequence[float],
        apply_bias_correction: bool = True,
    ) -> List[float]:
        """Filters a sequence of outcome deltas, applying bias correction for N < 3."""
        smoothed: List[float] = []
        theta = 0.0
        for n, delta in enumerate(deltas, start=1):
            theta = self.beta * theta + (1.0 - self.beta) * delta
            if apply_bias_correction and n < 3:
                corrected = theta / (1.0 - (self.beta ** n))
                smoothed.append(corrected)
            else:
                smoothed.append(theta)
        return smoothed

    @staticmethod
    def get_raw_variance(deltas: Sequence[float]) -> float:
        """Computes sample variance of raw series."""
        if not deltas:
            return 0.0
        mean = sum(deltas) / len(deltas)
        return sum((x - mean) ** 2 for x in deltas) / len(deltas)

    @staticmethod
    def get_smoothed_variance(smoothed: Sequence[float]) -> float:
        """Computes sample variance of smoothed series."""
        if not smoothed:
            return 0.0
        mean = sum(smoothed) / len(smoothed)
        return sum((x - mean) ** 2 for x in smoothed) / len(smoothed)


def validate_strategic_pivot_capacity(pivots: List[str], c_adapt: int) -> bool:
    """
    Enforces System 3 - System 4 homeostatic balance (Stafford Beer VSM).
    Rate-limits proposed strategic pivots: Pivots_max <= ceil(C_adapt / 2).
    """
    import math

    max_pivots = math.ceil(c_adapt / 2)
    if len(pivots) > max_pivots:
        raise StrategicWhiplashError(
            f"Strategic pivots exceed homeostatic adaptation capacity: {len(pivots)} > {max_pivots} (C_adapt={c_adapt})."
        )
    return True


def compute_lineage_kernel(
    root_spark: str,
    parent_refinement: Optional[str],
    generational_index: int,
    core_invariants: List[str],
    prior_knowledge_hash: Optional[str] = None,
) -> CumulativeLineageKernel:
    """
    Generates an immutable cumulative lineage kernel linking multi-phase generations.
    Preserves root spark, parent refinement, invariants, and hereditary knowledge hash.
    """
    import hashlib

    sorted_inv = sorted(core_invariants)
    hash_payload = (
        f"{root_spark}|{parent_refinement or 'ROOT'}|{generational_index}|"
        f"{','.join(sorted_inv)}|{prior_knowledge_hash or 'GENESIS'}"
    )
    knowledge_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

    return CumulativeLineageKernel(
        root_spark=root_spark,
        parent_refinement=parent_refinement,
        generational_index=generational_index,
        immutable_core_invariants=core_invariants,
        accumulated_knowledge_hash=knowledge_hash,
    )
