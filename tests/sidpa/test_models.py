"""Property-based and unit tests for Pydantic data models.

Validates: Requirements 2, 10
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from pmbok.models.business_case import BusinessCase, CostItem
from pmbok.models.enums import (
    ApprovalStatus,
    InputSourceType,
    KnowledgeArea,
    ProcessGroup,
    ProcessStatus,
)
from pmbok.models.ideation import Conflict, IdeationSummary
from pmbok.models.pmbok import ProjectArtifact


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_text = st.text(min_size=1, max_size=100)
_uuid_str = st.uuids().map(str)
_datetimes = st.datetimes(allow_imaginary=False)
_approval_status = st.sampled_from(ApprovalStatus)


@st.composite
def conflict_strategy(draw):
    return Conflict(
        field=draw(_text),
        source_a_id=draw(_uuid_str),
        value_a=draw(_text),
        source_b_id=draw(_uuid_str),
        value_b=draw(_text),
        resolved=draw(st.booleans()),
        resolution=draw(st.one_of(st.none(), _text)),
    )


@st.composite
def ideation_summary_strategy(draw):
    return IdeationSummary(
        id=draw(_uuid_str),
        session_id=draw(_uuid_str),
        version=draw(st.integers(min_value=1, max_value=10)),
        title=draw(_text),
        problem_statement=draw(_text),
        proposed_solution=draw(_text),
        key_goals=draw(st.lists(_text, min_size=1, max_size=5)),
        assumptions=draw(st.lists(_text, max_size=3)),
        constraints=draw(st.lists(_text, max_size=3)),
        conflicts=draw(st.lists(conflict_strategy(), max_size=2)),
        approval_status=draw(_approval_status),
        created_at=draw(_datetimes),
        version_history=[],  # avoid infinite recursion
    )


@st.composite
def cost_item_strategy(draw):
    return CostItem(
        label=draw(_text),
        amount=draw(st.one_of(st.none(), st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))),
        currency=draw(st.sampled_from(["USD", "EUR", "GBP"])),
        is_placeholder=draw(st.booleans()),
    )


@st.composite
def business_case_strategy(draw):
    return BusinessCase(
        id=draw(_uuid_str),
        ideation_summary_id=draw(_uuid_str),
        version=draw(st.integers(min_value=1, max_value=10)),
        executive_summary=draw(_text),
        problem_statement=draw(_text),
        proposed_solution=draw(_text),
        expected_benefits=draw(st.lists(_text, max_size=5)),
        estimated_costs=draw(st.lists(cost_item_strategy(), max_size=3)),
        key_risks=draw(st.lists(_text, max_size=3)),
        recommendation=draw(_text),
        placeholders=draw(st.lists(_text, max_size=3)),
        approval_status=draw(_approval_status),
        created_at=draw(_datetimes),
        version_history=[],  # avoid infinite recursion
    )


# Simple JSON-safe content dict
_simple_value = st.one_of(
    st.text(max_size=50),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
)


@st.composite
def project_artifact_strategy(draw):
    content = draw(
        st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_")),
            _simple_value,
            max_size=5,
        )
    )
    return ProjectArtifact(
        id=draw(_uuid_str),
        run_id=draw(_uuid_str),
        process_id=draw(st.text(min_size=1, max_size=20)),
        artifact_type=draw(_text),
        version=draw(st.integers(min_value=1, max_value=10)),
        content=content,
        produced_by=draw(_text),
        created_at=draw(_datetimes),
        previous_version_id=draw(st.one_of(st.none(), _uuid_str)),
    )


# ---------------------------------------------------------------------------
# Property-based round-trip tests
# Validates: Requirements 2, 10
# ---------------------------------------------------------------------------

@given(ideation_summary_strategy())
@settings(max_examples=50)
def test_ideation_summary_round_trip(model: IdeationSummary):
    """**Validates: Requirements 2, 10** — IdeationSummary serializes and deserializes without data loss."""
    assert IdeationSummary.model_validate_json(model.model_dump_json()) == model


@given(business_case_strategy())
@settings(max_examples=50)
def test_business_case_round_trip(model: BusinessCase):
    """**Validates: Requirements 2, 10** — BusinessCase serializes and deserializes without data loss."""
    assert BusinessCase.model_validate_json(model.model_dump_json()) == model


@given(project_artifact_strategy())
@settings(max_examples=50)
def test_project_artifact_round_trip(model: ProjectArtifact):
    """**Validates: Requirements 2, 10** — ProjectArtifact serializes and deserializes without data loss."""
    assert ProjectArtifact.model_validate_json(model.model_dump_json()) == model


# ---------------------------------------------------------------------------
# Unit tests — validation constraints
# ---------------------------------------------------------------------------

def test_ideation_summary_empty_key_goals_raises():
    """IdeationSummary.key_goals with empty list must raise ValidationError."""
    with pytest.raises(ValidationError):
        IdeationSummary(
            session_id="s1",
            title="T",
            problem_statement="P",
            proposed_solution="S",
            key_goals=[],  # violates min_length=1
        )


def test_ideation_summary_missing_key_goals_raises():
    """IdeationSummary without key_goals must raise ValidationError."""
    with pytest.raises(ValidationError):
        IdeationSummary(
            session_id="s1",
            title="T",
            problem_statement="P",
            proposed_solution="S",
        )


def test_model_validate_json_invalid_raises():
    """model_validate_json on invalid JSON must raise ValidationError."""
    with pytest.raises(ValidationError):
        IdeationSummary.model_validate_json('{"not": "valid ideation summary"}')


def test_model_validate_json_malformed_raises():
    """model_validate_json on malformed JSON string must raise an error."""
    with pytest.raises(Exception):
        IdeationSummary.model_validate_json("not json at all {{{")


def test_business_case_defaults():
    """BusinessCase can be constructed with minimal required fields."""
    bc = BusinessCase(
        ideation_summary_id="abc",
        executive_summary="exec",
        problem_statement="prob",
        proposed_solution="sol",
        expected_benefits=["benefit"],
        estimated_costs=[],
        key_risks=[],
        recommendation="rec",
    )
    assert bc.version == 1
    assert bc.approval_status == ApprovalStatus.PENDING
    assert bc.placeholders == []
    assert bc.version_history == []


def test_project_artifact_defaults():
    """ProjectArtifact can be constructed with minimal required fields."""
    artifact = ProjectArtifact(
        run_id="run1",
        process_id="proc1",
        artifact_type="plan",
        content={"key": "value"},
        produced_by="agent",
    )
    assert artifact.version == 1
    assert artifact.previous_version_id is None


def test_conflict_model():
    """Conflict model stores all fields correctly."""
    c = Conflict(
        field="goals",
        source_a_id="a",
        value_a="fast delivery",
        source_b_id="b",
        value_b="high quality",
    )
    assert c.resolved is False
    assert c.resolution is None
