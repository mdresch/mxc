"""Adjudicate approve-subsidiary-plan gates for Schedule foundation pack (user accept)."""
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
    ("7b0p-pillar-overview", MP / "schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md", "../../../gates"),
    ("7b1-basis-estimates", MP / "schedule-baseline/foundation/Schedule-Basis-of-Estimates.md", "../../../gates"),
    ("7b2-network", MP / "schedule-baseline/foundation/Schedule-Network-Phase1.md", "../../../gates"),
    ("7b2a-activity-list", MP / "schedule-baseline/foundation/Schedule-Activity-List-Phase1.md", "../../../gates"),
    ("7b2b-gantt", MP / "schedule-baseline/foundation/Schedule-Gantt-Phase1.md", "../../../gates"),
    ("7b3-reserve", MP / "schedule-baseline/foundation/Schedule-Reserve-Register.md", "../../../gates"),
    ("7b4-wbs-forecast", MP / "schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md", "../../../gates"),
    ("7b5-domain-checklist", MP / "schedule-baseline/foundation/Schedule-Domain-Checklist.md", "../../../gates"),
    ("7b7-pack-manifest", MP / "schedule-baseline/Schedule-Foundation-Pack-Manifest.md", "../../gates"),
    ("schedule-management-plan", MP / "Schedule-Management-Plan.md", "../gates"),
]

STATUS_BODY = (
    "**Status:** **Approved ({date})** — `approve-subsidiary-plan` accepted `approve_plan` on {date} "
    f"(policy `{POLICY_ID}`, human acceptance). "
    "Gate record: [approve-subsidiary-plan-schedule-{key}-{date}.adjudication.json]({link}).\n"
)

FOUNDATION_STATUS_OLD = re.compile(r"\*\*Status:\*\* Draft for review[^\n]*\n")

SCHEDULE_PLAN_OLD = re.compile(
    r"\*\*Status:\*\* Draft — Phase-1 schedule foundation populated from approved scope WBS \*\*001–006\*\*; pending subsidiary-plan gate and PMP roll-up\.\s*\n"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    env = {
        **dict(__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(REPO / "data" / "agent-learning" / "store"),
    }
    summary: list[dict] = []

    for key, doc_path, gate_prefix in ARTIFACTS:
        stem = f"{TASK_ID}-schedule-{key}-{DATE}"
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
        if key == "schedule-management-plan":
            if SCHEDULE_PLAN_OLD.search(text):
                text = SCHEDULE_PLAN_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
                doc_path.write_text(text, encoding="utf-8")
        elif FOUNDATION_STATUS_OLD.search(text) or key == "7b7-pack-manifest":
            if FOUNDATION_STATUS_OLD.search(text):
                text = FOUNDATION_STATUS_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
            elif f"Approved ({DATE})" not in text and key == "7b7-pack-manifest":
                title_end = text.find("\n\n", text.find("# Schedule Foundation Pack"))
                if title_end > 0:
                    insert = STATUS_BODY.format(date=DATE, key=key, link=link) + "\n"
                    text = text[: title_end + 2] + insert + text[title_end + 2 :]
            text = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", text, count=1, flags=re.M)
            doc_path.write_text(text, encoding="utf-8")

    # Domain checklist: subsidiary row
    dom = MP / "schedule-baseline/foundation/Schedule-Domain-Checklist.md"
    dom_text = dom.read_text(encoding="utf-8")
    dom_text = dom_text.replace(
        "| Subsidiary plan human approval | `approve-subsidiary-plan` on pack | PM | **pending** | Run 7.B-7 gate |",
        f"| Subsidiary plan human approval | `approve-subsidiary-plan` on pack | PM | **pass** | Approved {DATE} |",
    )
    dom.write_text(dom_text, encoding="utf-8")

    foundation_files = [
        "Schedule-Pillar-Overview-and-Trace.md",
        "Schedule-Basis-of-Estimates.md",
        "Schedule-Network-Phase1.md",
        "Schedule-Activity-List-Phase1.md",
        "Schedule-Gantt-Phase1.md",
        "Schedule-Reserve-Register.md",
        "Schedule-Baseline-WBS-Forecast.md",
        "Schedule-Domain-Checklist.md",
    ]
    hashes = {name: sha256_file(MP / "schedule-baseline/foundation" / name) for name in foundation_files}

    manifest = MP / "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
    mtext = manifest.read_text(encoding="utf-8")
    mtext = mtext.replace('pack_status: draft_complete', 'pack_status: approved')
    if "approval_status:" not in mtext.split("---", 2)[0]:
        mtext = mtext.replace('pack_status: approved', 'pack_status: approved\napproval_status: approved', 1)
    mtext = mtext.replace('version: "1.0.0"', 'version: "1.1.0"', 1)
    mtext = mtext.replace(
        "| Next gate | **7.B-7** — `approve-subsidiary-plan` |",
        f"| Subsidiary approval | **7.B-7** — `approve-subsidiary-plan` **Approved ({DATE})** |",
    )
    mtext = mtext.replace(
        "Fingerprints are **SHA-256 at roll-up** (not post–approval).",
        "Fingerprints below are **SHA-256 after approval**.",
    )
    for substage in (
        "| **draft_complete** |",
        "| draft_complete |",
    ):
        while substage in mtext and "**approved (" not in mtext[mtext.find(substage) : mtext.find(substage) + 80]:
            mtext = mtext.replace(substage, f"| **approved ({DATE})** |", 1)

    mtext = mtext.replace("| **complete (draft)** |", "| **complete** |")
    mtext = mtext.replace("| **pending** |", f"| **approved ({DATE})** |", 1)

    for name, digest in hashes.items():
        pattern = rf"(\| {re.escape(name)} \|[^|]+\|[^|]+\|) [^|]+(\| `)[a-f0-9]{{64}}(` \|)"

        def _repl(m: re.Match, d: str = digest) -> str:
            return f"{m.group(1)} approved ({DATE}) {m.group(2)}{d}{m.group(3)}"

        mtext = re.sub(pattern, _repl, mtext, count=1)

    mtext = mtext.replace(
        "**Reviewer / approval date:** TBD until `approve-subsidiary-plan` adjudication.",
        f"**Reviewer / approval date:** **{DATE}** — schedule foundation pack approved; registry shows **SHA-256 after approval**.",
    )
    mtext = mtext.replace(
        "| Q-SCH-004 | Manifest | Run `approve-subsidiary-plan` | PM | open |",
        f"| Q-SCH-004 | Manifest | Run `approve-subsidiary-plan` | PM | **closed ({DATE})** |",
    )
    pack_gate = f"../../gates/{TASK_ID}-schedule-7b7-pack-manifest-{DATE}.adjudication.json"
    if "pack_approved:" not in mtext:
        mtext = mtext.replace(
            'rollup_completed: "2026-11-10"',
            f'rollup_completed: "2026-11-10"\npack_approved: "{DATE}"\npack_approval_gate: "{pack_gate}"',
        )
    mtext = mtext.replace(
        "3. **7.B-6:** All required artifacts present and cross-referenced — **draft roll-up complete**.",
        "3. **7.B-6:** All required artifacts present and cross-referenced — **roll-up complete**.",
    )
    mtext = mtext.replace(
        "4. **7.B-7:** Roll schedule baseline, registry, reserves, and open issues into [Schedule-Management-Plan.md](../Schedule-Management-Plan.md); run **`approve-subsidiary-plan`**.",
        f"4. **7.B-7:** **Complete ({DATE})** — rolled into [Schedule-Management-Plan.md](../Schedule-Management-Plan.md).",
    )
    mtext = mtext.replace(
        "6. Cost and resource foundation packs (7.D / 7.C) may use this forecast as duration input when dependencies are met (schedule **7.B-7** pending).",
        "6. Cost and resource foundation packs (7.D / 7.C) may use this forecast; schedule **7.B-7** **approved**.",
    )
    manifest.write_text(mtext, encoding="utf-8")

    smp = MP / "Schedule-Management-Plan.md"
    stext = smp.read_text(encoding="utf-8")
    stext = stext.replace(
        "**Pack manifest:** [Schedule-Foundation-Pack-Manifest.md](schedule-baseline/Schedule-Foundation-Pack-Manifest.md) — **v1.0.0**, **`pack_status: draft_complete`** (7.B-6 roll-up 2026-11-10); **7.B-7** `approve-subsidiary-plan` pending.",
        f"**Pack manifest:** [Schedule-Foundation-Pack-Manifest.md](schedule-baseline/Schedule-Foundation-Pack-Manifest.md) — **v1.1.0**, **`pack_status: approved`** (7.B-7 complete {DATE}).",
    )
    # Roll-up summary block for PMP
    if "## 7. Approved schedule baseline roll-up" not in stext:
        stext = stext.replace(
            "## 6. Review & governance invariant",
            f"""## 6. Approved schedule baseline roll-up ({DATE})

| Element | Value |
|---|---|
| Integration path | WBS **1.1.1 → … → 1.6.4** per [Schedule-Network-Phase1.md](schedule-baseline/foundation/Schedule-Network-Phase1.md) |
| Likely critical path | **~78 WD** / **~15.6 wks** @ 1 FTE ([Schedule-Baseline-WBS-Forecast.md](schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md)) |
| Reserves | [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md) |
| Agentic execution | [§5 Agentic parallel execution](#5-agentic-parallel-execution-living--added-2026-11-10) (living; not in frozen pack) |
| Gate record | [approve-subsidiary-plan-schedule-schedule-management-plan-{DATE}.adjudication.json](../gates/approve-subsidiary-plan-schedule-schedule-management-plan-{DATE}.adjudication.json) |
| PMP next step | Roll manifest link + constraints into [Project-Management-Plan.md](../Project-Management-Plan.md) under **`approve-pmp`** |

## 7. Review & governance invariant""",
        )
    smp.write_text(stext, encoding="utf-8")

    # Scope WBS governance row for schedule pack
    wbs = MP / "scope-baseline/foundation/Scope-WBS-Dictionary.md"
    wbs_text = wbs.read_text(encoding="utf-8")
    if "| 2.2 |" not in wbs_text:
        wbs_text = wbs_text.replace(
            "| 2.1 | 2.0 | — | Scope foundation pack (7.A) | `approve-subsidiary-plan` | PM | approved (2026-11-10) |",
            "| 2.1 | 2.0 | — | Scope foundation pack (7.A) | `approve-subsidiary-plan` | PM | approved (2026-11-10) |\n"
            f"| 2.2 | 2.0 | — | Schedule foundation pack (7.B) | `approve-subsidiary-plan` | PM | approved ({DATE}) |",
        )
        wbs.write_text(wbs_text, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(json.dumps(hashes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
