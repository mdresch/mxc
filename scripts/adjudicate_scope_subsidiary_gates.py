"""Adjudicate approve-subsidiary-plan gates for Scope foundation pack (user accept)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATES = REPO / "docs" / "project-docs" / "gates"
MP = REPO / "docs" / "project-docs" / "management-plans"
CLI = REPO / ".venv" / "Scripts" / "agent-learn.exe"
DATE = "2026-11-10"
TASK_ID = "approve-subsidiary-plan"
POLICY_ID = "1c0b25f8-af6e-4573-a101-9f5568f28792"

ARTIFACTS = [
    ("7a0p-pillar-overview", MP / "scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md", "../../../gates"),
    ("7a1-scope-statement", MP / "scope-baseline/foundation/Scope-Project-Scope-Statement.md", "../../../gates"),
    ("7a2-wbs-dictionary", MP / "scope-baseline/foundation/Scope-WBS-Dictionary.md", "../../../gates"),
    ("7a3-monitor-control", MP / "scope-baseline/foundation/Scope-Monitor-Control-Scope.md", "../../../gates"),
    ("7a4-validate-scope", MP / "scope-baseline/foundation/Scope-Validate-Scope.md", "../../../gates"),
    ("7a5-domain-checklist", MP / "scope-baseline/foundation/Scope-Domain-Checklist.md", "../../../gates"),
    ("7a7-pack-manifest", MP / "scope-baseline/Scope-Foundation-Pack-Manifest.md", "../../gates"),
    ("scope-management-plan", MP / "Scope-Management-Plan.md", "../gates"),
]

STATUS_BODY = (
    "**Status:** **Approved ({date})** — `approve-subsidiary-plan` accepted `approve_plan` on {date} "
    f"(policy `{POLICY_ID}`, human acceptance). "
    "Gate record: [approve-subsidiary-plan-scope-{key}-{date}.adjudication.json]({link}).\n"
)

FOUNDATION_STATUS_OLD = re.compile(r"\*\*Status:\*\* Draft for review[^\n]*\n")

SCOPE_PLAN_OLD = re.compile(
    r"\*\*Status:\*\* Draft — foundation pack populated from ADR/BRD/FDD/epic 001–006; pending subsidiary-plan gate and PMP roll-up\.\s*\n"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    env = {
        **dict(__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(REPO / "data" / "agent-learning" / "store"),
    }
    summary: list[dict] = []

    for key, doc_path, gate_prefix in ARTIFACTS:
        stem = f"{TASK_ID}-scope-{key}-{DATE}"
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
                    TASK_ID,
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
                "artifact": key,
                "status": data.get("status"),
                "selected": (data.get("selected_action") or {}).get("id"),
                "adj": str(adj_path.relative_to(REPO)),
            }
        )

        link = f"{gate_prefix}/{stem}.adjudication.json"
        text = doc_path.read_text(encoding="utf-8")
        if FOUNDATION_STATUS_OLD.search(text) or key in ("7a7-pack-manifest",):
            if key == "scope-management-plan":
                if SCOPE_PLAN_OLD.search(text):
                    text = SCOPE_PLAN_OLD.sub(
                        STATUS_BODY.format(date=DATE, key=key, link=link),
                        text,
                        count=1,
                    )
                elif f"Approved ({DATE})" not in text:
                    text += "\n" + STATUS_BODY.format(date=DATE, key=key, link=link)
            elif "**Status:**" in text.split("\n", 30)[0] or "**Status:**" in text[:800]:
                text, n = FOUNDATION_STATUS_OLD.subn(
                    STATUS_BODY.format(date=DATE, key=key, link=link),
                    text,
                    count=1,
                )
                if n == 0 and f"Approved ({DATE})" not in text:
                    # manifest may use different draft wording
                    text = re.sub(
                        r"(?m)^\*\*Status:\*\*[^\n]*\n",
                        STATUS_BODY.format(date=DATE, key=key, link=link),
                        text,
                        count=1,
                    )
            text = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", text, count=1, flags=re.M)
            doc_path.write_text(text, encoding="utf-8")
        elif key == "scope-management-plan":
            if SCOPE_PLAN_OLD.search(text):
                text = SCOPE_PLAN_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
                doc_path.write_text(text, encoding="utf-8")

    # WBS + validate scope pack row
    wbs = MP / "scope-baseline/foundation/Scope-WBS-Dictionary.md"
    wbs_text = wbs.read_text(encoding="utf-8")
    wbs_text = wbs_text.replace(
        "| 2.1 | 2.0 | — | Scope foundation pack (7.A) | `approve-subsidiary-plan` | PM | draft |",
        f"| 2.1 | 2.0 | — | Scope foundation pack (7.A) | `approve-subsidiary-plan` | PM | approved ({DATE}) |",
    )
    wbs.write_text(wbs_text, encoding="utf-8")

    val = MP / "scope-baseline/foundation/Scope-Validate-Scope.md"
    val_text = val.read_text(encoding="utf-8")
    val_text = val_text.replace(
        "| 2.1 | — | Scope foundation pack | Pack 7.A | `approve-subsidiary-plan` (pending) | `scope-baseline/foundation/` |",
        f"| 2.1 | — | Scope foundation pack | Pack 7.A | `approve-subsidiary-plan` ({DATE}) | `scope-baseline/foundation/` |",
    )
    val.write_text(val_text, encoding="utf-8")

    # Manifest post-approval hashes and 7.A-7
    manifest = MP / "scope-baseline/Scope-Foundation-Pack-Manifest.md"
    mtext = manifest.read_text(encoding="utf-8")
    foundation_files = [
        "Scope-Pillar-Overview-and-Trace.md",
        "Scope-Project-Scope-Statement.md",
        "Scope-WBS-Dictionary.md",
        "Scope-Monitor-Control-Scope.md",
        "Scope-Validate-Scope.md",
        "Scope-Domain-Checklist.md",
    ]
    hashes = {name: sha256_file(MP / "scope-baseline/foundation" / name) for name in foundation_files}

    mtext = mtext.replace('pack_status: rolled_up_draft', 'pack_status: approved')
    mtext = mtext.replace(
        "| Next gate | **7.A-7** — `approve-subsidiary-plan` (human adjudication) |",
        f"| Subsidiary approval | **7.A-7** — `approve-subsidiary-plan` **Approved ({DATE})** |",
    )
    for name, digest in hashes.items():
        pattern = rf"(\| {re.escape(name)} \|[^|]+\|[^|]+\|) [^|]+(\| `)[a-f0-9]{{64}}(` \|)"

        def _repl(m: re.Match, d: str = digest) -> str:
            return f"{m.group(1)} approved ({DATE}) {m.group(2)}{d}{m.group(3)}"

        mtext = re.sub(pattern, _repl, mtext, count=1)

    mtext = mtext.replace("| 7.A-7 | Scope plan approval | `approve-subsidiary-plan` | **pending** |", f"| 7.A-7 | Scope plan approval | `approve-subsidiary-plan` | **approved ({DATE})** |")
    for substage in ("7.A-0P", "7.A-1", "7.A-2", "7.A-3", "7.A-4", "7.A-5"):
        mtext = mtext.replace(f"| **rolled_up** |", f"| **approved ({DATE})** |", 1)

    mtext = mtext.replace(
        "**Reviewer / approval date:** TBD until `approve-subsidiary-plan` adjudication. After approval, replace roll-up hashes with **SHA-256 after approval** per rule 2.",
        f"**Reviewer / approval date:** **{DATE}** — subsidiary pack approved under `approve-subsidiary-plan`; registry shows **SHA-256 after approval**.",
    )
    mtext = mtext.replace(
        "| Q-SCOPE-003 | Manifest | Run `approve-subsidiary-plan` | PM | open |",
        f"| Q-SCOPE-003 | Manifest | Run `approve-subsidiary-plan` | PM | **closed ({DATE})** |",
    )
    pack_gate = f"../../gates/{TASK_ID}-scope-7a7-pack-manifest-{DATE}.adjudication.json"
    if "pack_approval_gate:" not in mtext:
        mtext = mtext.replace(
            'rollup_completed: "2026-11-10"',
            f'rollup_completed: "2026-11-10"\npack_approved: "{DATE}"\npack_approval_gate: "{pack_gate}"',
        )
    manifest.write_text(mtext, encoding="utf-8")

    # Scope management plan section 2 pointer
    smp = MP / "Scope-Management-Plan.md"
    stext = smp.read_text(encoding="utf-8")
    stext = stext.replace(
        "**Pack manifest:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) — **v1.2.0**, **`pack_status: rolled_up_draft`** (7.A-6 complete 2026-11-10); **7.A-7** `approve-subsidiary-plan` pending.",
        f"**Pack manifest:** [Scope-Foundation-Pack-Manifest.md](scope-baseline/Scope-Foundation-Pack-Manifest.md) — **v1.2.0**, **`pack_status: approved`** (7.A-7 complete {DATE}).",
    )
    smp.write_text(stext, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(json.dumps(hashes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
