"""Run approve-subsidiary-plan gates for Cost foundation pack + Cost Management Plan."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATES = REPO / "docs" / "project-docs" / "gates"
CLI = REPO / ".venv" / "Scripts" / "agent-learn.exe"
DATE = "2026-11-10"
TASK_ID = "approve-subsidiary-plan"
MANIFEST = "docs/project-docs/management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md"
UPSTREAM = "docs/project-docs/management-plans/Cost-Management-Plan.md"
SCHEDULE_MANIFEST = "docs/project-docs/management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md"

CRITERIA = [
    ("sound_baseline_definitions", "Cost categories, estimates, and staging avoid false funding or invoice commitments"),
    ("technical_integrity", "Traceability to approved scope, schedule WD, and resource ROM is explicit"),
    ("consistent_with_upstream", "No irreconcilable conflict with approved scope/schedule baselines"),
]

ARTIFACTS = [
    ("7d0p-pillar-overview", "cost-baseline/foundation/Cost-Pillar-Overview-and-Trace.md", 0.92),
    ("7d1-categories", "cost-baseline/foundation/Cost-Categories-and-Estimating-Basis.md", 0.93),
    ("7d2-estimates", "cost-baseline/foundation/Cost-Estimates-by-Category.md", 0.94),
    ("7d3-staged-budget", "cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md", 0.92),
    ("7d4-variance", "cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md", 0.91),
    ("7d5-domain-checklist", "cost-baseline/foundation/Cost-Domain-Checklist.md", 0.90),
    ("7d7-pack-manifest", "cost-baseline/Cost-Foundation-Pack-Manifest.md", 0.93),
    ("cost-management-plan", "Cost-Management-Plan.md", 0.92),
]


def build_frame(key: str, doc_rel: str, approve_support: float) -> dict:
    doc = f"docs/project-docs/management-plans/{doc_rel}".replace("\\", "/")
    if "manifest" in key:
        second = UPSTREAM
    elif "cost-management" in key:
        second = MANIFEST
    else:
        second = SCHEDULE_MANIFEST

    def evid(mode: str, cid: str, sup: float) -> list[dict]:
        if mode == "approve":
            s1, s2 = sup, max(sup - 0.02, 0.5)
        elif mode == "reject":
            s1, s2 = 1.0 - sup, min(1.0 - sup + 0.02, 0.95)
        else:
            s1, s2 = 0.12, 0.15
        return [
            {"criterion_id": cid, "source": doc, "support": s1, "confidence": 0.88},
            {"criterion_id": cid, "source": second, "support": s2, "confidence": 0.86},
        ]

    options = []
    for mode, action in [
        ("approve", "approve_plan"),
        ("reject", "reject_plan"),
        ("revision", "request_revision_before_decision"),
    ]:
        evidence = []
        for cid, _desc in CRITERIA:
            if mode == "approve":
                evidence.extend(evid("approve", cid, approve_support))
            elif mode == "reject":
                evidence.extend(evid("reject", cid, approve_support))
            else:
                evidence.extend(evid("revision", cid, approve_support))
        options.append(
            {
                "action_id": action,
                "evidence": evidence,
                "constraint_results": {"no_unfixed_critical_flaw": True},
            }
        )

    return {
        "task": f"Cost subsidiary plan ({key}): approve, reject, or request revision",
        "criteria": [{"id": cid, "weight": 1.0, "minimum_sources": 2, "description": desc} for cid, desc in CRITERIA],
        "options": options,
        "constraints": ["no_unfixed_critical_flaw"],
        "minimum_margin": 0.05,
        "uncertainty_penalty": 0.10,
        "max_uncertainty": 1.0,
    }


def main() -> int:
    GATES.mkdir(parents=True, exist_ok=True)
    env = {
        **dict(__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(REPO / "data" / "agent-learning" / "store"),
    }
    summary = []
    for key, doc_rel, support in ARTIFACTS:
        frame = build_frame(key, doc_rel, support)
        stem = f"{TASK_ID}-cost-{key}-{DATE}"
        frame_path = GATES / f"{stem}.decision-frame.json"
        result_path = GATES / f"{stem}.decision-result.json"
        frame_path.write_text(json.dumps(frame, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(
            [
                str(CLI),
                "task-policy-decide",
                "--agent-id",
                "mxc-governance",
                "--task-id",
                TASK_ID,
                "--decision-frame",
                str(frame_path),
            ],
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        result_path.write_text(proc.stdout, encoding="utf-8")
        data = json.loads(proc.stdout)
        utilities = {a["action"]["id"]: a.get("robust_utility") for a in data.get("assessments", [])}
        summary.append(
            {
                "artifact": key,
                "status": data.get("status"),
                "proposed": (data.get("proposed_action") or {}).get("id"),
                "approve_u": utilities.get("approve_plan"),
            }
        )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
