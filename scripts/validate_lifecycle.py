"""Validate a SIDPA project against the unified 18-stage lifecycle.

Usage:
    python scripts/validate_lifecycle.py [--root .] [--strict]

Exit code 1 if an ordering invariant is violated (or, with --strict, if any
stage lacks evidence or a policy shape is missing).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from pmbok.lifecycle import format_report, validate_project  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(repo_root))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    rep = validate_project(args.root)
    print(format_report(rep))
    if not rep.ok:
        return 1
    if args.strict and (rep.stages_present < 18 or rep.missing_policies or rep.folder_gaps):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

