"""Regression contract: gate scripts must not crash on a cp1252 console (IMP-045)."""

from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

import pytest

import pr_gate
import spec_gate

ROOT = Path(__file__).resolve().parent.parent
VERDICT_LINES = [
    "✅ GATE RESULT: PASSED / APPROVED TO MERGE",
    "❌ GATE RESULT: HALTED / REVISIONS REQUIRED",
]


def _cp1252_console() -> io.TextIOWrapper:
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")


@pytest.mark.parametrize("module", [pr_gate, spec_gate], ids=["pr_gate", "spec_gate"])
def test_cp1252_console_cannot_print_verdict_without_fix(module: object) -> None:
    console = _cp1252_console()
    with pytest.raises(UnicodeEncodeError):
        print(VERDICT_LINES[0], file=console)
        console.flush()


@pytest.mark.parametrize("module", [pr_gate, spec_gate], ids=["pr_gate", "spec_gate"])
def test_ensure_utf8_stdout_lets_verdict_print(module: object, monkeypatch: pytest.MonkeyPatch) -> None:
    console = _cp1252_console()
    err = _cp1252_console()
    monkeypatch.setattr(sys, "stdout", console)
    monkeypatch.setattr(sys, "stderr", err)
    module.ensure_utf8_stdout()  # type: ignore[attr-defined]
    for line in VERDICT_LINES:
        print(line)
        print(line, file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    assert console.buffer.getvalue().decode("utf-8").splitlines() == VERDICT_LINES  # type: ignore[attr-defined]


@pytest.mark.parametrize("module", [pr_gate, spec_gate], ids=["pr_gate", "spec_gate"])
def test_ensure_utf8_stdout_tolerates_streams_without_reconfigure(
    module: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    monkeypatch.setattr(sys, "stderr", buf)
    module.ensure_utf8_stdout()  # type: ignore[attr-defined]
    print(VERDICT_LINES[0])
    assert buf.getvalue().strip() == VERDICT_LINES[0]


@pytest.mark.parametrize("script", ["pr_gate.py", "spec_gate.py"])
def test_main_calls_ensure_utf8_stdout_first(script: str) -> None:
    path = ROOT / "scripts" / script
    assert path.is_file(), f"missing {path}"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
    assert mains, f"{script} has no main()"
    body = [
        s
        for s in mains[0].body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
    ]
    first = body[0]
    assert (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Call)
        and isinstance(first.value.func, ast.Name)
        and first.value.func.id == "ensure_utf8_stdout"
    ), f"{script} main() must call ensure_utf8_stdout() before printing anything"
