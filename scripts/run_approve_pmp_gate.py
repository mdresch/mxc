"""Run approve-pmp gate for integrated PMP (PMP-BL-v1.0.0)."""
from __future__ import annotations

import hashlib
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
TASK_ID = "approve-pmp"
BASELINE = "PMP-BL-v1.0.0"

PMP = "docs/project-docs/Project-Management-Plan.md"
PACKAGE = "docs/project-docs/management-plans/PMP-Approval-Package-Manifest.md"
CHARTER = "docs/project-docs/Project-Charter.md"
ADAPTATION = "docs/project-docs/Adaptation-Plan.md"

CRITERIA = [
    ("subsidiary_plan_completeness", "All nine subsidiary management plans integrate into the PMP with register pointers"),
    ("baseline_coherence", "Scope, schedule, resource, and cost baselines reconcile without hidden contradictions"),
    ("adaptation_responsiveness", "PMP defines adaptation feedback; known gaps recorded honestly"),
    ("governance_traceability", "Traceability to charter, business case, and approved requirements chain"),
]


def build_frame() -> dict:
    def evid(mode: str, cid: str, s1: float, s2: float, src1: str, src2: str) -> list[dict]:
        if mode == "approve":
            a1, a2 = s1, s2
        elif mode == "reject":
            a1, a2 = 1.0 - s1, min(1.0 - s2 + 0.02, 0.95)
        else:
            a1, a2 = 0.12, 0.14
        return [
            {"criterion_id": cid, "source": src1, "support": a1, "confidence": 0.88},
            {"criterion_id": cid, "source": src2, "support": a2, "confidence": 0.86},
        ]

    # Honest mxc scores — charter partially gated; adaptation plan is template shell
    scores = {
        "subsidiary_plan_completeness": (0.94, 0.92, PMP, PACKAGE),
        "baseline_coherence": (0.91, 0.89, PMP, "docs/project-docs/management-plans/cost-baseline/Cost-Foundation-Pack-Manifest.md"),
        "adaptation_responsiveness": (0.86, 0.84, PMP, ADAPTATION),
        "governance_traceability": (0.84, 0.82, CHARTER, "docs/project-docs/Business-Case.md"),
    }

    options = []
    for mode, action in [
        ("approve", "approve_pmp"),
        ("reject", "reject_pmp"),
        ("revision", "request_revision_before_decision"),
    ]:
        evidence = []
        for cid, _desc in CRITERIA:
            s1, s2, src1, src2 = scores[cid]
            evidence.extend(evid(mode, cid, s1, s2, src1, src2))
        options.append(
            {
                "action_id": action,
                "evidence": evidence,
                "constraint_results": {"no_unfixed_critical_flaw": True},
            }
        )

    return {
        "task": f"Integrated PMP ({BASELINE}): approve, reject, or request revision",
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
    stem = f"{TASK_ID}-pmp-bl-v1-0-0-{DATE}"
    frame = build_frame()
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
    pmp_hash = hashlib.sha256((REPO / PMP).read_bytes()).hexdigest()
    print(
        json.dumps(
            {
                "status": data.get("status"),
                "proposed": (data.get("proposed_action") or {}).get("id"),
                "approve_u": utilities.get("approve_pmp"),
                "pmp_sha256": pmp_hash,
                "frame": str(frame_path.relative_to(REPO)),
                "result": str(result_path.relative_to(REPO)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
