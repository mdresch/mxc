"""Gate script helpers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

from gate_common import frontmatter_has, yaml_frontmatter_body  # noqa: E402


def test_frontmatter_has_reads_yaml_block_not_empty_prefix() -> None:
    text = "---\nkey: value\n---\n\n# Body\n"
    assert yaml_frontmatter_body(text) == "\nkey: value\n"
    assert frontmatter_has(text, "key")
    assert not frontmatter_has(text, "missing")


def test_frontmatter_has_false_when_no_fence() -> None:
    assert not frontmatter_has("# No frontmatter\n", "key")
