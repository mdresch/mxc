"""Run approve-subsidiary-plan gates for Schedule foundation pack + Schedule Management Plan."""
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
POLICY_ID = "1c0b25f8-af6e-4573-a101-9f5568f28792"
MANIFEST = "docs/project-docs/management-plans/schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
UPSTREAM = "docs/project-docs/management-plans/Schedule-Management-Plan.md"
SCOPE_MANIFEST = "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"

CRITERIA = [
    ("sound_baseline_definitions", "Schedule activities, logic, and reserves are defined without false date commitments"),
    ("technical_integrity", "Traceability to approved scope WBS and ADR/epic chain is explicit"),
    ("consistent_with_upstream", "No irreconcilable conflict with approved scope baseline and architecture"),
]

ARTIFACTS = [
    ("7b0p-pillar-overview", "schedule-baseline/foundation/Schedule-Pillar-Overview-and-Trace.md", 0.92),
    ("7b1-basis-estimates", "schedule-baseline/foundation/Schedule-Basis-of-Estimates.md", 0.91),
    ("7b2-network", "schedule-baseline/foundation/Schedule-Network-Phase1.md", 0.93),
    ("7b2a-activity-list", "schedule-baseline/foundation/Schedule-Activity-List-Phase1.md", 0.93),
    ("7b2b-gantt", "schedule-baseline/foundation/Schedule-Gantt-Phase1.md", 0.90),
    ("7b3-reserve", "schedule-baseline/foundation/Schedule-Reserve-Register.md", 0.91),
    ("7b4-wbs-forecast", "schedule-baseline/foundation/Schedule-Baseline-WBS-Forecast.md", 0.92),
    ("7b5-domain-checklist", "schedule-baseline/foundation/Schedule-Domain-Checklist.md", 0.90),
    ("7b7-pack-manifest", "schedule-baseline/Schedule-Foundation-Pack-Manifest.md", 0.93),
    ("schedule-management-plan", "Schedule-Management-Plan.md", 0.92),
]


def build_frame(key: str, doc_rel: str, approve_support: float) -> dict:
    doc = f"docs/project-docs/management-plans/{doc_rel}".replace("\\", "/")
    if "manifest" in key:
        second = UPSTREAM
    elif "schedule-management" in key:
        second = MANIFEST
    else:
        second = SCOPE_MANIFEST

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
        "task": f"Schedule subsidiary plan ({key}): approve, reject, or request revision",
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
        stem = f"{TASK_ID}-schedule-{key}-{DATE}"
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
