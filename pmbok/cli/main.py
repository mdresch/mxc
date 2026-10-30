"""Typer-based CLI for the PMBOK system."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from pmbok.config import settings
from pmbok.exceptions import PMBOKError
from pmbok.models.approval import ApprovalDecision
from pmbok.models.enums import ApprovalStatus, InputSourceType
from pmbok.models.inputs import RawInput
from pmbok.output.pretty_printer import PrettyPrinter

app = typer.Typer(help="PMBOK Idea-to-Reality CLI")
_printer = PrettyPrinter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ext_to_source_type(path: Path) -> InputSourceType:
    """Determine InputSourceType from file extension."""
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg"):
        return InputSourceType.IMAGE
    if suffix == ".pdf":
        return InputSourceType.PDF
    if suffix == ".md":
        return InputSourceType.MARKDOWN
    return InputSourceType.TEXT


def _make_state_store() -> "StateStore":  # noqa: F821
    from pmbok.storage.state_store import StateStore

    db_path = settings.STORAGE_PATH / "state.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return StateStore(str(db_path))


def _make_artifact_store() -> "ArtifactStore":  # noqa: F821
    from pmbok.storage.artifact_store import ArtifactStore

    return ArtifactStore(settings.STORAGE_PATH)


def _make_llm_client(system_message: str = "You are a helpful project management assistant.") -> Optional["AgentClient"]:  # noqa: F821
    """Create a real LLM client if USE_REAL_LLM is set, otherwise return None."""
    import os
    import sys
    use_real = "--real" in sys.argv or os.getenv("USE_REAL_LLM", "").lower() in ("1", "true", "yes")
    if not use_real:
        return None
    from pmbok.llm import create_llm_client
    return create_llm_client(system_message=system_message)


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def submit(
    files: list[Path] = typer.Argument(..., help="One or more input files to submit"),
    session_id: Optional[str] = typer.Option(None, "--session-id", help="Optional session ID"),
) -> None:
    """Submit input files and generate an ideation summary."""
    from pmbok.engines.ideation_engine import IdeationEngine
    from pmbok.processors.input_processor import InputProcessor

    async def _run() -> None:
        raw_inputs: list[RawInput] = []
        for file_path in files:
            if not file_path.exists():
                typer.echo(f"Error: file not found: {file_path}", err=True)
                raise typer.Exit(code=1)
            data = file_path.read_bytes()
            raw_inputs.append(
                RawInput(
                    source_type=_ext_to_source_type(file_path),
                    filename=file_path.name,
                    data=data,
                    size_bytes=len(data),
                )
            )

        processor = InputProcessor()
        batch_result = await processor.process_batch(raw_inputs)

        if batch_result.failed:
            for failed in batch_result.failed:
                typer.echo(f"Warning: failed to process '{failed.filename}': {failed.reason}", err=True)

        if not batch_result.successful:
            typer.echo("Error: no inputs were successfully processed.", err=True)
            raise typer.Exit(code=1)

        llm_client = _make_llm_client(
            "You are a project ideation assistant. "
            "Always respond with a single valid JSON object matching the requested schema. "
            "No markdown fences, no extra text."
        )
        engine = IdeationEngine(llm_client=llm_client)
        summary = await engine.generate_summary(
            batch_result.successful,
            session_id=session_id or batch_result.session_id,
        )

        typer.echo(_printer.render_ideation_summary(summary))

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def approve(
    gate: str = typer.Argument(..., help="Gate name, e.g. GATE_1_IDEATION"),
    run_id: str = typer.Option(..., "--run-id", help="Run ID to update"),
) -> None:
    """Approve a gate for the given run."""
    from pmbok.orchestrator.approval_gate import ApprovalGate

    async def _run() -> None:
        state_store = _make_state_store()
        gate_obj = ApprovalGate(state_store=state_store, run_id=run_id)
        decision = ApprovalDecision(status=ApprovalStatus.APPROVED)
        await gate_obj.present(
            artifact=gate,
            rendered_markdown="",
            gate_name=gate,
            decision_override=decision,
        )
        typer.echo(f"Gate '{gate}' approved for run '{run_id}'.")

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def reject(
    gate: str = typer.Argument(..., help="Gate name, e.g. GATE_1_IDEATION"),
    run_id: str = typer.Option(..., "--run-id", help="Run ID to update"),
    instructions: str = typer.Option(..., "--instructions", help="Revision instructions"),
) -> None:
    """Reject a gate with revision instructions."""
    from pmbok.orchestrator.approval_gate import ApprovalGate

    async def _run() -> None:
        state_store = _make_state_store()
        gate_obj = ApprovalGate(state_store=state_store, run_id=run_id)
        decision = ApprovalDecision(
            status=ApprovalStatus.REJECTED,
            revision_instructions=instructions,
        )
        await gate_obj.present(
            artifact=gate,
            rendered_markdown="",
            gate_name=gate,
            decision_override=decision,
        )
        typer.echo(f"Gate '{gate}' rejected for run '{run_id}'.")

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def status(
    run_id: str = typer.Argument(..., help="Run ID to inspect"),
) -> None:
    """Print the process map for a run."""
    from pmbok.agents.factory import ProcessAgentFactory
    from pmbok.orchestrator.orchestrator import PMBOKOrchestrator

    async def _run() -> None:
        state_store = _make_state_store()
        artifact_store = _make_artifact_store()
        factory = ProcessAgentFactory()
        orchestrator = PMBOKOrchestrator(
            agent_factory=factory,
            artifact_store=artifact_store,
            state_store=state_store,
        )
        process_map = await orchestrator.get_process_map(run_id)
        typer.echo(_printer.render_process_map(process_map))

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def artifact(
    run_id: str = typer.Argument(..., help="Run ID"),
    process_id: str = typer.Argument(..., help="Process ID, e.g. 4.1"),
    version: Optional[int] = typer.Option(None, "--version", "-v", help="Artifact version"),
) -> None:
    """Retrieve and render a project artifact."""
    async def _run() -> None:
        artifact_store = _make_artifact_store()
        if version is not None:
            # get_version scans by artifact_id; here we use process_id as artifact_id
            # per the task spec: get_version(artifact_id, version)
            # We need to find the artifact_id first via list_artifacts
            artifacts = await artifact_store.list_artifacts(run_id, process_id)
            matching = [a for a in artifacts if a.version == version]
            if not matching:
                typer.echo(
                    f"Error: no artifact version {version} found for process '{process_id}' in run '{run_id}'.",
                    err=True,
                )
                raise typer.Exit(code=1)
            art = matching[0]
        else:
            # get_latest requires artifact_type; scan all artifacts for the process
            artifacts = await artifact_store.list_artifacts(run_id, process_id)
            if not artifacts:
                typer.echo(
                    f"Error: no artifacts found for process '{process_id}' in run '{run_id}'.",
                    err=True,
                )
                raise typer.Exit(code=1)
            art = max(artifacts, key=lambda a: a.version)

        typer.echo(_printer.render_project_artifact(art))

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def report(
    run_id: str = typer.Argument(..., help="Run ID"),
) -> None:
    """Print the progress report for a run."""
    from pmbok.orchestrator.progress_tracker import ProgressTracker

    async def _run() -> None:
        state_store = _make_state_store()
        tracker = ProgressTracker(state_store=state_store)
        progress_report = await tracker.generate_report(run_id)
        typer.echo(_printer.render_progress_report(progress_report))

    try:
        asyncio.run(_run())
    except PMBOKError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1)
    except Exception as exc:
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=1)

if __name__ == '__main__':
    app()
