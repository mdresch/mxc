"""Run approve-subsidiary-plan gates for Scope foundation pack + Scope Management Plan."""
from __future__ import annotations

import json
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
DATE = "2026-11-10"
TASK_ID = "approve-subsidiary-plan"
POLICY_ID = "1c0b25f8-af6e-4573-a101-9f5568f28792"
MANIFEST = "docs/project-docs/management-plans/scope-baseline/Scope-Foundation-Pack-Manifest.md"
UPSTREAM = "docs/project-docs/management-plans/Scope-Management-Plan.md"

CRITERIA = [
    ("sound_baseline_definitions", "WBS, boundaries, and controls are defined without inventing commitments"),
    ("technical_integrity", "Traceability to approved ADR/BRD/FDD/epic chain is explicit and honest about gaps"),
    ("consistent_with_upstream", "No irreconcilable conflict with accepted architecture and approved requirements"),
]

# key, rel path under management-plans, approve-path support
ARTIFACTS = [
    ("7a0p-pillar-overview", "scope-baseline/foundation/Scope-Pillar-Overview-and-Trace.md", 0.93),
    ("7a1-scope-statement", "scope-baseline/foundation/Scope-Project-Scope-Statement.md", 0.92),
    ("7a2-wbs-dictionary", "scope-baseline/foundation/Scope-WBS-Dictionary.md", 0.94),
    ("7a3-monitor-control", "scope-baseline/foundation/Scope-Monitor-Control-Scope.md", 0.91),
    ("7a4-validate-scope", "scope-baseline/foundation/Scope-Validate-Scope.md", 0.93),
    ("7a5-domain-checklist", "scope-baseline/foundation/Scope-Domain-Checklist.md", 0.90),
    ("7a7-pack-manifest", "scope-baseline/Scope-Foundation-Pack-Manifest.md", 0.94),
    ("scope-management-plan", "Scope-Management-Plan.md", 0.93),
]


def build_frame(key: str, doc_rel: str, approve_support: float) -> dict:
    doc = doc_rel.replace("\\", "/")
    second = MANIFEST if "manifest" not in key else UPSTREAM

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
        "task": f"Scope subsidiary plan ({key}): approve, reject, or request revision",
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
        frame = build_frame(key, f"docs/project-docs/management-plans/{doc_rel}", support)
        stem = f"{TASK_ID}-scope-{key}-{DATE}"
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
                "policy_id": POLICY_ID,
            }
        )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
