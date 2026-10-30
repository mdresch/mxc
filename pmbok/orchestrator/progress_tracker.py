"""ProgressTracker: generates on-demand ProgressReport from StateStore."""

from __future__ import annotations

from pmbok.models.enums import KnowledgeArea, ProcessStatus
from pmbok.models.reporting import ProgressReport, StatusCounts
from pmbok.process_registry import PMBOK_PROCESSES
from pmbok.storage.state_store import StateStore


class ProgressTracker:
    """Aggregates process states by knowledge area into a ProgressReport."""

    def __init__(self, state_store: StateStore) -> None:
        self._state_store = state_store

    async def generate_report(self, run_id: str) -> ProgressReport:
        """
        Load all process states from StateStore and aggregate counts
        by knowledge area. Processes not yet in the store are counted
        as NOT_STARTED.
        """
        stored_states = await self._state_store.load_all_process_states(run_id)
        status_by_process: dict[str, ProcessStatus] = {
            s.process_id: s.status for s in stored_states
        }

        # Initialise per-area counters
        by_area: dict[KnowledgeArea, StatusCounts] = {
            area: StatusCounts() for area in KnowledgeArea
        }

        for process in PMBOK_PROCESSES:
            status = status_by_process.get(process.process_id, ProcessStatus.NOT_STARTED)
            counts = by_area[process.knowledge_area]
            if status == ProcessStatus.NOT_STARTED:
                counts.not_started += 1
            elif status == ProcessStatus.IN_PROGRESS:
                counts.in_progress += 1
            elif status == ProcessStatus.COMPLETE:
                counts.complete += 1
            elif status == ProcessStatus.BLOCKED:
                counts.blocked += 1

        # Compute totals
        total = StatusCounts(
            not_started=sum(c.not_started for c in by_area.values()),
            in_progress=sum(c.in_progress for c in by_area.values()),
            complete=sum(c.complete for c in by_area.values()),
            blocked=sum(c.blocked for c in by_area.values()),
        )

        return ProgressReport(
            run_id=run_id,
            by_knowledge_area=by_area,
            total=total,
        )
