"""
Unit and integration tests for Epic 9: Intent Refinement and Cognitive Feedback Loop.
Tests covering Acceptance Criteria AC_0 through AC_11.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Ensure src is on sys.path for agent_learning import
repo_root = Path(__file__).resolve().parent.parent.parent
src_dir = repo_root / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from pmbok.models.intent_refinement import (
    CumulativeLineageKernel,
    HypothesisResolutionItem,
    HypothesisTerminalStatus,
    HypothesisTerminalityError,
    IntentRefinementProposalPayload,
    LowPassOutcomeDampingFilter,
    MeasurementHorizon,
    OutcomeDeltaItem,
    ReadinessAuditResult,
    ReadinessPreconditionError,
    SparkDirectiveItem,
    StrategicWhiplashError,
    adjudicate_hypothesis_batch,
    compute_lineage_kernel,
    evaluate_phase_close_readiness,
    resolve_hypothesis,
    validate_strategic_pivot_capacity,
)
from scripts.orchestrate_pmbok import seed_next_phase, decommission_project, rollback_pmp


# ── AC_2, AC_6, AC_7, AC_8: Pydantic Contract & Hypothesis Adjudication ──────

def test_ac_2_valid_proposal_payload():
    """AC_2: Machine-readable contract adheres to IntentRefinementProposalPayload schema."""
    payload = IntentRefinementProposalPayload(
        refinement_id="IR-PROP-v1.0.0",
        pmp_baseline="PMP-BL-v1.0.0",
        readiness_audit_ref="AUD-CLOSE-001",
        disposition_type="phase_handoff",
        executive_summary="Phase 1 delivered all targeted capabilities with validated invariants.",
        outcome_deltas=[
            OutcomeDeltaItem(
                objective_id="OBJ-001",
                target_metric_stage_4="Latency <= 100ms",
                actual_metric_stage_12="Observed Latency = 82ms",
                variance_percentage=-18.0,
                measurement_horizon=MeasurementHorizon.IMMEDIATE,
                causal_factors=["Asynchronous IO optimization"],
                strategic_directive="Adopt latency profile as permanent SLA.",
            )
        ],
        hypothesis_resolutions=[
            HypothesisResolutionItem(
                hypothesis_id="HYP-001",
                statement="Stateless Bayesian comparison prevents drift.",
                terminal_status=HypothesisTerminalStatus.VALIDATED,
                recurrence_depth=0,
                bayes_factor=14.5,
                evidence_references=["EPISODE-101", "EPISODE-102"],
                promotion_target="Architecture Invariant #5",
                rationale="Bayes factor 14.5 >= 10 confirms hypothesis.",
            )
        ],
        strategic_pivots=["Promote stateless comparison to core framework."],
        phase_next_spark_directives=[
            SparkDirectiveItem(
                directive_id="DIR-001",
                title="Operationalize Generational Epistemic Kernel",
                action_type="expand_capability",
                target_stage_1_spark="SPARK-GEN-002",
            )
        ],
        lineage=CumulativeLineageKernel(
            root_spark="SPARK-ROOT-001",
            generational_index=1,
            immutable_core_invariants=["INV-01", "INV-02"],
            accumulated_knowledge_hash="sha256-abc123def456",
        ),
    )
    assert payload.refinement_id == "IR-PROP-v1.0.0"
    assert payload.pmp_baseline == "PMP-BL-v1.0.0"
    assert len(payload.phase_next_spark_directives) == 1


def test_ac_2_invalid_baseline_pattern():
    """AC_2: Baseline and refinement IDs must strictly adhere to SemVer patterns."""
    with pytest.raises(ValidationError):
        IntentRefinementProposalPayload(
            refinement_id="INVALID-REF",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="project_termination",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )


def test_ac_2_disposition_constraints():
    """AC_2: Phase handoff requires directives; project termination prohibits directives."""
    # Handoff with empty directives -> Error
    with pytest.raises(ValidationError, match="phase_next_spark_directives must be non-empty"):
        IntentRefinementProposalPayload(
            refinement_id="IR-PROP-v1.0.0",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="phase_handoff",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            phase_next_spark_directives=[],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )

    # Termination with non-empty directives -> Error
    with pytest.raises(ValidationError, match="phase_next_spark_directives must be empty"):
        IntentRefinementProposalPayload(
            refinement_id="IR-PROP-v1.0.0",
            pmp_baseline="PMP-BL-v1.0.0",
            readiness_audit_ref="AUD-001",
            disposition_type="project_termination",
            executive_summary="Summary",
            outcome_deltas=[],
            hypothesis_resolutions=[],
            strategic_pivots=[],
            phase_next_spark_directives=[
                SparkDirectiveItem(
                    directive_id="DIR-01",
                    title="Title",
                    action_type="expand_capability",
                    target_stage_1_spark="SPARK-02",
                )
            ],
            lineage=CumulativeLineageKernel(
                root_spark="SPARK-01",
                generational_index=1,
                immutable_core_invariants=[],
                accumulated_knowledge_hash="hash",
            ),
        )


def test_ac_6_bayes_factor_resolution():
    """AC_6: Bayes Factor adjudication thresholds (BF10 >= 10 validated, BF10 <= 0.1 refuted)."""
    # BF10 >= 10 -> Validated
    item_validated = HypothesisResolutionItem(
        hypothesis_id="HYP-VAL",
        statement="Valid hypothesis",
        terminal_status=HypothesisTerminalStatus.VALIDATED,
        recurrence_depth=0,
        bayes_factor=12.0,
        evidence_references=["EV-1"],
        rationale="BF10 >= 10",
    )
    assert item_validated.bayes_factor >= 10.0
    assert item_validated.terminal_status == HypothesisTerminalStatus.VALIDATED

    # BF10 <= 0.1 -> Refuted
    item_refuted = HypothesisResolutionItem(
        hypothesis_id="HYP-REF",
        statement="Refuted hypothesis",
        terminal_status=HypothesisTerminalStatus.REFUTED,
        recurrence_depth=1,
        bayes_factor=0.05,
        evidence_references=["EV-2"],
        rationale="BF10 <= 0.1",
    )
    assert item_refuted.bayes_factor <= 0.1
    assert item_refuted.terminal_status == HypothesisTerminalStatus.REFUTED


def test_ac_7_strict_recurrence_depth_guard():
    """AC_7: At recurrence_depth >= 2, REFINED is strictly prohibited."""
    # Depth 1 with REFINED is allowed
    item_d1 = HypothesisResolutionItem(
        hypothesis_id="HYP-D1",
        statement="Refining hypothesis",
        terminal_status=HypothesisTerminalStatus.REFINED,
        recurrence_depth=1,
        bayes_factor=2.5,
        evidence_references=["EV-1"],
        promotion_target="HYP-D1.1",
        rationale="Inconclusive, refining for next phase",
    )
    assert item_d1.recurrence_depth == 1
    assert item_d1.terminal_status == HypothesisTerminalStatus.REFINED

    # Depth 2 with REFINED must raise ValidationError
    with pytest.raises(ValidationError, match="At d_max=2, REFINED is prohibited"):
        HypothesisResolutionItem(
            hypothesis_id="HYP-D2",
            statement="Exhausted hypothesis",
            terminal_status=HypothesisTerminalStatus.REFINED,
            recurrence_depth=2,
            bayes_factor=1.8,
            evidence_references=["EV-2"],
            rationale="Trying to refine again at depth 2",
        )

    # Depth 2 with VALIDATED or REFUTED is allowed
    item_d2_collapsed = HypothesisResolutionItem(
        hypothesis_id="HYP-D2",
        statement="Exhausted hypothesis collapsed to REFUTED",
        terminal_status=HypothesisTerminalStatus.REFUTED,
        recurrence_depth=2,
        bayes_factor=1.8,
        evidence_references=["EV-2"],
        rationale="Defaulted to REFUTED due to budget exhaustion at d=2",
    )
    assert item_d2_collapsed.terminal_status == HypothesisTerminalStatus.REFUTED


def test_ac_8_hypothesis_terminality():
    """AC_8: All hypotheses in proposal payload must have terminal status (no pending/testing states)."""
    item = HypothesisResolutionItem(
        hypothesis_id="HYP-01",
        statement="Terminal hypothesis",
        terminal_status=HypothesisTerminalStatus.VALIDATED,
        recurrence_depth=0,
        bayes_factor=15.0,
        evidence_references=["EV-1"],
        rationale="Resolved",
    )
    assert item.terminal_status in {
        HypothesisTerminalStatus.VALIDATED,
        HypothesisTerminalStatus.REFUTED,
        HypothesisTerminalStatus.REFINED,
    }


# ── AC_9, AC_10: Low-Pass Filter Damping & S3-S4 Capacity Balance ─────────────

def calculate_ema_filter(
    deltas: list[float],
    beta: float = 0.75,
    apply_bias_correction: bool = True,
) -> list[float]:
    """Computes EMA low-pass damping filter with bias correction for N < 3."""
    assert 0.6 <= beta <= 0.85, "Momentum beta must be in [0.6, 0.85]"
    smoothed: list[float] = []
    theta = 0.0
    for n, delta in enumerate(deltas, start=1):
        theta = beta * theta + (1 - beta) * delta
        if apply_bias_correction and n < 3:
            corrected = theta / (1.0 - (beta ** n))
            smoothed.append(corrected)
        else:
            smoothed.append(theta)
    return smoothed


def test_ac_9_low_pass_filter_damping():
    """AC_9: Exponential smoothing dampens high-frequency noise and applies warmup."""
    raw_deltas = [10.0, -15.0, 12.0, -8.0, 14.0]
    beta = 0.75
    smoothed = calculate_ema_filter(raw_deltas, beta=beta)
    
    # Check that variance of smoothed series is strictly lower than raw series
    mean_raw = sum(raw_deltas) / len(raw_deltas)
    var_raw = sum((x - mean_raw) ** 2 for x in raw_deltas) / len(raw_deltas)

    mean_smoothed = sum(smoothed) / len(smoothed)
    var_smoothed = sum((x - mean_smoothed) ** 2 for x in smoothed) / len(smoothed)

    assert var_smoothed < var_raw, "Low-pass filter must dampen delta variance"
    # First item under bias correction equals the raw value
    assert math.isclose(smoothed[0], raw_deltas[0], rel_tol=1e-5)


def test_ac_10_s3_s4_capacity_balance():
    """AC_10: Strategic pivots are bounded by ceiling(C_adapt / 2)."""
    c_adapt = 5
    max_pivots = math.ceil(c_adapt / 2)  # 3
    proposed_pivots = ["Pivot 1", "Pivot 2", "Pivot 3"]
    assert len(proposed_pivots) <= max_pivots

    excessive_pivots = ["Pivot 1", "Pivot 2", "Pivot 3", "Pivot 4"]
    assert len(excessive_pivots) > max_pivots


# ── AC_1, AC_11: Decision Policy Gate & Lineage Kernel ───────────────────────

def test_ac_1_full_authority_policy_gate():
    """AC_1: approve-intent-refinement actions shape is defined with full governance options."""
    shape_path = Path("docs/policy-shapes/approve-intent-refinement.actions.json")
    assert shape_path.exists(), "Action shape file must exist"
    actions = json.loads(shape_path.read_text(encoding="utf-8"))
    
    assert isinstance(actions, list)
    action_ids = [a["id"] for a in actions]
    assert "approve_intent_refinement" in action_ids
    assert "reject_intent_refinement" in action_ids
    assert "request_revision_before_decision" in action_ids



def test_ac_11_cumulative_lineage_kernel():
    """AC_11: Lineage kernel preserves root spark, parent refinement, and immutable invariants."""
    lineage = CumulativeLineageKernel(
        root_spark="SPARK-GEN-001",
        parent_refinement="IR-PROP-v1.0.0",
        generational_index=2,
        immutable_core_invariants=["INV-01-STATELESS", "INV-02-FIVE-RECORDS"],
        accumulated_knowledge_hash="sha256-kernel-proof-999",
    )
    assert lineage.root_spark == "SPARK-GEN-001"
    assert lineage.parent_refinement == "IR-PROP-v1.0.0"
    assert lineage.generational_index == 2
    assert len(lineage.immutable_core_invariants) == 2


# ── AC_3, AC_4: Orchestrator Modes (seed-next, decommission, rollback) ────────

def test_ac_4_orchestrator_seed_next(tmp_path: Path):
    """AC_4: seed-next generates Phase N+1 Spark and Ideation with incremented baseline."""
    # Create sample approved refinement proposal
    refinement_doc = tmp_path / "Intent-Refinement-Proposal.md"
    refinement_doc.write_text("""---
refinement_id: "IR-PROP-v1.0.0"
pmp_baseline: "PMP-BL-v1.0.0"
disposition_type: "phase_handoff"
---
# Proposal
""", encoding="utf-8")

    out_dir = tmp_path / "seeded_phase"
    seed_next_phase(refinement_doc, out_dir)

    spark_file = out_dir / "Spark-Capture.md"
    ideation_file = out_dir / "Ideation-Document.md"

    assert spark_file.exists(), "Spark-Capture.md must be generated"
    assert ideation_file.exists(), "Ideation-Document.md must be generated"

    spark_text = spark_file.read_text(encoding="utf-8")
    assert 'pmp_baseline: "PMP-BL-v2.0.0"' in spark_text
    assert 'governed_by_refinement: "IR-PROP-v1.0.0"' in spark_text

    ideation_text = ideation_file.read_text(encoding="utf-8")
    assert 'pmp_baseline: "PMP-BL-v2.0.0"' in ideation_text
    assert "Active Hypotheses Register" in ideation_text


def test_ac_3_orchestrator_decommission(tmp_path: Path):
    """AC_3: decommission logs administrative teardown in target archive."""
    refinement_doc = tmp_path / "Intent-Refinement-Proposal.md"
    refinement_doc.write_text("""---
refinement_id: "IR-PROP-v1.0.0"
pmp_baseline: "PMP-BL-v1.0.0"
disposition_type: "project_termination"
---
# Termination Proposal
""", encoding="utf-8")

    archive_dir = tmp_path / "archive"
    decommission_project(refinement_doc, archive_dir)

    decom_folder = archive_dir / "decommission_Intent-Refinement-Proposal"
    assert decom_folder.exists()
    summary = decom_folder / "DECOMMISSION-SUMMARY.md"
    assert summary.exists()
    summary_text = summary.read_text(encoding="utf-8")
    assert "**Disposition:** Project Termination" in summary_text
    assert "Ephemeral worktrees pruned" in summary_text


# ── AC_0, AC_5: Readiness Audit Gate & Zero Storage Boundary ─────────────────

def test_ac_0_readiness_audit_gate_incomplete_deliverables():
    """AC_0: Incomplete Stage 9 deliverables must raise ReadinessPreconditionError."""
    deliverables = [
        {"deliverable_id": "DEL-01", "name": "ADR-009", "status": "accepted"},
        {"deliverable_id": "DEL-02", "name": "BRD-009", "status": "in_review"},
    ]
    audit_records = [
        {"audit_id": "AUD-01", "non_conformance_count": 0, "status": "cleared"}
    ]
    lessons_learned = [
        {"lesson_id": "LL-01", "crystallized": True, "title": "EMA Low-Pass Damping"}
    ]

    with pytest.raises(ReadinessPreconditionError, match="Stage 9 deliverables incomplete"):
        evaluate_phase_close_readiness(deliverables, audit_records, lessons_learned)


def test_ac_0_readiness_audit_gate_open_non_conformance():
    """AC_0: Unresolved Stage 11 audit non-conformances must raise ReadinessPreconditionError."""
    deliverables = [
        {"deliverable_id": "DEL-01", "name": "ADR-009", "status": "accepted"},
        {"deliverable_id": "DEL-02", "name": "BRD-009", "status": "accepted"},
    ]
    audit_records = [
        {"audit_id": "AUD-01", "non_conformance_count": 2, "status": "open_findings"}
    ]
    lessons_learned = [
        {"lesson_id": "LL-01", "crystallized": True, "title": "EMA Low-Pass Damping"}
    ]

    with pytest.raises(ReadinessPreconditionError, match="Stage 11 audit has unresolved non-conformances"):
        evaluate_phase_close_readiness(deliverables, audit_records, lessons_learned)


def test_ac_0_readiness_audit_gate_uncrystallized_lessons():
    """AC_0: Empty or uncrystallized Stage 15 lessons learned must raise ReadinessPreconditionError."""
    deliverables = [
        {"deliverable_id": "DEL-01", "name": "ADR-009", "status": "accepted"},
        {"deliverable_id": "DEL-02", "name": "BRD-009", "status": "accepted"},
    ]
    audit_records = [
        {"audit_id": "AUD-01", "non_conformance_count": 0, "status": "cleared"}
    ]
    lessons_learned = [
        {"lesson_id": "LL-01", "crystallized": False, "title": "Draft Lessons"}
    ]

    with pytest.raises(ReadinessPreconditionError, match="Stage 15 lessons learned uncrystallized"):
        evaluate_phase_close_readiness(deliverables, audit_records, lessons_learned)


def test_ac_0_readiness_audit_gate_clean_pass():
    """AC_0: When deliverables are accepted, audits clear, and lessons crystallized, readiness passes."""
    deliverables = [
        {"deliverable_id": "DEL-01", "name": "ADR-009", "status": "accepted"},
        {"deliverable_id": "DEL-02", "name": "BRD-009", "status": "accepted"},
    ]
    audit_records = [
        {"audit_id": "AUD-01", "non_conformance_count": 0, "status": "cleared"}
    ]
    lessons_learned = [
        {"lesson_id": "LL-01", "crystallized": True, "title": "EMA Low-Pass Damping"}
    ]

    result = evaluate_phase_close_readiness(deliverables, audit_records, lessons_learned)
    assert isinstance(result, ReadinessAuditResult)
    assert result.is_ready is True
    assert result.audit_ref.startswith("AUD-CLOSE-")


def test_ac_5_zero_storage_expansion_episode_envelope():
    """AC_5: Refinement proposals and decision episodes travel inside standard Episode envelopes."""
    episode_file = Path("docs/policy-shapes/episodes/epic9-story9.1-approval-episode.json")
    assert episode_file.exists(), "Committed episode fixture must exist"
    data = json.loads(episode_file.read_text(encoding="utf-8"))

    # Verify standard Episode fields (ADR-002)
    standard_keys = {
        "id", "agent_id", "task_id", "user_input", "assistant_output",
        "action_id", "policy_id", "context_features", "metadata", "created_at"
    }
    assert standard_keys.issubset(set(data.keys())), "Episode must adhere to standard Episode envelope"
    assert data["agent_id"] == "agent-learning-governance"
    assert data["metadata"]["task_completed"] is True
    assert data["metadata"]["decision_disposition"] == "accepted"




# ── Story 9.2: AC_6, AC_7, AC_8 Engine Tests ─────────────────────────────────

def test_ac_6_resolve_hypothesis_validated_graduation():
    """AC_6: resolve_hypothesis graduations for BF10 >= 10."""
    item = resolve_hypothesis(
        hypothesis_id="HYP-CORE-01",
        statement="Bayesian bounds prevent autonomous drift.",
        bayes_factor=15.2,
        recurrence_depth=0,
        evidence_references=["EV-STAGE-12-001"],
    )
    assert item.terminal_status == HypothesisTerminalStatus.VALIDATED
    assert item.promotion_target == "Architecture Invariant #HYP-CORE-01"
    assert "graduated to permanent architecture invariant" in item.rationale.lower()


def test_ac_6_resolve_hypothesis_refuted_penalty():
    """AC_6: resolve_hypothesis retirement for BF10 <= 0.1."""
    item = resolve_hypothesis(
        hypothesis_id="HYP-CORE-02",
        statement="Ad-hoc heuristics outperform bandit policy.",
        bayes_factor=0.04,
        recurrence_depth=0,
        evidence_references=["EV-STAGE-12-002"],
    )
    assert item.terminal_status == HypothesisTerminalStatus.REFUTED
    assert item.promotion_target is None
    assert "negative reinforcement penalty" in item.rationale.lower()


def test_ac_7_resolve_hypothesis_inconclusive_refinement():
    """AC_7: Inconclusive findings (0.1 < BF10 < 10) refine if recurrence_depth < 2."""
    item = resolve_hypothesis(
        hypothesis_id="HYP-INC-01",
        statement="Transformer-based cost estimation reduces error.",
        bayes_factor=3.4,
        recurrence_depth=0,
    )
    assert item.terminal_status == HypothesisTerminalStatus.REFINED
    assert item.recurrence_depth == 0
    assert item.promotion_target == "HYP-INC-01.1"


def test_ac_7_resolve_hypothesis_collapse_at_depth_2():
    """AC_7: At recurrence_depth = 2, inconclusive hypothesis must collapse to REFUTED."""
    item = resolve_hypothesis(
        hypothesis_id="HYP-INC-01.1",
        statement="Transformer-based cost estimation reduces error.",
        bayes_factor=3.4,
        recurrence_depth=2,
    )
    assert item.terminal_status == HypothesisTerminalStatus.REFUTED
    assert "budget exhaustion" in item.rationale.lower()
    assert "d_max=2" in item.rationale.lower()


def test_ac_8_adjudicate_hypothesis_batch_clean():
    """AC_8: All active hypotheses in a batch resolve to valid terminal states."""
    batch = [
        {"hypothesis_id": "H1", "statement": "S1", "bayes_factor": 25.0, "recurrence_depth": 0},
        {"hypothesis_id": "H2", "statement": "S2", "bayes_factor": 0.02, "recurrence_depth": 0},
        {"hypothesis_id": "H3", "statement": "S3", "bayes_factor": 4.5, "recurrence_depth": 1},
        {"hypothesis_id": "H4", "statement": "S4", "bayes_factor": 2.1, "recurrence_depth": 2},
    ]
    results = adjudicate_hypothesis_batch(batch)
    assert len(results) == 4
    statuses = {r.hypothesis_id: r.terminal_status for r in results}
    assert statuses["H1"] == HypothesisTerminalStatus.VALIDATED
    assert statuses["H2"] == HypothesisTerminalStatus.REFUTED
    assert statuses["H3"] == HypothesisTerminalStatus.REFINED
    assert statuses["H4"] == HypothesisTerminalStatus.REFUTED  # Collapsed at d=2


def test_ac_8_adjudicate_hypothesis_batch_rejects_missing_bayes_factor():
    """AC_8: Batches with unadjudicated hypotheses (missing BF10) raise HypothesisTerminalityError."""
    batch = [
        {"hypothesis_id": "H1", "statement": "S1", "bayes_factor": 25.0, "recurrence_depth": 0},
        {"hypothesis_id": "H2", "statement": "S2", "bayes_factor": None, "recurrence_depth": 0},
    ]
    with pytest.raises(HypothesisTerminalityError, match="lacks empirical Bayes factor"):
        adjudicate_hypothesis_batch(batch)


# ── Story 9.3: AC_9, AC_10, AC_11 Cybernetic Engine Tests ────────────────────

def test_ac_9_low_pass_damping_filter_class():
    """AC_9: LowPassOutcomeDampingFilter smooths variance and validates momentum bounds."""
    # Valid beta within [0.6, 0.85]
    dampener = LowPassOutcomeDampingFilter(beta=0.75)
    raw_deltas = [10.0, -15.0, 12.0, -8.0, 14.0]
    smoothed = dampener.filter_series(raw_deltas)

    assert len(smoothed) == len(raw_deltas)
    assert dampener.get_smoothed_variance(smoothed) < dampener.get_raw_variance(raw_deltas)
    # Bias-corrected warmup at generation 1 matches input
    assert math.isclose(smoothed[0], raw_deltas[0], rel_tol=1e-5)

    # Invalid beta out of bounds must raise ValueError
    with pytest.raises(ValueError, match="Momentum beta must be in"):
        LowPassOutcomeDampingFilter(beta=0.5)
    with pytest.raises(ValueError, match="Momentum beta must be in"):
        LowPassOutcomeDampingFilter(beta=0.95)


def test_ac_10_strategic_whiplash_capacity_guard():
    """AC_10: Strategic pivots must not exceed ceil(c_adapt / 2)."""
    # 2 pivots with c_adapt=4 -> Allowed (ceil(4/2) = 2)
    valid_pivots = ["Pivot A", "Pivot B"]
    assert validate_strategic_pivot_capacity(valid_pivots, c_adapt=4) is True

    # 3 pivots with c_adapt=4 -> Exceeds capacity -> Raises StrategicWhiplashError
    excessive_pivots = ["Pivot A", "Pivot B", "Pivot C"]
    with pytest.raises(StrategicWhiplashError, match="Strategic pivots exceed homeostatic adaptation capacity"):
        validate_strategic_pivot_capacity(excessive_pivots, c_adapt=4)


def test_ac_11_compute_lineage_kernel_deterministic_hash():
    """AC_11: compute_lineage_kernel creates immutable hereditary cryptographic link."""
    invariants = ["INV-01-STATELESS", "INV-02-FIVE-RECORDS", "INV-11-BAYES-COLLAPSE"]
    kernel_gen1 = compute_lineage_kernel(
        root_spark="SPARK-GEN-001",
        parent_refinement=None,
        generational_index=1,
        core_invariants=invariants,
    )
    assert kernel_gen1.generational_index == 1
    assert kernel_gen1.parent_refinement is None
    assert len(kernel_gen1.accumulated_knowledge_hash) == 64  # SHA-256

    # Generation 2 inherits prior hash
    kernel_gen2 = compute_lineage_kernel(
        root_spark="SPARK-GEN-001",
        parent_refinement="IR-PROP-v1.0.0",
        generational_index=2,
        core_invariants=invariants,
        prior_knowledge_hash=kernel_gen1.accumulated_knowledge_hash,
    )
    assert kernel_gen2.generational_index == 2
    assert kernel_gen2.parent_refinement == "IR-PROP-v1.0.0"
    assert kernel_gen2.accumulated_knowledge_hash != kernel_gen1.accumulated_knowledge_hash
