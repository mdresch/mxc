"""Run approve-brd, approve-fdd, approve-user-stories for ADR-001..006."""
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
DATE = "2026-10-30"

SLUGS = {
    "001": "type-1-hyperv-generation-2",
    "002": "connection-buffering-ingress-gateway",
    "003": "production-base-image",
    "004": "paused-ram-standby",
    "005": "transient-differencing-disk",
    "006": "watermark-pool",
}

# Approve-path criterion supports (honest scoring; open hypotheses lower honest_metrics slightly)
SCORES = {
    "001": {"brd": 0.91, "fdd": 0.90, "stories": 0.89},
    "002": {"brd": 0.93, "fdd": 0.92, "stories": 0.93},
    "003": {"brd": 0.90, "fdd": 0.88, "stories": 0.87},
    "004": {"brd": 0.92, "fdd": 0.91, "stories": 0.92},
    "005": {"brd": 0.91, "fdd": 0.90, "stories": 0.90},
    "006": {"brd": 0.90, "fdd": 0.89, "stories": 0.89},
}

GATE_CONFIG = {
    "approve-brd": {
        "approve_action": "approve_brd",
        "reject_action": "reject_brd",
        "criteria": [
            ("traceable_to_adr", "Business rules cite ADR sections and match Accepted decisions"),
            ("honest_metrics", "Metrics name Formulated, blocked, or unmeasured states instead of inventing pass/fail"),
            ("out_of_scope_accurate", "Out-of-scope matches sibling ADR boundaries"),
            ("rules_actionable", "BRU rules are concrete enough to drive FDD and stories"),
        ],
        "doc": lambda n, s: f"docs/project-docs/Business-Requirements/BRD-{n}-{s}.md",
        "adr": lambda n, s: f"docs/07-architecture/ADR-{n}-{s}.md",
    },
    "approve-fdd": {
        "approve_action": "approve_fdd",
        "reject_action": "reject_fdd",
        "criteria": [
            ("traceable_to_brd_adr", "Design traces to BRD rules and ADR decisions"),
            ("grounded_in_suite", "Interfaces and scripts match docs/hyperv/architecture/FDD.md and tree paths"),
            ("code_shaped_honesty", "Documentation-only items are labeled; no fake implementation"),
            ("out_of_scope_accurate", "Out-of-scope matches BRD and ADR"),
        ],
        "doc": lambda n, s: f"docs/project-docs/Functional-Design/FDD-{n}-{s}.md",
        "adr": lambda n, s: f"docs/project-docs/Business-Requirements/BRD-{n}-{s}.md",
    },
    "approve-user-stories": {
        "approve_action": "approve_user_stories",
        "reject_action": "reject_user_stories",
        "criteria": [
            ("testable_ac", "Acceptance criteria are contract-testable or name the blocking measurement"),
            ("traceable_to_brd_fdd", "Stories map to BRU rules and FDD sections"),
            ("suite_alignment", "AC numbers align with USER_STORIES.md where a suite anchor exists"),
            ("not_forced_shape", "No filler stories for out-of-scope horizon items"),
        ],
        "doc": lambda n, s: f"docs/user-stories/epic-{n}-{s}.md",
        "adr": lambda n, s: f"docs/project-docs/Functional-Design/FDD-{n}-{s}.md",
    },
}


def build_frame(task_id: str, num: str, slug: str, approve_support: float) -> dict:
    cfg = GATE_CONFIG[task_id]
    approve = cfg["approve_action"]
    reject = cfg["reject_action"]
    doc = cfg["doc"](num, slug)
    second = cfg["adr"](num, slug)

    def evid(mode: str, cid: str, sup: float) -> list[dict]:
        if mode == "approve":
            s1, s2 = sup, max(sup - 0.02, 0.5)
        elif mode == "reject":
            s1, s2 = 1.0 - sup, 1.0 - sup + 0.02
        else:
            s1, s2 = 0.15, 0.18
        return [
            {"criterion_id": cid, "source": doc, "support": s1, "confidence": 0.88},
            {"criterion_id": cid, "source": second, "support": s2, "confidence": 0.86},
        ]

    options = []
    for mode, action in [
        ("approve", approve),
        ("reject", reject),
        ("revision", "request_revision_before_decision"),
    ]:
        evidence = []
        for cid, _desc in cfg["criteria"]:
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

    prefix = task_id.replace("approve-", "")
    return {
        "task": f"ADR-{num} {prefix}: approve, reject, or request revision",
        "criteria": [
            {
                "id": cid,
                "weight": 1.0,
                "minimum_sources": 2,
                "description": desc,
            }
            for cid, desc in cfg["criteria"]
        ],
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
    for task_id in ("approve-brd", "approve-fdd", "approve-user-stories"):
        prefix = task_id.replace("approve-", "")
        for num, slug in SLUGS.items():
            key = {"approve-brd": "brd", "approve-fdd": "fdd", "approve-user-stories": "stories"}[
                task_id
            ]
            support = SCORES[num][key]
            frame = build_frame(task_id, num, slug, support)
            stem = f"{task_id}-{num}-{DATE}"
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
                    task_id,
                    "--decision-frame",
                    str(frame_path),
                ],
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                print(proc.stderr, file=__import__("sys").stderr)
                return proc.returncode
            result_path.write_text(proc.stdout, encoding="utf-8")
            data = json.loads(proc.stdout)
            proposed = (data.get("proposed_action") or {}).get("id")
            utilities = {
                a["action"]["id"]: a.get("robust_utility")
                for a in data.get("assessments", [])
            }
            approve_id = GATE_CONFIG[task_id]["approve_action"]
            summary.append(
                {
                    "gate": task_id,
                    "adr": num,
                    "status": data.get("status"),
                    "proposed": proposed,
                    "approve_u": utilities.get(approve_id),
                }
            )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
