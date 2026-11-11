"""Lifecycle conformance validator for a SIDPA project.

Checks a repository against the unified 18-stage registry
(``pmbok.lifecycle.stages``):

* per-stage artifact presence (canonical folders first, legacy paths second;
  ``*.template.md`` / ``*-TEMPLATE.md`` files never count as evidence)
* governing policy shape present for each stage policy
* ordering invariants I1, I2 and I4 (see ``stages.INVARIANTS``)

Missing stages are reported as gaps (a fresh project legitimately has them);
only invariant violations make ``ok`` false.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from .stages import FOLDERS, INVARIANTS, STAGES, Stage, required_policies

LIFECYCLE_ROOT = Path("docs") / "lifecycle"
POLICY_DIR = Path("docs") / "policy-shapes"
_SKIP_PARTS = {".git", "node_modules", "__pycache__", ".venv", "history", "archive"}


def _is_template(path: Path) -> bool:
    n = path.name.lower()
    return ".template." in n or n.endswith("-template.md") or n == ".gitkeep"


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if kv:
            out[kv.group(1)] = kv.group(2).strip().strip("'\"")
    return out


def _find(base: Path, globs: tuple[str, ...]) -> list[Path]:
    if not base.exists():
        return []
    hits: list[Path] = []
    for p in base.rglob("*"):
        if not p.is_file() or _is_template(p):
            continue
        if any(part in _SKIP_PARTS for part in p.relative_to(base).parts[:-1]):
            continue
        if any(fnmatch(p.name, g) for g in globs):
            hits.append(p)
    return sorted(hits)


@dataclass
class StageResult:
    stage: Stage
    canonical: list[Path] = field(default_factory=list)
    legacy: list[Path] = field(default_factory=list)
    policy_shape: bool = False

    @property
    def present(self) -> bool:
        return bool(self.canonical or self.legacy)


@dataclass
class Report:
    root: Path
    stages: list[StageResult]
    violations: list[str]
    folder_gaps: list[str]
    missing_policies: list[str]

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def stages_present(self) -> int:
        return sum(1 for s in self.stages if s.present)


def _baseline(pmp: Path) -> tuple[int, int, int] | None:
    fm = parse_frontmatter(pmp)
    m = re.search(r"PMP-BL-v(\d+)\.(\d+)\.(\d+)", fm.get("pmp_baseline", ""))
    return tuple(int(x) for x in m.groups()) if m else None  # type: ignore[return-value]


_EMPTY_LINK = {"", "tbd", "pending", "n/a", "none", "null", "~", "[]", "{}", '""', "''"}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _frontmatter_block(text: str) -> str:
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def _front_value(text: str, key: str) -> str:
    """Return a frontmatter scalar, or a comma-joined list when the scalar is empty."""
    lines = _frontmatter_block(text).splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^\s*{re.escape(key)}:\s*(.*)$", line)
        if not match:
            continue
        raw = re.sub(r"\s+#.*$", "", match.group(1).strip()).strip().strip("'\"")
        if raw:
            return raw
        items: list[str] = []
        for nxt in lines[index + 1 :]:
            item = re.match(r"^\s+-\s+(.+)$", nxt)
            if not item:
                break
            items.append(re.sub(r"\s+#.*$", "", item.group(1).strip()).strip().strip("'\""))
        return ", ".join(items)
    return ""


def _concrete(value: str) -> bool:
    if value.lower() in _EMPTY_LINK:
        return False
    return not any(token in value for token in ("<", ">", "X.Y.Z"))


def _proposal_in_force(text: str) -> bool:
    status = _front_value(text, "status") or _front_value(text, "approval_status")
    if status.lower() == "approved":
        return True
    return _concrete(_front_value(text, "refinement_id"))


def _closes_loop(text: str) -> bool:
    """A proposal closes the loop the way the Stage 18 template records it.

    ``lineage.root_spark`` names the Stage 1 spark. Section 6 names the Phase N+1
    catalyst. ``refinesIntent`` and ``amendsADR`` remain accepted explicit links.
    """
    if _concrete(_front_value(text, "refinesIntent")) or _concrete(_front_value(text, "amendsADR")):
        return True
    if _concrete(_front_value(text, "root_spark")):
        return True
    catalyst = re.search(r"Primary Catalyst for Phase N\+1:\**\s*(.+)", text)
    if catalyst and _concrete(catalyst.group(1).strip().strip("*")):
        return True
    return False


def _i4_violations(stage_files: dict[int, list[Path]]) -> list[str]:
    """Loop closure is Stage 18. Design-time changes and adaptations must not refine intent."""
    violations: list[str] = []
    for path in stage_files.get(16, []):
        if not path.name.startswith("GC-"):
            continue
        text = _read_text(path)
        basis = _front_value(text, "evidence_basis").replace("-", "_")
        if "design_time" in basis and _concrete(_front_value(text, "refinesIntent")):
            violations.append(
                f"I4: {path.name} is a design-time governance change and must not refine intent"
            )
    for path in stage_files.get(17, []):
        if path.name != "Adaptation-Plan.md" and not path.name.startswith("ADAPT-"):
            continue
        if _concrete(_front_value(_read_text(path), "refinesIntent")):
            violations.append(
                f"I4: {path.name} refines intent; Stage 17 adaptation must not redefine intent"
            )
    for path in stage_files.get(18, []):
        if not path.name.startswith("Intent-Refinement"):
            continue
        text = _read_text(path)
        if not _proposal_in_force(text):
            continue
        if _closes_loop(text):
            continue
        violations.append(
            f"I4: {path.name} closes no loop "
            "(needs lineage.root_spark, a Phase N+1 spark catalyst, refinesIntent, or amendsADR)"
        )
    return violations


def validate_project(root: str | Path) -> Report:
    root = Path(root).resolve()
    life = root / LIFECYCLE_ROOT
    results: list[StageResult] = []
    for st in STAGES:
        r = StageResult(st)
        for folder in st.folders:
            r.canonical += _find(life / folder, st.artifact_globs)
        for lp in st.legacy_paths:
            r.legacy += _find(root / lp, st.artifact_globs)
        r.policy_shape = (root / POLICY_DIR / f"{st.policy}.actions.json").exists()
        results.append(r)

    by = {r.stage.number: r for r in results}
    violations: list[str] = []

    # I1: benefit documents before an approved charter (chain §2 stages 4 then 2)
    charter = [p for p in (by[2].canonical + by[2].legacy) if p.name.startswith("Project-Charter")]
    if charter and parse_frontmatter(charter[0]).get("status", "").lower() == "approved":
        biz = by[4].canonical + by[4].legacy
        kinds = {k: [p for p in biz if p.name.startswith(k)]
                 for k in ("Business-Case", "Benefits-Statement", "Stakeholder-Register")}
        for k, files in kinds.items():
            if not files:
                violations.append(f"I1: Project Charter is Approved but {k} is missing")
            elif not any(parse_frontmatter(f).get("status", "").lower() == "approved" for f in files):
                violations.append(f"I1: Project Charter is Approved but {k} is not Approved")

    # I2: canonical execution evidence requires an elaborated Stage 7 PMP and Stage 6 stories
    exec_evidence = by[9].canonical + by[10].canonical
    if exec_evidence:
        pmps = [p for p in (by[7].canonical + by[7].legacy) if p.name == "Project-Management-Plan.md"]
        bl = _baseline(pmps[0]) if pmps else None
        if bl is None:
            violations.append("I2: Stage 9/10 artifacts exist but no baselined Project-Management-Plan.md")
        elif bl < (1, 1, 0):
            violations.append(
                f"I2: Stage 9/10 artifacts exist but PMP baseline is PMP-BL-v{bl[0]}.{bl[1]}.{bl[2]} "
                "(needs elaboration to >= v1.1.0)")
        if not (by[6].canonical + by[6].legacy):
            violations.append("I2: Stage 9/10 artifacts exist but no Stage 6 requirements exist")

    # I4: Stage 18 closes the loop. Design-time Stage 16 records and Stage 17
    # adaptations must not refine intent.
    violations.extend(
        _i4_violations(
            {
                16: by[16].canonical + by[16].legacy,
                17: by[17].canonical + by[17].legacy,
                18: by[18].canonical + by[18].legacy,
            }
        )
    )

    folder_gaps = [f for f in FOLDERS.values() if not (life / f).is_dir()]
    missing_policies = [p for p in required_policies()
                        if not (root / POLICY_DIR / f"{p}.actions.json").exists()]
    return Report(root, results, violations, folder_gaps, missing_policies)


def format_report(rep: Report) -> str:
    lines = [f"SIDPA lifecycle conformance — {rep.root}", ""]
    for r in rep.stages:
        loc = (r.canonical or r.legacy)
        where = ""
        if loc:
            where = loc[0].relative_to(rep.root).as_posix() + ("  [legacy path]" if not r.canonical else "")
        mark = "OK " if r.present else "-- "
        pol = "policy:ok" if r.policy_shape else "policy:MISSING"
        lines.append(f"  {mark}Stage {r.stage.number:>2} {r.stage.name:<58} {pol:<15} {where}")
    lines.append("")
    lines.append(f"Stages with evidence: {rep.stages_present}/18")
    lines.append(f"Canonical folders missing: {len(rep.folder_gaps)}/{len(FOLDERS)}")
    lines.append(f"Policy shapes missing: {len(rep.missing_policies)} {rep.missing_policies}")
    lines.append("Invariants: " + ("PASS" if rep.ok else "FAIL"))
    for v in rep.violations:
        lines.append(f"  ! {v}")
    return "\n".join(lines)


__all__ = ["validate_project", "format_report", "Report", "INVARIANTS"]

