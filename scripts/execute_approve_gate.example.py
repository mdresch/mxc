"""
EXAMPLE ONLY -- worked example of how to execute one of this template's
Bayesian approve-* decision gates by hand (building a decision frame,
scoring options, writing an episode, and updating the policy learner).

This is not meant to be run against the template repository itself.
Copy it into a real project, point --target-root at that project's
repo root, and replace the evidence/criteria below with that project's
real, reviewed content before trusting the result. Never hardcode a
real person's name as having already approved something they have not
actually reviewed -- `adjudicated_by` and `result_summary` below must
reflect a genuine human decision, not a fabricated one.

Usage:
    python scripts/execute_approve_gate.example.py \
        --target-root /path/to/your-project \
        --agent-id your-project-governance \
        --task-id approve-ideation \
        --reviewer "Real Reviewer Name"
"""

import argparse
import json
import uuid
import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True, help="Real project root (not this template repo)")
    parser.add_argument("--agent-id", required=True, help="This project's governance agent id, e.g. your-project-governance")
    parser.add_argument("--task-id", required=True, help="Policy task id, e.g. approve-ideation, approve-charter, approve-pmp")
    parser.add_argument("--reviewer", required=True, help="Real human reviewer name -- only use after they have actually reviewed the artifact")
    args = parser.parse_args()

    repo_root = args.target_root.resolve()
    agent_id = args.agent_id
    task_id = args.task_id

    active_policy_path = repo_root / "data" / "agent-learning" / "store" / "active-policies" / agent_id / f"{task_id}.json"
    with open(active_policy_path, "r", encoding="utf-8") as f:
        active_policy = json.load(f)
    policy_id = active_policy["policy_id"]

    # Replace this decision frame with one built from the real artifact(s)
    # being reviewed -- criteria, sources, and support/confidence scores
    # should reflect what a human actually found, not placeholder numbers.
    frame_path = repo_root / "docs" / "policy-shapes" / "decision-frames" / f"{agent_id}-{task_id}-approval.json"
    frame_data = {
        "task": f"{task_id}: approve, reject, or request revision",
        "criteria": [
            {"id": "example_criterion", "weight": 1.0, "minimum_sources": 1, "description": "Replace with this gate's real criteria"}
        ],
        "options": [
            {
                "action_id": f"approve_{task_id.removeprefix('approve-')}",
                "evidence": [{"criterion_id": "example_criterion", "source": "REPLACE", "support": 0.9, "confidence": 0.9}],
                "constraint_results": {"no_unfixed_critical_flaw": True}
            },
            {
                "action_id": f"reject_{task_id.removeprefix('approve-')}",
                "evidence": [{"criterion_id": "example_criterion", "source": "REPLACE", "support": 0.1, "confidence": 0.8}],
                "constraint_results": {"no_unfixed_critical_flaw": True}
            },
            {
                "action_id": "request_revision_before_decision",
                "evidence": [{"criterion_id": "example_criterion", "source": "REPLACE", "support": 0.15, "confidence": 0.75}],
                "constraint_results": {"no_unfixed_critical_flaw": True}
            }
        ],
        "constraints": ["no_unfixed_critical_flaw"],
        "minimum_margin": 0.05,
        "uncertainty_penalty": 0.1,
        "max_uncertainty": 1.0
    }
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    with open(frame_path, "w", encoding="utf-8") as f:
        json.dump(frame_data, f, indent=2)
    print(f"Decision frame written to {frame_path.name} -- EDIT ITS CRITERIA/EVIDENCE before relying on this result.")

    uncertainty_penalty = frame_data["uncertainty_penalty"]
    weights = {c["id"]: c["weight"] for c in frame_data["criteria"]}
    total_weight = sum(weights.values())

    utilities = {}
    for opt in frame_data["options"]:
        penalized = sum(
            weights.get(ev["criterion_id"], 1.0) * (ev["support"] - uncertainty_penalty * (1.0 - ev["confidence"]))
            for ev in opt["evidence"]
        )
        utilities[opt["action_id"]] = round(penalized / total_weight if total_weight else 0.0, 4)

    ranked = sorted(utilities.items(), key=lambda kv: kv[1], reverse=True)
    best_act, best_u = ranked[0]
    runner_act, runner_u = ranked[1]
    margin = round(best_u - runner_u, 4)
    print(f"Best={best_act} ({best_u:.4f}), RunnerUp={runner_act} ({runner_u:.4f}), Margin={margin:.4f}")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    episodes_dir = repo_root / "docs" / "policy-shapes" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    episode_path = episodes_dir / f"{agent_id}-{task_id}-approval-episode.json"

    episode_data = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": agent_id,
        "task_id": task_id,
        "task_name": task_id,
        "action_type": "recommendation",
        "action_id": best_act,
        "policy_id": policy_id,
        "policy_version": 0,
        "result_summary": f"Approved by {args.reviewer} on {datetime.date.today().isoformat()}. Utility {best_u:.4f}, margin {margin:.4f}.",
        "context_features": {"utility_approve": best_u, "utility_margin": margin},
        "metadata": {
            "decision_disposition": "accepted",
            "adjudicated_by": args.reviewer,
            "adjudicated_at": now_iso,
            "decision_frame": f"docs/policy-shapes/decision-frames/{frame_path.name}"
        },
        "created_at": now_iso
    }
    with open(episode_path, "w", encoding="utf-8") as f:
        json.dump(episode_data, f, indent=2)
    print(f"Episode written to {episode_path.name}")

    policy_file_path = repo_root / "data" / "agent-learning" / "store" / "policies" / agent_id / f"{policy_id}.json"
    if policy_file_path.exists():
        with open(policy_file_path, "r", encoding="utf-8") as f:
            pol_data = json.load(f)
        pol_data["episodes_seen"] = pol_data.get("episodes_seen", 0) + 1
        pol_data["updates_applied"] = pol_data.get("updates_applied", 0) + 1
        pol_data.setdefault("logits", {})[best_act] = round(pol_data.get("logits", {}).get(best_act, 0.0) + best_u, 4)
        pol_data["version"] = pol_data.get("version", 0) + 1
        with open(policy_file_path, "w", encoding="utf-8") as f:
            json.dump(pol_data, f, indent=2)
        print(f"Policy learner updated: {policy_file_path.name} (version {pol_data['version']})")


if __name__ == "__main__":
    main()
