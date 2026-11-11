"""Adjudicate approve-subsidiary-plan gates for Cost foundation pack (user accept)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from gate_common import frontmatter_has, resolve_agent_learn_cli

REPO = Path(__file__).resolve().parents[1]
GATES = REPO / "docs" / "project-docs" / "gates"
MP = REPO / "docs" / "project-docs" / "management-plans"
PMP = REPO / "docs" / "project-docs" / "Project-Management-Plan.md"
REG = REPO / "docs" / "registers" / "Project-Status-Register.md"
CLI = resolve_agent_learn_cli(REPO)
DATE = "2026-11-10"
TASK_ID = "approve-subsidiary-plan"
POLICY_ID = "1c0b25f8-af6e-4573-a101-9f5568f28792"

ARTIFACTS = [
    ("7d0p-pillar-overview", MP / "cost-baseline/foundation/Cost-Pillar-Overview-and-Trace.md", "../../../gates"),
    ("7d1-categories", MP / "cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md", "../../../gates"),
    ("7d2-estimates", MP / "cost-baseline/foundation/Cost-Estimates-by-Category.md", "../../../gates"),
    ("7d3-staged-budget", MP / "cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md", "../../../gates"),
    ("7d4-variance", MP / "cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md", "../../../gates"),
    ("7d5-domain-checklist", MP / "cost-baseline/foundation/Cost-Domain-Checklist.md", "../../../gates"),
    ("7d7-pack-manifest", MP / "cost-baseline/Cost-Foundation-Pack-Manifest.md", "../../gates"),
    ("cost-management-plan", MP / "Cost-Management-Plan.md", "../gates"),
]

STATUS_BODY = (
    "**Status:** **Approved ({date})** — `approve-subsidiary-plan` accepted `approve_plan` on {date} "
    f"(policy `{POLICY_ID}`, human acceptance). "
    "Gate record: [approve-subsidiary-plan-cost-{key}-{date}.adjudication.json]({link}).\n"
)

FOUNDATION_STATUS_OLD = re.compile(r"\*\*Status:\*\* Draft for review[^\n]*\n")
COST_MANIFEST_OLD = re.compile(
    r"\*\*Status:\*\* \*\*Draft complete \(2026-11-10\)\*\* — foundation populated[^\n]*\n"
)
COST_PLAN_OLD = re.compile(
    r"\*\*Status:\*\* \*\*Draft complete \(2026-11-10\)\*\* — foundation rolled into this plan and PMP; \*\*7\.D-7\*\* subsidiary approval \*\*pending\*\*\.\s*\n"
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
        stem = f"{TASK_ID}-cost-{key}-{DATE}"
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
        if key == "cost-management-plan":
            if COST_PLAN_OLD.search(text):
                text = COST_PLAN_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
                doc_path.write_text(text, encoding="utf-8")
        elif key == "7d7-pack-manifest":
            if COST_MANIFEST_OLD.search(text):
                text = COST_MANIFEST_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
            text = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", text, count=1, flags=re.M)
            doc_path.write_text(text, encoding="utf-8")
        else:
            if FOUNDATION_STATUS_OLD.search(text):
                text = FOUNDATION_STATUS_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
            text = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", text, count=1, flags=re.M)
            doc_path.write_text(text, encoding="utf-8")

    foundation_files = [
        "Cost-Pillar-Overview-and-Trace.md",
        "Cost-Categories-and-Estimating-Basis.md",
        "Cost-Estimates-by-Category.md",
        "Cost-Staged-Budget-and-Baseline.md",
        "Cost-Variance-and-Control-Protocol.md",
        "Cost-Domain-Checklist.md",
    ]
    hashes = {name: sha256_file(MP / "cost-baseline/foundation" / name) for name in foundation_files}

    manifest = MP / "cost-baseline/Cost-Foundation-Pack-Manifest.md"
    mtext = manifest.read_text(encoding="utf-8")
    mtext = mtext.replace("pack_status: draft_complete", "pack_status: approved", 1)
    if not frontmatter_has(mtext, "approval_status"):
        mtext = mtext.replace(
            "pack_status: approved",
            "pack_status: approved\napproval_status: approved",
            1,
        )
    else:
        mtext = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", mtext, count=1, flags=re.M)
    pack_gate = f"../../gates/{TASK_ID}-cost-7d7-pack-manifest-{DATE}.adjudication.json"
    if "pack_approved:" not in mtext:
        mtext = mtext.replace(
            'rollup_completed: "2026-11-10"',
            f'rollup_completed: "2026-11-10"\npack_approved: "{DATE}"\npack_approval_gate: "{pack_gate}"',
        )
    mtext = mtext.replace(
        "| Resource prerequisite | [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) **draft_complete** — contractor market ROM |",
        "| Resource prerequisite | [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) **approved** 2026-11-10 — contractor market ROM |",
    )
    mtext = mtext.replace(
        "| Subsidiary approval | **7.D-7** — `approve-subsidiary-plan` **pending** |",
        f"| Subsidiary approval | **7.D-7** — `approve-subsidiary-plan` **Approved ({DATE})** |",
    )
    mtext = mtext.replace("| Draft cost baseline ID |", "| Cost baseline ID |")
    mtext = mtext.replace("`COST-BL-v1.0.0-draft`", "`COST-BL-v1.0.0`")
    for substage in ("| **draft_complete** |", "| draft_complete |"):
        while substage in mtext and "**approved (" not in mtext[max(0, mtext.find(substage) - 5) : mtext.find(substage) + 40]:
            mtext = mtext.replace(substage, f"| **approved ({DATE})** |", 1)
    mtext = mtext.replace(
        "| 7.D-7 | Cost plan approval | `approve-subsidiary-plan` | **pending** |",
        f"| 7.D-7 | Cost plan approval | `approve-subsidiary-plan` | **approved ({DATE})** |",
    )
    mtext = mtext.replace(
        "Fingerprints below are **SHA-256 at roll-up** (pre–7.D-7 approval).",
        "Fingerprints below are **SHA-256 after approval**.",
    )
    mtext = mtext.replace(
        "| Artifact | Substage | Version | Review status | SHA-256 at roll-up (2026-11-10) |",
        f"| Artifact | Substage | Version | Approval status | SHA-256 after approval ({DATE}) |",
    )
    for name, digest in hashes.items():
        pattern = rf"(\| {re.escape(name)} \|[^|]+\|[^|]+\|) [^|]+(\| `)[a-f0-9]{{64}}(` \|)"

        def _repl(m: re.Match, d: str = digest) -> str:
            return f"{m.group(1)} approved ({DATE}) {m.group(2)}{d}{m.group(3)}"

        mtext = re.sub(pattern, _repl, mtext, count=1)
    mtext = mtext.replace(
        "**Reviewer / approval date:** Roll-up **2026-11-10**; SHA-256 recalculated **after approval** at 7.D-7.",
        f"**Reviewer / approval date:** **{DATE}** — cost foundation pack approved; registry shows **SHA-256 after approval**.",
    )
    mtext = mtext.replace(
        "4. **7.D-7:** Roll into [Cost-Management-Plan.md](../Cost-Management-Plan.md) when subsidiary gate passes.",
        f"4. **7.D-7:** **Complete ({DATE})** — rolled into [Cost-Management-Plan.md](../Cost-Management-Plan.md).",
    )
    mtext = mtext.replace(
        "| [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) | draft_complete | Rates, ROM |",
        f"| [Resource-Foundation-Pack-Manifest.md](../resource-baseline/Resource-Foundation-Pack-Manifest.md) | Approved {DATE} | Rates, ROM |",
    )
    manifest.write_text(mtext, encoding="utf-8")

    # Promote cost baseline ID in staged budget
    staged = MP / "cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md"
    st = staged.read_text(encoding="utf-8")
    st = st.replace("COST-BL-v1.0.0-draft", "COST-BL-v1.0.0")
    st = st.replace(
        "**Not** authorized spend until **7.D-7** and sponsor release.",
        f"**Performance baseline** formalized at **7.D-7** ({DATE}); spend still requires Stage 8 / procurement gates.",
    )
    staged.write_text(st, encoding="utf-8")

    cmp = MP / "Cost-Management-Plan.md"
    ct = cmp.read_text(encoding="utf-8")
    ct = ct.replace(
        "**Pack manifest:** [Cost-Foundation-Pack-Manifest.md](cost-baseline/Cost-Foundation-Pack-Manifest.md) — **v1.1.0**, **`pack_status: draft_complete`** (7.D-6 roll-up **2026-11-10**).",
        f"**Pack manifest:** [Cost-Foundation-Pack-Manifest.md](cost-baseline/Cost-Foundation-Pack-Manifest.md) — **v1.1.0**, **`pack_status: approved`** (7.D-7 complete {DATE}).",
    )
    ct = ct.replace("COST-BL-v1.0.0-draft", "COST-BL-v1.0.0")
    ct = ct.replace(
        "| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **pending** |",
        f"| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **approved ({DATE})** |",
    )
    ct = ct.replace(
        "This subsidiary plan integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Foundation pack approval uses **`approve-subsidiary-plan`**; integrated PMP lock uses **`approve-pmp`**. **Draft_complete** cost baseline does **not** authorize spend or override Stage 8 rules.",
        "This subsidiary plan integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). Foundation pack approval uses **`approve-subsidiary-plan`**; integrated PMP lock uses **`approve-pmp`**. **Approved** cost baseline does **not** authorize invoices or override Stage 8 rules.",
    )
    if "| Gate record |" not in ct:
        ct = ct.replace(
            f"| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **approved ({DATE})** |",
            f"| Gate record | [approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json](../gates/approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json) |\n"
            f"| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **approved ({DATE})** |",
        )
    cmp.write_text(ct, encoding="utf-8")

    if PMP.is_file():
        pt = PMP.read_text(encoding="utf-8")
        pt = pt.replace(
            "| Pack manifest | [Cost-Foundation-Pack-Manifest.md](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md) **v1.1.0**, `pack_status: draft_complete` |",
            "| Pack manifest | [Cost-Foundation-Pack-Manifest.md](management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md) **v1.1.0**, `pack_status: approved` |",
        )
        pt = pt.replace(
            "| Subsidiary gate | **7.D-7** `approve-subsidiary-plan` **pending** |",
            f"| Subsidiary gate | [approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json](gates/approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json) |",
        )
        pt = pt.replace("| PMP register | §3.4 — integrated **2026-11-10** (draft roll-up) |", f"| PMP register | §3.4 — integrated **{DATE}** |")
        pt = pt.replace("### 3.4 Cost (7.D — draft roll-up 2026-11-10)", "### 3.4 Cost (7.D)")
        pt = pt.replace("| Cost baseline ID (draft) | `COST-BL-v1.0.0-draft` |", "| Cost baseline ID | `COST-BL-v1.0.0` |")
        pt = pt.replace(
            "| Subsidiary plan | [Cost-Management-Plan.md](management-plans/Cost-Management-Plan.md) — **draft_complete** |",
            "| Subsidiary plan | [Cost-Management-Plan.md](management-plans/Cost-Management-Plan.md) — **approved** |",
        )
        pt = pt.replace(
            "| Subsidiary approval | **7.D-7** — `approve-subsidiary-plan` **pending** |",
            f"| Subsidiary plan approval | {DATE} — policy `{POLICY_ID}` |",
        )
        if "Gate record" not in pt[pt.find("### 3.4 Cost"): pt.find("## 4. Feedback")]:
            pt = pt.replace(
                "| Subsidiary plan approval |",
                f"| Gate record | [approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json](gates/approve-subsidiary-plan-cost-cost-management-plan-{DATE}.adjudication.json) |\n| Subsidiary plan approval |",
                1,
            )
        PMP.write_text(pt, encoding="utf-8")

    if REG.is_file():
        rt = REG.read_text(encoding="utf-8")
        rt = rt.replace(
            "cost rolled into PMP §3.4 (**€58,710** draft perf.)",
            "cost rolled into PMP §3.4 (**€58,710** perf. baseline)",
        )
        rt = rt.replace(
            "| 7.D | Cost foundation | 1 | Pack **draft_complete**; PMP §3.4 | — |",
            f"| 7.D | Cost foundation | 1 | Pack **approved** {DATE}; PMP §3.4 | — |",
        )
        REG.write_text(rt, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(json.dumps(hashes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
