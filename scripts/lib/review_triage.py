"""Review-triage record parsing for PR gate vocabulary checks (IMP-030).

Pure stdlib module: no file I/O. Vendored for sidpa-template so gates do not
depend on the agent-learning package. Reliability / Wilson scoring is omitted
here; the gate only needs parse + find helpers.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CLAIM_TYPES",
    "DECISIONS",
    "TriageRecord",
    "VERIFIED",
    "find_triage_lines",
    "parse_triage_line",
    "to_episode_metadata",
]

CLAIM_TYPES = frozenset({"logic error", "crash risk", "test gap", "documentation", "style", "unknown"})
VERIFIED = frozenset({"yes", "no", "partial", "unknown"})
DECISIONS = frozenset({"accepted", "declined", "deferred", "unknown"})
REVIEWERS: Mapping[str, str] = {"Q": "amazon-q"}

_CLAIM_ALIASES = {"logic": "logic error"}
_MODIFIED = "accepted with modification"
_FINDING_ID = re.compile(r"^([A-Z]+)-(\d+)-(\d+)$")
_LOGGED_LINE = re.compile(r"`([A-Z]+-\d+-\d+ \| [^`]*)`")


@dataclass(frozen=True)
class TriageRecord:
    """One triaged review finding."""

    finding_id: str
    reviewer: str
    pr: int
    claim_type: str
    verified: str
    decision: str
    reason: str
    fix: str | None
    reconstructed: bool = False


def _choice(name: str, value: str, valid: frozenset[str]) -> str:
    if value not in valid:
        raise ValueError(f"{name} must be one of {', '.join(sorted(valid))}; got {value!r}")
    return value


def _identify(finding_id: str, reviewers: Mapping[str, str]) -> tuple[str, int]:
    match = _FINDING_ID.match(finding_id)
    if match is None:
        raise ValueError(
            f"finding id must look like Q-12-3 (reviewer initial, PR, ordinal); got {finding_id!r}"
        )
    initial, pr, _ordinal = match.groups()
    if initial not in reviewers:
        raise ValueError(
            f"reviewer initial {initial!r} in {finding_id} is not known; "
            f"known: {', '.join(sorted(reviewers))}"
        )
    return reviewers[initial], int(pr)


def parse_triage_line(
    line: str, *, reconstructed: bool = False, reviewers: Mapping[str, str] = REVIEWERS
) -> TriageRecord:
    """Parse one triage line; reject any field outside its vocabulary."""
    parts = [part.strip() for part in line.strip().split(" | ")]
    if len(parts) < 6:
        raise ValueError(
            "triage line needs: finding_id | claim type | verified: <v> | "
            "decision: <d> | <reason> | fix: <commit or none>"
        )
    finding_id, claim, verified, decision, fix = parts[0], parts[1], parts[2], parts[3], parts[-1]
    reason = " | ".join(parts[4:-1])
    if not verified.startswith("verified: "):
        raise ValueError(f"{finding_id}: third field must start with 'verified: '; got {verified!r}")
    if not decision.startswith("decision: "):
        raise ValueError(f"{finding_id}: fourth field must start with 'decision: '; got {decision!r}")
    if not fix.startswith("fix: "):
        raise ValueError(f"{finding_id}: last field must start with 'fix: '; got {fix!r}")
    reviewer, pr = _identify(finding_id, reviewers)

    claim = _CLAIM_ALIASES.get(claim, claim)
    decision_value = decision[len("decision: ") :]
    if decision_value == _MODIFIED:
        decision_value = "accepted"
        reason = f"(with modification) {reason}"
    fix_value = fix[len("fix: ") :]
    return TriageRecord(
        finding_id=finding_id,
        reviewer=reviewer,
        pr=pr,
        claim_type=_choice("claim type", claim, CLAIM_TYPES),
        verified=_choice("verified", verified[len("verified: ") :], VERIFIED),
        decision=_choice("decision", decision_value, DECISIONS),
        reason=reason,
        fix=None if fix_value in {"none", ""} else fix_value,
        reconstructed=reconstructed,
    )


def find_triage_lines(text: str) -> list[str]:
    """Return triage lines written in backticks, in order."""
    return _LOGGED_LINE.findall(text)


def to_episode_metadata(record: TriageRecord) -> dict[str, Any]:
    """Return the record's fields as a plain dict for episode metadata."""
    return {
        "finding_id": record.finding_id,
        "reviewer": record.reviewer,
        "pr": record.pr,
        "claim_type": record.claim_type,
        "verified": record.verified,
        "decision": record.decision,
        "reason": record.reason,
        "fix": record.fix,
        "reconstructed": record.reconstructed,
    }
