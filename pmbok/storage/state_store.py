"""SQLite-backed StateStore implementation via SQLAlchemy Core."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import create_engine, text

from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus
from pmbok.models.pmbok import ProcessState, ProjectRun


# ── Table definitions ─────────────────────────────────────────────────────────

metadata = sa.MetaData()

project_runs_table = sa.Table(
    "project_runs",
    metadata,
    sa.Column("run_id", sa.Text, primary_key=True),
    sa.Column("session_id", sa.Text, nullable=False),
    sa.Column("business_case_id", sa.Text, nullable=False),
    sa.Column("current_group", sa.Text, nullable=False),
    sa.Column("gate_status", sa.Text, nullable=False),  # JSON dict
    sa.Column("created_at", sa.Text, nullable=False),
    sa.Column("completed_at", sa.Text, nullable=True),
)

process_states_table = sa.Table(
    "process_states",
    metadata,
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("process_id", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("started_at", sa.Text, nullable=True),
    sa.Column("completed_at", sa.Text, nullable=True),
    sa.Column("attempt_count", sa.Integer, default=0),
    sa.Column("error_log", sa.Text, nullable=True),  # JSON array
    sa.Column("output_artifact_ids", sa.Text, nullable=True),  # JSON array
    sa.PrimaryKeyConstraint("run_id", "process_id"),
)

approval_gates_table = sa.Table(
    "approval_gates",
    metadata,
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("gate_name", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("decided_at", sa.Text, nullable=True),
    sa.Column("revision_instructions", sa.Text, nullable=True),
    sa.PrimaryKeyConstraint("run_id", "gate_name"),
)


# ── StateStore ────────────────────────────────────────────────────────────────

class StateStore:
    """
    SQLite-backed store for ProjectRun, ProcessState, and ApprovalGate records.

    All writes use WAL mode for atomic, concurrent-safe operations.
    Async methods delegate to synchronous helpers via asyncio.to_thread.
    """

    def __init__(self, db_path: str) -> None:
        from pathlib import Path as _P
        _p = _P(db_path).resolve()
        _p.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{_p.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        self._create_tables()

    def _create_tables(self) -> None:
        metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_process_states_run "
                    "ON process_states(run_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_process_states_status "
                    "ON process_states(status)"
                )
            )
            conn.commit()

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _dt_str(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt is not None else None

    @staticmethod
    def _parse_dt(s: str | None) -> datetime | None:
        return datetime.fromisoformat(s) if s else None

    @staticmethod
    def _gate_status_to_json(gate_status: dict[ProcessGroup, ApprovalStatus]) -> str:
        return json.dumps({k.value: v.value for k, v in gate_status.items()})

    @staticmethod
    def _gate_status_from_json(s: str) -> dict[ProcessGroup, ApprovalStatus]:
        raw: dict[str, str] = json.loads(s)
        return {ProcessGroup(k): ApprovalStatus(v) for k, v in raw.items()}

    # ── ProjectRun ────────────────────────────────────────────────────────────

    async def save_run(self, run: ProjectRun, session_id: str) -> None:
        await asyncio.to_thread(self._save_run_sync, run, session_id)

    def _save_run_sync(self, run: ProjectRun, session_id: str) -> None:
        row: dict[str, Any] = {
            "run_id": run.id,
            "session_id": session_id,
            "business_case_id": run.business_case_id,
            "current_group": run.current_process_group.value,
            "gate_status": self._gate_status_to_json(run.gate_status),
            "created_at": self._dt_str(run.created_at),
            "completed_at": self._dt_str(run.completed_at),
        }
        with self.engine.begin() as conn:
            existing = conn.execute(
                sa.select(project_runs_table).where(
                    project_runs_table.c.run_id == run.id
                )
            ).fetchone()
            if existing:
                conn.execute(
                    project_runs_table.update()
                    .where(project_runs_table.c.run_id == run.id)
                    .values(**{k: v for k, v in row.items() if k != "run_id"})
                )
            else:
                conn.execute(project_runs_table.insert().values(**row))

    async def load_run(self, run_id: str) -> ProjectRun:
        return await asyncio.to_thread(self._load_run_sync, run_id)

    def _load_run_sync(self, run_id: str) -> ProjectRun:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(project_runs_table).where(
                    project_runs_table.c.run_id == run_id
                )
            ).fetchone()
        if row is None:
            raise KeyError(f"ProjectRun not found: {run_id}")
        return ProjectRun(
            id=row.run_id,
            business_case_id=row.business_case_id,
            current_process_group=ProcessGroup(row.current_group),
            gate_status=self._gate_status_from_json(row.gate_status),
            created_at=self._parse_dt(row.created_at),
            completed_at=self._parse_dt(row.completed_at),
        )

    # ── ProcessState ──────────────────────────────────────────────────────────

    async def set_status(
        self, run_id: str, process_id: str, status: ProcessStatus
    ) -> None:
        await asyncio.to_thread(self._set_status_sync, run_id, process_id, status)

    def _set_status_sync(
        self, run_id: str, process_id: str, status: ProcessStatus
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self.engine.begin() as conn:
            existing = conn.execute(
                sa.select(process_states_table).where(
                    (process_states_table.c.run_id == run_id)
                    & (process_states_table.c.process_id == process_id)
                )
            ).fetchone()
            if existing:
                updates: dict[str, Any] = {"status": status.value}
                if status == ProcessStatus.IN_PROGRESS and existing.started_at is None:
                    updates["started_at"] = now
                if status in (ProcessStatus.COMPLETE, ProcessStatus.BLOCKED):
                    updates["completed_at"] = now
                conn.execute(
                    process_states_table.update()
                    .where(
                        (process_states_table.c.run_id == run_id)
                        & (process_states_table.c.process_id == process_id)
                    )
                    .values(**updates)
                )
            else:
                row: dict[str, Any] = {
                    "run_id": run_id,
                    "process_id": process_id,
                    "status": status.value,
                    "started_at": now if status == ProcessStatus.IN_PROGRESS else None,
                    "completed_at": now
                    if status in (ProcessStatus.COMPLETE, ProcessStatus.BLOCKED)
                    else None,
                    "attempt_count": 0,
                    "error_log": json.dumps([]),
                    "output_artifact_ids": json.dumps([]),
                }
                conn.execute(process_states_table.insert().values(**row))

    async def get_status(self, run_id: str, process_id: str) -> ProcessStatus:
        return await asyncio.to_thread(self._get_status_sync, run_id, process_id)

    def _get_status_sync(self, run_id: str, process_id: str) -> ProcessStatus:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(process_states_table.c.status).where(
                    (process_states_table.c.run_id == run_id)
                    & (process_states_table.c.process_id == process_id)
                )
            ).fetchone()
        if row is None:
            return ProcessStatus.NOT_STARTED
        return ProcessStatus(row.status)

    async def append_error(
        self, run_id: str, process_id: str, error_msg: str
    ) -> None:
        await asyncio.to_thread(self._append_error_sync, run_id, process_id, error_msg)

    def _append_error_sync(
        self, run_id: str, process_id: str, error_msg: str
    ) -> None:
        with self.engine.begin() as conn:
            row = conn.execute(
                sa.select(process_states_table).where(
                    (process_states_table.c.run_id == run_id)
                    & (process_states_table.c.process_id == process_id)
                )
            ).fetchone()
            if row is None:
                errors: list[str] = [error_msg]
                conn.execute(
                    process_states_table.insert().values(
                        run_id=run_id,
                        process_id=process_id,
                        status=ProcessStatus.NOT_STARTED.value,
                        attempt_count=0,
                        error_log=json.dumps(errors),
                        output_artifact_ids=json.dumps([]),
                    )
                )
            else:
                errors = json.loads(row.error_log or "[]")
                errors.append(error_msg)
                conn.execute(
                    process_states_table.update()
                    .where(
                        (process_states_table.c.run_id == run_id)
                        & (process_states_table.c.process_id == process_id)
                    )
                    .values(
                        error_log=json.dumps(errors),
                        attempt_count=(row.attempt_count or 0) + 1,
                    )
                )

    async def load_all_process_states(self, run_id: str) -> list[ProcessState]:
        return await asyncio.to_thread(self._load_all_process_states_sync, run_id)

    def _load_all_process_states_sync(self, run_id: str) -> list[ProcessState]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                sa.select(process_states_table).where(
                    process_states_table.c.run_id == run_id
                )
            ).fetchall()
        return [
            ProcessState(
                process_id=row.process_id,
                run_id=row.run_id,
                status=ProcessStatus(row.status),
                started_at=self._parse_dt(row.started_at),
                completed_at=self._parse_dt(row.completed_at),
                attempt_count=row.attempt_count or 0,
                error_log=json.loads(row.error_log or "[]"),
                output_artifact_ids=json.loads(row.output_artifact_ids or "[]"),
            )
            for row in rows
        ]

    # ── ApprovalGate ──────────────────────────────────────────────────────────

    async def save_gate(
        self,
        run_id: str,
        gate_name: str,
        status: ApprovalStatus,
        decided_at: datetime | None = None,
        revision_instructions: str | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._save_gate_sync,
            run_id,
            gate_name,
            status,
            decided_at,
            revision_instructions,
        )

    def _save_gate_sync(
        self,
        run_id: str,
        gate_name: str,
        status: ApprovalStatus,
        decided_at: datetime | None,
        revision_instructions: str | None,
    ) -> None:
        row: dict[str, Any] = {
            "run_id": run_id,
            "gate_name": gate_name,
            "status": status.value,
            "decided_at": self._dt_str(decided_at),
            "revision_instructions": revision_instructions,
        }
        with self.engine.begin() as conn:
            existing = conn.execute(
                sa.select(approval_gates_table).where(
                    (approval_gates_table.c.run_id == run_id)
                    & (approval_gates_table.c.gate_name == gate_name)
                )
            ).fetchone()
            if existing:
                conn.execute(
                    approval_gates_table.update()
                    .where(
                        (approval_gates_table.c.run_id == run_id)
                        & (approval_gates_table.c.gate_name == gate_name)
                    )
                    .values(**{k: v for k, v in row.items() if k not in ("run_id", "gate_name")})
                )
            else:
                conn.execute(approval_gates_table.insert().values(**row))

    async def load_gate(
        self, run_id: str, gate_name: str
    ) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._load_gate_sync, run_id, gate_name)

    def _load_gate_sync(
        self, run_id: str, gate_name: str
    ) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(approval_gates_table).where(
                    (approval_gates_table.c.run_id == run_id)
                    & (approval_gates_table.c.gate_name == gate_name)
                )
            ).fetchone()
        if row is None:
            return None
        return {
            "run_id": row.run_id,
            "gate_name": row.gate_name,
            "status": ApprovalStatus(row.status),
            "decided_at": self._parse_dt(row.decided_at),
            "revision_instructions": row.revision_instructions,
        }
