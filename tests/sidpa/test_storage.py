"""Tests for ArtifactStore, StateStore, and IndexStore."""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus
from pmbok.models.pmbok import ProcessState, ProjectArtifact, ProjectRun
from pmbok.storage.artifact_store import ArtifactStore
from pmbok.storage.index import IndexStore
from pmbok.storage.state_store import StateStore


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(base_path=tmp_path)


@pytest.fixture
def state_store(tmp_path: Path) -> StateStore:
    return StateStore(db_path=str(tmp_path / "state.db"))


@pytest.fixture
def index_store(tmp_path: Path) -> IndexStore:
    return IndexStore(base_path=tmp_path)


def make_artifact(
    run_id: str = "run-001",
    process_id: str = "4.1",
    artifact_type: str = "Project Charter",
    version: int = 1,
    previous_version_id: str | None = None,
) -> ProjectArtifact:
    return ProjectArtifact(
        run_id=run_id,
        process_id=process_id,
        artifact_type=artifact_type,
        version=version,
        content={"title": "Test Project", "version": version},
        produced_by=process_id,
        created_at=datetime(2025, 1, 15, 11, 0, 0),
        previous_version_id=previous_version_id,
    )


def make_run(run_id: str = "run-001") -> ProjectRun:
    return ProjectRun(
        id=run_id,
        business_case_id="bc-001",
        current_process_group=ProcessGroup.INITIATING,
        gate_status={},
        created_at=datetime(2025, 1, 15, 10, 0, 0),
    )


# ── ArtifactStore tests ───────────────────────────────────────────────────────


def test_save_creates_versioned_file(tmp_store: ArtifactStore, tmp_path: Path) -> None:
    artifact = make_artifact()
    asyncio.run(tmp_store.save(artifact))

    versioned = (
        tmp_path
        / "runs"
        / "run-001"
        / "artifacts"
        / "4.1"
        / f"v1_{artifact.id}.json"
    )
    assert versioned.exists()


def test_save_creates_latest_json(tmp_store: ArtifactStore, tmp_path: Path) -> None:
    artifact = make_artifact()
    asyncio.run(tmp_store.save(artifact))

    latest = tmp_path / "runs" / "run-001" / "artifacts" / "4.1" / "latest.json"
    assert latest.exists()


def test_get_latest_returns_artifact(tmp_store: ArtifactStore) -> None:
    artifact = make_artifact()
    asyncio.run(tmp_store.save(artifact))

    result = asyncio.run(tmp_store.get_latest("run-001", "4.1", "Project Charter"))
    assert result.id == artifact.id
    assert result.version == 1
    assert result.artifact_type == "Project Charter"


def test_get_latest_returns_highest_version(tmp_store: ArtifactStore) -> None:
    a1 = make_artifact(version=1)
    a2 = make_artifact(version=2, previous_version_id=a1.id)
    asyncio.run(tmp_store.save(a1))
    asyncio.run(tmp_store.save(a2))

    result = asyncio.run(tmp_store.get_latest("run-001", "4.1", "Project Charter"))
    assert result.version == 2


def test_get_version_retrieves_specific_version(tmp_store: ArtifactStore) -> None:
    a1 = make_artifact(version=1)
    a2 = make_artifact(version=2, previous_version_id=a1.id)
    asyncio.run(tmp_store.save(a1))
    asyncio.run(tmp_store.save(a2))

    result = asyncio.run(tmp_store.get_version(a1.id, 1))
    assert result.version == 1
    assert result.id == a1.id


def test_get_version_not_found_raises(tmp_store: ArtifactStore) -> None:
    with pytest.raises(FileNotFoundError):
        asyncio.run(tmp_store.get_version("nonexistent-id", 1))


def test_list_artifacts_all(tmp_store: ArtifactStore) -> None:
    a1 = make_artifact(process_id="4.1", version=1)
    a2 = make_artifact(process_id="13.1", version=1)
    asyncio.run(tmp_store.save(a1))
    asyncio.run(tmp_store.save(a2))

    results = asyncio.run(tmp_store.list_artifacts("run-001"))
    assert len(results) == 2


def test_list_artifacts_filtered_by_process(tmp_store: ArtifactStore) -> None:
    a1 = make_artifact(process_id="4.1", version=1)
    a2 = make_artifact(process_id="13.1", version=1)
    asyncio.run(tmp_store.save(a1))
    asyncio.run(tmp_store.save(a2))

    results = asyncio.run(tmp_store.list_artifacts("run-001", process_id="4.1"))
    assert len(results) == 1
    assert results[0].process_id == "4.1"


def test_list_artifacts_empty_run(tmp_store: ArtifactStore) -> None:
    results = asyncio.run(tmp_store.list_artifacts("nonexistent-run"))
    assert results == []


def test_artifact_round_trip_content(tmp_store: ArtifactStore) -> None:
    artifact = make_artifact()
    asyncio.run(tmp_store.save(artifact))
    result = asyncio.run(tmp_store.get_latest("run-001", "4.1", "Project Charter"))
    assert result.content == artifact.content
    assert result.produced_by == artifact.produced_by
    assert result.previous_version_id == artifact.previous_version_id


# ── StateStore tests ──────────────────────────────────────────────────────────


def test_save_and_load_run(state_store: StateStore) -> None:
    run = make_run()
    asyncio.run(state_store.save_run(run, session_id="sess-001"))

    loaded = asyncio.run(state_store.load_run("run-001"))
    assert loaded.id == run.id
    assert loaded.business_case_id == run.business_case_id
    assert loaded.current_process_group == ProcessGroup.INITIATING


def test_load_run_not_found_raises(state_store: StateStore) -> None:
    with pytest.raises(KeyError):
        asyncio.run(state_store.load_run("nonexistent"))


def test_save_run_updates_existing(state_store: StateStore) -> None:
    run = make_run()
    asyncio.run(state_store.save_run(run, session_id="sess-001"))

    run.current_process_group = ProcessGroup.PLANNING
    asyncio.run(state_store.save_run(run, session_id="sess-001"))

    loaded = asyncio.run(state_store.load_run("run-001"))
    assert loaded.current_process_group == ProcessGroup.PLANNING


def test_set_and_get_status(state_store: StateStore) -> None:
    asyncio.run(
        state_store.set_status("run-001", "4.1", ProcessStatus.IN_PROGRESS)
    )
    status = asyncio.run(state_store.get_status("run-001", "4.1"))
    assert status == ProcessStatus.IN_PROGRESS


def test_get_status_default_not_started(state_store: StateStore) -> None:
    status = asyncio.run(state_store.get_status("run-001", "4.1"))
    assert status == ProcessStatus.NOT_STARTED


def test_append_error_accumulates(state_store: StateStore) -> None:
    asyncio.run(state_store.append_error("run-001", "4.1", "Error A"))
    asyncio.run(state_store.append_error("run-001", "4.1", "Error B"))

    states = asyncio.run(state_store.load_all_process_states("run-001"))
    assert len(states) == 1
    assert "Error A" in states[0].error_log
    assert "Error B" in states[0].error_log


def test_load_all_process_states(state_store: StateStore) -> None:
    asyncio.run(state_store.set_status("run-001", "4.1", ProcessStatus.COMPLETE))
    asyncio.run(state_store.set_status("run-001", "13.1", ProcessStatus.IN_PROGRESS))

    states = asyncio.run(state_store.load_all_process_states("run-001"))
    assert len(states) == 2
    status_map = {s.process_id: s.status for s in states}
    assert status_map["4.1"] == ProcessStatus.COMPLETE
    assert status_map["13.1"] == ProcessStatus.IN_PROGRESS


def test_load_all_process_states_empty(state_store: StateStore) -> None:
    states = asyncio.run(state_store.load_all_process_states("nonexistent"))
    assert states == []


def test_save_and_load_gate(state_store: StateStore) -> None:
    decided = datetime(2025, 1, 15, 12, 0, 0)
    asyncio.run(
        state_store.save_gate(
            "run-001",
            "GATE_1_IDEATION",
            ApprovalStatus.APPROVED,
            decided_at=decided,
            revision_instructions=None,
        )
    )

    gate = asyncio.run(state_store.load_gate("run-001", "GATE_1_IDEATION"))
    assert gate is not None
    assert gate["status"] == ApprovalStatus.APPROVED
    assert gate["decided_at"] == decided


def test_load_gate_not_found_returns_none(state_store: StateStore) -> None:
    result = asyncio.run(state_store.load_gate("run-001", "GATE_MISSING"))
    assert result is None


def test_save_gate_updates_existing(state_store: StateStore) -> None:
    asyncio.run(
        state_store.save_gate("run-001", "GATE_1", ApprovalStatus.PENDING)
    )
    asyncio.run(
        state_store.save_gate(
            "run-001",
            "GATE_1",
            ApprovalStatus.REJECTED,
            revision_instructions="Please revise section 2",
        )
    )

    gate = asyncio.run(state_store.load_gate("run-001", "GATE_1"))
    assert gate is not None
    assert gate["status"] == ApprovalStatus.REJECTED
    assert gate["revision_instructions"] == "Please revise section 2"


def test_gate_status_round_trip_with_run(state_store: StateStore) -> None:
    run = make_run()
    run.gate_status = {ProcessGroup.INITIATING: ApprovalStatus.APPROVED}
    asyncio.run(state_store.save_run(run, session_id="sess-001"))

    loaded = asyncio.run(state_store.load_run("run-001"))
    assert loaded.gate_status[ProcessGroup.INITIATING] == ApprovalStatus.APPROVED


# ── IndexStore tests ──────────────────────────────────────────────────────────


def test_register_and_lookup(index_store: IndexStore) -> None:
    asyncio.run(index_store.register("run-001", "sess-001"))
    result = asyncio.run(index_store.lookup("run-001"))
    assert result == "sess-001"


def test_lookup_missing_returns_none(index_store: IndexStore) -> None:
    result = asyncio.run(index_store.lookup("nonexistent"))
    assert result is None


def test_register_overwrites(index_store: IndexStore) -> None:
    asyncio.run(index_store.register("run-001", "sess-001"))
    asyncio.run(index_store.register("run-001", "sess-002"))
    result = asyncio.run(index_store.lookup("run-001"))
    assert result == "sess-002"


def test_register_multiple_runs(index_store: IndexStore) -> None:
    asyncio.run(index_store.register("run-001", "sess-A"))
    asyncio.run(index_store.register("run-002", "sess-B"))
    assert asyncio.run(index_store.lookup("run-001")) == "sess-A"
    assert asyncio.run(index_store.lookup("run-002")) == "sess-B"


def test_index_file_created(index_store: IndexStore, tmp_path: Path) -> None:
    asyncio.run(index_store.register("run-001", "sess-001"))
    assert (tmp_path / "index.json").exists()
