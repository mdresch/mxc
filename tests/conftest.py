"""Keep the suite out of the real governance store (IMP-063).

``scripts.pr_gate`` persists a passive episode into ``DEFAULT_STORE_DIR`` whenever a test
drives the gate without a store. Every test gets a temporary default, and the session fails
if the configured store gained or lost a file.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "scripts" / "lib"
for path in (ROOT, ROOT / "scripts", LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Fixed at import, before any test changes the variable.
_REAL_STORE_RAW = os.environ.get("AGENT_LEARNING_LOCAL_STORE_DIR") or "data/agent-learning/store"


def _configured_store() -> Path:
    raw = _REAL_STORE_RAW
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def _listing(store: Path) -> frozenset[str]:
    if not store.exists():
        return frozenset()
    return frozenset(str(p.relative_to(store)) for p in store.rglob("*") if p.is_file())


@pytest.fixture(autouse=True)
def _temporary_store(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pr_gate

    temporary = tmp_path_factory.mktemp("store")
    monkeypatch.setattr(pr_gate, "DEFAULT_STORE_DIR", temporary)

    def no_diff(pr_number: int) -> str:
        return ""

    no_diff.real = pr_gate.fetch_pr_diff  # type: ignore[attr-defined]
    monkeypatch.setattr(pr_gate, "fetch_pr_diff", no_diff)
    if not request.module.__name__.endswith("_real_data"):
        monkeypatch.setenv("AGENT_LEARNING_LOCAL_STORE_DIR", str(temporary))


@pytest.fixture(scope="session", autouse=True)
def _suite_leaves_the_store_unchanged():
    store = _configured_store()
    before = _listing(store)
    yield
    after = _listing(store)
    assert after == before, (
        f"The suite changed the governance store {store}: added {sorted(after - before)[:5]}, "
        f"removed {sorted(before - after)[:5]}"
    )
