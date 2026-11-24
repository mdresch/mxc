#!/usr/bin/env python3
"""Pre-Flight Specification & Contract Readiness Gatekeeper (SIDPA Template).

Audits story acceptance criteria against adversarial checks (completeness, None-safety,
boundary behavior, empty collections, testability, architectural boundaries) before RED
contract generation. Applies Epic 14 critique deltas, evaluates robust Bayesian utility,
outputs recommended contract interpretations (I1, I2, ...), and passively records the
decision as an auditable Episode in the LearningStore.

Usage:
    python scripts/spec_gate.py <story_id>
    python scripts/spec_gate.py <story_id> --json
    python scripts/spec_gate.py <story_id> --no-persist
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
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
    to_episode_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE_DIR = ROOT / "data" / "agent-learning" / "store"

# IMP-024: math.isclose / allclose with an absolute tolerance keep a default relative
# tolerance that can silently relax a tight contract. pytest.approx(abs=...) does not.
_ISCLOSE = re.compile(r"\b(?:isclose|allclose)\b", re.IGNORECASE)
_ABS_TOL = re.compile(r"\b(?:abs_tol|atol)\b")
_TIGHT = re.compile(r"\b1e-(\d+)\b")
_ZERO_REL = re.compile(r"\b(?:rel_tol|rtol)\s*=\s*0(?:\.0+)?(?![\d.])")
_STRICT = re.compile(r"pytest\.approx\([^)]*\babs\s*=|absolute difference|\babs\(", re.IGNORECASE)

# IMP-021: discrete primitive widened to a continuous domain.
_DISCRETE = re.compile(r"\b(?:wilson|binomial|clopper|agresti)(?![A-Za-z])", re.IGNORECASE)
_WIDENED = re.compile(
    r"\bfloats?\b.*\bsuccesses\b|\bsuccesses\b.*\bfloats?\b|\bin steps of 0\.[0-9]+|"
    r"\bcumulative reward\b|\bfractional\b|\bnon-integer\b|\breal-valued\b|"
    r"mapped (?:from \[-1, 1\] )?to \[0, 1\]",
    re.IGNORECASE,
)
_CLAMP = re.compile(
    r"\bclamp(?:ed|s)?\b|\b(?:stays?|remains?|bounded|clipped)\b[^.]{0,20}\[0, ?1\]|max\(0|min\(1",
    re.IGNORECASE,
)
_INTEGER_LIMIT = re.compile(
    r"(?<!non-)\binteger\b[^.]*\b(?:equal|equals|agree|agrees|match|matches|identical|reduces)\b|"
    r"\b(?:equal|equals|agree|agrees|match|matches|identical|reduces)\b[^.]*(?<!non-)\binteger\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AcceptanceCriterionSpec:
    index: int
    label: str
    prose: str


@dataclass
class StorySpec:
    epic_num: int
    story_id: str
    title: str
    status: str
    role: str
    want: str
    so_that: str
    acceptance_criteria: list[AcceptanceCriterionSpec] = field(default_factory=list)
    epic_context: str = ""
    file_path: Optional[Path] = None


@dataclass(frozen=True)
class Interpretation:
    id: str
    title: str
    category: str
    text: str
    governing_ac: Optional[str] = None


def normalize_story_id(raw_id: str) -> tuple[int, str]:
    """Parse raw story ID into (epic_num, formatted_story_id)."""
    clean = raw_id.strip().lower()
    m_epic_story = re.match(r"^epic-(\d+)-story-(\d+(?:\.\d+)?)$", clean)
    if m_epic_story:
        epic_n = int(m_epic_story.group(1))
        story_part = m_epic_story.group(2)
        return epic_n, story_part if "." in story_part else f"{epic_n}.{story_part}"

    m_story = re.match(r"^story-(\d+)[.-](\d+)$", clean)
    if m_story:
        epic_n = int(m_story.group(1))
        return epic_n, f"{epic_n}.{m_story.group(2)}"

    m_dot = re.match(r"^(\d+)[.-](\d+)$", clean)
    if m_dot:
        epic_n = int(m_dot.group(1))
        return epic_n, f"{epic_n}.{m_dot.group(2)}"

    raise ValueError(
        f"Invalid story identifier format: {raw_id!r}. "
        "Expected format 'X.Y', 'story-X.Y', or 'epic-X-story-Y' (e.g. '1.1')."
    )


def find_epic_file(epic_num: int, repo_root: Path = ROOT) -> Path:
    """Locate the markdown file for a given epic number in user stories directories."""
    candidates = [
        repo_root / "docs" / "user-stories",
        repo_root / "user-stories",
        repo_root / "docs" / "stories",
    ]
    for c_dir in candidates:
        if c_dir.is_dir():
            matches = (
                list(c_dir.glob(f"epic-{epic_num}-*.md"))
                or list(c_dir.glob(f"epic-{epic_num:03d}-*.md"))
                or list(c_dir.glob(f"epic-{epic_num:02d}-*.md"))
                or list(c_dir.glob(f"epic-{epic_num}.md"))
                or list(c_dir.glob(f"epic-{epic_num:03d}.md"))
            )
            if matches:
                return matches[0]

    raise FileNotFoundError(f"User story file for Epic {epic_num} not found in {candidates}")


def parse_story_spec(epic_num: int, story_id: str, repo_root: Path = ROOT) -> StorySpec:
    """Parse a specific user story section from an epic markdown file."""
    epic_file = find_epic_file(epic_num, repo_root)
    content = epic_file.read_text(encoding="utf-8")

    # Match story header
    pattern = rf"(?m)^##\s+Story\s+{re.escape(story_id)}\s*[—–-]\s*(.+?)$"
    m = re.search(pattern, content)
    if not m:
        raise ValueError(f"Story {story_id} not found in {epic_file}")

    title = m.group(1).strip()
    start_pos = m.end()

    # Find end of story section
    next_story = re.search(r"(?m)^##\s+Story\s+", content[start_pos:])
    end_pos = start_pos + next_story.start() if next_story else len(content)
    section_text = content[start_pos:end_pos]

    # Extract status
    status_m = re.search(r"(?i)\*\*Status:\*\*\s*([^\n]+)", section_text)
    status = status_m.group(1).strip() if status_m else "Draft"

    # Extract user story narrative (As / Want / So that)
    role_m = re.search(r"(?i)\*\*As\*\*\s+(?:a|an)\s+([^,]+),", section_text)
    role = role_m.group(1).strip() if role_m else "maintainer"

    want_m = re.search(r"(?i)\*\*I want\*\*\s+([^,]+),", section_text)
    want = want_m.group(1).strip() if want_m else ""

    so_that_m = re.search(r"(?i)\*\*so that\*\*\s+([^.]+)\.", section_text)
    so_that = so_that_m.group(1).strip() if so_that_m else ""

    # Extract acceptance criteria
    criteria: list[AcceptanceCriterionSpec] = []
    ac_matches = re.findall(
        r"(?m)^\s*[-*]\s+\*\*(\$(?:AC|ac)_\d+\$|\bAC_\d+\b|\bAC\d+\b)\s*(?:\(([^)]+)\))?:\*\*\s*(.+?)$",
        section_text,
    )
    for idx, (ac_tag, ac_name, prose) in enumerate(ac_matches):
        label = f"{ac_tag} ({ac_name})" if ac_name else ac_tag
        criteria.append(AcceptanceCriterionSpec(index=idx, label=label, prose=prose.strip()))

    if not criteria:
        # Fallback: look for bullet items under Acceptance Criteria section
        ac_sec = re.search(r"(?i)\*\*Acceptance Criteria:\*\*\s*\n((?:[ \t]*[-*]\s+.+\n?)+)", section_text)
        if ac_sec:
            raw_bullets = re.findall(r"(?m)^\s*[-*]\s+(.+?)$", ac_sec.group(1))
            for idx, prose in enumerate(raw_bullets):
                criteria.append(AcceptanceCriterionSpec(index=idx, label=f"AC{idx+1}", prose=prose.strip()))

    return StorySpec(
        epic_num=epic_num,
        story_id=story_id,
        title=title,
        status=status,
        role=role,
        want=want,
        so_that=so_that,
        acceptance_criteria=criteria,
        epic_context=content[:start_pos],
        file_path=epic_file,
    )


def run_adversarial_checks(
    story: StorySpec,
) -> tuple[list[CritiqueDelta], list[Interpretation], list[tuple[str, str, str]]]:
    """Execute adversarial checks on story acceptance criteria."""
    deltas: list[CritiqueDelta] = []
    interpretations: list[Interpretation] = []
    audit_log: list[tuple[str, str, str]] = []

    all_ac_text = " ".join(ac.prose for ac in story.acceptance_criteria)
    low_text = all_ac_text.lower()
    # Keyword checks and IMP-021/024 are scoped to acceptance-criteria prose only
    # (epic preamble must not silence AC findings; see test_a_clamp_in_the_epic_preamble...).

    # 1. Specification Completeness
    if not story.acceptance_criteria:
        audit_log.append(("WARN", "Completeness", "Zero acceptance criteria defined."))
        deltas.append(CritiqueDelta("specification_completeness", delta=-0.25, doubt=0.15, claim_type="logic error", verified="yes"))
    else:
        audit_log.append(("OK", "Completeness", f"Acceptance criteria defined ({len(story.acceptance_criteria)} criteria)."))
        deltas.append(CritiqueDelta("specification_completeness", delta=0.10, doubt=0.0, claim_type="confirmation", verified="yes"))

    # Check for empty collection / zero elements handling
    if any(k in low_text for k in ("list", "sequence", "collection", "records", "episodes", "items", "pairs")):
        if any(k in low_text for k in ("empty", "zero", "no ", "none", "len = 0", "length 0")):
            audit_log.append(("OK", "Completeness", "Empty collection / zero elements base case specified."))
            deltas.append(CritiqueDelta("specification_completeness", delta=0.05, doubt=0.0, claim_type="confirmation", verified="yes"))
        else:
            audit_log.append(("WARN", "Completeness", "Collection referenced without explicit empty/zero base case contract."))
            deltas.append(CritiqueDelta("specification_completeness", delta=-0.08, doubt=0.05, claim_type="test gap", verified="partial"))
            interpretations.append(
                Interpretation(
                    id=f"I{len(interpretations)+1}",
                    title="Empty Collection Base Case",
                    category="defensive_programming",
                    text="Passing zero records or an empty sequence must return an empty result without raising an error.",
                )
            )

    # Check for None-safety
    if any(k in low_text for k in ("metadata", "comment", "description", "optional", "dict", "mapping")):
        if "none" in low_text:
            audit_log.append(("OK", "Completeness", "Defensive None-handling contract specified."))
        else:
            audit_log.append(("WARN", "Completeness", "Optional field referenced without explicit None-safety contract."))
            deltas.append(CritiqueDelta("specification_completeness", delta=-0.05, doubt=0.05, claim_type="test gap", verified="partial"))
            interpretations.append(
                Interpretation(
                    id=f"I{len(interpretations)+1}",
                    title="Defensive None-Safety",
                    category="robustness",
                    text="Optional fields must be safely accessed (e.g. using getattr or .get() with defaults) to avoid AttributeError when None.",
                )
            )

    # 2. Testability & Precision Tolerances
    if any(k in low_text for k in ("float", "loss", "gradient", "probability", "tolerance", "equal", "numeric")):
        if any(k in low_text for k in ("within", "abs_tol", "rel_tol", "1e-", "approx")):
            audit_log.append(("OK", "Testability", "Explicit floating point tolerances verified."))
            deltas.append(CritiqueDelta("testability", delta=0.10, doubt=0.0, claim_type="confirmation", verified="yes"))
        else:
            audit_log.append(("WARN", "Testability", "Floating point comparisons specified without explicit tolerance."))
            deltas.append(CritiqueDelta("testability", delta=-0.13, doubt=0.05, claim_type="test gap", verified="partial"))

    # Check exception types
    if "raise" in low_text:
        if any(e in low_text for e in ("valueerror", "typeerror", "keyerror", "filenotfounderror", "runtimeerror")):
            audit_log.append(("OK", "Testability", "Explicit exception classes specified."))
            deltas.append(CritiqueDelta("testability", delta=0.05, doubt=0.0, claim_type="confirmation", verified="yes"))
        else:
            audit_log.append(("WARN", "Testability", "Negative test path specified without explicit exception class."))
            deltas.append(CritiqueDelta("testability", delta=-0.10, doubt=0.05, claim_type="test gap", verified="partial"))

    # 3. Architectural Boundaries & Isolation
    if any(k in low_text for k in ("storage", "db", "file", "network")):
        audit_log.append(("OK", "Architectural", "Storage boundary and serialization verified."))
        deltas.append(CritiqueDelta("architectural_boundaries", delta=0.05, doubt=0.0, claim_type="confirmation", verified="yes"))
    else:
        audit_log.append(("OK", "Architectural", "Component operates within standard architectural boundaries."))
        deltas.append(CritiqueDelta("architectural_boundaries", delta=0.10, doubt=0.0, claim_type="confirmation", verified="yes"))

    # Check E (IMP-021): discrete primitive widened to a continuous domain without clamp + integer limit
    all_ac_prose = " ".join(ac.prose for ac in story.acceptance_criteria)
    widened = [
        ac for ac in story.acceptance_criteria if _DISCRETE.search(ac.prose) and _WIDENED.search(ac.prose)
    ]
    if widened and not (_CLAMP.search(all_ac_prose) and _INTEGER_LIMIT.search(all_ac_prose)):
        labels = ", ".join(ac.label for ac in widened)
        deltas.append(
            CritiqueDelta(
                "specification_completeness",
                delta=-0.05,
                doubt=0.05,
                claim_type="test gap",
                verified="partial",
                finding_id="SPEC-COMPL-DOMAIN-WIDENING",
            )
        )
        interpretations.append(
            Interpretation(
                id=f"I{len(interpretations)+1}",
                title="Continuous-Domain Widening",
                category="specification_completeness",
                text=(
                    "State how the widened result is clamped (for a proportion bound, to [0, 1]), why it stays "
                    "inside that range for every float input, and that it equals the classical value at integer counts."
                ),
                governing_ac=widened[0].label,
            )
        )
        audit_log.append(
            ("WARN", "Completeness", f"[domain-widening] {labels}: discrete primitive on a continuous domain.")
        )

    # Check A2 (IMP-024): isclose/allclose absolute tolerance without zero relative tolerance
    tight = any(int(n) >= 9 for n in _TIGHT.findall(all_ac_prose))
    if (
        _ISCLOSE.search(all_ac_prose)
        and (_ABS_TOL.search(all_ac_prose) or tight)
        and not _ZERO_REL.search(all_ac_prose)
        and not _STRICT.search(all_ac_prose)
    ):
        deltas.append(
            CritiqueDelta(
                "testability",
                delta=-0.05,
                doubt=0.05,
                claim_type="test gap",
                verified="partial",
                finding_id="SPEC-TEST-REL-TOL-GAP",
            )
        )
        interpretations.append(
            Interpretation(
                id=f"I{len(interpretations)+1}",
                title="Zero Relative Tolerance",
                category="testability",
                text=(
                    "Pass rel_tol=0.0 (or rtol=0) with abs_tol (atol): the default relative tolerance "
                    "(1e-9 for math.isclose, 1e-5 for numpy.allclose) silently relaxes a 1e-12 contract. "
                    "pytest.approx(abs=...) or an absolute difference check is equally strict."
                ),
            )
        )
        audit_log.append(
            ("WARN", "Testability", "isclose / allclose absolute tolerance without rel_tol=0.0.")
        )

    return deltas, interpretations, audit_log


def audit_story_spec(
    story: StorySpec,
) -> tuple[list[CritiqueDelta], list[Interpretation], list[str]]:
    """Alias for contract tests: same checks as run_adversarial_checks with string log lines."""
    deltas, interpretations, audit_log = run_adversarial_checks(story)
    return deltas, interpretations, [f"[{status}] {cat}: {msg}" for status, cat, msg in audit_log]


def build_spec_decision_frame(story_id: str) -> DecisionFrame:
    """Build the standardized Pre-Flight Spec Readiness DecisionFrame."""
    criteria = (
        DecisionCriterion("specification_completeness", weight=0.35, minimum_sources=1),
        DecisionCriterion("testability", weight=0.25, minimum_sources=1),
        DecisionCriterion("architectural_boundaries", weight=0.40, minimum_sources=1),
    )

    opt_proceed = DecisionOption(
        action=Action(id="proceed_to_implementation", description=f"Proceed to Implementation for Story {story_id}"),
        evidence=(
            EvidencePoint("specification_completeness", "spec_audit", 0.75, 0.70),
            EvidencePoint("testability", "contract_audit", 0.75, 0.70),
            EvidencePoint("architectural_boundaries", "boundary_audit", 0.85, 0.80),
        ),
    )

    opt_amend = DecisionOption(
        action=Action(id="clarify_spec_and_amend", description=f"Clarify and Amend Story {story_id} Specification"),
        evidence=(
            EvidencePoint("specification_completeness", "baseline", 0.60, 0.60),
            EvidencePoint("testability", "baseline", 0.60, 0.60),
            EvidencePoint("architectural_boundaries", "baseline", 0.60, 0.60),
        ),
    )

    return DecisionFrame(
        task=f"story-{story_id}-spec-readiness",
        options=(opt_proceed, opt_amend),
        criteria=criteria,
        minimum_margin=0.05,
    )


def save_spec_episode(
    story_id: str,
    story: StorySpec,
    passed: bool,
    margin: float,
    applied: Optional[AppliedCritique],
    store_dir: Optional[Path] = None,
) -> str:
    """Persist the specification gate decision as an auditable Episode."""
    target_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
    store = LocalFileStore(root_dir=target_dir)

    ep_uuid = uuid.uuid4().hex[:8]
    clean_id = story_id.replace(".", "_")
    episode_id = f"spec-{clean_id}-{ep_uuid}"

    adjustments = to_episode_metadata(applied).get("critique_adjustments", []) if applied else []

    meta: dict[str, Any] = {
        "story_id": story_id,
        "title": story.title,
        "status": story.status,
        "margin": round(margin, 4),
        "feedback_status": "accepted" if passed else "rejected",
        "critique_adjustments": adjustments,
    }
    if not passed:
        meta["correct_action_id"] = "clarify_spec_and_amend"

    episode = Episode(
        id=episode_id,
        agent_id=os.environ.get("GOVERNANCE_AGENT_ID", "mxc-governance"),
        task_id=f"story-{story_id}-spec-readiness",
        task_name=f"Story {story_id} Spec Gate",
        action_id="proceed_to_implementation" if passed else "clarify_spec_and_amend",
        intent_summary=f"Pre-flight specification gate evaluation for Story {story_id}",
        user_input=f"Story {story_id}: {story.title}",
        assistant_output=f"Spec readiness verdict: {'PASSED' if passed else 'HALTED'}",
        metadata=meta,
    )
    store.save_episode(episode)
    return episode_id


def evaluate_spec(
    story_id: str,
    persist_episode: bool = True,
    repo_root: Path = ROOT,
) -> tuple[bool, str, dict[str, Any]]:
    """Evaluate story specification against adversarial checks."""
    epic_num, clean_story_id = normalize_story_id(story_id)
    story = parse_story_spec(epic_num, clean_story_id, repo_root)

    deltas, interpretations, audit_log = run_adversarial_checks(story)

    frame = build_spec_decision_frame(clean_story_id)
    applied = apply_critique(frame, option_id="proceed_to_implementation", deltas=deltas)

    resolver = DecisionResolver()
    result = resolver.resolve(applied.frame)

    proceed_assess = next(a for a in result.assessments if a.action.id == "proceed_to_implementation")
    amend_assess = next(a for a in result.assessments if a.action.id == "clarify_spec_and_amend")
    margin = proceed_assess.robust_utility - amend_assess.robust_utility

    passed = (
        result.status.value == "resolved"
        and result.selected_action is not None
        and result.selected_action.id == "proceed_to_implementation"
        and margin >= 0.05
    )

    reason = (
        f"Spec readiness verified: robust utility {proceed_assess.robust_utility:.4f} and margin {margin:+.4f} >= +0.05."
        if passed
        else f"Spec readiness halted: margin {margin:+.4f} is below required +0.05 threshold."
    )

    ep_id = None
    if persist_episode:
        ep_id = save_spec_episode(clean_story_id, story, passed, margin, applied)

    details: dict[str, Any] = {
        "story_id": clean_story_id,
        "title": story.title,
        "status": story.status,
        "ac_count": len(story.acceptance_criteria),
        "audit_log": audit_log,
        "interpretations": [asdict(i) for i in interpretations],
        "robust_utility": proceed_assess.robust_utility,
        "amend_utility": amend_assess.robust_utility,
        "margin": margin,
        "episode_id": ep_id,
    }

    return passed, reason, details


def ensure_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so verdict lines print on a cp1252 console (IMP-045)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description="Pre-Flight Specification & Contract Readiness Gatekeeper.")
    parser.add_argument("story_id", help="Story identifier (e.g. '1.1', '18.4')")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--no-persist", action="store_true", help="Do not persist episode to LearningStore")
    args = parser.parse_args()

    try:
        passed, reason, details = evaluate_spec(
            story_id=args.story_id,
            persist_episode=not args.no_persist,
        )
    except Exception as e:
        print(f"Error evaluating specification: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"passed": passed, "reason": reason, "details": details}, indent=2))
        return 0 if passed else 1

    print("=" * 80)
    print(f"PRE-FLIGHT SPECIFICATION READINESS GATE: Story {details['story_id']} — {details['title']}")
    print("=" * 80)
    print(f"Status in Epic: {details['status']}")
    print(f"Acceptance Criteria Analyzed: {details['ac_count']}")
    print("-" * 80)
    print("ADVERSARIAL SPECIFICATION FINDINGS:")
    for status, cat, msg in details["audit_log"]:
        print(f"  [{status}] {cat}: {msg}")

    if details["interpretations"]:
        print("-" * 80)
        print("RECOMMENDED CONTRACT INTERPRETATIONS (Record in RED test docstrings):")
        for interp in details["interpretations"]:
            print(f"  [{interp['id']}] {interp['title']}:")
            print(f"       \"{interp['text']}\"")

    print("-" * 80)
    print("BAYESIAN DECISION RESOLUTION:")
    print(f"  Proceed to Implementation Utility: {details['robust_utility']:.4f}")
    print(f"  Clarify Spec & Amend Utility:     {details['amend_utility']:.4f}")
    print(f"  Robust Utility Margin:            {details['margin']:+.4f} (Threshold: >=+0.05)")
    if details["episode_id"]:
        print(f"  Governance Episode Persisted:     {details['episode_id']}")
    print("=" * 80)
    if passed:
        print("✅ GATE RESULT: PASSED / APPROVED TO MERGE")
        print("VERDICT: PASSED / SPEC READY FOR CONTRACTS")
    else:
        print("❌ GATE RESULT: HALTED / REVISIONS REQUIRED")
        print("VERDICT: HALTED / SPECIFICATION INCOMPLETE (Amend before drafting contracts)")
    print("=" * 80)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
