"""Lightweight Critique-to-Evidence Ingestion Engine (SIDPA Template).

Converts markdown critique findings into structured CritiqueDelta instances
following the tag grammar of FDD-014, applies them to DecisionFrame options
via log-odds shifts and doubt adjustments, and generates episode metadata.
Pure Python standard library with zero external dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any, Optional, Sequence

try:
    from .decision import DecisionFrame, DecisionOption, EvidencePoint
except ImportError:
    from decision import DecisionFrame, DecisionOption, EvidencePoint

# FDD-014 Constants
KAPPA_DEFAULT: float = 0.2
CONFIDENCE_FLOOR: float = 0.05
TARGET_EPSILON: float = 1e-6
RESOLVER_EPSILON: float = 1e-12
RUBRIC_VERSION: str = "1"

# FDD-014 §2.4 Delta rubric (design A, version "1")
RUBRIC_TABLE: dict[tuple[str, str], float] = {
    ("crash risk", "yes"): -0.30,
    ("crash risk", "partial"): -0.15,
    ("crash risk", "no"): 0.00,
    ("logic error", "yes"): -0.25,
    ("logic error", "partial"): -0.13,
    ("logic error", "no"): 0.00,
    ("test gap", "yes"): -0.15,
    ("test gap", "partial"): -0.08,
    ("test gap", "no"): 0.00,
    ("documentation", "yes"): -0.10,
    ("documentation", "partial"): -0.05,
    ("documentation", "no"): 0.00,
    ("style", "yes"): -0.05,
    ("style", "partial"): -0.03,
    ("style", "no"): 0.00,
    ("confirmation", "yes"): 0.10,
    ("confirmation", "partial"): 0.05,
    ("confirmation", "no"): 0.00,
}

VALID_CLAIM_TYPES = {k[0] for k in RUBRIC_TABLE.keys()}
VALID_VERIFIED = {k[1] for k in RUBRIC_TABLE.keys()}


def rubric_delta(claim_type: str, verified: str) -> float:
    """Return the delta for a given claim type and verification result."""
    key = (claim_type, verified)
    if key not in RUBRIC_TABLE:
        if claim_type not in VALID_CLAIM_TYPES:
            raise ValueError(f"Unknown claim_type '{claim_type}'; must be one of {sorted(VALID_CLAIM_TYPES)}")
        if verified not in VALID_VERIFIED:
            raise ValueError(f"Unknown verified '{verified}'; must be one of {sorted(VALID_VERIFIED)}")
    return RUBRIC_TABLE[key]


@dataclass(frozen=True)
class CritiqueDelta:
    criterion_id: str
    delta: float
    doubt: float = 0.0
    claim_type: Optional[str] = None
    verified: Optional[str] = None
    finding_id: Optional[str] = None
    source_id: str = "review_critique"
    rubric_delta: Optional[float] = None
    override: bool = False
    comment_text: Optional[str] = None
    rubric_version: str = RUBRIC_VERSION


@dataclass(frozen=True)
class AppliedAdjustment:
    criterion_id: str
    support_before: float
    support_after: float
    confidence_before: float
    confidence_after: float
    doubt_before: float
    doubt_after: float
    applied_delta: float
    source_id: str
    basis: str
    rubric_delta: Optional[float]
    override: bool
    rubric_version: str
    finding_id: Optional[str]
    claim_type: Optional[str]
    verified: Optional[str]
    comment_text: Optional[str]


@dataclass(frozen=True)
class AppliedCritique:
    frame: DecisionFrame
    adjustments: tuple[AppliedAdjustment, ...]
    unparsed_lines: tuple[str, ...] = ()


def parse_critique(text: str, source_id: str = "review_critique") -> list[CritiqueDelta]:
    """Parse markdown bullet list of critique tags into CritiqueDelta objects."""
    deltas: list[CritiqueDelta] = []
    lines = text.strip().splitlines()

    for line in lines:
        line_str = line.strip()
        if not line_str.startswith(("-", "*")):
            continue
        bullet_body = line_str.lstrip("-* ").strip()
        if not bullet_body.startswith("["):
            continue

        tag_pattern = re.compile(r"\[([a-zA-Z0-9_\-]+)\s*:\s*([^\]]+)\]")
        tags: dict[str, str] = {}
        last_match_end = 0

        for match in tag_pattern.finditer(bullet_body):
            key = match.group(1).strip().lower()
            val = match.group(2).strip()
            tags[key] = val
            last_match_end = match.end()

        comment_text = bullet_body[last_match_end:].strip().lstrip(":").strip() or None

        criterion_id = tags.get("criterion")
        if not criterion_id:
            continue

        claim_type = tags.get("claim")
        verified = tags.get("verified")
        finding_id = tags.get("finding")
        raw_doubt = tags.get("doubt")
        raw_delta = tags.get("delta")

        doubt = 0.0
        if raw_doubt is not None:
            try:
                doubt = float(raw_doubt)
            except ValueError:
                doubt = 0.0

        if claim_type is not None:
            claim_type = claim_type.lower()
        if verified is not None:
            verified = verified.lower()

        r_delta: Optional[float] = None
        if claim_type and verified:
            try:
                r_delta = rubric_delta(claim_type, verified)
            except ValueError:
                r_delta = None

        if raw_delta is not None:
            try:
                delta_val = float(raw_delta)
            except ValueError:
                delta_val = r_delta if r_delta is not None else 0.0
            override = r_delta is not None and abs(delta_val - r_delta) > 0.005
        else:
            delta_val = r_delta if r_delta is not None else 0.0
            override = False

        deltas.append(
            CritiqueDelta(
                criterion_id=criterion_id,
                delta=delta_val,
                doubt=doubt,
                claim_type=claim_type,
                verified=verified,
                finding_id=finding_id,
                source_id=source_id,
                rubric_delta=r_delta,
                override=override,
                comment_text=comment_text,
            )
        )

    return deltas


def _logit(p: float) -> float:
    p_clamped = max(TARGET_EPSILON, min(1.0 - TARGET_EPSILON, p))
    return math.log(p_clamped / (1.0 - p_clamped))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def apply_critique(
    frame: DecisionFrame,
    option_id: str,
    deltas: Sequence[CritiqueDelta],
    *,
    kappa: float = KAPPA_DEFAULT,
) -> AppliedCritique:
    """Apply critique deltas to the specified option in a DecisionFrame."""
    target_opt = next((o for o in frame.options if o.action.id == option_id), None)
    if not target_opt:
        return AppliedCritique(frame=frame, adjustments=())

    adjustments: list[AppliedAdjustment] = []
    ev_by_crit: dict[str, list[EvidencePoint]] = defaultdict(list)
    for ev in target_opt.evidence:
        ev_by_crit[ev.criterion_id].append(ev)

    for delta in deltas:
        cid = delta.criterion_id
        pts = ev_by_crit.get(cid, [])
        if pts:
            sum_c = sum(p.confidence for p in pts) or 1.0
            curr_s = sum(p.support * p.confidence for p in pts) / sum_c
            curr_c = max(p.confidence for p in pts)
        else:
            curr_s = 0.5
            curr_c = 0.5

        curr_d = 1.0 - curr_c
        new_d = max(0.0, min(1.0 - CONFIDENCE_FLOOR, curr_d + delta.doubt))
        new_c = max(CONFIDENCE_FLOOR, 1.0 - new_d)

        # Log-odds shift
        l_curr = _logit(curr_s)
        l_new = l_curr + delta.delta
        new_s = max(0.0, min(1.0, _sigmoid(l_new)))

        # Update evidence points for this criterion
        adj_ev = EvidencePoint(
            criterion_id=cid,
            source_id=delta.source_id,
            support=round(new_s, 4),
            confidence=round(new_c, 4),
        )
        ev_by_crit[cid] = [adj_ev]

        basis = "explicit" if delta.override or delta.rubric_delta is None else "rubric"

        adjustments.append(
            AppliedAdjustment(
                criterion_id=cid,
                support_before=round(curr_s, 4),
                support_after=round(new_s, 4),
                confidence_before=round(curr_c, 4),
                confidence_after=round(new_c, 4),
                doubt_before=round(curr_d, 4),
                doubt_after=round(new_d, 4),
                applied_delta=delta.delta,
                source_id=delta.source_id,
                basis=basis,
                rubric_delta=delta.rubric_delta,
                override=delta.override,
                rubric_version=delta.rubric_version,
                finding_id=delta.finding_id,
                claim_type=delta.claim_type,
                verified=delta.verified,
                comment_text=delta.comment_text,
            )
        )

    # Reconstruct updated option and frame
    new_evidence: list[EvidencePoint] = []
    for c in frame.criteria:
        if c.id in ev_by_crit:
            new_evidence.extend(ev_by_crit[c.id])

    updated_opt = DecisionOption(action=target_opt.action, evidence=tuple(new_evidence))
    new_options = tuple(updated_opt if o.action.id == option_id else o for o in frame.options)

    new_frame = DecisionFrame(
        task=frame.task,
        options=new_options,
        criteria=frame.criteria,
        uncertainty_penalty=frame.uncertainty_penalty,
        minimum_margin=frame.minimum_margin,
    )

    return AppliedCritique(frame=new_frame, adjustments=tuple(adjustments))


def to_episode_metadata(applied: Optional[AppliedCritique]) -> dict[str, Any]:
    """Convert applied adjustments into episode metadata dictionary."""
    if not applied:
        return {"critique_adjustments": []}
    return {
        "critique_adjustments": [
            {
                "criterion_id": a.criterion_id,
                "support_before": a.support_before,
                "support_after": a.support_after,
                "confidence_before": a.confidence_before,
                "confidence_after": a.confidence_after,
                "doubt_before": a.doubt_before,
                "doubt_after": a.doubt_after,
                "applied_delta": a.applied_delta,
                "source_id": a.source_id,
                "basis": a.basis,
                "rubric_delta": a.rubric_delta,
                "override": a.override,
                "rubric_version": a.rubric_version,
                "finding_id": a.finding_id,
                "claim_type": a.claim_type,
                "verified": a.verified,
                "comment_text": a.comment_text,
            }
            for a in applied.adjustments
        ]
    }
