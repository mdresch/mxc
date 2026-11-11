"""Tests for ApprovalGate — present, is_group_complete, gate persistence."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pmbok.models.approval import ApprovalDecision
from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus
from pmbok.models.pmbok import ProcessMap, ProcessState
from pmbok.orchestrator.approval_gate import (
    GATE_1_IDEATION,
    GATE_2_BUSINESS_CASE,
    GATE_3_INITIATING,
    GATE_4_PLANNING,
    GATE_5_EXECUTING,
    GATE_6_MONITORING_CONTROLLING,
    GATE_NAMES,
    ApprovalGate,
)
from pmbok.process_registry import get_processes_by_group
from pmbok.storage.state_store import StateStore


# ── Fixtures ──────────────────────────────────────────────────────────────────


def make_state_store(tmp_path: Path) -> StateStore:
    return StateStore(str(tmp_path / "state.db"))


def make_gate(tmp_path: Path, run_id: str = "run-1") -> ApprovalGate:
    store = make_state_store(tmp_path)
    return ApprovalGate(state_store=store, run_id=run_id)


def make_process_map(
    group: ProcessGroup, status: ProcessStatus
) -> ProcessMap:
    """Build a ProcessMap where all processes in *group* have the given status."""
    processes = [
        ProcessState(process_id=p.process_id, run_id="run-1", status=status)
        for p in get_processes_by_group(group)
    ]
    return ProcessMap(run_id="run-1", processes=processes)


# ── Gate name constants ───────────────────────────────────────────────────────


def test_gate_name_constants_defined():
    assert GATE_1_IDEATION == "GATE_1_IDEATION"
    assert GATE_2_BUSINESS_CASE == "GATE_2_BUSINESS_CASE"
    assert GATE_3_INITIATING == "GATE_3_INITIATING"
    assert GATE_4_PLANNING == "GATE_4_PLANNING"
    assert GATE_5_EXECUTING == "GATE_5_EXECUTING"
    assert GATE_6_MONITORING_CONTROLLING == "GATE_6_MONITORING_CONTROLLING"


def test_gate_names_dict_covers_all_groups():
    assert ProcessGroup.INITIATING in GATE_NAMES
    assert ProcessGroup.PLANNING in GATE_NAMES
    assert ProcessGroup.EXECUTING in GATE_NAMES
    assert ProcessGroup.MONITORING_CONTROLLING in GATE_NAMES


# ── is_group_complete ─────────────────────────────────────────────────────────


def test_is_group_complete_all_complete(tmp_path):
    gate = make_gate(tmp_path)
    pm = make_process_map(ProcessGroup.INITIATING, ProcessStatus.COMPLETE)
    assert gate.is_group_complete(pm, ProcessGroup.INITIATING) is True


def test_is_group_complete_one_blocked(tmp_path):
    gate = make_gate(tmp_path)
    processes = get_processes_by_group(ProcessGroup.INITIATING)
    states = [
        ProcessState(
            process_id=p.process_id,
            run_id="run-1",
            status=ProcessStatus.COMPLETE,
        )
        for p in processes
    ]
    # Block the first process
    states[0] = ProcessState(
        process_id=processes[0].process_id,
        run_id="run-1",
        status=ProcessStatus.BLOCKED,
    )
    pm = ProcessMap(run_id="run-1", processes=states)
    assert gate.is_group_complete(pm, ProcessGroup.INITIATING) is False


def test_is_group_complete_one_in_progress(tmp_path):
    gate = make_gate(tmp_path)
    processes = get_processes_by_group(ProcessGroup.PLANNING)
    states = [
        ProcessState(
            process_id=p.process_id,
            run_id="run-1",
            status=ProcessStatus.COMPLETE,
        )
        for p in processes
    ]
    states[0] = ProcessState(
        process_id=processes[0].process_id,
        run_id="run-1",
        status=ProcessStatus.IN_PROGRESS,
    )
    pm = ProcessMap(run_id="run-1", processes=states)
    assert gate.is_group_complete(pm, ProcessGroup.PLANNING) is False


def test_is_group_complete_not_started(tmp_path):
    gate = make_gate(tmp_path)
    pm = make_process_map(ProcessGroup.INITIATING, ProcessStatus.NOT_STARTED)
    assert gate.is_group_complete(pm, ProcessGroup.INITIATING) is False


# ── present with decision_override ───────────────────────────────────────────


@pytest.mark.anyio
async def test_present_approve_override(tmp_path):
    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-2")

    decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
    result = await gate.present(
        artifact=ProcessGroup.INITIATING,
        rendered_markdown="# Initiating Group Complete",
        gate_name=GATE_3_INITIATING,
        decision_override=decision,
    )

    assert result.status == ApprovalStatus.APPROVED


@pytest.mark.anyio
async def test_present_reject_override_returns_instructions(tmp_path):
    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-3")

    decision = ApprovalDecision(
        status=ApprovalStatus.REJECTED,
        revision_instructions="Please add more detail to the charter.",
    )
    result = await gate.present(
        artifact=ProcessGroup.INITIATING,
        rendered_markdown="# Initiating Group",
        gate_name=GATE_3_INITIATING,
        decision_override=decision,
    )

    assert result.status == ApprovalStatus.REJECTED
    assert result.revision_instructions == "Please add more detail to the charter."


# ── Gate persistence ──────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_present_persists_approved_decision(tmp_path):
    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-4")

    decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
    await gate.present(
        artifact=ProcessGroup.PLANNING,
        rendered_markdown="# Planning Group",
        gate_name=GATE_4_PLANNING,
        decision_override=decision,
    )

    saved = await store.load_gate("run-4", GATE_4_PLANNING)
    assert saved is not None
    assert saved["status"] == ApprovalStatus.APPROVED
    assert saved["gate_name"] == GATE_4_PLANNING


@pytest.mark.anyio
async def test_present_persists_rejected_decision_with_instructions(tmp_path):
    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-5")

    decision = ApprovalDecision(
        status=ApprovalStatus.REJECTED,
        revision_instructions="Revise cost estimates.",
    )
    await gate.present(
        artifact=ProcessGroup.PLANNING,
        rendered_markdown="# Planning Group",
        gate_name=GATE_4_PLANNING,
        decision_override=decision,
    )

    saved = await store.load_gate("run-5", GATE_4_PLANNING)
    assert saved is not None
    assert saved["status"] == ApprovalStatus.REJECTED
    assert saved["revision_instructions"] == "Revise cost estimates."


# ── user_interface callback ───────────────────────────────────────────────────


@pytest.mark.anyio
async def test_present_uses_user_interface_callback(tmp_path):
    store = make_state_store(tmp_path)

    async def mock_ui(rendered: str) -> ApprovalDecision:
        assert "# Test" in rendered
        return ApprovalDecision(status=ApprovalStatus.APPROVED)

    gate = ApprovalGate(state_store=store, run_id="run-6", user_interface=mock_ui)
    result = await gate.present(
        artifact=ProcessGroup.EXECUTING,
        rendered_markdown="# Test",
        gate_name=GATE_5_EXECUTING,
    )
    assert result.status == ApprovalStatus.APPROVED


# ── Gate name derivation ──────────────────────────────────────────────────────


def test_derive_gate_name_from_process_group(tmp_path):
    assert ApprovalGate._derive_gate_name(ProcessGroup.INITIATING) == GATE_3_INITIATING
    assert ApprovalGate._derive_gate_name(ProcessGroup.PLANNING) == GATE_4_PLANNING
    assert ApprovalGate._derive_gate_name(ProcessGroup.EXECUTING) == GATE_5_EXECUTING
    assert (
        ApprovalGate._derive_gate_name(ProcessGroup.MONITORING_CONTROLLING)
        == GATE_6_MONITORING_CONTROLLING
    )


@pytest.mark.anyio
async def test_present_derives_gate_name_from_ideation_summary(tmp_path):
    """When artifact is an IdeationSummary, gate name should be GATE_1_IDEATION."""
    from pmbok.models.ideation import IdeationSummary

    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-7")

    summary = IdeationSummary(
        session_id="sess-1",
        title="Test",
        problem_statement="Problem",
        proposed_solution="Solution",
        key_goals=["Goal 1"],
    )
    decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
    await gate.present(
        artifact=summary,
        rendered_markdown="# Ideation Summary",
        decision_override=decision,
    )

    saved = await store.load_gate("run-7", GATE_1_IDEATION)
    assert saved is not None
    assert saved["status"] == ApprovalStatus.APPROVED


@pytest.mark.anyio
async def test_present_derives_gate_name_from_business_case(tmp_path):
    """When artifact is a BusinessCase, gate name should be GATE_2_BUSINESS_CASE."""
    from pmbok.models.business_case import BusinessCase, CostItem

    store = make_state_store(tmp_path)
    gate = ApprovalGate(state_store=store, run_id="run-8")

    bc = BusinessCase(
        ideation_summary_id="sum-1",
        executive_summary="Exec",
        problem_statement="Problem",
        proposed_solution="Solution",
        expected_benefits=["Benefit"],
        estimated_costs=[CostItem(label="Dev", amount=50_000.0)],
        key_risks=["Risk"],
        recommendation="Proceed",
    )
    decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
    await gate.present(
        artifact=bc,
        rendered_markdown="# Business Case",
        decision_override=decision,
    )

    saved = await store.load_gate("run-8", GATE_2_BUSINESS_CASE)
    assert saved is not None
    assert saved["status"] == ApprovalStatus.APPROVED


# ── __init__ exports ──────────────────────────────────────────────────────────


def test_approval_gate_exported_from_orchestrator_package():
    from pmbok.orchestrator import ApprovalGate as AG, PMBOKOrchestrator
    assert AG is ApprovalGate
    assert PMBOKOrchestrator is not None
