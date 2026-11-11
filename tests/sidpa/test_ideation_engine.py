"""Tests for IdeationEngine."""

from __future__ import annotations

import json
import pytest
import anyio

from pmbok.engines.ideation_engine import IdeationEngine, CONFLICT_THRESHOLD, _jaccard
from pmbok.exceptions import LLMParseError
from pmbok.models.enums import InputSourceType
from pmbok.models.ideation import IdeationSummary
from pmbok.models.inputs import ParsedInput


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_parsed_input(text: str, source_type: InputSourceType = InputSourceType.TEXT) -> ParsedInput:
    return ParsedInput(
        raw_input_id="raw-1",
        extracted_text=text,
        source_type=source_type,
    )


def _valid_summary_dict(**overrides) -> dict:
    base = {
        "session_id": "sess-001",
        "title": "Smart Irrigation Controller",
        "problem_statement": "Farmers waste 40% of water.",
        "proposed_solution": "IoT sensor network with AI scheduling.",
        "key_goals": ["Reduce water usage by 30%", "Automate scheduling"],
        "assumptions": ["Farmers have smartphones"],
        "constraints": ["Budget under $500k"],
        "conflicts": [],
        "version_history": [],
    }
    base.update(overrides)
    return base


class MockLLMClient:
    """Returns a configurable JSON string."""

    def __init__(self, response: str | None = None):
        self._response = response or json.dumps(_valid_summary_dict())

    async def complete(self, prompt: str) -> str:  # noqa: ARG002
        return self._response


# ---------------------------------------------------------------------------
# Jaccard helper
# ---------------------------------------------------------------------------

def test_jaccard_identical():
    assert _jaccard("reduce water usage", "reduce water usage") == 1.0


def test_jaccard_no_overlap():
    assert _jaccard("reduce water usage", "increase profit margin") == 0.0


def test_jaccard_partial_overlap():
    score = _jaccard("reduce water usage by 30%", "reduce energy usage by 50%")
    assert 0.0 < score < 1.0


def test_jaccard_empty_strings():
    assert _jaccard("", "") == 1.0


# ---------------------------------------------------------------------------
# generate_summary — happy path
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generate_summary_returns_ideation_summary():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [_make_parsed_input("We need a smart irrigation system.")]
    summary = await engine.generate_summary(inputs, session_id="sess-001")

    assert isinstance(summary, IdeationSummary)
    assert summary.title == "Smart Irrigation Controller"
    assert summary.session_id == "sess-001"
    assert len(summary.key_goals) >= 1


@pytest.mark.anyio
async def test_generate_summary_uses_first_input_id_as_session_id_when_not_provided():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inp = _make_parsed_input("Some idea text.")
    summary = await engine.generate_summary([inp])

    # session_id should be the first input's id when not explicitly passed
    assert summary.session_id == inp.id


@pytest.mark.anyio
async def test_generate_summary_consolidates_multiple_inputs():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [
        _make_parsed_input("Input one text."),
        _make_parsed_input("Input two text."),
        _make_parsed_input("Input three text."),
    ]
    summary = await engine.generate_summary(inputs, session_id="multi-sess")
    assert isinstance(summary, IdeationSummary)


@pytest.mark.anyio
async def test_generate_summary_stub_client_when_no_llm():
    """Engine with no LLM client uses the stub and still returns a valid summary."""
    engine = IdeationEngine()
    inputs = [_make_parsed_input("Some idea.")]
    summary = await engine.generate_summary(inputs)
    assert isinstance(summary, IdeationSummary)
    assert len(summary.key_goals) >= 1


# ---------------------------------------------------------------------------
# generate_summary — LLMParseError
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generate_summary_raises_llm_parse_error_on_invalid_json():
    engine = IdeationEngine(llm_client=MockLLMClient(response="not valid json"))
    with pytest.raises(LLMParseError) as exc_info:
        await engine.generate_summary([_make_parsed_input("text")])
    assert "generate_summary" in str(exc_info.value)
    assert "not valid json"[:50] in str(exc_info.value)


@pytest.mark.anyio
async def test_generate_summary_raises_llm_parse_error_on_missing_required_field():
    # key_goals is required (min_length=1); omit it to trigger ValidationError
    bad = _valid_summary_dict()
    del bad["key_goals"]
    engine = IdeationEngine(llm_client=MockLLMClient(response=json.dumps(bad)))
    with pytest.raises(LLMParseError) as exc_info:
        await engine.generate_summary([_make_parsed_input("text")])
    assert "generate_summary" in str(exc_info.value)


@pytest.mark.anyio
async def test_llm_parse_error_includes_first_500_chars():
    long_invalid = "x" * 600
    engine = IdeationEngine(llm_client=MockLLMClient(response=long_invalid))
    with pytest.raises(LLMParseError) as exc_info:
        await engine.generate_summary([_make_parsed_input("text")])
    # The error message should contain the first 500 chars of the raw response
    assert "x" * 500 in str(exc_info.value)


# ---------------------------------------------------------------------------
# _detect_conflicts
# ---------------------------------------------------------------------------

def test_detect_conflicts_no_conflicts_when_items_similar():
    engine = IdeationEngine()
    # These two strings share 3 out of 4 unique words → Jaccard ≥ 0.6
    raw = {
        "key_goals": ["reduce water usage now", "reduce water usage today"],
        "assumptions": [],
        "constraints": [],
    }
    conflicts = engine._detect_conflicts(raw)
    goal_conflicts = [c for c in conflicts if c.field == "key_goals"]
    assert goal_conflicts == []


def test_detect_conflicts_produces_conflict_for_dissimilar_items():
    engine = IdeationEngine()
    raw = {
        "key_goals": ["reduce water usage", "maximize shareholder profit"],
        "assumptions": [],
        "constraints": [],
    }
    conflicts = engine._detect_conflicts(raw)
    goal_conflicts = [c for c in conflicts if c.field == "key_goals"]
    assert len(goal_conflicts) == 1
    assert goal_conflicts[0].resolved is False


def test_detect_conflicts_checks_all_three_fields():
    engine = IdeationEngine()
    raw = {
        "key_goals": ["alpha beta gamma", "delta epsilon zeta"],
        "assumptions": ["team is available", "budget is unlimited"],
        "constraints": ["deliver in 6 months", "use only open source"],
    }
    conflicts = engine._detect_conflicts(raw)
    fields_with_conflicts = {c.field for c in conflicts}
    # All three fields have dissimilar pairs → all should appear
    assert "key_goals" in fields_with_conflicts
    assert "assumptions" in fields_with_conflicts
    assert "constraints" in fields_with_conflicts


def test_detect_conflicts_stored_without_auto_resolution():
    engine = IdeationEngine()
    raw = {
        "key_goals": ["reduce water usage", "maximize shareholder profit"],
        "assumptions": [],
        "constraints": [],
    }
    conflicts = engine._detect_conflicts(raw)
    for c in conflicts:
        assert c.resolved is False
        assert c.resolution is None


def test_detect_conflicts_empty_fields_produce_no_conflicts():
    engine = IdeationEngine()
    conflicts = engine._detect_conflicts({"key_goals": [], "assumptions": [], "constraints": []})
    assert conflicts == []


def test_detect_conflicts_single_item_per_field_no_conflict():
    engine = IdeationEngine()
    raw = {
        "key_goals": ["only one goal"],
        "assumptions": ["only one assumption"],
        "constraints": ["only one constraint"],
    }
    assert engine._detect_conflicts(raw) == []


@pytest.mark.anyio
async def test_generate_summary_attaches_conflicts():
    """Conflicts detected by _detect_conflicts are stored in the returned summary."""
    dissimilar_goals = ["reduce water usage", "maximize shareholder profit"]
    response = json.dumps(_valid_summary_dict(key_goals=dissimilar_goals))
    engine = IdeationEngine(llm_client=MockLLMClient(response=response))
    summary = await engine.generate_summary([_make_parsed_input("text")], session_id="s1")
    assert len(summary.conflicts) >= 1
    assert all(c.resolved is False for c in summary.conflicts)


# ---------------------------------------------------------------------------
# revise_summary
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_revise_summary_increments_version():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [_make_parsed_input("Initial idea.")]
    original = await engine.generate_summary(inputs, session_id="sess-rev")

    revised = await engine.revise_summary(original, "Add more detail to goals.")
    assert revised.version == original.version + 1


@pytest.mark.anyio
async def test_revise_summary_preserves_previous_in_version_history():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [_make_parsed_input("Initial idea.")]
    original = await engine.generate_summary(inputs, session_id="sess-rev")

    revised = await engine.revise_summary(original, "Clarify constraints.")
    assert len(revised.version_history) == 1
    assert revised.version_history[0].id == original.id


@pytest.mark.anyio
async def test_revise_summary_chains_version_history():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [_make_parsed_input("Initial idea.")]
    v1 = await engine.generate_summary(inputs, session_id="sess-chain")
    v2 = await engine.revise_summary(v1, "First revision.")
    v3 = await engine.revise_summary(v2, "Second revision.")

    assert v3.version == 3
    assert len(v3.version_history) == 2
    # Most recent previous version is first
    assert v3.version_history[0].id == v2.id
    assert v3.version_history[1].id == v1.id


@pytest.mark.anyio
async def test_revise_summary_preserves_session_id():
    engine = IdeationEngine(llm_client=MockLLMClient())
    inputs = [_make_parsed_input("Initial idea.")]
    original = await engine.generate_summary(inputs, session_id="my-session")
    revised = await engine.revise_summary(original, "Minor tweak.")
    assert revised.session_id == "my-session"


@pytest.mark.anyio
async def test_revise_summary_raises_llm_parse_error_on_bad_response():
    engine = IdeationEngine(llm_client=MockLLMClient(response="bad json"))
    inputs = [_make_parsed_input("Initial idea.")]
    # First generate with a valid client, then swap to bad one for revision
    good_engine = IdeationEngine(llm_client=MockLLMClient())
    original = await good_engine.generate_summary(inputs, session_id="sess")

    with pytest.raises(LLMParseError):
        await engine.revise_summary(original, "Some instructions.")


# ---------------------------------------------------------------------------
# _build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_includes_input_text():
    engine = IdeationEngine()
    inp = _make_parsed_input("We need a smart irrigation system.")
    prompt = engine._build_prompt([inp])
    assert "smart irrigation system" in prompt


def test_build_prompt_includes_diagram_description_when_present():
    engine = IdeationEngine()
    inp = ParsedInput(
        raw_input_id="r1",
        extracted_text="Some text.",
        diagram_description="A flowchart showing data flow.",
        source_type=InputSourceType.IMAGE,
    )
    prompt = engine._build_prompt([inp])
    assert "flowchart" in prompt


def test_build_prompt_includes_all_inputs():
    engine = IdeationEngine()
    inputs = [
        _make_parsed_input("First input text."),
        _make_parsed_input("Second input text."),
    ]
    prompt = engine._build_prompt(inputs)
    assert "First input text." in prompt
    assert "Second input text." in prompt


def test_build_prompt_uses_custom_template():
    engine = IdeationEngine(prompt_template="CUSTOM TEMPLATE: ")
    inp = _make_parsed_input("Some idea.")
    prompt = engine._build_prompt([inp])
    assert prompt.startswith("CUSTOM TEMPLATE: ")
