"""
Initialize a new project from sidpa-template.

Usage:
    python scripts/init_project.py --name my-project
    python scripts/init_project.py --name my-project --stage plans

Actions performed:
1. Renames data/agent-learning/store/{active-policies,policies}/template-governance/
   to <name>-governance/ and updates agent_id in the policy JSON files.
2. Leaves agent-learning-governance unchanged (shared global namespace).
3. Copies the *.template.md files for the chosen stage to their working .md names,
   never overwriting an existing file, and fills <project name> and the start date.

Stages (documents are copied when their stage is reached, not all at once):
    start    Spark, Ideation, Business Case, Benefits Statement, Charter, and the registers
    plans    the nine subsidiary plan skeletons and the Project Management Plan
    closing  the Adaptation Plan and the Intent Refinement Proposal
    all      everything
"""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent

STAGES = {
    "start": [
        "docs/project-docs/Spark-Capture.template.md",
        "docs/project-docs/Ideation-Document.template.md",
        "docs/project-docs/Business-Case.template.md",
        "docs/project-docs/Benefits-Statement.template.md",
        "docs/project-docs/Project-Charter.template.md",
        "docs/registers/Cycle-Register.template.md",
        "docs/registers/Lessons-Learned-Register.template.md",
        "docs/registers/Implementation-Log.template.md",
        "docs/registers/Story-Execution-Register.template.md",
        "docs/registers/Audit-Register.template.md",
        "docs/registers/Methodology-Best-Practice-Ledger.template.md",
    ],
    "plans": [
        "docs/project-docs/management-plans/*.template.md",
        "docs/project-docs/Project-Management-Plan.template.md",
    ],
    "closing": [
        "docs/project-docs/Adaptation-Plan.template.md",
        "docs/project-docs/Intent-Refinement-Proposal.template.md",
    ],
}
STAGES["all"] = STAGES["start"] + STAGES["plans"] + STAGES["closing"]

NEXT_STEPS = {
    "start": [
        "Write the Spark, then the Ideation Document, then the Business Case and Benefits Statement, then the Charter.",
        "Run the matching approve-* gate for each (see docs/policy-shapes/decision-frames/README.md).",
        "CYC-001 is open in docs/registers/Cycle-Register.md. Add the upstream pins as those documents are approved.",
        "After the Charter is approved, run: python scripts/init_project.py --name <name> --stage plans",
    ],
    "plans": [
        "Draft the plans in dependency order (Scope first). See .claude/skills/pmbok-planning/SKILL.md.",
        "Approve each full_plan, then synthesize and approve the Project Management Plan.",
    ],
    "closing": ["Use these when a governance change reaches Stage 17 or the phase reaches Stage 18."],
    "all": ["Every skeleton is in place. Work through the stages in order."],
}


def clean_project_name(project_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "-", project_name).lower().strip("-")


def rename_governance(clean_name: str) -> int:
    """Rename the template governance agent and rewrite agent_id. Returns files updated."""
    new_agent_id = f"{clean_name}-governance"
    old_agent_id = "template-governance"
    store_dir = repo_root / "data" / "agent-learning" / "store"
    updated = 0
    for kind in ("active-policies", "policies"):
        old_dir = store_dir / kind / old_agent_id
        new_dir = store_dir / kind / new_agent_id
        if old_dir.exists():
            if new_dir.exists():
                shutil.rmtree(new_dir)
            old_dir.rename(new_dir)
            print(f"  [OK] Renamed {new_dir.relative_to(repo_root)}")
        if new_dir.exists():
            for json_file in new_dir.glob("*.json"):
                try:
                    content = json_file.read_text(encoding="utf-8")
                    if old_agent_id in content:
                        json_file.write_text(
                            content.replace(f'"{old_agent_id}"', f'"{new_agent_id}"'),
                            encoding="utf-8",
                        )
                        updated += 1
                except (OSError, PermissionError) as err:
                    print(f"  [WARN] Failed to update {json_file.relative_to(repo_root)}: {err}")
    return updated


def copy_stage_documents(stage: str, project_title: str, clean_name: str, today: str) -> int:
    """Copy the stage's templates to their working names without overwriting anything."""
    created = 0
    for pattern in STAGES[stage]:
        for template_file in sorted(repo_root.glob(pattern)):
            dest = template_file.with_name(template_file.name.replace(".template.md", ".md"))
            if dest.exists():
                print(f"  [SKIP] Already exists: {dest.relative_to(repo_root)}")
                continue
            text = template_file.read_text(encoding="utf-8")
            text = (
                text.replace("<project name>", project_title)
                .replace("HYP-<project>-", f"HYP-{clean_name}-")
                .replace("<project>", project_title)
                .replace("<date the project starts>", today)
                .replace("<date this project starts using it>", today)
            )
            dest.write_text(text, encoding="utf-8")
            created += 1
            print(f"  [OK] Created {dest.relative_to(repo_root)}")
    return created


def init_project(project_name: str, stage: str = "start", create_docs: bool = True) -> None:
    clean_name = clean_project_name(project_name)
    if not clean_name:
        raise SystemExit("Project name is empty after sanitizing; use letters, digits, '-' or '_'.")
    print(f"\nSIDPA Project Initializer\n  Project: {clean_name}\n  Governance agent: {clean_name}-governance\n  Stage: {stage}\n")

    updated = rename_governance(clean_name)
    print(f"  [OK] Updated agent_id in {updated} policy file(s).")

    if create_docs:
        created = copy_stage_documents(stage, project_name.strip(), clean_name, datetime.date.today().isoformat())
        print(f"  [OK] Created {created} document(s) for stage '{stage}'.")

    print("\nNext steps:")
    for step in NEXT_STEPS[stage]:
        print(f"  - {step}")
    print(f"\nUse agent-id '{clean_name}-governance' for governance decisions.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a new project from sidpa-template")
    parser.add_argument("--name", required=True, help="Project name (for example 'my-awesome-app')")
    parser.add_argument("--stage", choices=sorted(STAGES), default="start", help="Which documents to create")
    parser.add_argument("--skip-docs", action="store_true", help="Rename the governance agent only")
    args = parser.parse_args()
    init_project(args.name, stage=args.stage, create_docs=not args.skip_docs)


if __name__ == "__main__":
    main()
