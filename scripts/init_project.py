"""
Initialize a new project from sidpa-template.

Usage:
    python scripts/init_project.py --name my-project

Actions performed:
1. Renames data/agent-learning/store/active-policies/template-governance/ -> <name>-governance/
2. Renames data/agent-learning/store/policies/template-governance/ -> <name>-governance/
3. Updates agent_id: "template-governance" to "<name>-governance" in all policy JSONs.
4. Leaves agent-learning-governance unchanged (shared global namespace).
5. Copies *.template.md files to active *.md documents if they do not already exist.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent

def init_project(project_name: str, create_docs: bool = True):
    # Sanitize project name
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "-", project_name).lower().strip("-")
    new_agent_id = f"{clean_name}-governance"
    old_agent_id = "template-governance"

    print(f"\n=======================================================")
    print(f"  SIDPA Project Initializer")
    print(f"  Project Name: {clean_name}")
    print(f"  New Governance Agent ID: {new_agent_id}")
    print(f"=======================================================\n")

    store_dir = repo_root / "data" / "agent-learning" / "store"
    active_dir = store_dir / "active-policies"
    policies_dir = store_dir / "policies"

    # 1. Update and rename active-policies
    old_active = active_dir / old_agent_id
    new_active = active_dir / new_agent_id
    if old_active.exists():
        if new_active.exists():
            shutil.rmtree(new_active)
        old_active.rename(new_active)
        print(f"  [OK] Renamed active policies directory: {new_active.relative_to(repo_root)}")

    # 2. Update and rename policies
    old_policies = policies_dir / old_agent_id
    new_policies = policies_dir / new_agent_id
    if old_policies.exists():
        if new_policies.exists():
            shutil.rmtree(new_policies)
        old_policies.rename(new_policies)
        print(f"  [OK] Renamed policy definitions directory: {new_policies.relative_to(repo_root)}")

    # 3. Update agent_id in all JSON policy files inside new_policies and new_active
    updated_files = 0
    for target_dir in [new_active, new_policies]:
        if not target_dir.exists():
            continue
        for json_file in target_dir.glob("*.json"):
            try:
                content = json_file.read_text(encoding="utf-8")
                if old_agent_id in content:
                    updated = content.replace(f'"{old_agent_id}"', f'"{new_agent_id}"')
                    json_file.write_text(updated, encoding="utf-8")
                    updated_files += 1
            except Exception as e:
                print(f"  [WARN] Failed updating {json_file.name}: {e}")

    print(f"  [OK] Updated agent_id in {updated_files} policy file(s).")

    # 4. Copy template documents to active .md documents if requested
    if create_docs:
        docs_created = 0
        for template_file in repo_root.glob("docs/**/*.template.md"):
            # Target path replaces .template.md with .md
            dest_name = template_file.name.replace(".template.md", ".md")
            dest_file = template_file.parent / dest_name
            if not dest_file.exists():
                shutil.copy2(template_file, dest_file)
                docs_created += 1
                print(f"  [OK] Created document: {dest_file.relative_to(repo_root)}")
            else:
                print(f"  [SKIP] Document already exists: {dest_file.relative_to(repo_root)}")

        print(f"  [OK] Generated {docs_created} initial project document(s) from templates.")

    print(f"\nProject initialization complete! You can now start with Step 2 (Spark & Ideation).")
    print(f"To run governance decisions, use agent-id: '{new_agent_id}'\n")

def main():
    parser = argparse.ArgumentParser(description="Initialize a new project from sidpa-template")
    parser.add_argument("--name", required=True, help="New project name (e.g. 'my-awesome-app')")
    parser.add_argument("--skip-docs", action="store_true", help="Skip copying .template.md files to active .md files")
    args = parser.parse_args()

    init_project(args.name, create_docs=not args.skip_docs)

if __name__ == "__main__":
    main()

