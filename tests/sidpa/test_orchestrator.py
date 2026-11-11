"""Tests for PMBOKOrchestrator — dependency resolution, blocked propagation, gate enforcement."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pmbok.models.approval import ApprovalDecision
from pmbok.models.business_case import BusinessCase, CostItem
from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus
from pmbok.models.pmbok import PMBOKProcess, ProcessMap, ProjectArtifact, ProjectRun
from pmbok.orchestrator.orchestrator import (
    PMBOKOrchestrator,
    _PROCESS_BY_ID,
    _REVERSE_DEP_MAP,
    _build_reverse_dep_map,
)
from pmbok.process_registry import PMBOK_PROCESSES, get_processes_by_group
from pmbok.storage.artifact_store import ArtifactStore
from pmbok.storage.state_store import StateStore


# ── Fixtures ──────────────────────────────────────────────────────────────────


def make_business_case() -> BusinessCase:
    return BusinessCase(
        ideation_summary_id="summary-1",
        executive_summary="Test",
        problem_statement="Problem",
        proposed_solution="Solution",
        expected_benefits=["Benefit A"],
        estimated_costs=[CostItem(label="Dev", amount=100_000.0)],
        key_risks=["Risk A"],
        recommendation="Proceed",
    )


def make_stores(tmp_path: Path) -> tuple[ArtifactStore, StateStore]:
    artifact_store = ArtifactStore(tmp_path / "artifacts")
    state_store = StateStore(str(tmp_path / "state.db"))
    return artifact_store, state_store


def make_orchestrator(
    tmp_path: Path,
    agent_factory: MagicMock | None = None,
) -> tuple[PMBOKOrchestrator, ArtifactStore, StateStore]:
    artifact_store, state_store = make_stores(tmp_path)
    if agent_factory is None:
        agent_factory = MagicMock()
        mock_agent = AsyncMock()
        mock_agent.execute = AsyncMock(return_value=[])
        agent_factory.create.return_value = mock_agent
    orch = PMBOKOrchestrator(
        agent_factory=agent_factory,
        artifact_store=artifact_store,
        state_store=state_store,
    )
    return orch, artifact_store, state_store


# ── Reverse dependency map ────────────────────────────────────────────────────


def test_reverse_dep_map_built_correctly():
    """4.1 is a prerequisite of many planning processes — they should appear in its dependents."""
    rev = _build_reverse_dep_map()
    # 4.1 → 4.2, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 12.1
    assert "4.2" in rev["4.1"]
    assert "5.1" in rev["4.1"]
    assert "6.1" in rev["4.1"]


def test_get_direct_dependents(tmp_path):
    orch, _, _ = make_orchestrator(tmp_path)
    deps = orch._get_direct_dependents("4.1")
    assert "4.2" in deps
    assert "5.1" in deps


def test_get_direct_dependents_leaf_process(tmp_path):
    """4.7 (Close Project) has no dependents."""
    orch, _, _ = make_orchestrator(tmp_path)
    deps = orch._get_direct_dependents("4.7")
    assert deps == []


# ── _resolve_ready_processes ──────────────────────────────────────────────────


def test_resolve_ready_processes_initiating_all_not_started(tmp_path):
    """With all processes NOT_STARTED, only Initiating processes with no prereqs are ready."""
    orch, _, _ = make_orchestrator(tmp_path)
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    ready = orch._resolve_ready_processes("run-1", status_map)
    ready_ids = {p.process_id for p in ready}
    # 4.1 and 13.1 have no prerequisites
    assert "4.1" in ready_ids
    assert "13.1" in ready_ids
    # Planning processes should NOT be ready yet
    assert "4.2" not in ready_ids
    assert "5.1" not in ready_ids


def test_resolve_ready_processes_after_initiating_complete(tmp_path):
    """After 4.1 and 13.1 complete, planning processes that depend only on them become ready."""
    orch, _, _ = make_orchestrator(tmp_path)
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    status_map["4.1"] = ProcessStatus.COMPLETE
    status_map["13.1"] = ProcessStatus.COMPLETE

    ready = orch._resolve_ready_processes("run-1", status_map)
    ready_ids = {p.process_id for p in ready}

    # 4.2 depends on subsidiary plans (PMBOK 8 ADR-008) → NOT ready until subsidiary plans complete
    assert "4.2" not in ready_ids
    # 5.1 depends only on 4.1 → should be ready
    assert "5.1" in ready_ids
    # 13.2 depends only on 13.1 → should be ready
    assert "13.2" in ready_ids
    # 5.2 depends on 5.1 (not complete) → NOT ready
    assert "5.2" not in ready_ids


def test_resolve_ready_processes_skips_in_progress(tmp_path):
    """Processes already IN_PROGRESS are not returned as ready."""
    orch, _, _ = make_orchestrator(tmp_path)
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    status_map["4.1"] = ProcessStatus.IN_PROGRESS

    ready = orch._resolve_ready_processes("run-1", status_map)
    ready_ids = {p.process_id for p in ready}
    # 4.1 is IN_PROGRESS, not NOT_STARTED → not returned
    assert "4.1" not in ready_ids


def test_resolve_ready_processes_multi_prereq(tmp_path):
    """7.2 requires both 7.1 and 6.5 — only ready when both are complete."""
    orch, _, _ = make_orchestrator(tmp_path)
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    # Only 7.1 complete, 6.5 not
    status_map["7.1"] = ProcessStatus.COMPLETE
    ready_ids = {p.process_id for p in orch._resolve_ready_processes("run-1", status_map)}
    assert "7.2" not in ready_ids

    # Both complete
    status_map["6.5"] = ProcessStatus.COMPLETE
    ready_ids = {p.process_id for p in orch._resolve_ready_processes("run-1", status_map)}
    assert "7.2" in ready_ids


# ── _is_group_complete ────────────────────────────────────────────────────────


def test_is_group_complete_all_complete(tmp_path):
    orch, _, _ = make_orchestrator(tmp_path)
    initiating = get_processes_by_group(ProcessGroup.INITIATING)
    status_map = {p.process_id: ProcessStatus.COMPLETE for p in initiating}
    assert orch._is_group_complete(ProcessGroup.INITIATING, status_map) is True


def test_is_group_complete_one_blocked(tmp_path):
    orch, _, _ = make_orchestrator(tmp_path)
    initiating = get_processes_by_group(ProcessGroup.INITIATING)
    status_map = {p.process_id: ProcessStatus.COMPLETE for p in initiating}
    # Block one process
    status_map[initiating[0].process_id] = ProcessStatus.BLOCKED
    assert orch._is_group_complete(ProcessGroup.INITIATING, status_map) is False


def test_is_group_complete_one_not_started(tmp_path):
    orch, _, _ = make_orchestrator(tmp_path)
    initiating = get_processes_by_group(ProcessGroup.INITIATING)
    status_map = {p.process_id: ProcessStatus.COMPLETE for p in initiating}
    status_map[initiating[0].process_id] = ProcessStatus.NOT_STARTED
    assert orch._is_group_complete(ProcessGroup.INITIATING, status_map) is False


# ── _propagate_blocked ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_propagate_blocked_direct_dependent(tmp_path):
    """Blocking 4.1 should propagate to 4.2 (direct dependent)."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-prop-1"

    # Initialize all as NOT_STARTED
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    await orch._propagate_blocked(run_id, "4.1")

    # 4.2 depends on 4.1 → should be BLOCKED
    assert await state_store.get_status(run_id, "4.2") == ProcessStatus.BLOCKED
    # 5.1 depends on 4.1 → should be BLOCKED
    assert await state_store.get_status(run_id, "5.1") == ProcessStatus.BLOCKED


@pytest.mark.anyio
async def test_propagate_blocked_transitive(tmp_path):
    """Blocking 5.1 should transitively block 5.2 → 5.3 → 5.4."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-prop-2"

    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    await orch._propagate_blocked(run_id, "5.1")

    assert await state_store.get_status(run_id, "5.2") == ProcessStatus.BLOCKED
    assert await state_store.get_status(run_id, "5.3") == ProcessStatus.BLOCKED
    assert await state_store.get_status(run_id, "5.4") == ProcessStatus.BLOCKED


@pytest.mark.anyio
async def test_propagate_blocked_does_not_affect_complete(tmp_path):
    """Propagation should not change COMPLETE processes."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-prop-3"

    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    # Mark 5.2 as COMPLETE before propagation
    await state_store.set_status(run_id, "5.2", ProcessStatus.COMPLETE)

    await orch._propagate_blocked(run_id, "5.1")

    # 5.2 was COMPLETE, should remain COMPLETE
    assert await state_store.get_status(run_id, "5.2") == ProcessStatus.COMPLETE
    # But 5.3 (depends on 5.2) should NOT be blocked since 5.2 is complete
    # (propagation only marks NOT_STARTED processes)
    assert await state_store.get_status(run_id, "5.3") == ProcessStatus.NOT_STARTED


# ── Gate enforcement ──────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_advance_to_next_group_requires_complete(tmp_path):
    """advance_to_next_group raises if current group is not complete."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-gate-1"

    run = ProjectRun(
        id=run_id,
        business_case_id="bc-1",
        current_process_group=ProcessGroup.INITIATING,
    )
    await state_store.save_run(run, "sess-1")

    # Initialize all as NOT_STARTED (group not complete)
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    approval = ApprovalDecision(status=ApprovalStatus.APPROVED)
    with pytest.raises(ValueError, match="not complete"):
        await orch.advance_to_next_group(run_id, approval)


@pytest.mark.anyio
async def test_advance_to_next_group_requires_approved(tmp_path):
    """advance_to_next_group raises if approval is not APPROVED."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-gate-2"

    run = ProjectRun(
        id=run_id,
        business_case_id="bc-1",
        current_process_group=ProcessGroup.INITIATING,
    )
    await state_store.save_run(run, "sess-1")

    # Mark all Initiating processes as COMPLETE
    for p in get_processes_by_group(ProcessGroup.INITIATING):
        await state_store.set_status(run_id, p.process_id, ProcessStatus.COMPLETE)

    approval = ApprovalDecision(status=ApprovalStatus.REJECTED)
    with pytest.raises(ValueError, match="not approved"):
        await orch.advance_to_next_group(run_id, approval)


@pytest.mark.anyio
async def test_advance_to_next_group_advances_group(tmp_path):
    """advance_to_next_group updates current_process_group to the next group."""
    agent_factory = MagicMock()
    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=[])
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-gate-3"

    run = ProjectRun(
        id=run_id,
        business_case_id="bc-1",
        current_process_group=ProcessGroup.INITIATING,
    )
    await state_store.save_run(run, "sess-1")

    # Initialize all processes
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    # Mark all Initiating processes as COMPLETE
    for p in get_processes_by_group(ProcessGroup.INITIATING):
        await state_store.set_status(run_id, p.process_id, ProcessStatus.COMPLETE)

    approval = ApprovalDecision(status=ApprovalStatus.APPROVED)
    await orch.advance_to_next_group(run_id, approval)

    updated_run = await state_store.load_run(run_id)
    assert updated_run.current_process_group == ProcessGroup.PLANNING
    assert updated_run.gate_status[ProcessGroup.INITIATING] == ApprovalStatus.APPROVED


# ── get_process_map ───────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_get_process_map_returns_all_49(tmp_path):
    """get_process_map returns a ProcessMap with all 49 processes."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-map-1"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    process_map = await orch.get_process_map(run_id)
    assert isinstance(process_map, ProcessMap)
    assert len(process_map.processes) == 49
    assert process_map.run_id == run_id


@pytest.mark.anyio
async def test_get_process_map_reflects_status(tmp_path):
    """get_process_map reflects current status from state store."""
    orch, _, state_store = make_orchestrator(tmp_path)
    run_id = "run-map-2"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    await state_store.set_status(run_id, "4.1", ProcessStatus.COMPLETE)
    await state_store.set_status(run_id, "13.1", ProcessStatus.IN_PROGRESS)

    process_map = await orch.get_process_map(run_id)
    status_by_id = {ps.process_id: ps.status for ps in process_map.processes}

    assert status_by_id["4.1"] == ProcessStatus.COMPLETE
    assert status_by_id["13.1"] == ProcessStatus.IN_PROGRESS
    assert status_by_id["4.2"] == ProcessStatus.NOT_STARTED


# ── start ─────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_start_creates_project_run(tmp_path):
    """start() creates and persists a ProjectRun."""
    agent_factory = MagicMock()
    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=[])
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    bc = make_business_case()

    run = await orch.start(bc)

    assert isinstance(run, ProjectRun)
    assert run.business_case_id == bc.id
    assert run.current_process_group == ProcessGroup.INITIATING

    # Verify it was persisted
    loaded = await state_store.load_run(run.id)
    assert loaded.id == run.id


@pytest.mark.anyio
async def test_start_initializes_all_process_states(tmp_path):
    """start() initializes all 49 process states."""
    agent_factory = MagicMock()
    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=[])
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    bc = make_business_case()

    run = await orch.start(bc)

    # After start, all processes should have a state (either NOT_STARTED, IN_PROGRESS, or COMPLETE)
    process_map = await orch.get_process_map(run.id)
    assert len(process_map.processes) == 49


@pytest.mark.anyio
async def test_start_dispatches_initiating_processes(tmp_path):
    """start() dispatches all Initiating-group processes."""
    dispatched: list[str] = []

    agent_factory = MagicMock()

    async def fake_execute(run_id, input_artifacts):
        return []

    mock_agent = MagicMock()
    mock_agent.execute = fake_execute
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    bc = make_business_case()

    await orch.start(bc)

    # ProcessAgentFactory.create should have been called for each Initiating process
    initiating = get_processes_by_group(ProcessGroup.INITIATING)
    assert agent_factory.create.call_count >= len(initiating)


# ── Topological sort correctness ──────────────────────────────────────────────


def test_topological_sort_no_cycles(tmp_path):
    """Verify the dependency graph has no cycles (topological sort terminates)."""
    orch, _, _ = make_orchestrator(tmp_path)

    # Simulate completing processes one by one in topological order
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    completed: set[str] = set()
    max_iterations = len(PMBOK_PROCESSES) + 1

    for _ in range(max_iterations):
        ready = orch._resolve_ready_processes("run-topo", status_map)
        if not ready:
            break
        for p in ready:
            status_map[p.process_id] = ProcessStatus.COMPLETE
            completed.add(p.process_id)

    # All processes should eventually be reachable
    assert len(completed) == len(PMBOK_PROCESSES)


def test_resolve_ready_processes_blocked_not_returned(tmp_path):
    """BLOCKED processes are not returned as ready."""
    orch, _, _ = make_orchestrator(tmp_path)
    status_map: dict[str, ProcessStatus] = {
        p.process_id: ProcessStatus.NOT_STARTED for p in PMBOK_PROCESSES
    }
    status_map["4.1"] = ProcessStatus.BLOCKED

    ready = orch._resolve_ready_processes("run-1", status_map)
    ready_ids = {p.process_id for p in ready}
    assert "4.1" not in ready_ids


# ── Tenacity retry / _invoke_agent_with_retry ─────────────────────────────────


@pytest.mark.anyio
async def test_invoke_agent_with_retry_succeeds_on_first_attempt(tmp_path):
    """_invoke_agent_with_retry returns artifacts when agent succeeds immediately."""
    from pmbok.models.pmbok import ProjectArtifact

    artifact = ProjectArtifact(
        run_id="run-1",
        process_id="4.1",
        artifact_type="Project Charter",
        content={"title": "Test"},
        produced_by="4.1",
    )

    agent_factory = MagicMock()
    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=[artifact])
    agent_factory.create.return_value = mock_agent

    orch, _, _ = make_orchestrator(tmp_path, agent_factory)
    process = _PROCESS_BY_ID["4.1"]

    result = await orch._invoke_agent_with_retry("run-1", process, [])
    assert result == [artifact]
    assert mock_agent.execute.call_count == 1


@pytest.mark.anyio
async def test_invoke_agent_with_retry_retries_on_process_execution_error(tmp_path):
    """_invoke_agent_with_retry retries up to 3 times on ProcessExecutionError."""
    from pmbok.exceptions import ProcessExecutionError

    call_count = 0

    async def failing_execute(run_id, input_artifacts, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ProcessExecutionError("simulated failure")

    agent_factory = MagicMock()
    mock_agent = MagicMock()
    mock_agent.execute = failing_execute
    agent_factory.create.return_value = mock_agent

    orch, _, _ = make_orchestrator(tmp_path, agent_factory)
    process = _PROCESS_BY_ID["4.1"]

    # Patch wait to avoid real sleep in tests
    with patch("pmbok.orchestrator.orchestrator.RETRY_CONFIG", {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=0, min=0, max=0),
        "retry": retry_if_exception_type(ProcessExecutionError),
        "reraise": False,
    }):
        from tenacity import RetryError
        # _invoke_agent_with_retry should exhaust retries and raise RetryError
        with pytest.raises(RetryError):
            await orch._invoke_agent_with_retry("run-1", process, [])

    assert call_count == 3


@pytest.mark.anyio
async def test_dispatch_process_marks_blocked_after_all_retries_fail(tmp_path):
    """_dispatch_process marks process BLOCKED when all tenacity retries are exhausted."""
    from pmbok.exceptions import ProcessExecutionError

    async def always_fail(run_id, input_artifacts):
        raise ProcessExecutionError("always fails")

    agent_factory = MagicMock()
    mock_agent = MagicMock()
    mock_agent.execute = always_fail
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-retry-block"

    # Initialize all processes
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    # Patch RETRY_CONFIG to use zero wait so test runs fast
    with patch("pmbok.orchestrator.orchestrator.RETRY_CONFIG", {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=0, min=0, max=0),
        "retry": retry_if_exception_type(ProcessExecutionError),
        "reraise": False,
    }):
        process = _PROCESS_BY_ID["4.1"]
        await orch._dispatch_process(run_id, process)

    status = await state_store.get_status(run_id, "4.1")
    assert status == ProcessStatus.BLOCKED


from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential


# ── resume-on-restart ─────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_resume_fully_completed_run_returns_run_without_dispatching(tmp_path):
    """resume() on a fully completed run returns the ProjectRun without dispatching any processes."""
    agent_factory = MagicMock()
    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=[])
    agent_factory.create.return_value = mock_agent

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-resume-complete"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    # Mark all 49 processes as COMPLETE
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.COMPLETE)

    agent_factory.create.reset_mock()

    result = await orch.resume(run_id)

    assert isinstance(result, ProjectRun)
    assert result.id == run_id
    # No agents should have been created/dispatched
    agent_factory.create.assert_not_called()


@pytest.mark.anyio
async def test_resume_redispatches_not_started_processes(tmp_path):
    """resume() re-dispatches NOT_STARTED processes whose prerequisites are COMPLETE."""
    dispatched_ids: list[str] = []

    agent_factory = MagicMock()

    async def fake_execute(run_id, input_artifacts):
        return []

    mock_agent = MagicMock()
    mock_agent.execute = fake_execute
    agent_factory.create.side_effect = lambda process: (
        dispatched_ids.append(process.process_id) or mock_agent
    )

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-resume-not-started"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    # Mark all processes NOT_STARTED
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    await orch.resume(run_id)

    # 4.1 and 13.1 have no prerequisites → should be dispatched
    assert "4.1" in dispatched_ids
    assert "13.1" in dispatched_ids


@pytest.mark.anyio
async def test_resume_does_not_redispatch_complete_processes(tmp_path):
    """resume() does NOT re-dispatch processes that are already COMPLETE."""
    dispatched_ids: list[str] = []

    agent_factory = MagicMock()

    async def fake_execute(run_id, input_artifacts):
        return []

    mock_agent = MagicMock()
    mock_agent.execute = fake_execute
    agent_factory.create.side_effect = lambda process: (
        dispatched_ids.append(process.process_id) or mock_agent
    )

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-resume-no-complete"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    # Mark all processes NOT_STARTED, then mark 4.1 and 13.1 as COMPLETE
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)
    await state_store.set_status(run_id, "4.1", ProcessStatus.COMPLETE)
    await state_store.set_status(run_id, "13.1", ProcessStatus.COMPLETE)

    await orch.resume(run_id)

    # 4.1 and 13.1 are COMPLETE → must NOT be re-dispatched
    assert "4.1" not in dispatched_ids
    assert "13.1" not in dispatched_ids


@pytest.mark.anyio
async def test_resume_does_not_redispatch_blocked_processes(tmp_path):
    """resume() does NOT re-dispatch processes that are BLOCKED."""
    dispatched_ids: list[str] = []

    agent_factory = MagicMock()

    async def fake_execute(run_id, input_artifacts):
        return []

    mock_agent = MagicMock()
    mock_agent.execute = fake_execute
    agent_factory.create.side_effect = lambda process: (
        dispatched_ids.append(process.process_id) or mock_agent
    )

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-resume-no-blocked"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    # Mark all processes NOT_STARTED, then mark 4.1 as BLOCKED and 13.1 as COMPLETE
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)
    await state_store.set_status(run_id, "4.1", ProcessStatus.BLOCKED)
    await state_store.set_status(run_id, "13.1", ProcessStatus.COMPLETE)

    await orch.resume(run_id)

    # 4.1 is BLOCKED → must NOT be re-dispatched
    assert "4.1" not in dispatched_ids


@pytest.mark.anyio
async def test_resume_mid_run_crash_simulation(tmp_path):
    """
    Integration test: simulate a mid-run crash after 5 processes complete,
    then call resume and verify those 5 completed processes are NOT re-dispatched.
    """
    dispatched_ids: list[str] = []

    agent_factory = MagicMock()

    async def fake_execute(run_id, input_artifacts):
        return []

    mock_agent = MagicMock()
    mock_agent.execute = fake_execute
    agent_factory.create.side_effect = lambda process: (
        dispatched_ids.append(process.process_id) or mock_agent
    )

    orch, _, state_store = make_orchestrator(tmp_path, agent_factory)
    run_id = "run-resume-crash"

    run = ProjectRun(id=run_id, business_case_id="bc-1")
    await state_store.save_run(run, "sess-1")

    # Initialize all processes as NOT_STARTED
    for p in PMBOK_PROCESSES:
        await state_store.set_status(run_id, p.process_id, ProcessStatus.NOT_STARTED)

    # Simulate crash: mark 5 processes as COMPLETE (the first 5 in topological order)
    # 4.1 and 13.1 have no prerequisites; 4.2, 5.1, 13.2 depend only on those
    completed_before_crash = ["4.1", "13.1", "4.2", "5.1", "13.2"]
    for pid in completed_before_crash:
        await state_store.set_status(run_id, pid, ProcessStatus.COMPLETE)

    # Call resume — simulating restart after crash
    result = await orch.resume(run_id)

    assert isinstance(result, ProjectRun)
    assert result.id == run_id

    # None of the 5 completed processes should have been re-dispatched
    for pid in completed_before_crash:
        assert pid not in dispatched_ids, (
            f"Process {pid} was COMPLETE before crash but was re-dispatched on resume"
        )
