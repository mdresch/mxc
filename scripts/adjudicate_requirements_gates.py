"""Adjudicate approve-brd / approve-fdd / approve-user-stories gates (user accept)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from gate_common import resolve_agent_learn_cli

REPO = Path(__file__).resolve().parents[1]
GATES = REPO / "docs" / "project-docs" / "gates"
CLI = resolve_agent_learn_cli(REPO)
DATE = "2026-10-30"

SLUGS = {
    "001": "type-1-hyperv-generation-2",
    "002": "connection-buffering-ingress-gateway",
    "003": "production-base-image",
    "004": "paused-ram-standby",
    "005": "transient-differencing-disk",
    "006": "watermark-pool",
}

GATE_META = {
    "approve-brd": {
        "task_id": "approve-brd",
        "action": "approve_brd",
        "policy_id": "d72b24a8-0fb3-4735-aade-81ec7991c837",
        "doc": lambda n, s: REPO / f"docs/project-docs/Business-Requirements/BRD-{n}-{s}.md",
        "gate_link": lambda n: f"../gates/approve-brd-{n}-{DATE}.adjudication.json",
        "status_old": re.compile(
            r"\*\*Status:\*\* Draft — business rules derived from an Accepted ADR; `approve-brd` has not been run\.\s*\n"
        ),
        "status_new": lambda n, link: (
            f"**Status:** **Approved ({DATE})** — `approve-brd` accepted `approve_brd` on {DATE} "
            f"(policy `d72b24a8-0fb3-4735-aade-81ec7991c837`, human acceptance). "
            f"Gate record: [approve-brd-{n}-{DATE}.adjudication.json]({link}).\n"
        ),
    },
    "approve-fdd": {
        "task_id": "approve-fdd",
        "action": "approve_fdd",
        "policy_id": "ada1bc73-753a-450b-b640-6b6fedd5493c",
        "doc": lambda n, s: REPO / f"docs/project-docs/Functional-Design/FDD-{n}-{s}.md",
        "gate_link": lambda n: f"../gates/approve-fdd-{n}-{DATE}.adjudication.json",
        "status_old": re.compile(
            r"\*\*Status:\*\* Draft — technical design aligned with suite \[FDD\.md\]\(\../../hyperv/architecture/FDD\.md\); `approve-fdd` has not been run\.\s*\n"
        ),
        "status_new": lambda n, link: (
            f"**Status:** **Approved ({DATE})** — `approve-fdd` accepted `approve_fdd` on {DATE} "
            f"(policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). "
            f"Gate record: [approve-fdd-{n}-{DATE}.adjudication.json]({link}).\n"
        ),
    },
    "approve-user-stories": {
        "task_id": "approve-user-stories",
        "action": "approve_user_stories",
        "policy_id": "f864addc-593f-46b1-93e0-0720f6d18a6b",
        "doc": lambda n, s: REPO / f"docs/user-stories/epic-{n}-{s}.md",
        "gate_link": lambda n: f"../project-docs/gates/approve-user-stories-{n}-{DATE}.adjudication.json",
        "status_old": re.compile(
            r"\*\*Status:\*\* Draft — stories trace to suite acceptance criteria where they exist; `approve-user-stories` has not been run\.\s*\n"
        ),
        "status_new": lambda n, link: (
            f"**Status:** **Approved ({DATE})** — `approve-user-stories` accepted `approve_user_stories` on {DATE} "
            f"(policy `f864addc-593f-46b1-93e0-0720f6d18a6b`, human acceptance). "
            f"Gate record: [approve-user-stories-{n}-{DATE}.adjudication.json]({link}).\n"
        ),
    },
}

BRD_SOURCE_OLD = re.compile(
    r"(\*\*Source BRD:\*\* \[BRD-\d{3}\]\([^)]+\))\s*\n"
)
BRD_SOURCE_NEW = r"\1 — Approved ({date}).\n".format(date=DATE)

EPIC_BRD_FDD_OLD = re.compile(
    r"(\*\*Source BRD/FDD:\*\* \[BRD-\d{3}\]\([^)]+\)) / (\[FDD-\d{3}\]\([^)]+\))\s*\n"
)
EPIC_BRD_FDD_NEW = (
    r"\1 — Approved ({date}) / \2 — Approved ({date}).\n".format(date=DATE)
)


def main() -> int:
    env = {
        **dict(**__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(REPO / "data" / "agent-learning" / "store"),
    }
    summary: list[dict] = []

    for task_id, meta in GATE_META.items():
        for num, slug in SLUGS.items():
            stem = f"{task_id}-{num}-{DATE}"
            result_path = GATES / f"{stem}.decision-result.json"
            adj_path = GATES / f"{stem}.adjudication.json"
            if not result_path.is_file():
                print(f"missing {result_path}", file=sys.stderr)
                return 1
            if adj_path.is_file():
                data = json.loads(adj_path.read_text(encoding="utf-8"))
            else:
                proc = subprocess.run(
                    [
                        str(CLI),
                        "task-policy-adjudicate",
                        "--agent-id",
                        "mxc-governance",
                        "--task-id",
                        meta["task_id"],
                        "--decision-result",
                        str(result_path),
                        "--disposition",
                        "accept",
                    ],
                    cwd=str(REPO),
                    env=env,
                    capture_output=True,
                    text=True,
                )
                if proc.returncode != 0:
                    print(proc.stdout, proc.stderr, file=sys.stderr)
                    return proc.returncode
                adj_path.write_text(proc.stdout, encoding="utf-8")
                data = json.loads(proc.stdout)
            summary.append(
                {
                    "gate": task_id,
                    "adr": num,
                    "status": data.get("status"),
                    "selected": (data.get("selected_action") or {}).get("id"),
                    "adj": str(adj_path.relative_to(REPO)),
                }
            )

            doc_path = meta["doc"](num, slug)
            text = doc_path.read_text(encoding="utf-8")
            link = meta["gate_link"](num)
            if meta["status_old"].search(text):
                text, n = meta["status_old"].subn(meta["status_new"](num, link), text, count=1)
                if n != 1:
                    print(f"status not updated in {doc_path}", file=sys.stderr)
                    return 1
                doc_path.write_text(text, encoding="utf-8")
            elif f"Approved ({DATE})" not in text:
                print(f"unexpected status block in {doc_path}", file=sys.stderr)
                return 1

    # FDD: mark source BRD approved
    for num, slug in SLUGS.items():
        fdd = REPO / f"docs/project-docs/Functional-Design/FDD-{num}-{slug}.md"
        text = fdd.read_text(encoding="utf-8")
        if " — Approved" not in text.split("**Source BRD:**")[1].split("\n")[0]:
            text, n = BRD_SOURCE_OLD.subn(BRD_SOURCE_NEW, text, count=1)
            if n != 1:
                print(f"BRD source not updated in {fdd}", file=sys.stderr)
                return 1
            fdd.write_text(text, encoding="utf-8")

    # Epic: mark source BRD/FDD approved
    for num, slug in SLUGS.items():
        epic = REPO / f"docs/user-stories/epic-{num}-{slug}.md"
        text = epic.read_text(encoding="utf-8")
        if " — Approved" not in text.split("**Source BRD/FDD:**")[1].split("\n")[0]:
            text, n = EPIC_BRD_FDD_OLD.subn(EPIC_BRD_FDD_NEW, text, count=1)
            if n != 1:
                print(f"BRD/FDD source not updated in {epic}", file=sys.stderr)
                return 1
            epic.write_text(text, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
