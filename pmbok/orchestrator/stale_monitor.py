"""StaleProcessMonitor: asyncio background task that alerts on stale IN_PROGRESS processes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime

from pmbok.config import settings
from pmbok.models.enums import ProcessStatus
from pmbok.storage.state_store import StateStore


class StaleProcessMonitor:
    """
    Background asyncio task that polls process states every `poll_interval_seconds`
    and emits an alert when any process has been IN_PROGRESS longer than
    `threshold_hours`.
    """

    def __init__(
        self,
        state_store: StateStore,
        threshold_hours: float | None = None,
        notify_callback: Callable[[str, str], None] | None = None,
        poll_interval_seconds: float = 60,
    ) -> None:
        self._state_store = state_store
        self._threshold_hours: float = (
            threshold_hours
            if threshold_hours is not None
            else settings.STALE_PROCESS_THRESHOLD_HOURS
        )
        self._notify_callback = notify_callback
        self._poll_interval = poll_interval_seconds
        self._task: asyncio.Task | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self, run_id: str) -> asyncio.Task:
        """Start the background polling task and return it."""
        self._task = asyncio.create_task(
            self._stale_process_monitor(run_id, self._threshold_hours)
        )
        return self._task

    def stop(self) -> None:
        """Cancel the background polling task."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
            self._task = None

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _stale_process_monitor(
        self, run_id: str, threshold_hours: float
    ) -> None:
        while True:
            await asyncio.sleep(self._poll_interval)
            states = await self._state_store.load_all_process_states(run_id)
            now = datetime.utcnow()
            for state in states:
                if state.status == ProcessStatus.IN_PROGRESS and state.started_at:
                    elapsed = (now - state.started_at).total_seconds() / 3600
                    if elapsed > threshold_hours:
                        await self._notify_user(
                            run_id,
                            f"Process {state.process_id} has been IN_PROGRESS for "
                            f"{elapsed:.1f} hours (threshold: {threshold_hours}h)",
                        )

    async def _notify_user(self, run_id: str, message: str) -> None:
        if self._notify_callback is not None:
            self._notify_callback(run_id, message)
        else:
            print(f"[STALE ALERT] run={run_id}: {message}")
