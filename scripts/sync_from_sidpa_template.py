"""Merge latest SIDPA template scaffold into MXC without clobbering project artifacts."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

TEMPLATE_ROOT = Path(r"D:\Source\repos\sidpa-template")
REPO = Path(__file__).resolve().parents[1]
AGENT_ID = "mxc-governance"
OLD_AGENT = "template-governance"


def copy_tree(src: Path, dst: Path) -> int:
    if not src.is_dir():
        return 0
    n = 0
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        if "__pycache__" in rel.parts or rel.suffix == ".pyc":
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        n += 1
    return n


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def merge_claude_skills() -> int:
    src = TEMPLATE_ROOT / ".claude" / "skills"
    dst = REPO / ".claude" / "skills"
    if not src.is_dir():
        return 0
    return copy_tree(src, dst)


def install_subsidiary_policy() -> None:
    shape_src = TEMPLATE_ROOT / "docs" / "policy-shapes" / "approve-subsidiary-plan.actions.json"
    copy_file(shape_src, REPO / "docs" / "policy-shapes" / "approve-subsidiary-plan.actions.json")

    active_dst = REPO / "data" / "agent-learning" / "store" / "active-policies" / AGENT_ID
    active_dst.mkdir(parents=True, exist_ok=True)
    active = json.loads(
        (TEMPLATE_ROOT / "data" / "agent-learning" / "store" / "active-policies" / OLD_AGENT / "approve-subsidiary-plan.json").read_text(
            encoding="utf-8"
        )
    )
    active["agent_id"] = AGENT_ID
    (active_dst / "approve-subsidiary-plan.json").write_text(json.dumps(active, indent=2) + "\n", encoding="utf-8")

    pol_src = TEMPLATE_ROOT / "data" / "agent-learning" / "store" / "policies" / OLD_AGENT / "1c0b25f8-af6e-4573-a101-9f5568f28792.json"
    pol = json.loads(pol_src.read_text(encoding="utf-8"))
    pol["agent_id"] = AGENT_ID
    pol_dst = REPO / "data" / "agent-learning" / "store" / "policies" / AGENT_ID / "1c0b25f8-af6e-4573-a101-9f5568f28792.json"
    pol_dst.parent.mkdir(parents=True, exist_ok=True)
    pol_dst.write_text(json.dumps(pol, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if not TEMPLATE_ROOT.is_dir():
        print(f"Template repo not found: {TEMPLATE_ROOT}", file=sys.stderr)
        return 1

    report: list[str] = []

    # Core scripts (always take template latest)
    script_names = [
        "init_project.py",
        "init_management_plan_foundations.py",
        "orchestrate_pmbok.py",
        "execute_approve_gate.example.py",
        "complete-story.mjs",
        "run-contracts.mjs",
    ]
    for name in script_names:
        src = TEMPLATE_ROOT / "scripts" / name
        if src.is_file():
            copy_file(src, REPO / "scripts" / name)
            report.append(f"scripts/{name}")

    n_brain = copy_tree(TEMPLATE_ROOT / "scripts" / "brain", REPO / "scripts" / "brain")
    if n_brain:
        report.append(f"scripts/brain/ ({n_brain} files)")

    n_tpl = copy_tree(TEMPLATE_ROOT / "templates" / "management-plans", REPO / "templates" / "management-plans")
    if n_tpl:
        report.append(f"templates/management-plans/ ({n_tpl} files)")

    n_skills = merge_claude_skills()
    if n_skills:
        report.append(f".claude/skills/ ({n_skills} files)")

    doc_files = [
        "docs/chain-coverage.md",
        "docs/sequence-and-lessons.md",
        "docs/second-brain-lifecycle-and-scripts.md",
        "docs/registers/Project-Status-Register.template.md",
        "docs/registers/Continuous-Improvement-Register.template.md",
        "docs/project-docs/Status-Reports/Stage-8-Implementation-Authorization-Notice.template.md",
        "docs/policy-shapes/decision-frames/charter-approval.json",
        "docs/policy-shapes/episodes/EXAMPLE-pmp-approval-episode.json",
        ".github/instructions/sidpa-governance-qa.instructions.md",
    ]
    for rel in doc_files:
        src = TEMPLATE_ROOT / rel
        if src.is_file():
            copy_file(src, REPO / rel)
            report.append(rel)

    install_subsidiary_policy()
    report.append("approve-subsidiary-plan policy + shape")

    pkg_src = TEMPLATE_ROOT / "package.json"
    if pkg_src.is_file():
        pkg = json.loads(pkg_src.read_text(encoding="utf-8"))
        pkg["name"] = "mxc"
        pkg["description"] = "MXC — Hyper-V sandbox + SIDPA governance (synced from sidpa-template)"
        (REPO / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
        report.append("package.json (sidpa lifecycle scripts)")

    n_tests = copy_tree(TEMPLATE_ROOT / "tests", REPO / "tests" / "sidpa")
    if n_tests:
        report.append(f"tests/sidpa/ ({n_tests} files)")

    meta = {
        "template_repo": str(TEMPLATE_ROOT),
        "template_version": json.loads((TEMPLATE_ROOT / "package.json").read_text())["version"],
        "synced_paths": report,
    }
    sync_doc = REPO / "docs" / "project-docs" / "SIDPA-Template-Sync.md"
    sync_doc.write_text(
        "---\n"
        'governance_policy: "none (sync record)"\n'
        "---\n\n"
        f"# SIDPA template sync\n\n"
        f"Last sync from **sidpa-template v{meta['template_version']}**.\n\n"
        "## Paths updated\n\n"
        + "\n".join(f"- `{p}`" for p in report)
        + "\n",
        encoding="utf-8",
    )
    report.append("docs/project-docs/SIDPA-Template-Sync.md")

    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
