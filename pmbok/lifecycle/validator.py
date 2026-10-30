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

    # I1: business documents before charter
    charter = (by[4].canonical + by[4].legacy)
    charter = [p for p in charter if p.name.startswith("Project-Charter")]
    if charter:
        biz = by[3].canonical + by[3].legacy
        kinds = {k: [p for p in biz if p.name.startswith(k)]
                 for k in ("Business-Case", "Benefits-Statement", "Stakeholder-Register")}
        for k, files in kinds.items():
            if not files:
                violations.append(f"I1: Project Charter exists but {k} is missing")
            elif parse_frontmatter(charter[0]).get("status", "").lower() == "approved" and \
                    not any(parse_frontmatter(f).get("status", "").lower() == "approved" for f in files):
                violations.append(f"I1: Project Charter is Approved but {k} is not Approved")

    # I2: progressive PMP elaboration before execution/contract evidence
    exec_evidence = by[11].canonical + by[12].canonical
    if exec_evidence:
        pmps = [p for p in (by[10].canonical + by[10].legacy) if p.name == "Project-Management-Plan.md"]
        bl = _baseline(pmps[0]) if pmps else None
        if bl is None:
            violations.append("I2: Stage 11/12 artifacts exist but no baselined Project-Management-Plan.md")
        elif bl[1] < 1 and bl[0] < 2:
            violations.append(
                f"I2: Stage 11/12 artifacts exist but PMP baseline is PMP-BL-v{bl[0]}.{bl[1]}.{bl[2]} "
                "(needs elaboration to >= v1.1.0 after User Stories)")
        if bl is not None and not (by[9].canonical + by[9].legacy):
            violations.append("I2: PMP elaborated but no Stage 9 User Stories/Epics exist")

    # I4: loop closure
    for p in by[18].canonical + by[18].legacy:
        text = ""
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass
        if p.name.startswith(("GC-", "ADAPT-")) and not re.search(r"refinesIntent|amendsADR", text):
            violations.append(f"I4: {p.name} closes no loop (needs refinesIntent and/or amendsADR)")

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

