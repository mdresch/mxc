"""FastAPI REST API exposing all PMBOK system capabilities."""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from pmbok.config import settings
from pmbok.engines.ideation_engine import IdeationEngine
from pmbok.exceptions import InputValidationError, PMBOKError
from pmbok.models.approval import ApprovalDecision
from pmbok.models.enums import ApprovalStatus, InputSourceType
from pmbok.models.ideation import IdeationSummary
from pmbok.models.inputs import RawInput
from pmbok.models.pmbok import ProcessMap, ProjectArtifact
from pmbok.models.reporting import ProgressReport
from pmbok.orchestrator.approval_gate import ApprovalGate
from pmbok.orchestrator.progress_tracker import ProgressTracker
from pmbok.orchestrator.orchestrator import PMBOKOrchestrator
from pmbok.processors.input_processor import InputProcessor
from pmbok.storage.artifact_store import ArtifactStore
from pmbok.storage.state_store import StateStore

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="PMBOK Idea-to-Reality API",
    description="REST API for the AI-powered PMBOK project management system.",
    version="0.1.0",
)

# ── In-memory session store: session_id → list[RawInput] ─────────────────────

_sessions: dict[str, list[RawInput]] = {}

# ── Shared resource singletons ────────────────────────────────────────────────

_state_store: StateStore | None = None
_artifact_store: ArtifactStore | None = None


def get_state_store() -> StateStore:
    global _state_store
    if _state_store is None:
        db_path = str(settings.STORAGE_PATH / "state.db")
        settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        _state_store = StateStore(db_path)
    return _state_store


def get_artifact_store() -> ArtifactStore:
    global _artifact_store
    if _artifact_store is None:
        _artifact_store = ArtifactStore(settings.STORAGE_PATH)
    return _artifact_store


# ── Request / Response models ─────────────────────────────────────────────────

class TextInputBody(BaseModel):
    text: str
    filename: str = "note.txt"


class RejectBody(BaseModel):
    revision_instructions: str


# ── Error handler helper ──────────────────────────────────────────────────────

def _pmbok_error_to_http(exc: PMBOKError) -> HTTPException:
    if isinstance(exc, InputValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


# ── Session endpoints ─────────────────────────────────────────────────────────

@app.post("/sessions", status_code=201)
async def create_session() -> dict[str, str]:
    """Create a new input session and return its ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = []
    return {"session_id": session_id}


@app.post("/sessions/{session_id}/inputs", status_code=201)
async def add_input(
    session_id: str,
    file: Annotated[Optional[UploadFile], File()] = None,
    text: Annotated[Optional[str], Form()] = None,
    filename: Annotated[Optional[str], Form()] = None,
) -> dict[str, str]:
    """
    Add a raw input to a session.

    Accepts either:
    - Multipart file upload (file field)
    - Form fields: text + optional filename
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    if file is not None:
        data = await file.read()
        fname = file.filename or "upload"
        content_type = file.content_type or "text/plain"
        source_type = _mime_to_source_type(content_type)
        raw = RawInput(
            source_type=source_type,
            filename=fname,
            data=data,
            size_bytes=len(data),
        )
    elif text is not None:
        fname = filename or "note.txt"
        data = text.encode("utf-8")
        raw = RawInput(
            source_type=InputSourceType.TEXT,
            filename=fname,
            data=data,
            size_bytes=len(data),
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either a file upload or a text field.",
        )

    _sessions[session_id].append(raw)
    return {"raw_input_id": raw.id}


@app.post("/sessions/{session_id}/process")
async def process_session(session_id: str) -> IdeationSummary:
    """Process all inputs in a session and return an IdeationSummary."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    inputs = _sessions[session_id]
    if not inputs:
        raise HTTPException(status_code=422, detail="Session has no inputs to process.")

    processor = InputProcessor()
    engine = IdeationEngine()

    try:
        batch_result = await processor.process_batch(inputs)
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc

    if not batch_result.successful:
        raise HTTPException(
            status_code=422,
            detail="All inputs failed to process.",
        )

    try:
        summary = await engine.generate_summary(
            batch_result.successful, session_id=session_id
        )
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc

    return summary


# ── Gate endpoints ────────────────────────────────────────────────────────────

@app.post("/gates/{run_id}/{gate_name}/approve", status_code=200)
async def approve_gate(
    run_id: str,
    gate_name: str,
    state_store: Annotated[StateStore, Depends(get_state_store)],
) -> dict[str, str]:
    """Approve a gate, allowing the workflow to advance."""
    decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
    gate = ApprovalGate(state_store=state_store, run_id=run_id)
    try:
        await gate.present(
            artifact=gate_name,
            rendered_markdown="",
            gate_name=gate_name,
            decision_override=decision,
        )
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc
    return {"status": "approved", "run_id": run_id, "gate_name": gate_name}


@app.post("/gates/{run_id}/{gate_name}/reject", status_code=200)
async def reject_gate(
    run_id: str,
    gate_name: str,
    body: RejectBody,
    state_store: Annotated[StateStore, Depends(get_state_store)],
) -> dict[str, str]:
    """Reject a gate with revision instructions."""
    decision = ApprovalDecision(
        status=ApprovalStatus.REJECTED,
        revision_instructions=body.revision_instructions,
    )
    gate = ApprovalGate(state_store=state_store, run_id=run_id)
    try:
        await gate.present(
            artifact=gate_name,
            rendered_markdown="",
            gate_name=gate_name,
            decision_override=decision,
        )
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc
    return {"status": "rejected", "run_id": run_id, "gate_name": gate_name}


# ── Run endpoints ─────────────────────────────────────────────────────────────

@app.get("/runs/{run_id}/status")
async def get_run_status(
    run_id: str,
    state_store: Annotated[StateStore, Depends(get_state_store)],
    artifact_store: Annotated[ArtifactStore, Depends(get_artifact_store)],
) -> ProcessMap:
    """Return the current ProcessMap for a run."""
    try:
        # We need a minimal orchestrator just to call get_process_map
        orchestrator = PMBOKOrchestrator(
            agent_factory=None,  # type: ignore[arg-type]
            artifact_store=artifact_store,
            state_store=state_store,
        )
        return await orchestrator.get_process_map(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc


@app.get("/runs/{run_id}/artifacts/{process_id}")
async def get_artifact(
    run_id: str,
    process_id: str,
    artifact_store: Annotated[ArtifactStore, Depends(get_artifact_store)],
    version: Annotated[Optional[int], Query()] = None,
) -> ProjectArtifact:
    """Return the latest artifact for a process, or a specific version if ?version=N."""
    try:
        if version is not None:
            # Scan for the artifact by run_id + process_id + version
            artifacts = await artifact_store.list_artifacts(run_id, process_id)
            matching = [a for a in artifacts if a.version == version]
            if not matching:
                raise FileNotFoundError(
                    f"No artifact at version {version} for run={run_id} process={process_id}"
                )
            return matching[0]
        else:
            # Return latest — list all and pick highest version
            artifacts = await artifact_store.list_artifacts(run_id, process_id)
            if not artifacts:
                raise FileNotFoundError(
                    f"No artifacts found for run={run_id} process={process_id}"
                )
            return max(artifacts, key=lambda a: a.version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc


@app.get("/runs/{run_id}/report")
async def get_report(
    run_id: str,
    state_store: Annotated[StateStore, Depends(get_state_store)],
) -> ProgressReport:
    """Return the ProgressReport for a run."""
    try:
        tracker = ProgressTracker(state_store)
        return await tracker.generate_report(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    except PMBOKError as exc:
        raise _pmbok_error_to_http(exc) from exc


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mime_to_source_type(content_type: str) -> InputSourceType:
    """Map a MIME type to InputSourceType; default to TEXT for unknown types."""
    mapping = {
        "image/png": InputSourceType.IMAGE,
        "image/jpeg": InputSourceType.IMAGE,
        "image/jpg": InputSourceType.IMAGE,
        "application/pdf": InputSourceType.PDF,
        "text/plain": InputSourceType.TEXT,
        "text/markdown": InputSourceType.MARKDOWN,
    }
    return mapping.get(content_type, InputSourceType.TEXT)
