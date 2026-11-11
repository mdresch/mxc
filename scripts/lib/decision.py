"""Standard-library Bayesian Decision and Governance Abstractions (SIDPA Template).

Provides lightweight, zero-dependency implementations of DecisionFrame, EvidencePoint,
DecisionOption, DecisionCriterion, DecisionResolver, PolicySnapshot, Episode, and
LocalFileStore compatible with agent-learning.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import math
from pathlib import Path
from typing import Any, Optional, Sequence
import uuid


class DecisionAuthority(str, Enum):
    FULL = "full"
    LOW = "low"
    STANDARD = "standard"


class DecisionStatus(str, Enum):
    RESOLVED = "resolved"
    NEEDS_USER_TIE_BREAK = "needs_user_tie_break"
    AMBIGUOUS = "ambiguous"
    CONSTRAINED = "constrained"


@dataclass(frozen=True)
class Action:
    id: str
    description: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        return cls(id=data["id"], description=data.get("description"), name=data.get("name"))


@dataclass(frozen=True)
class EvidencePoint:
    criterion_id: str
    source_id: str
    support: float  # [0.0, 1.0]
    confidence: float  # [0.0, 1.0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "source_id": self.source_id,
            "support": float(self.support),
            "confidence": float(self.confidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidencePoint:
        return cls(
            criterion_id=str(data["criterion_id"]),
            source_id=str(data["source_id"]),
            support=float(data["support"]),
            confidence=float(data["confidence"]),
        )


@dataclass(frozen=True)
class DecisionOption:
    action: Action
    evidence: tuple[EvidencePoint, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass(frozen=True)
class DecisionCriterion:
    id: str
    weight: float = 1.0
    minimum_sources: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "weight": float(self.weight),
            "minimum_sources": int(self.minimum_sources),
        }


@dataclass(frozen=True)
class DecisionFrame:
    task: str
    options: tuple[DecisionOption, ...]
    criteria: tuple[DecisionCriterion, ...]
    uncertainty_penalty: float = 0.1
    minimum_margin: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "options": [o.to_dict() for o in self.options],
            "criteria": [c.to_dict() for c in self.criteria],
            "uncertainty_penalty": float(self.uncertainty_penalty),
            "minimum_margin": float(self.minimum_margin),
        }


@dataclass(frozen=True)
class CriterionAssessment:
    criterion_id: str
    support: float
    confidence: float
    doubt: float
    penalized_support: float


@dataclass(frozen=True)
class ActionAssessment:
    action: Action
    robust_utility: float
    expected_utility: float
    criteria_assessments: dict[str, CriterionAssessment]


@dataclass(frozen=True)
class DecisionResult:
    status: DecisionStatus
    selected_action: Optional[Action]
    decision_margin: float
    assessments: tuple[ActionAssessment, ...]


class DecisionResolver:
    """Pure-Python Bayesian Decision Resolver evaluating robust utility and Pareto dominance."""

    def resolve(self, snapshot_or_frame: Any, frame: Optional[DecisionFrame] = None) -> DecisionResult:
        # Support both resolve(frame) and resolve(snapshot, frame)
        if frame is None and isinstance(snapshot_or_frame, DecisionFrame):
            df = snapshot_or_frame
        elif frame is not None:
            df = frame
        else:
            raise TypeError("Expected DecisionFrame argument")

        weights = {c.id: float(c.weight) for c in df.criteria}
        total_weight = sum(weights.values()) or 1.0
        penalty = float(df.uncertainty_penalty)

        assessments: list[ActionAssessment] = []

        for opt in df.options:
            ev_by_crit: dict[str, list[EvidencePoint]] = {c.id: [] for c in df.criteria}
            for ev in opt.evidence:
                if ev.criterion_id in ev_by_crit:
                    ev_by_crit[ev.criterion_id].append(ev)

            crit_map: dict[str, CriterionAssessment] = {}
            weighted_robust = 0.0
            weighted_expected = 0.0

            for c in df.criteria:
                w = weights[c.id]
                pts = ev_by_crit.get(c.id, [])
                if pts:
                    # Confidence-weighted pooled support
                    sum_conf = sum(p.confidence for p in pts) or 1.0
                    pooled_s = sum(p.support * p.confidence for p in pts) / sum_conf
                    pooled_c = max(p.confidence for p in pts)
                else:
                    pooled_s = 0.5
                    pooled_c = 0.1

                doubt = 1.0 - pooled_c
                penalized = max(0.0, min(1.0, pooled_s - penalty * doubt))
                crit_map[c.id] = CriterionAssessment(
                    criterion_id=c.id,
                    support=pooled_s,
                    confidence=pooled_c,
                    doubt=doubt,
                    penalized_support=penalized,
                )
                weighted_robust += w * penalized
                weighted_expected += w * pooled_s

            rob_u = weighted_robust / total_weight
            exp_u = weighted_expected / total_weight

            assessments.append(
                ActionAssessment(
                    action=opt.action,
                    robust_utility=round(rob_u, 4),
                    expected_utility=round(exp_u, 4),
                    criteria_assessments=crit_map,
                )
            )

        sorted_assess = sorted(assessments, key=lambda a: a.robust_utility, reverse=True)
        if not sorted_assess:
            return DecisionResult(
                status=DecisionStatus.AMBIGUOUS,
                selected_action=None,
                decision_margin=0.0,
                assessments=(),
            )

        best = sorted_assess[0]
        second = sorted_assess[1] if len(sorted_assess) > 1 else None
        margin = round(best.robust_utility - (second.robust_utility if second else 0.0), 4)

        if margin >= df.minimum_margin:
            status = DecisionStatus.RESOLVED
            chosen = best.action
        else:
            status = DecisionStatus.NEEDS_USER_TIE_BREAK
            chosen = None

        return DecisionResult(
            status=status,
            selected_action=chosen,
            decision_margin=margin,
            assessments=tuple(sorted_assess),
        )


@dataclass
class PolicySnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "default"
    task_id: str = "default"
    version: int = 1
    actions: list[Action] = field(default_factory=list)
    logits: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "version": self.version,
            "actions": [a.to_dict() for a in self.actions],
            "logits": self.logits,
            "metadata": self.metadata,
        }


@dataclass
class Episode:
    id: str
    agent_id: str
    action_id: str
    task_id: str = "default"
    task_name: str = ""
    policy_id: str = "default"
    policy_version: int = 1
    intent_summary: str = ""
    user_input: str = ""
    assistant_output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "action_id": self.action_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "intent_summary": self.intent_summary,
            "user_input": self.user_input,
            "assistant_output": self.assistant_output,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class LocalFileStore:
    """Pure-Python file store persisting episodes to data/agent-learning/store/episodes/."""

    def __init__(self, root_dir: Path | str) -> None:
        self.root = Path(root_dir)

    def save_episode(self, episode: Episode) -> str:
        ep_dir = self.root / "episodes" / episode.agent_id
        ep_dir.mkdir(parents=True, exist_ok=True)
        file_path = ep_dir / f"{episode.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(episode.to_dict(), f, indent=2)
        return episode.id
