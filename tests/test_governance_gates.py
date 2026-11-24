"""Unit and contract tests for SIDPA Template Bayesian Governance Gates.

Tests DecisionResolver, Critique-to-Evidence Ingestion Engine, and Pre-Flight
Specification Gatekeeper using Python standard library unittest.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure scripts and scripts/lib are in path
REPO_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for d in (str(REPO_ROOT), str(LIB_DIR), str(SCRIPTS_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)

from decision import (
    Action,
    DecisionCriterion,
    DecisionFrame,
    DecisionOption,
    DecisionResolver,
    DecisionStatus,
    Episode,
    EvidencePoint,
    LocalFileStore,
)
from critique_evidence import (
    CritiqueDelta,
    apply_critique,
    parse_critique,
    rubric_delta,
    to_episode_metadata,
)
from spec_gate import (
    AcceptanceCriterionSpec,
    StorySpec,
    normalize_story_id,
    run_adversarial_checks,
)


class TestDecisionResolver(unittest.TestCase):
    """Test Bayesian DecisionResolver robust utility and margin calculations."""

    def test_basic_resolution(self) -> None:
        crit = (
            DecisionCriterion("quality", weight=0.6),
            DecisionCriterion("speed", weight=0.4),
        )
        opt_a = DecisionOption(
            action=Action(id="opt_a"),
            evidence=(
                EvidencePoint("quality", "audit", 0.9, 0.8),
                EvidencePoint("speed", "bench", 0.8, 0.7),
            ),
        )
        opt_b = DecisionOption(
            action=Action(id="opt_b"),
            evidence=(
                EvidencePoint("quality", "audit", 0.5, 0.6),
                EvidencePoint("speed", "bench", 0.5, 0.6),
            ),
        )
        frame = DecisionFrame(
            task="test_task",
            options=(opt_a, opt_b),
            criteria=crit,
            uncertainty_penalty=0.1,
            minimum_margin=0.05,
        )

        resolver = DecisionResolver()
        result = resolver.resolve(frame)

        self.assertEqual(result.status, DecisionStatus.RESOLVED)
        self.assertIsNotNone(result.selected_action)
        self.assertEqual(result.selected_action.id, "opt_a")
        self.assertGreater(result.decision_margin, 0.05)
        self.assertEqual(len(result.assessments), 2)

    def test_ambiguous_tie_break(self) -> None:
        crit = (DecisionCriterion("c1", weight=1.0),)
        opt_a = DecisionOption(action=Action(id="a"), evidence=(EvidencePoint("c1", "s", 0.8, 0.8),))
        opt_b = DecisionOption(action=Action(id="b"), evidence=(EvidencePoint("c1", "s", 0.79, 0.8),))
        frame = DecisionFrame(task="tie", options=(opt_a, opt_b), criteria=crit, minimum_margin=0.05)

        resolver = DecisionResolver()
        result = resolver.resolve(frame)

        self.assertEqual(result.status, DecisionStatus.NEEDS_USER_TIE_BREAK)
        self.assertIsNone(result.selected_action)
        self.assertLess(result.decision_margin, 0.05)

    def test_episode_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = LocalFileStore(tmp_dir)
            ep = Episode(
                id="ep-101",
                agent_id="test-agent",
                action_id="approve",
                intent_summary="test intent",
                metadata={"status": "accepted"},
            )
            saved_id = store.save_episode(ep)
            self.assertEqual(saved_id, "ep-101")

            expected_file = Path(tmp_dir) / "episodes" / "test-agent" / "ep-101.json"
            self.assertTrue(expected_file.exists())
            with open(expected_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["id"], "ep-101")
            self.assertEqual(data["metadata"]["status"], "accepted")


class TestCritiqueEvidence(unittest.TestCase):
    """Test Epic 14 Lightweight Critique-to-Evidence Ingestion Engine."""

    def test_rubric_deltas(self) -> None:
        self.assertEqual(rubric_delta("crash risk", "yes"), -0.30)
        self.assertEqual(rubric_delta("logic error", "partial"), -0.13)
        self.assertEqual(rubric_delta("style", "no"), 0.00)
        self.assertEqual(rubric_delta("confirmation", "yes"), 0.10)

        with self.assertRaises(ValueError):
            rubric_delta("unknown claim", "yes")

    def test_parse_critique_bullets(self) -> None:
        markdown = """
        Review Notes:
        - [criterion: correctness] [claim: crash risk] [verified: yes] [finding: Q-1]: Uncaught KeyError
        - [criterion: test_coverage] [claim: test gap] [verified: partial] [finding: Q-2]
        - Not a bullet
        * [criterion: style] [claim: style] [verified: no]: cosmetic
        """
        deltas = parse_critique(markdown, source_id="pr_test")
        self.assertEqual(len(deltas), 3)

        self.assertEqual(deltas[0].criterion_id, "correctness")
        self.assertEqual(deltas[0].delta, -0.30)
        self.assertEqual(deltas[0].claim_type, "crash risk")
        self.assertEqual(deltas[0].finding_id, "Q-1")
        self.assertEqual(deltas[0].comment_text, "Uncaught KeyError")

        self.assertEqual(deltas[1].criterion_id, "test_coverage")
        self.assertEqual(deltas[1].delta, -0.08)

    def test_apply_critique_log_odds_shift(self) -> None:
        crit = (DecisionCriterion("correctness", weight=1.0),)
        opt = DecisionOption(action=Action(id="approve"), evidence=(EvidencePoint("correctness", "ci", 0.8, 0.8),))
        frame = DecisionFrame(task="pr_check", options=(opt,), criteria=crit)

        # Defect finding lowers support
        deltas = [CritiqueDelta(criterion_id="correctness", delta=-0.30, claim_type="crash risk", verified="yes")]
        applied = apply_critique(frame, option_id="approve", deltas=deltas)

        self.assertEqual(len(applied.adjustments), 1)
        adj = applied.adjustments[0]
        self.assertEqual(adj.criterion_id, "correctness")
        self.assertLess(adj.support_after, adj.support_before)

        # Check metadata conversion
        meta = to_episode_metadata(applied)
        self.assertIn("critique_adjustments", meta)
        self.assertEqual(len(meta["critique_adjustments"]), 1)


class TestSpecGate(unittest.TestCase):
    """Test Pre-Flight Specification & Contract Readiness Gatekeeper."""

    def test_normalize_story_id(self) -> None:
        self.assertEqual(normalize_story_id("1.1"), (1, "1.1"))
        self.assertEqual(normalize_story_id("story-18.4"), (18, "18.4"))
        self.assertEqual(normalize_story_id("epic-14-story-5"), (14, "14.5"))

    def test_adversarial_checks_completeness(self) -> None:
        spec = StorySpec(
            epic_num=1,
            story_id="1.1",
            title="Sample Story",
            status="Ready",
            role="developer",
            want="a feature",
            so_that="it works",
            acceptance_criteria=[
                AcceptanceCriterionSpec(0, "AC_0", "Returns float within 1e-6."),
                AcceptanceCriterionSpec(1, "AC_1", "Invalid argument raises ValueError."),
                AcceptanceCriterionSpec(2, "AC_2", "Passing empty list returns empty result."),
                AcceptanceCriterionSpec(3, "AC_3", "Missing metadata defaults defensively to None."),
            ],
        )

        deltas, interpretations, log = run_adversarial_checks(spec)
        self.assertTrue(len(deltas) >= 3)
        # All checks passed, no warnings should be raised for missing bounds
        warning_entries = [entry for entry in log if entry[0] == "WARN"]
        self.assertEqual(len(warning_entries), 0)


if __name__ == "__main__":
    unittest.main()
