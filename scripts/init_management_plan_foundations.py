"""Instantiate SIDPA management-plan foundation templates in a project."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKS = ("scope", "schedule", "resource", "cost")


def initialize_foundation_packs(
    target_root: Path,
    project_name: str,
    packs: tuple[str, ...] = PACKS,
    template_root: Path | None = None,
) -> tuple[int, int]:
    """Copy missing pack templates into a project without overwriting work."""
    target_root = target_root.resolve()
    if not target_root.is_dir():
        raise NotADirectoryError(f"Target project root does not exist: {target_root}")
    if not (target_root / "docs").is_dir():
        raise FileNotFoundError(f"Target project has no docs directory: {target_root / 'docs'}")
    invalid_packs = set(packs).difference(PACKS)
    if invalid_packs:
        raise ValueError(f"Unknown management-plan pack(s): {', '.join(sorted(invalid_packs))}")

    source_root = (template_root or REPOSITORY_ROOT / "templates" / "management-plans").resolve()
    destination_root = target_root / "docs" / "project-docs" / "management-plans"
    display_name = project_name.strip()
    if not display_name:
        raise ValueError("Project name must not be empty")
    project_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", display_name).lower().strip("-")
    if not project_slug:
        raise ValueError("Project name must contain at least one letter or number")
    replacements = {
        "{{PROJECT_NAME}}": display_name,
        "{{PROJECT_SLUG}}": project_slug,
        "{{BASELINE_ID}}": "PMP-BL-v1.0.0",
    }

    created = 0
    skipped = 0
    for pack in packs:
        pack_root = source_root / f"{pack}-baseline"
        templates = sorted(pack_root.rglob("*.template.md"))
        if not templates:
            raise FileNotFoundError(f"No templates found for {pack} pack under {pack_root}")
        for template_path in templates:
            relative_path = template_path.relative_to(source_root)
            output_path = destination_root / relative_path.with_name(
                template_path.name.removesuffix(".template.md") + ".md"
            )
            if output_path.exists():
                skipped += 1
                continue
            content = template_path.read_text(encoding="utf-8")
            for token, value in replacements.items():
                content = content.replace(token, value)
            content = content.replace(".template.md", ".md")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8", newline="\n")
            created += 1
    return created, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create missing scope, schedule, resource, and cost foundation-pack documents."
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="Existing project root (defaults to the SIDPA template repository).",
    )
    parser.add_argument(
        "--template-root",
        type=Path,
        default=None,
        help="Custom root directory holding management-plans templates.",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Display name used in generated documents (defaults to the target folder name).",
    )
    parser.add_argument(
        "--packs",
        nargs="+",
        choices=PACKS,
        default=list(PACKS),
        help="Foundation packs to initialize.",
    )
    args = parser.parse_args()
    project_name = args.project_name or args.target_root.resolve().name
    created, skipped = initialize_foundation_packs(
        args.target_root,
        project_name,
        tuple(args.packs),
        template_root=args.template_root,
    )
    print(f"Foundation-pack documents created: {created}; already present and preserved: {skipped}.")


if __name__ == "__main__":
    main()
