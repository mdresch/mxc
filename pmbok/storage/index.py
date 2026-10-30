"""IndexStore — maintains index.json mapping run_id → session_id."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path


class IndexStore:
    """
    Maintains a JSON file at {base_path}/index.json that maps
    run_id → session_id for quick cross-reference lookups.

    All writes are atomic (temp-file swap) so concurrent readers
    always see a consistent snapshot.
    """

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self._index_path = self.base_path / "index.json"

    # ── internal sync helpers ─────────────────────────────────────────────────

    def _read_index(self) -> dict[str, str]:
        if not self._index_path.exists():
            return {}
        with self._index_path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _write_index(self, data: dict[str, str]) -> None:
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=self._index_path.parent, suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self._index_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _register_sync(self, run_id: str, session_id: str) -> None:
        index = self._read_index()
        index[run_id] = session_id
        self._write_index(index)

    def _lookup_sync(self, run_id: str) -> str | None:
        index = self._read_index()
        return index.get(run_id)

    # ── public async API ──────────────────────────────────────────────────────

    async def register(self, run_id: str, session_id: str) -> None:
        """Add or update the run_id → session_id mapping."""
        await asyncio.to_thread(self._register_sync, run_id, session_id)

    async def lookup(self, run_id: str) -> str | None:
        """Return the session_id for *run_id*, or None if not found."""
        return await asyncio.to_thread(self._lookup_sync, run_id)
