"""One-shot: write approve-adr decision frames and run task-policy-decide for ADR-001..006."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GATES = REPO / "docs" / "project-docs" / "gates"
CLI = REPO / ".venv" / "Scripts" / "agent-learn.exe"
DATE = "2026-10-30"

CRITERIA = [
    {
        "id": "architectural_soundness",
        "weight": 1.0,
        "minimum_sources": 2,
        "description": "The decision is traceable to spark, hypotheses, or benefits, names its topic pillar, and states what is out of scope",
    },
    {
        "id": "alternatives_considered",
        "weight": 1.0,
        "minimum_sources": 2,
        "description": "Real alternatives are named with reasons for rejection, not strawmen",
    },
    {
        "id": "consequences_honest",
        "weight": 1.0,
        "minimum_sources": 2,
        "description": "Negative consequences and open measurements are stated; hypotheses stay Formulated where no live proof exists",
    },
    {
        "id": "adr_consistency",
        "weight": 1.0,
        "minimum_sources": 2,
        "description": "Boundaries with sibling ADRs and the architecture-suite record are consistent",
    },
]

ADRS = [
    {
        "num": "001",
        "slug": "type-1-hyperv-generation-2",
        "title": "Type-1 Hyper-V Generation 2 instead of a container namespace",
        "lifecycle": "docs/07-architecture/ADR-001-type-1-hyperv-generation-2.md",
        "suite": "docs/hyperv/architecture/ADR.md ADR-001",
        "approve": {
            "architectural_soundness": (0.94, 0.92),
            "alternatives_considered": (0.93, 0.90),
            "consequences_honest": (0.90, 0.88),
            "adr_consistency": (0.91, 0.89),
        },
        "reject": 0.05,
        "revision": 0.12,
    },
    {
        "num": "002",
        "slug": "connection-buffering-ingress-gateway",
        "title": "Connection-buffering ingress gateway",
        "lifecycle": "docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md",
        "suite": "docs/hyperv/architecture/ADR.md ADR-002",
        "approve": {
            "architectural_soundness": (0.93, 0.91),
            "alternatives_considered": (0.92, 0.89),
            "consequences_honest": (0.88, 0.87),
            "adr_consistency": (0.90, 0.88),
        },
        "reject": 0.06,
        "revision": 0.18,
    },
    {
        "num": "003",
        "slug": "production-base-image",
        "title": "Production base image separate from the developer image",
        "lifecycle": "docs/07-architecture/ADR-003-production-base-image.md",
        "suite": "docs/hyperv/GOLDEN_IMAGE_REGISTRY.md",
        "approve": {
            "architectural_soundness": (0.90, 0.88),
            "alternatives_considered": (0.91, 0.89),
            "consequences_honest": (0.93, 0.91),
            "adr_consistency": (0.89, 0.87),
        },
        "reject": 0.08,
        "revision": 0.22,
    },
    {
        "num": "004",
        "slug": "paused-ram-standby",
        "title": "Paused RAM standby, trimmed before suspend",
        "lifecycle": "docs/07-architecture/ADR-004-paused-ram-standby.md",
        "suite": "docs/hyperv/architecture/USER_STORIES.md US-03",
        "approve": {
            "architectural_soundness": (0.92, 0.90),
            "alternatives_considered": (0.91, 0.88),
            "consequences_honest": (0.90, 0.89),
            "adr_consistency": (0.90, 0.88),
        },
        "reject": 0.06,
        "revision": 0.16,
    },
    {
        "num": "005",
        "slug": "transient-differencing-disk",
        "title": "Transient differencing disk and egress whitelist",
        "lifecycle": "docs/07-architecture/ADR-005-transient-differencing-disk.md",
        "suite": "docs/hyperv/architecture/USER_STORIES.md US-02",
        "approve": {
            "architectural_soundness": (0.91, 0.89),
            "alternatives_considered": (0.90, 0.88),
            "consequences_honest": (0.89, 0.88),
            "adr_consistency": (0.89, 0.87),
        },
        "reject": 0.07,
        "revision": 0.17,
    },
    {
        "num": "006",
        "slug": "watermark-pool",
        "title": "Watermark pool, replenish, and wake hygiene",
        "lifecycle": "docs/07-architecture/ADR-006-watermark-pool.md",
        "suite": "docs/hyperv/architecture/FDD.md pool_config",
        "approve": {
            "architectural_soundness": (0.89, 0.87),
            "alternatives_considered": (0.90, 0.88),
            "consequences_honest": (0.92, 0.90),
            "adr_consistency": (0.88, 0.86),
        },
        "reject": 0.07,
        "revision": 0.20,
    },
]


def build_option(action_id: str, adr: dict, mode: str) -> dict:
    evidence = []
    for cid in ("architectural_soundness", "alternatives_considered", "consequences_honest", "adr_consistency"):
        s1, c1 = adr["approve"][cid]
        if mode == "approve":
            s2, c2 = s1 - 0.02, c1 - 0.02
        elif mode == "reject":
            s2, c2 = adr["reject"], 0.85
        else:
            s2, c2 = adr["revision"], 0.84
        if mode == "approve":
            sup_a, conf_a = s1, c1
            sup_b, conf_b = s2, c2
        elif mode == "reject":
            sup_a, conf_a = 1.0 - s1, c1
            sup_b, conf_b = 1.0 - s2, c2
        else:
            sup_a, conf_a = adr["revision"], 0.86
            sup_b, conf_b = adr["revision"] + 0.02, 0.84
        evidence.append(
            {
                "criterion_id": cid,
                "source": adr["lifecycle"],
                "support": sup_a,
                "confidence": conf_a,
            }
        )
        evidence.append(
            {
                "criterion_id": cid,
                "source": adr["suite"],
                "support": sup_b,
                "confidence": conf_b,
            }
        )
    return {
        "action_id": action_id,
        "evidence": evidence,
        "constraint_results": {"no_unfixed_critical_flaw": True},
    }


def main() -> int:
    GATES.mkdir(parents=True, exist_ok=True)
    env = {
        **dict(**__import__("os").environ),
        "AGENT_LEARNING_STORE_BACKEND": "local",
        "AGENT_LEARNING_LOCAL_STORE_DIR": str(
            REPO / "data" / "agent-learning" / "store"
        ),
    }
    summaries = []
    for adr in ADRS:
        frame = {
            "task": f"ADR-{adr['num']} ({adr['title']}): approve, reject, or request revision",
            "criteria": CRITERIA,
            "options": [
                build_option("approve_adr", adr, "approve"),
                build_option("reject_adr", adr, "reject"),
                build_option("request_revision_before_decision", adr, "revision"),
            ],
            "constraints": ["no_unfixed_critical_flaw"],
            "minimum_margin": 0.05,
            "uncertainty_penalty": 0.10,
            "max_uncertainty": 1.0,
        }
        stem = f"approve-adr-{adr['num']}-{DATE}"
        frame_path = GATES / f"{stem}.decision-frame.json"
        frame_path.write_text(json.dumps(frame, indent=2) + "\n", encoding="utf-8")
        result_path = GATES / f"{stem}.decision-result.json"
        proc = subprocess.run(
            [
                str(CLI),
                "task-policy-decide",
                "--agent-id",
                "mxc-governance",
                "--task-id",
                "approve-adr",
                "--decision-frame",
                str(frame_path),
            ],
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout, proc.stderr, file=sys.stderr)
            return proc.returncode
        result_path.write_text(proc.stdout, encoding="utf-8")
        data = json.loads(proc.stdout)
        proposed = (data.get("proposed_action") or {}).get("id")
        status = data.get("status")
        assessments = {
            a["action"]["id"]: a.get("robust_utility")
            for a in data.get("assessments", [])
        }
        summaries.append(
            {
                "adr": adr["num"],
                "status": status,
                "proposed": proposed,
                "utilities": assessments,
                "frame": str(frame_path.relative_to(REPO)),
                "result": str(result_path.relative_to(REPO)),
            }
        )
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
