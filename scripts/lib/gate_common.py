"""Shared helpers for SIDPA gate runner/adjudicator scripts."""
from __future__ import annotations

import shutil
from pathlib import Path


def resolve_agent_learn_cli(repo: Path) -> Path:
    """Return agent-learn executable (.venv Windows/Unix or PATH)."""
    win = repo / ".venv" / "Scripts" / "agent-learn.exe"
    if win.is_file():
        return win
    unix = repo / ".venv" / "bin" / "agent-learn"
    if unix.is_file():
        return unix
    found = shutil.which("agent-learn")
    if found:
        return Path(found)
    return win


def yaml_frontmatter_body(text: str) -> str:
    """YAML between the first pair of `---` lines; empty if missing or malformed."""
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[1]


def frontmatter_has(text: str, key: str) -> bool:
    """True if `key:` appears in YAML frontmatter (not in the doc body)."""
    return f"{key}:" in yaml_frontmatter_body(text)
