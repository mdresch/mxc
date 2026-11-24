"""IMP-045: every gate script call that reads text from a subprocess decodes it as UTF-8."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import pr_gate

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ["pr_gate.py"]  # stage16_amend / approve CLI deferred until IMP-007 / IMP-062


def _text_runs(script: str) -> list[ast.Call]:
    tree = ast.parse((ROOT / "scripts" / script).read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"run", "check_output"}
        ):
            kw = {k.arg: k.value for k in node.keywords}
            if "text" in kw or "universal_newlines" in kw:
                calls.append(node)
    return calls


@pytest.mark.parametrize("script", SCRIPTS)
def test_every_text_subprocess_call_names_utf8(script: str) -> None:
    for call in _text_runs(script):
        kw = {k.arg: k.value for k in call.keywords}
        enc = kw.get("encoding")
        assert isinstance(enc, ast.Constant) and enc.value == "utf-8", (
            f"{script}:{call.lineno} has no encoding='utf-8'"
        )
        errors = kw.get("errors")
        assert isinstance(errors, ast.Constant) and errors.value == "replace", (
            f"{script}:{call.lineno} has no errors='replace'"
        )


def test_fetch_pr_data_decodes_gh_output_as_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    class Done:
        returncode = 0
        stdout = '{"ok": "✅"}'
        stderr = ""

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)
        return Done()

    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    assert pr_gate.fetch_pr_data(1) == {"ok": "✅"}
    assert seen.get("encoding") == "utf-8" and seen.get("errors") == "replace"
