"""Tests for BusinessCaseGenerator."""

from __future__ import annotations

import json
import pytest

from pmbok.engines.business_case_generator import BusinessCaseGenerator
from pmbok.exceptions import LLMParseError
from pmbok.models.business_case import BusinessCase, CostItem
from pmbok.models.ideation import IdeationSummary


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_summary(**overrides) -> IdeationSummary:
    base = dict(
        session_id="sess-001",
        title="Smart Irrigation Controller",
        problem_statement="Farmers waste 40% of water due to manual irrigation.",
        proposed_solution="IoT sensor network with AI-driven scheduling.",
        key_goals=["Reduce water usage by 30%", "Automate scheduling"],
        assumptions=["Farmers have basic smartphone access"],
        constraints=["Budget under $500k", "6-month delivery"],
    )
    base.update(overrides)
    return IdeationSummary(**base)


def _valid_business_case_dict(summary_id: str = "stub-summary-id", **overrides) -> dict:
    base = {
        "ideation_summary_id": summary_id,
        "executive_summary": "This project delivers a robust irrigation solution.",
        "problem_statement": "Farmers waste 40% of water.",
        "proposed_solution": "IoT sensor network with AI scheduling.",
        "expected_benefits": ["Reduce water usage by 30%", "Automate scheduling"],
        "estimated_costs": [
            {"label": "Development", "amount": 150000.0, "currency": "USD", "is_placeholder": False},
        ],
        "key_risks": ["Scope creep may delay delivery"],
        "recommendation": "Proceed with the project.",
        "placeholders": [],
        "version_history": [],
    }
    base.update(overrides)
    return base


class MockLLMClient:
    """Returns a configurable JSON string."""

    def __init__(self, response: str | None = None, summary_id: str = "stub-summary-id"):
        self._response = response or json.dumps(_valid_business_case_dict(summary_id=summary_id))

    async def complete(self, prompt: str) -> str:  # noqa: ARG002
        return self._response


# ---------------------------------------------------------------------------
# Full generation — happy path
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generate_returns_business_case():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    case = await generator.generate(summary)

    assert isinstance(case, BusinessCase)
    assert case.executive_summary
    assert case.problem_statement
    assert case.proposed_solution
    assert len(case.expected_benefits) >= 1
    assert len(case.estimated_costs) >= 1
    assert len(case.key_risks) >= 1
    assert case.recommendation


@pytest.mark.anyio
async def test_generate_sets_ideation_summary_id():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    case = await generator.generate(summary)
    assert case.ideation_summary_id == summary.id


@pytest.mark.anyio
async def test_generate_stub_client_when_no_llm():
    """Generator with no LLM client uses the stub and returns a valid BusinessCase."""
    summary = _make_summary()
    generator = BusinessCaseGenerator()
    case = await generator.generate(summary)
    assert isinstance(case, BusinessCase)
    assert case.executive_summary


# ---------------------------------------------------------------------------
# Placeholder insertion
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generate_inserts_placeholder_cost_when_no_cost_info():
    """Summary without cost/budget info should produce a placeholder CostItem."""
    summary = _make_summary(
        problem_statement="We need a better system.",
        proposed_solution="Build a new platform.",
        key_goals=["Improve efficiency"],
        assumptions=[],   # empty → triggers placeholder
        constraints=[],   # empty → triggers placeholder
    )
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    case = await generator.generate(summary)

    placeholder_costs = [c for c in case.estimated_costs if c.is_placeholder]
    assert len(placeholder_costs) >= 1
    assert any("[PLACEHOLDER]" in c.label for c in placeholder_costs)
    assert all(c.amount is None for c in placeholder_costs)


@pytest.mark.anyio
async def test_generate_placeholder_fields_listed_in_placeholders():
    """Field names that need completion are listed in BusinessCase.placeholders."""
    summary = _make_summary(
        problem_statement="We need a better system.",
        proposed_solution="Build a new platform.",
        key_goals=["Improve efficiency"],
        assumptions=[],
        constraints=[],
    )
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    case = await generator.generate(summary)

    assert "estimated_costs" in case.placeholders
    assert "expected_benefits" in case.placeholders


@pytest.mark.anyio
async def test_generate_no_placeholders_when_cost_info_present():
    """Summary with explicit cost info should not trigger placeholder insertion."""
    summary = _make_summary(
        problem_statement="Budget is $200k for this project.",
        assumptions=["Team is available"],
        constraints=["6-month timeline"],
    )
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    case = await generator.generate(summary)

    assert case.placeholders == []
    assert not any(c.is_placeholder for c in case.estimated_costs)


@pytest.mark.anyio
async def test_identify_placeholders_empty_assumptions_and_constraints():
    generator = BusinessCaseGenerator()
    summary = _make_summary(assumptions=[], constraints=[])
    placeholders = generator._identify_placeholders(summary)
    assert "estimated_costs" in placeholders
    assert "expected_benefits" in placeholders


@pytest.mark.anyio
async def test_identify_placeholders_no_cost_mention():
    generator = BusinessCaseGenerator()
    summary = _make_summary(
        problem_statement="We need a better system.",
        proposed_solution="Build a new platform.",
        key_goals=["Improve efficiency"],
        assumptions=["Team is available"],
        constraints=["6-month timeline"],
    )
    placeholders = generator._identify_placeholders(summary)
    assert "estimated_costs" in placeholders


@pytest.mark.anyio
async def test_identify_placeholders_with_cost_mention():
    generator = BusinessCaseGenerator()
    summary = _make_summary(
        problem_statement="Budget is $200k.",
        assumptions=["Team is available"],
        constraints=["6-month timeline"],
    )
    placeholders = generator._identify_placeholders(summary)
    assert "estimated_costs" not in placeholders


# ---------------------------------------------------------------------------
# LLMParseError
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generate_raises_llm_parse_error_on_invalid_json():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(response="not valid json"))
    with pytest.raises(LLMParseError) as exc_info:
        await generator.generate(summary)
    assert "generate" in str(exc_info.value)


@pytest.mark.anyio
async def test_generate_raises_llm_parse_error_on_missing_required_field():
    bad = _valid_business_case_dict()
    del bad["executive_summary"]
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(response=json.dumps(bad)))
    with pytest.raises(LLMParseError) as exc_info:
        await generator.generate(summary)
    assert "generate" in str(exc_info.value)


@pytest.mark.anyio
async def test_llm_parse_error_includes_first_500_chars():
    long_invalid = "z" * 600
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(response=long_invalid))
    with pytest.raises(LLMParseError) as exc_info:
        await generator.generate(summary)
    assert "z" * 500 in str(exc_info.value)


# ---------------------------------------------------------------------------
# Revision versioning
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_revise_increments_version():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    original = await generator.generate(summary)

    revised = await generator.revise(original, "Add more detail to cost estimates.")
    assert revised.version == original.version + 1


@pytest.mark.anyio
async def test_revise_stores_previous_in_version_history():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    original = await generator.generate(summary)

    revised = await generator.revise(original, "Clarify risks.")
    assert len(revised.version_history) == 1
    assert revised.version_history[0].id == original.id


@pytest.mark.anyio
async def test_revise_chains_version_history():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    v1 = await generator.generate(summary)
    v2 = await generator.revise(v1, "First revision.")
    v3 = await generator.revise(v2, "Second revision.")

    assert v3.version == 3
    assert len(v3.version_history) == 2
    assert v3.version_history[0].id == v2.id
    assert v3.version_history[1].id == v1.id


@pytest.mark.anyio
async def test_revise_preserves_ideation_summary_id():
    summary = _make_summary()
    generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    original = await generator.generate(summary)
    revised = await generator.revise(original, "Minor tweak.")
    assert revised.ideation_summary_id == summary.id


@pytest.mark.anyio
async def test_revise_raises_llm_parse_error_on_bad_response():
    summary = _make_summary()
    good_generator = BusinessCaseGenerator(llm_client=MockLLMClient(summary_id=summary.id))
    original = await good_generator.generate(summary)

    bad_generator = BusinessCaseGenerator(llm_client=MockLLMClient(response="bad json"))
    with pytest.raises(LLMParseError):
        await bad_generator.revise(original, "Some instructions.")
