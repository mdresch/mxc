#!/usr/bin/env python3
"""Bayesian PR Review Gatekeeper (SIDPA Template).

Evaluates a pull request against CI checks, architectural boundaries, and reviewer
critiques using the Epic 14 Lightweight Critique-to-Evidence Ingestion Engine.
Resolves a calibrated Bayesian DecisionFrame, verifies robust utility margin (>= +0.05),
passively records an auditable Episode in the LearningStore, and optionally executes
merge via GitHub CLI.

Usage:
    python scripts/pr_gate.py <pr_number>
    python scripts/pr_gate.py <pr_number> --merge
    python scripts/pr_gate.py <pr_number> --json
    python scripts/pr_gate.py <pr_number> --no-persist
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Optional
import uuid

# Ensure local script library is accessible
LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from decision import (
    Action,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    Episode,
    EvidencePoint,
    LocalFileStore,
    PolicySnapshot,
)
from critique_evidence import (
    AppliedCritique,
    CritiqueDelta,
    apply_critique,
    parse_critique,
    rubric_delta,
    to_episode_metadata,
)
from review_triage import TriageRecord, find_triage_lines, parse_triage_line
from triage_replay import map_claim_to_criterion

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE_DIR = ROOT / "data" / "agent-learning" / "store"

# Root implementation log only (IMP-030). Nested copies such as docs/implementation-log.md are ignored.
# Template projects may also use the register path produced by init_project.
TRIAGE_LOGS = frozenset(
    {
        "implementation-log.md",
        "docs/registers/Implementation-Log.md",
    }
)


def run_gh_command(cmd_args: list[str]) -> str:
    """Execute a GitHub CLI command and return stdout (UTF-8; IMP-045)."""
    res = subprocess.run(
        ["gh"] + cmd_args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"gh command failed: {res.stderr.strip() or res.stdout.strip()}")
    return res.stdout


def fetch_pr_data(pr_number: int) -> dict[str, Any]:
    """Fetch complete PR JSON details via GitHub CLI."""
    fields = "headRefOid,title,state,statusCheckRollup,comments,reviews,files"
    stdout = run_gh_command(["pr", "view", str(pr_number), "--json", fields])
    return json.loads(stdout)


def fetch_pr_diff(pr_number: int) -> str:
    """Fetch the unified diff of a PR via GitHub CLI (fails closed; IMP-045 UTF-8)."""
    run = subprocess.run(
        ["gh", "pr", "diff", str(pr_number)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if run.returncode != 0:
        raise RuntimeError(f"Failed to fetch the diff of PR #{pr_number} via gh: {run.stderr.strip()}")
    return run.stdout


def added_triage_lines(diff: str) -> list[str]:
    """The review-triage lines a PR adds to a known implementation log (IMP-030)."""
    added: list[str] = []
    in_log = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_log = any(line.rstrip().endswith(" b/" + path) for path in TRIAGE_LOGS)
        elif in_log and line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    return find_triage_lines("\n".join(added))


def check_triage_lines(lines: list[str]) -> tuple[list[TriageRecord], list[str]]:
    """Parse each added triage line; a field outside the vocabulary is an error (IMP-030)."""
    records: list[TriageRecord] = []
    errors: list[str] = []
    for text in lines:
        try:
            records.append(parse_triage_line(text))
        except ValueError as err:
            errors.append(f"`{text[:60]}`: {err}")
    return records, errors


def reconcile_triage(
    deltas: list[CritiqueDelta], records: list[TriageRecord], pr_number: int
) -> tuple[list[CritiqueDelta], list[str]]:
    """Respect the maintainer's triage of this PR's own findings (IMP-017).

    A declined or deferred row cancels one review-derived defect on the same criterion;
    an accepted row keeps the defect, and adds the rubric delta when the review text
    produced none. Untriaged findings still count in full.
    """
    remaining = list(deltas)
    reserved: set[int] = set()
    notes: list[str] = []
    for rec in records:
        if rec.pr != pr_number:
            continue
        try:
            criterion = map_claim_to_criterion(rec.claim_type)
        except ValueError as err:
            notes.append(f"{rec.finding_id}: skipped ({err})")
            continue
        match = next(
            (
                d
                for d in remaining
                if d.criterion_id == criterion and d.delta < 0 and id(d) not in reserved
            ),
            None,
        )
        if rec.decision == "accepted":
            if match is not None:
                reserved.add(id(match))
                notes.append(f"{rec.finding_id} accepted: kept {match.finding_id}")
                continue
            try:
                value = rubric_delta(rec.claim_type, rec.verified)
            except ValueError:
                notes.append(
                    f"{rec.finding_id} accepted: no rubric delta for "
                    f"({rec.claim_type}, {rec.verified}); not scored"
                )
                continue
            if value < 0:
                added = CritiqueDelta(
                    criterion_id=criterion,
                    delta=value,
                    finding_id=rec.finding_id,
                    claim_type=rec.claim_type,
                    verified=rec.verified,
                    comment_text=rec.reason,
                    rubric_delta=value,
                )
                remaining.append(added)
                reserved.add(id(added))
                notes.append(f"{rec.finding_id} accepted: added rubric delta {value:+.2f}")
        elif rec.decision in {"declined", "deferred"} and match is not None:
            remaining.remove(match)
            notes.append(f"{rec.finding_id} {rec.decision}: cancelled {match.finding_id}")
    return remaining, notes


def extract_raw_review_texts(pr_data: dict[str, Any]) -> list[tuple[str, str]]:
    """Extract reviewer comments from PR reviews and issue comments."""
    sources: list[tuple[str, str]] = []
    for r in pr_data.get("reviews", []):
        author = (r.get("author") or {}).get("login", "unknown")
        body = r.get("body", "")
        if body.strip():
            sources.append((author, body))
        for c in r.get("comments", []):
            c_body = c.get("body", "")
            if c_body.strip():
                sources.append((author, c_body))

    for c in pr_data.get("comments", []):
        author = (c.get("author") or {}).get("login", "unknown")
        body = c.get("body", "")
        if body.strip() and not body.strip().startswith("/q"):
            sources.append((author, body))

    return sources


def convert_unstructured_review_to_tags(author: str, text: str, source_prefix: str = "REV") -> list[str]:
    """Convert common unstructured review patterns into Epic 14 tag grammar."""
    tagged_lines: list[str] = []

    # First check if the text already contains tagged bullets
    tag_bullets = re.findall(r"^[*-]\s*(\[criterion:[^\]]+\].+)$", text, re.MULTILINE)
    if tag_bullets:
        for b in tag_bullets:
            tagged_lines.append(f"- {b}")
        return tagged_lines

    low_author = author.lower()
    low_text = text.lower()

    # 1. Critical / Blocking issues
    crit_match = re.search(
        r"###?\s*(?:Blocking issues found|Critical Issues|Issues Found|Issues requiring fixes|Findings)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
        text,
        re.IGNORECASE,
    )
    if crit_match:
        items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\*|-)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-)\s+)|\Z)", crit_match.group(1), re.DOTALL)
        for idx, item in enumerate(items, start=1):
            clean_item = " ".join(item.split()).replace("**", "")
            f_id = f"{source_prefix}-CRIT-{idx}"
            low_item = clean_item.lower()
            if any(w in low_item for w in ("crash", "exception", "attributeerror", "keyerror", "vulnerability")):
                tagged_lines.append(f"- [criterion: correctness] [claim: crash risk] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
            elif any(w in low_item for w in ("test", "coverage", "untested", "fragile")):
                tagged_lines.append(f"- [criterion: test_coverage] [claim: test gap] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")
            elif any(w in low_item for w in ("style", "linter", "unused", "format")):
                tagged_lines.append(f"- [criterion: implementation_quality] [claim: style] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")
            else:
                tagged_lines.append(f"- [criterion: correctness] [claim: logic error] [verified: yes] [finding: {f_id}]: {clean_item[:120]}")

    # 2. Open / Remaining items (Minor gaps)
    rem_match = re.search(
        r"###?\s*(?:Remaining items|Open items|Suggestions|Minor issues)[^\n]*\n([\s\S]*?)(?=\n###?|\Z)",
        text,
        re.IGNORECASE,
    )
    if rem_match:
        items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\*|-)\s+(.+?)(?=(?:\n\s*(?:\d+\.|\*|-)\s+)|\Z)", rem_match.group(1), re.DOTALL)
        for idx, item in enumerate(items, start=1):
            clean_item = " ".join(item.split()).replace("**", "")
            f_id = f"{source_prefix}-OPEN-{idx}"
            tagged_lines.append(f"- [criterion: implementation_quality] [claim: logic error] [verified: partial] [finding: {f_id}]: {clean_item[:120]}")

    # 3. Positive Confirmation
    if (
        "no blocking issues found" in low_text
        or "looks good" in low_text
        or "lgtm" in low_text
        or "low risk" in low_text
        or "all checks passed" in low_text
    ) and not any("crash risk" in l or "logic error" in l for l in tagged_lines):
        f_id = f"{source_prefix}-CONFIRM"
        tagged_lines.append(
            f"- [criterion: correctness] [claim: confirmation] [verified: yes] [finding: {f_id}]: "
            "Implementation verified correct by automated/human reviewer."
        )

    return tagged_lines


def build_pr_decision_frame(pr_number: int) -> DecisionFrame:
    """Construct standardized PR Governance DecisionFrame."""
    criteria = (
        DecisionCriterion(id="correctness", weight=0.40, minimum_sources=1),
        DecisionCriterion(id="implementation_quality", weight=0.35, minimum_sources=1),
        DecisionCriterion(id="test_coverage", weight=0.25, minimum_sources=1),
    )

    opt_approve = DecisionOption(
        action=Action(id="approve_and_merge", description=f"Approve and Merge PR #{pr_number}"),
        evidence=(
            EvidencePoint("correctness", "ci_tests", 0.85, 0.80),
            EvidencePoint("implementation_quality", "code_review", 0.85, 0.80),
            EvidencePoint("test_coverage", "test_suite", 0.80, 0.75),
        ),
    )

    opt_revise = DecisionOption(
        action=Action(id="request_revisions", description=f"Request Revisions on PR #{pr_number}"),
        evidence=(
            EvidencePoint("correctness", "baseline_eval", 0.60, 0.60),
            EvidencePoint("implementation_quality", "baseline_eval", 0.60, 0.60),
            EvidencePoint("test_coverage", "baseline_eval", 0.60, 0.60),
        ),
    )

    return DecisionFrame(
        task=f"pr-{pr_number}-governance-gate",
        options=(opt_approve, opt_revise),
        criteria=criteria,
        minimum_margin=0.05,
    )


def save_gate_episode(
    pr_number: int,
    pr_data: dict[str, Any],
    passed: bool,
    reason: str,
    margin: float,
    applied: Optional[AppliedCritique],
    store_dir: Optional[Path] = None,
) -> str:
    """Persist the PR gate decision as an auditable Episode."""
    target_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
    store = LocalFileStore(root_dir=target_dir)

    head_commit = str(pr_data.get("headRefOid") or "unknown")
    ep_uuid = uuid.uuid4().hex[:8]
    short_commit = head_commit[:7] if head_commit != "unknown" else "run"
    episode_id = f"pr-{pr_number}-{short_commit}-{ep_uuid}"

    adjustments = to_episode_metadata(applied).get("critique_adjustments", []) if applied else []

    meta: dict[str, Any] = {
        "pr_number": pr_number,
        "title": pr_data.get("title", ""),
        "head_commit": head_commit,
        "margin": round(margin, 4),
        "feedback_status": "accepted" if passed else "rejected",
        "critique_adjustments": adjustments,
    }
    if not passed:
        meta["correct_action_id"] = "request_revisions"
        meta["rejection_reason"] = reason

    episode = Episode(
        id=episode_id,
        agent_id=os.environ.get("GOVERNANCE_AGENT_ID", "mxc-governance"),
        task_id=f"pr-{pr_number}-governance-gate",
        task_name=f"PR #{pr_number} Governance Review Gate",
        action_id="approve_and_merge" if passed else "request_revisions",
        intent_summary=f"Bayesian gatekeeper evaluation of PR #{pr_number}",
        user_input=f"PR #{pr_number}: {pr_data.get('title', '')}",
        assistant_output=reason,
        metadata=meta,
    )
    store.save_episode(episode)
    return episode_id


def evaluate_pr(
    pr_number: int,
    persist_episode: bool = True,
    store_dir: Optional[Path] = None,
) -> tuple[bool, str, dict[str, Any]]:
    """Evaluate a PR against CI checks, boundaries, and Epic 14 Bayesian critique."""
    pr_data = fetch_pr_data(pr_number)

    # 1. CI Status Checks
    ci_status = "SUCCESS"
    rollup = pr_data.get("statusCheckRollup", []) or []
    failed_checks: list[str] = []
    for check in rollup:
        conclusion = (check.get("conclusion") or check.get("status") or "").upper()
        name = check.get("name") or check.get("context") or "unknown_check"
        if conclusion in ("FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "CANCELLED"):
            failed_checks.append(f"{name} ({conclusion})")

    if failed_checks:
        reason = f"CI status checks failed: {', '.join(failed_checks)}. Gate halted."
        ep_id = None
        if persist_episode:
            ep_id = save_gate_episode(pr_number, pr_data, False, reason, -1.0, None, store_dir)
        return False, reason, {"pr_number": pr_number, "failed_checks": failed_checks, "episode_id": ep_id}

    # 2. IMP-030: review-triage lines the PR adds must stay inside the vocabulary
    triage_records, triage_errors = check_triage_lines(added_triage_lines(fetch_pr_diff(pr_number)))
    if triage_errors:
        reason = "Triage line outside the vocabulary: " + "; ".join(triage_errors)
        ep_id = None
        if persist_episode:
            ep_id = save_gate_episode(pr_number, pr_data, False, reason, -1.0, None, store_dir)
        return (
            False,
            reason,
            {
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "head_commit": pr_data.get("headRefOid"),
                "triage_errors": triage_errors,
                "episode_id": ep_id,
            },
        )

    # 3. Extract & Parse Reviews into Epic 14 critique tags
    review_sources = extract_raw_review_texts(pr_data)
    all_tagged_bullets: list[str] = []
    for r_idx, (author, body) in enumerate(review_sources, start=1):
        tags = convert_unstructured_review_to_tags(author, body, source_prefix=f"REV{r_idx}")
        all_tagged_bullets.extend(tags)

    deltas: list[CritiqueDelta] = []
    if all_tagged_bullets:
        full_critique_text = "\n".join(all_tagged_bullets)
        try:
            deltas = parse_critique(full_critique_text, source_id="pr_review")
        except Exception as e:
            print(f"Warning: Parse issue on critique: {e}", file=sys.stderr)

    deltas, triage_notes = reconcile_triage(deltas, triage_records, pr_number)

    # 4. Decision Frame Resolution
    frame = build_pr_decision_frame(pr_number)
    applied = apply_critique(frame, option_id="approve_and_merge", deltas=deltas)

    resolver = DecisionResolver()
    result = resolver.resolve(applied.frame)

    approve_assess = next(a for a in result.assessments if a.action.id == "approve_and_merge")
    revise_assess = next(a for a in result.assessments if a.action.id == "request_revisions")
    margin = approve_assess.robust_utility - revise_assess.robust_utility

    passed = (
        result.status.value == "resolved"
        and result.selected_action is not None
        and result.selected_action.id == "approve_and_merge"
        and margin >= 0.05
    )

    reason = (
        f"Approved: robust utility {approve_assess.robust_utility:.3f} and margin {margin:+.3f} exceed threshold (+0.05)."
        if passed
        else f"Revisions required: margin {margin:+.3f} is below required threshold (+0.05)."
    )

    ep_id = None
    if persist_episode:
        ep_id = save_gate_episode(pr_number, pr_data, passed, reason, margin, applied, store_dir)

    details: dict[str, Any] = {
        "pr_number": pr_number,
        "title": pr_data.get("title"),
        "head_commit": pr_data.get("headRefOid"),
        "approve_robust_utility": approve_assess.robust_utility,
        "revise_robust_utility": revise_assess.robust_utility,
        "margin": margin,
        "critique_deltas_count": len(deltas),
        "triage_replay": triage_notes,
        "episode_id": ep_id,
        "adjustments": to_episode_metadata(applied).get("critique_adjustments", []),
    }

    return passed, reason, details


def ensure_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so emoji verdict lines print on a cp1252 console (IMP-045)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="Bayesian PR Review Gatekeeper.")
    parser.add_argument("pr_number", type=int, help="Pull Request number to evaluate")
    parser.add_argument("--merge", action="store_true", help="Execute merge if gatekeeper passes")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--no-persist", action="store_true", help="Do not persist episode to LearningStore")
    args = parser.parse_args()

    try:
        passed, reason, details = evaluate_pr(
            pr_number=args.pr_number,
            persist_episode=not args.no_persist,
        )
    except Exception as e:
        print(f"Error evaluating PR #{args.pr_number}: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"passed": passed, "reason": reason, "details": details}, indent=2))
        return 0 if passed else 1

    print("=" * 80)
    print(f"PR GATEKEEPER EVALUATION: PR #{args.pr_number} — {details.get('title')}")
    print("=" * 80)
    print(f"Commit: {details.get('head_commit')}")
    if details.get("episode_id"):
        print(f"Passive Learning Episode: {details.get('episode_id')}")
    print(f"Ingested Findings: {details.get('critique_deltas_count')} critique deltas applied.")
    print("-" * 80)
    print(f"Approve Option: Robust Utility = {details.get('approve_robust_utility')} (Margin: {details.get('margin'):+.3f})")
    print(f"Revise Option:  Robust Utility = {details.get('revise_robust_utility')}")
    print("-" * 80)
    if passed:
        print(f"✅ GATE RESULT: PASSED / APPROVED TO MERGE")
        print(f"   Reason: {reason}")
    else:
        print(f"❌ GATE RESULT: HALTED / REVISIONS REQUIRED")
        print(f"   Reason: {reason}")

    if passed and args.merge:
        print("\nExecuting gh pr merge...")
        try:
            run_gh_command(["pr", "merge", str(args.pr_number), "--squash", "--delete-branch"])
            print("Successfully merged!")
        except Exception as e:
            print(f"Merge execution failed: {e}", file=sys.stderr)
            return 1

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
