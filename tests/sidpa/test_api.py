"""Tests for the FastAPI REST API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from pmbok.api.app import app, _sessions, get_state_store, get_artifact_store


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear in-memory sessions between tests."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ── Session endpoints ─────────────────────────────────────────────────────────

def test_create_session(client):
    resp = client.post("/sessions")
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


def test_add_text_input(client):
    # Create session
    session_id = client.post("/sessions").json()["session_id"]

    # Add text input via form fields
    resp = client.post(
        f"/sessions/{session_id}/inputs",
        data={"text": "Build a smart irrigation system.", "filename": "idea.txt"},
    )
    assert resp.status_code == 201
    assert "raw_input_id" in resp.json()


def test_add_file_input(client):
    session_id = client.post("/sessions").json()["session_id"]

    resp = client.post(
        f"/sessions/{session_id}/inputs",
        files={"file": ("notes.txt", b"Some project notes", "text/plain")},
    )
    assert resp.status_code == 201
    assert "raw_input_id" in resp.json()


def test_add_input_unknown_session(client):
    resp = client.post(
        "/sessions/nonexistent/inputs",
        data={"text": "hello"},
    )
    assert resp.status_code == 404


def test_add_input_no_content(client):
    session_id = client.post("/sessions").json()["session_id"]
    resp = client.post(f"/sessions/{session_id}/inputs")
    assert resp.status_code == 422


def test_process_session(client):
    session_id = client.post("/sessions").json()["session_id"]
    client.post(
        f"/sessions/{session_id}/inputs",
        data={"text": "Build a smart irrigation system to save water.", "filename": "idea.txt"},
    )

    resp = client.post(f"/sessions/{session_id}/process")
    assert resp.status_code == 200
    data = resp.json()
    # IdeationSummary fields
    assert "session_id" in data
    assert "title" in data
    assert "key_goals" in data


def test_process_empty_session(client):
    session_id = client.post("/sessions").json()["session_id"]
    resp = client.post(f"/sessions/{session_id}/process")
    assert resp.status_code == 422


def test_process_unknown_session(client):
    resp = client.post("/sessions/nonexistent/process")
    assert resp.status_code == 404


# ── Gate endpoints ────────────────────────────────────────────────────────────

@pytest.fixture
def isolated_stores(tmp_path):
    """Override FastAPI dependencies to use tmp_path-backed stores."""
    from pmbok.storage.artifact_store import ArtifactStore
    from pmbok.storage.state_store import StateStore

    db_path = str(tmp_path / "state.db")
    state_store = StateStore(db_path)
    artifact_store = ArtifactStore(tmp_path)

    app.dependency_overrides[get_state_store] = lambda: state_store
    app.dependency_overrides[get_artifact_store] = lambda: artifact_store
    yield state_store, artifact_store
    app.dependency_overrides.clear()


def test_approve_gate(client, isolated_stores):
    """Approve gate should persist and return 200."""
    resp = client.post("/gates/run-001/GATE_1_IDEATION/approve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"
    assert data["run_id"] == "run-001"
    assert data["gate_name"] == "GATE_1_IDEATION"


def test_reject_gate(client, isolated_stores):
    """Reject gate should persist and return 200."""
    resp = client.post(
        "/gates/run-001/GATE_1_IDEATION/reject",
        json={"revision_instructions": "Please add more detail."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"


# ── Run endpoints ─────────────────────────────────────────────────────────────

def test_get_run_status_not_found(client, isolated_stores):
    """Status endpoint returns a ProcessMap (with all NOT_STARTED) even for unknown runs."""
    resp = client.get("/runs/nonexistent-run/status")
    # The orchestrator returns a valid ProcessMap for any run_id (processes default to NOT_STARTED)
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == "nonexistent-run"
    assert "processes" in data


def test_get_artifact_not_found(client, isolated_stores):
    resp = client.get("/runs/nonexistent-run/artifacts/4.1")
    assert resp.status_code == 404


def test_get_report(client, isolated_stores):
    """Report endpoint should return a ProgressReport even for a run with no states."""
    resp = client.get("/runs/any-run-id/report")
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert "by_knowledge_area" in data
    assert "total" in data


# ── OpenAPI docs ──────────────────────────────────────────────────────────────

def test_openapi_docs_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "PMBOK Idea-to-Reality API"
