"""Tests for ProgressTracker and StaleProcessMonitor."""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from pmbok.models.enums import KnowledgeArea, ProcessStatus
from pmbok.models.pmbok import ProcessState
from pmbok.models.reporting import ProgressReport, StatusCounts
from pmbok.orchestrator.progress_tracker import ProgressTracker
from pmbok.orchestrator.stale_monitor import StaleProcessMonitor
from pmbok.process_registry import PMBOK_PROCESSES
from pmbok.storage.state_store import StateStore


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_state_store() -> StateStore:
    tmp = tempfile.mktemp(suffix=".db")
    return StateStore(tmp)


# ── ProgressTracker tests ─────────────────────────────────────────────────────

class TestProgressTracker:
    @pytest.mark.asyncio
    async def test_empty_store_all_not_started(self):
        """With no states persisted, every process should be NOT_STARTED."""
        store = make_state_store()
        tracker = ProgressTracker(store)
        report = await tracker.generate_report("run-1")

        assert isinstance(report, ProgressReport)
        assert report.run_id == "run-1"
        # All 49 processes are NOT_STARTED
        assert report.total.not_started == len(PMBOK_PROCESSES)
        assert report.total.in_progress == 0
        assert report.total.complete == 0
        assert report.total.blocked == 0

    @pytest.mark.asyncio
    async def test_totals_match_sum_of_areas(self):
        """Total counts must equal the sum across all knowledge areas."""
        store = make_state_store()
        tracker = ProgressTracker(store)
        report = await tracker.generate_report("run-2")

        area_not_started = sum(c.not_started for c in report.by_knowledge_area.values())
        area_in_progress = sum(c.in_progress for c in report.by_knowledge_area.values())
        area_complete = sum(c.complete for c in report.by_knowledge_area.values())
        area_blocked = sum(c.blocked for c in report.by_knowledge_area.values())

        assert report.total.not_started == area_not_started
        assert report.total.in_progress == area_in_progress
        assert report.total.complete == area_complete
        assert report.total.blocked == area_blocked

    @pytest.mark.asyncio
    async def test_all_knowledge_areas_present(self):
        """Report must include an entry for every KnowledgeArea."""
        store = make_state_store()
        tracker = ProgressTracker(store)
        report = await tracker.generate_report("run-3")

        for area in KnowledgeArea:
            assert area in report.by_knowledge_area

    @pytest.mark.asyncio
    async def test_reflects_stored_states(self):
        """Counts should reflect actual ProcessState values in the store."""
        store = make_state_store()
        run_id = "run-4"

        # Mark a couple of processes
        await store.set_status(run_id, "4.1", ProcessStatus.COMPLETE)
        await store.set_status(run_id, "4.2", ProcessStatus.IN_PROGRESS)
        await store.set_status(run_id, "4.3", ProcessStatus.BLOCKED)

        tracker = ProgressTracker(store)
        report = await tracker.generate_report(run_id)

        integration_counts = report.by_knowledge_area[KnowledgeArea.INTEGRATION]
        assert integration_counts.complete >= 1
        assert integration_counts.in_progress >= 1
        assert integration_counts.blocked >= 1

        # Total across all areas must still equal 49
        total_processes = (
            report.total.not_started
            + report.total.in_progress
            + report.total.complete
            + report.total.blocked
        )
        assert total_processes == len(PMBOK_PROCESSES)

    @pytest.mark.asyncio
    async def test_total_always_49(self):
        """Sum of all status counts must always equal 49 regardless of state."""
        store = make_state_store()
        run_id = "run-5"

        for pid in ["4.1", "13.1", "4.2"]:
            await store.set_status(run_id, pid, ProcessStatus.COMPLETE)

        tracker = ProgressTracker(store)
        report = await tracker.generate_report(run_id)

        total = (
            report.total.not_started
            + report.total.in_progress
            + report.total.complete
            + report.total.blocked
        )
        assert total == 49


# ── StaleProcessMonitor tests ─────────────────────────────────────────────────

class TestStaleProcessMonitor:
    @pytest.mark.asyncio
    async def test_no_alert_when_no_stale_processes(self):
        """Monitor should not call notify when no process exceeds threshold."""
        store = make_state_store()
        run_id = "run-stale-1"

        # Process started just now — not stale
        await store.set_status(run_id, "4.1", ProcessStatus.IN_PROGRESS)

        alerts: list[tuple[str, str]] = []
        monitor = StaleProcessMonitor(
            store,
            threshold_hours=24,
            notify_callback=lambda r, m: alerts.append((r, m)),
            poll_interval_seconds=0.05,
        )
        task = monitor.start(run_id)
        await asyncio.sleep(0.15)
        monitor.stop()
        with pytest.raises((asyncio.CancelledError, Exception)):
            await task

        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_alert_emitted_for_stale_process(self):
        """Monitor should call notify when a process exceeds the threshold."""
        store = make_state_store()
        run_id = "run-stale-2"

        # Manually insert a state with started_at far in the past
        await store.set_status(run_id, "4.1", ProcessStatus.IN_PROGRESS)
        # Patch started_at to be 25 hours ago
        import sqlalchemy as sa
        from pmbok.storage.state_store import process_states_table

        old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        with store.engine.begin() as conn:
            conn.execute(
                process_states_table.update()
                .where(
                    (process_states_table.c.run_id == run_id)
                    & (process_states_table.c.process_id == "4.1")
                )
                .values(started_at=old_time)
            )

        alerts: list[tuple[str, str]] = []
        monitor = StaleProcessMonitor(
            store,
            threshold_hours=24,
            notify_callback=lambda r, m: alerts.append((r, m)),
            poll_interval_seconds=0.05,
        )
        task = monitor.start(run_id)
        await asyncio.sleep(0.15)
        monitor.stop()
        with pytest.raises((asyncio.CancelledError, Exception)):
            await task

        assert len(alerts) >= 1
        assert alerts[0][0] == run_id
        assert "4.1" in alerts[0][1]

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """stop() should cancel the background task."""
        store = make_state_store()
        monitor = StaleProcessMonitor(store, poll_interval_seconds=60)
        task = monitor.start("run-stop")
        assert not task.done()
        monitor.stop()
        await asyncio.sleep(0.01)
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_default_threshold_from_settings(self):
        """When threshold_hours is None, settings.STALE_PROCESS_THRESHOLD_HOURS is used."""
        from pmbok.config import settings

        store = make_state_store()
        monitor = StaleProcessMonitor(store)
        assert monitor._threshold_hours == settings.STALE_PROCESS_THRESHOLD_HOURS

    @pytest.mark.asyncio
    async def test_stdout_fallback_when_no_callback(self, capsys):
        """When no callback is provided, alert is printed to stdout."""
        store = make_state_store()
        run_id = "run-stdout"

        await store.set_status(run_id, "4.1", ProcessStatus.IN_PROGRESS)
        import sqlalchemy as sa
        from pmbok.storage.state_store import process_states_table

        old_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        with store.engine.begin() as conn:
            conn.execute(
                process_states_table.update()
                .where(
                    (process_states_table.c.run_id == run_id)
                    & (process_states_table.c.process_id == "4.1")
                )
                .values(started_at=old_time)
            )

        monitor = StaleProcessMonitor(store, threshold_hours=24, poll_interval_seconds=0.05)
        task = monitor.start(run_id)
        await asyncio.sleep(0.15)
        monitor.stop()
        with pytest.raises((asyncio.CancelledError, Exception)):
            await task

        captured = capsys.readouterr()
        assert "STALE ALERT" in captured.out
