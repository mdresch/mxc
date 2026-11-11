"""Adjudicate approve-pmp gate (sponsor accept) and lock PMP-BL-v1.0.0."""
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
PACKAGE = MP / "PMP-Approval-Package-Manifest.md"
CLI = resolve_agent_learn_cli(REPO)
DATE = "2026-11-10"
TASK_ID = "approve-pmp"
POLICY_ID = "46c60639-c24f-4045-8ace-a3dbe2142e61"
BASELINE = "PMP-BL-v1.0.0"
STEM = f"{TASK_ID}-pmp-bl-v1-0-0-{DATE}"
GATE_REL = f"../../gates/{STEM}.adjudication.json"

OPERATIONAL_PLANS = [
    "Quality-Management-Plan.md",
    "Communications-Management-Plan.md",
    "Risk-Management-Plan.md",
    "Procurement-Management-Plan.md",
    "Stakeholder-Engagement-Plan.md",
]

LOCK_OLD = re.compile(
    r"\*\*Integrated PMP lock:\*\* `approve-pmp` \*\*not yet run\*\*[^\n]*\n",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    env = {
        **dict(__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(REPO / "data" / "agent-learning" / "store"),
    }
    result_path = GATES / f"{STEM}.decision-result.json"
    adj_path = GATES / f"{STEM}.adjudication.json"
    if not result_path.is_file():
        print(f"Run scripts/run_approve_pmp_gate.py first — missing {result_path}", file=sys.stderr)
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

    selected = (data.get("selected_action") or {}).get("id")
    if selected != "approve_pmp":
        print(json.dumps({"error": "adjudication did not select approve_pmp", "data": data}, indent=2), file=sys.stderr)
        return 1

    # --- PMP frontmatter ---
    pt = PMP.read_text(encoding="utf-8")
    if not frontmatter_has(pt, "pmp_approved"):
        pt = pt.replace(
            'governance_policy: "approve-pmp"',
            f'governance_policy: "approve-pmp"\n'
            f'pmp_status: approved\n'
            f'pmp_approved: "{DATE}"\n'
            f'pmp_approval_gate: "gates/{STEM}.adjudication.json"',
            1,
        )
    if LOCK_OLD.search(pt):
        pt = LOCK_OLD.sub(
            f"**Integrated PMP lock:** **Approved ({DATE})** — `approve_pmp` accepted on {DATE} "
            f"(policy `{POLICY_ID}`, human acceptance). "
            f"Gate: [approve-pmp-pmp-bl-v1-0-0-{DATE}.adjudication.json](gates/{STEM}.adjudication.json). "
            f"**Stage 8** still required for execution.\n",
            pt,
            count=1,
        )
    pt = pt.replace(
        "; lock at **`approve-pmp`**.",
        f"; **approved** at PMP gate **{DATE}**.",
        1,
    )
    pt = pt.replace(
        "| QG-01 status | Foundation packs approved; completes at **`approve-pmp`** |",
        f"| QG-01 status | **Passed ({DATE})** — integrated PMP approved |",
    )
    pt = pt.replace(" — **draft_complete** |", f" — **approved ({DATE})** |")
    pt = pt.replace(
        "## 5. Governance Authorization\nThis integrated PMP must be formally evaluated and approved via `approve-pmp`",
        f"## 5. Governance Authorization\n\n**Status:** **Approved ({DATE})** — integrated PMP **`{BASELINE}`** locked under `approve-pmp` "
        f"(policy `{POLICY_ID}`, human acceptance). "
        f"Gate: [gates/{STEM}.adjudication.json](gates/{STEM}.adjudication.json). "
        "PMP SHA-256 at approval: `__PMP_SHA256__`.\n\n"
        "This integrated PMP was formally evaluated and approved via `approve-pmp`",
    )
    PMP.write_text(pt, encoding="utf-8")
    pmp_hash = sha256_file(PMP)
    pt = PMP.read_text(encoding="utf-8")
    if not frontmatter_has(pt, "pmp_sha256_at_approval"):
        pt = pt.replace(
            f'pmp_approval_gate: "gates/{STEM}.adjudication.json"',
            f'pmp_approval_gate: "gates/{STEM}.adjudication.json"\n'
            f'pmp_sha256_at_approval: "{pmp_hash}"',
            1,
        )
    else:
        pt = re.sub(
            r'^pmp_sha256_at_approval:\s*".*"$',
            f'pmp_sha256_at_approval: "{pmp_hash}"',
            pt,
            count=1,
            flags=re.M,
        )
    pt = pt.replace("__PMP_SHA256__", pmp_hash)
    PMP.write_text(pt, encoding="utf-8")
    pmp_hash = sha256_file(PMP)

    for name in OPERATIONAL_PLANS:
        path = MP / name
        text = path.read_text(encoding="utf-8")
        text = text.replace("**Status:** **Draft complete (2026-11-10)**", f"**Status:** **Approved ({DATE})**")
        text = text.replace("| Lock | **`approve-pmp`** pending |", f"| Lock | **`approve-pmp`** **approved ({DATE})** |")
        text = re.sub(r"\*\*QG-01 status.*?\n", f"**QG-01 status (2026-11-10):** **Passed** — integrated PMP approved **{DATE}**.\n", text, count=1)
        path.write_text(text, encoding="utf-8")

    # Subsidiary plans — PMP lock lines
    for sub in (
        "Scope-Management-Plan.md",
        "Schedule-Management-Plan.md",
        "Cost-Management-Plan.md",
        "Resource-Management-Plan.md",
    ):
        sp = MP / sub
        if not sp.is_file():
            continue
        st = sp.read_text(encoding="utf-8")
        st = st.replace("| Integrated PMP lock | **`approve-pmp`** not yet run |", f"| Integrated PMP lock | **`approve-pmp`** **approved ({DATE})** |")
        st = st.replace("| Full PMP lock | **`approve-pmp`** not yet run |", f"| Full PMP lock | **`approve-pmp`** **approved ({DATE})** |")
        st = st.replace("pending integrated **`approve-pmp`** lock", f"integrated **`approve-pmp`** lock **{DATE}**")
        st = st.replace("pending **`approve-pmp`** lock", f"**`approve-pmp`** lock **{DATE}**")
        sp.write_text(st, encoding="utf-8")

    # Approval package manifest
    if PACKAGE.is_file():
        pk = PACKAGE.read_text(encoding="utf-8")
        pk = pk.replace("pack_status: ready_for_gate", "pack_status: approved", 1)
        pk = pk.replace(
            "**Prepared:** 2026-11-10 — pending sponsor adjudication",
            f"**Approved:** **{DATE}** — gate [approve-pmp-pmp-bl-v1-0-0-{DATE}.adjudication.json](../gates/{STEM}.adjudication.json); "
            f"PMP SHA-256 `{pmp_hash}`",
        )
        pk = pk.replace("| RSK-11 | PMP lock | **Closes** on **`approve-pmp`** |", f"| RSK-11 | PMP lock | **closed ({DATE})** |")
        pk = pk.replace("| **QG-01** | Planning quality gate | **Closes** on **`approve-pmp`** |", f"| **QG-01** | Planning quality gate | **closed ({DATE})** |")
        PACKAGE.write_text(pk, encoding="utf-8")

    if REG.is_file():
        rt = REG.read_text(encoding="utf-8")
        rt = rt.replace(
            "**`approve-pmp`** not run; Stage 8 **not** issued",
            f"**`approve-pmp`** **approved {DATE}**; Stage 8 **not** issued",
        )
        REG.write_text(rt, encoding="utf-8")

    print(
        json.dumps(
            {
                "selected": selected,
                "policy_id": POLICY_ID,
                "baseline": BASELINE,
                "pmp_sha256": pmp_hash,
                "adjudication": str(adj_path.relative_to(REPO)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
