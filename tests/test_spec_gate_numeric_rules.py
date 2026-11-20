"""IMP-024 and IMP-021: spec_gate flags a zero-relative-tolerance gap and a continuous-domain widening."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from spec_gate import AcceptanceCriterionSpec, StorySpec, audit_story_spec

ROOT = Path(__file__).resolve().parents[1]


def _spec(*prose: str) -> StorySpec:
    return StorySpec(
        epic_num=99,
        story_id="99.9",
        title="t",
        status="Ready",
        role="developer",
        want="w",
        so_that="s",
        acceptance_criteria=[
            AcceptanceCriterionSpec(index=i, label=f"AC{i}", prose=p) for i, p in enumerate(prose)
        ],
    )


def _findings(spec: StorySpec) -> set[str]:
    deltas, _interps, _log = audit_story_spec(spec)
    return {d.finding_id for d in deltas if d.finding_id}


@pytest.mark.parametrize(
    "prose",
    [
        "The logits equal the reference within 1e-12 using math.isclose with abs_tol=1e-12.",
        "numpy.allclose(a, b, atol=1e-12) holds for the weights.",
        "The loss matches via math.isclose and within 1e-10.",
    ],
)
def test_isclose_with_an_absolute_tolerance_and_no_zero_relative_tolerance_is_flagged(prose: str) -> None:
    spec = _spec(prose)
    deltas, interps, log = audit_story_spec(spec)
    hit = [d for d in deltas if d.finding_id == "SPEC-TEST-REL-TOL-GAP"]
    assert len(hit) == 1 and hit[0].delta < 0 and hit[0].criterion_id == "testability"
    assert any("rel_tol=0.0" in i.text for i in interps)
    assert any("rel_tol" in line for line in log)


@pytest.mark.parametrize(
    "prose",
    [
        "The logits equal the reference within 1e-12 using math.isclose with rel_tol=0.0 and abs_tol=1e-12.",
        "numpy.allclose(a, b, rtol=0, atol=1e-12) holds for the weights.",
        "The loss is within 1e-12 by absolute difference: abs(a - b) <= 1e-12 (math.isclose is not used).",
        "The logits equal the reference within 1e-12 using pytest.approx(abs=1e-12).",
        "The logits equal the reference within 1e-6.",
    ],
)
def test_a_zero_relative_tolerance_or_a_strict_comparison_is_not_flagged(prose: str) -> None:
    assert "SPEC-TEST-REL-TOL-GAP" not in _findings(_spec(prose))


def test_a_wilson_bound_widened_to_float_successes_is_flagged() -> None:
    spec = _spec("The Wilson upper bound takes float successes in [0, total].")
    deltas, interps, log = audit_story_spec(spec)
    hit = [d for d in deltas if d.finding_id == "SPEC-COMPL-DOMAIN-WIDENING"]
    assert len(hit) == 1 and hit[0].delta < 0 and hit[0].criterion_id == "specification_completeness"
    text = " ".join(i.text for i in interps)
    assert "clamp" in text and "integer" in text
    assert any("[domain-widening]" in line for line in log)


def test_a_widening_that_states_its_clamp_and_integer_limit_is_not_flagged() -> None:
    spec = _spec(
        "The Wilson bound takes float successes in [0, total] and is clamped to [0, 1].",
        "At integer successes the bound equals the classical Wilson value.",
    )
    assert "SPEC-COMPL-DOMAIN-WIDENING" not in _findings(spec)


@pytest.mark.parametrize(
    "prose",
    [
        "The Wilson lower bound is computed from integer successes and total.",
        "The logits are float values and the loss is a float.",
        "A binomial test uses the number of trials.",
    ],
)
def test_a_discrete_primitive_alone_or_a_float_alone_is_not_flagged(prose: str) -> None:
    assert "SPEC-COMPL-DOMAIN-WIDENING" not in _findings(_spec(prose))


def test_the_real_epic_16_wording_is_flagged() -> None:
    spec = _spec(
        "over a grid of `N` from 1 to 50 and `k` from 0 to `N` in steps of 0.5, "
        "`1 - wilson_lower_bound(N - k, N)` equals the `wilson` score within 1e-12"
    )
    assert "SPEC-COMPL-DOMAIN-WIDENING" in _findings(spec)


def test_a_clamp_in_the_epic_preamble_does_not_silence_the_widening_finding() -> None:
    spec = _spec("The Wilson bound takes float successes in [0, total].")
    spec.epic_context = (
        "Everything is clamped to [0, 1] and at integer counts the value equals the classical one."
    )
    assert "SPEC-COMPL-DOMAIN-WIDENING" in _findings(spec)


def test_the_isclose_check_reads_the_acceptance_criteria_only() -> None:
    spec = _spec("The weights are saved.")
    spec.epic_context = "math.isclose is used elsewhere with abs_tol=1e-12."
    spec.want = "results within 1e-10"
    assert "SPEC-TEST-REL-TOL-GAP" not in _findings(spec)


def test_the_cue_and_the_input_domain_are_not_taken_for_a_clamp_or_an_integer_limit() -> None:
    spec = _spec(
        "The Wilson bound takes rewards mapped to [0, 1] as successes in [0, total] "
        "and equals the reference for non-integer counts."
    )
    assert "SPEC-COMPL-DOMAIN-WIDENING" in _findings(spec)


@pytest.mark.parametrize("name", ["wilson_lower_bound", "wilson_upper", "binomial_ci"])
def test_a_compound_primitive_name_counts(name: str) -> None:
    spec = _spec(f"`{name}` takes float successes in [0, total].")
    assert "SPEC-COMPL-DOMAIN-WIDENING" in _findings(spec)


def test_run_adversarial_checks_does_not_bind_unused_full_context() -> None:
    """Q-7-1: do not compute a dead full_context that never feeds the keyword checks."""
    tree = ast.parse((ROOT / "scripts" / "spec_gate.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_adversarial_checks":
            assigned = {
                t.id
                for stmt in node.body
                if isinstance(stmt, ast.Assign)
                for t in stmt.targets
                if isinstance(t, ast.Name)
            }
            assert "full_context" not in assigned, (
                "full_context is assigned in run_adversarial_checks but unused; "
                "remove it or feed the keyword checks from it"
            )
            return
    raise AssertionError("run_adversarial_checks not found")
