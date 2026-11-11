"""Adjudicate approve-subsidiary-plan gates for Resource foundation pack (user accept)."""
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
PMP = REPO / "docs" / "project-docs" / "Project-Management-Plan.md"
REG = REPO / "docs" / "registers" / "Project-Status-Register.md"
CLI = REPO / ".venv" / "Scripts" / "agent-learn.exe"
DATE = "2026-11-10"
TASK_ID = "approve-subsidiary-plan"
POLICY_ID = "1c0b25f8-af6e-4573-a101-9f5568f28792"

ARTIFACTS = [
    ("7c0p-pillar-overview", MP / "resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md", "../../../gates"),
    ("7c1-role-catalogue", MP / "resource-baseline/foundation/Resource-Role-Catalogue.md", "../../../gates"),
    ("7c2-capacity", MP / "resource-baseline/foundation/Resource-Capacity-Estimates.md", "../../../gates"),
    ("7c3-tooling", MP / "resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md", "../../../gates"),
    ("7c4-charter", MP / "resource-baseline/foundation/Resource-Team-Operating-Charter.md", "../../../gates"),
    ("7c5-utilization", MP / "resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md", "../../../gates"),
    ("7c6-domain-checklist", MP / "resource-baseline/foundation/Resource-Domain-Checklist.md", "../../../gates"),
    ("7c8-pack-manifest", MP / "resource-baseline/Resource-Foundation-Pack-Manifest.md", "../../gates"),
    ("resource-management-plan", MP / "Resource-Management-Plan.md", "../gates"),
]

STATUS_BODY = (
    "**Status:** **Approved ({date})** — `approve-subsidiary-plan` accepted `approve_plan` on {date} "
    f"(policy `{POLICY_ID}`, human acceptance). "
    "Gate record: [approve-subsidiary-plan-resource-{key}-{date}.adjudication.json]({link}).\n"
)

FOUNDATION_STATUS_OLD = re.compile(r"\*\*Status:\*\* Draft for review[^\n]*\n")
RESOURCE_PLAN_OLD = re.compile(
    r"\*\*Status:\*\* \*\*Draft\*\* — subsidiary `approve-subsidiary-plan` \*\*pending\*\* for foundation pack\.\s*\n"
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
        stem = f"{TASK_ID}-resource-{key}-{DATE}"
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
        if key == "resource-management-plan":
            if RESOURCE_PLAN_OLD.search(text):
                text = RESOURCE_PLAN_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
                doc_path.write_text(text, encoding="utf-8")
        else:
            if FOUNDATION_STATUS_OLD.search(text):
                text = FOUNDATION_STATUS_OLD.sub(STATUS_BODY.format(date=DATE, key=key, link=link), text, count=1)
            text = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", text, count=1, flags=re.M)
            doc_path.write_text(text, encoding="utf-8")

    foundation_files = [
        "Resource-Pillar-Overview-and-Trace.md",
        "Resource-Role-Catalogue.md",
        "Resource-Capacity-Estimates.md",
        "Resource-Tooling-and-Assignment-Register.md",
        "Resource-Team-Operating-Charter.md",
        "Resource-Utilization-and-Control-Protocol.md",
        "Resource-Domain-Checklist.md",
    ]
    hashes = {name: sha256_file(MP / "resource-baseline/foundation" / name) for name in foundation_files}

    manifest = MP / "resource-baseline/Resource-Foundation-Pack-Manifest.md"
    mtext = manifest.read_text(encoding="utf-8")
    if "pack_status: pending" in mtext:
        mtext = mtext.replace("pack_status: pending", "pack_status: approved", 1)
    elif "pack_status: draft_complete" in mtext:
        mtext = mtext.replace("pack_status: draft_complete", "pack_status: approved", 1)
    if "approval_status:" not in mtext.split("---", 2)[0]:
        mtext = mtext.replace("pack_status: approved", "pack_status: approved\napproval_status: approved", 1)
    else:
        mtext = re.sub(r"^approval_status: pending\s*$", "approval_status: approved", mtext, count=1, flags=re.M)
    if "rollup_completed:" not in mtext.split("---", 2)[0]:
        mtext = mtext.replace(
            "owner_role: Project Manager",
            f'owner_role: Project Manager\nrollup_completed: "{DATE}"',
            1,
        )
    pack_gate = f"../../gates/{TASK_ID}-resource-7c8-pack-manifest-{DATE}.adjudication.json"
    if "pack_approved:" not in mtext:
        header_end = mtext.find("---", mtext.find("---") + 3)
        insert = f'pack_approved: "{DATE}"\npack_approval_gate: "{pack_gate}"\n'
        mtext = mtext[:header_end] + insert + mtext[header_end:]

    status_insert = STATUS_BODY.format(date=DATE, key="7c8-pack-manifest", link=pack_gate)
    if f"Approved ({DATE})" not in mtext.split("\n", 20)[0:20]:
        title_end = mtext.find("\n\n", mtext.find("# Resource Foundation Pack"))
        if title_end > 0 and "Approved (" not in mtext[: title_end + 50]:
            mtext = mtext[: title_end + 2] + status_insert + "\n" + mtext[title_end + 2 :]

    for substage in ("| **draft_complete** |", "| draft_complete |"):
        while substage in mtext:
            mtext = mtext.replace(substage, f"| **approved ({DATE})** |", 1)

    mtext = mtext.replace("| pending |", f"| **approved ({DATE})** |", 1)
    mtext = mtext.replace(
        "| 7.C-7 | Pack roll-up | Artifacts reviewed; registry complete | pending |",
        f"| 7.C-7 | Pack roll-up | Artifacts reviewed; registry complete | **complete ({DATE})** |",
    )
    mtext = mtext.replace(
        "| 7.C-8 | Resource plan approval | Human approval under configured plan gate | pending |",
        f"| 7.C-8 | Resource plan approval | `approve-subsidiary-plan` | **approved ({DATE})** |",
    )

    for name, digest in hashes.items():
        pattern = rf"(\| {re.escape(name)} \|[^|]+\|) (?:draft_complete|pending approval)( \| PM / {DATE} \|) pending approval"
        repl = rf"\1 approved ({DATE}) \2 `{digest}`"
        mtext = re.sub(pattern, repl, mtext, count=1)
        pattern2 = rf"(\| {re.escape(name)} \|[^|]+\|) draft_complete \| PM / {DATE} \| pending approval"
        if pattern2:
            mtext = re.sub(
                pattern2,
                lambda m, d=digest: f"{m.group(1)} approved ({DATE}) | PM / {DATE} | `{d}`",
                mtext,
                count=1,
            )

    mtext = mtext.replace(
        "| Artifact | Substage | Review status | Reviewer / date | SHA-256 after approval |",
        "| Artifact | Substage | Version | Approval status | SHA-256 after approval ({}) |".format(DATE),
    )
    manifest.write_text(mtext, encoding="utf-8")

    rmp = MP / "Resource-Management-Plan.md"
    rt = rmp.read_text(encoding="utf-8")
    rt = rt.replace(
        "**Pack manifest:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) — **`pack_status: pending`**; foundation artifacts **draft_complete 2026-11-10**.",
        f"**Pack manifest:** [Resource-Foundation-Pack-Manifest.md](resource-baseline/Resource-Foundation-Pack-Manifest.md) — **v1.0.0**, **`pack_status: approved`** (7.C-8 complete {DATE}).",
    )
    if "## 5. Approved resource baseline roll-up" not in rt:
        rt = rt.replace(
            "## 4. Review & governance invariant",
            f"""## 4. Approved resource baseline roll-up ({DATE})

| Element | Value |
|---|---|
| CP labor ROM | **€50,610** contractor market ↔ **CAT-LAB** |
| Roles | R-PLT, R-REL, R-SEC, R-SRE, R-QA, R-PM, R-ARC + **V-AGT** |
| Gate record | [approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json](../gates/approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json) |
| PMP next step | Register in [Project-Management-Plan.md](../Project-Management-Plan.md) §3.3 under **`approve-pmp`** |

## 5. Review & governance invariant""",
        )
    rt = rt.replace(
        "Integrates into [Project-Management-Plan.md](../Project-Management-Plan.md) after **7.C-8** subsidiary approval and PMP register update. **Draft_complete** does not authorize hiring or contractor SOWs.",
        "Integrates into [Project-Management-Plan.md](../Project-Management-Plan.md). **Approved** resource baseline does not authorize hiring or contractor SOWs without Stage 8 and procurement gates.",
    )
    rmp.write_text(rt, encoding="utf-8")

    if PMP.is_file():
        pt = PMP.read_text(encoding="utf-8")
        pt = pt.replace(
            "### 2.9.1 Resource Management Plan\n**Document Link:** [management-plans/Resource-Management-Plan.md](management-plans/Resource-Management-Plan.md)\n- **Summary:** Formulated Resource Management Plan addressing Formalize PMBOK 8 planning baselines, Generate verified subsidiary management plans, Integrate into Project Management Plan (PMP)....",
            f"""### 2.9.1 Resource Management Plan

**Document Link:** [management-plans/Resource-Management-Plan.md](management-plans/Resource-Management-Plan.md)

| Roll-up item | Record |
|---|---|
| Pack manifest | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0**, `pack_status: approved` |
| CP labor ROM | **€50,610** contractor market |
| Subsidiary gate | [approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json](gates/approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json) |
| PMP register | §3.3 — integrated **{DATE}** |
| Execution | **Stage 8** not issued — ROM does not authorize SOWs |""",
        )
        pt = pt.replace("### 3.3 Resource (7.C — draft_complete)", f"### 3.3 Resource (7.C)")
        pt = pt.replace("| Baseline identifier | `PMP-BL-v1.0.0` (resource pack draft) |", "| Baseline identifier | `PMP-BL-v1.0.0` |")
        pt = pt.replace(
            "| Subsidiary approval | **7.C-8** — `approve-subsidiary-plan` **pending** |",
            f"| Subsidiary plan approval | {DATE} — policy `{POLICY_ID}` |",
        )
        if "Gate record" not in pt[pt.find("### 3.3 Resource"): pt.find("### 3.4 Cost")]:
            pt = pt.replace(
                "| Manifest | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0** |\n| CP labor ROM |",
                f"| Manifest | [Resource-Foundation-Pack-Manifest.md](management-plans/resource-baseline/Resource-Foundation-Pack-Manifest.md) **v1.0.0** |\n"
                f"| Gate record | [approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json](gates/approve-subsidiary-plan-resource-resource-management-plan-{DATE}.adjudication.json) |\n"
                f"| CP labor ROM |",
            )
        PMP.write_text(pt, encoding="utf-8")

    if REG.is_file():
        rt = REG.read_text(encoding="utf-8")
        rt = rt.replace(
            "Resource + Cost foundations **draft_complete**",
            "Resource + Cost foundations **approved**",
        )
        rt = rt.replace(
            "| 7.C | Resource foundation | 1 | Pack **draft_complete** | — |",
            f"| 7.C | Resource foundation | 1 | Pack **approved** {DATE} | — |",
        )
        REG.write_text(rt, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(json.dumps(hashes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
