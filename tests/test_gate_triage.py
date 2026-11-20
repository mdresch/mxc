"""IMP-030 and IMP-017: the PR gate checks triage lines a PR adds and respects maintainer triage."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import pr_gate
from critique_evidence import CritiqueDelta
from review_triage import parse_triage_line

GOOD = "Q-145-1 | logic error | verified: yes | decision: accepted | real defect | fix: abc1234"
BAD_CLAIM = "Q-145-2 | auditability | verified: yes | decision: accepted | reason | fix: none"
DECLINED = "Q-123-1 | logic error | verified: no | decision: declined | not a defect | fix: none"

DIFF = f"""diff --git a/src/x.py b/src/x.py
+++ b/src/x.py
+`{BAD_CLAIM}`
diff --git a/implementation-log.md b/implementation-log.md
+++ b/implementation-log.md
 context `{GOOD}` already there
+- triage: `{GOOD}`
+- prose without a triage line
-removed `{BAD_CLAIM}`
"""


def _delta(finding: str, criterion: str = "correctness", value: float = -0.25) -> CritiqueDelta:
    return CritiqueDelta(criterion_id=criterion, delta=value, finding_id=finding)


def test_only_lines_added_to_the_implementation_log_are_read() -> None:
    assert pr_gate.added_triage_lines(DIFF) == [GOOD]


def test_a_claim_type_outside_the_vocabulary_is_an_error() -> None:
    records, errors = pr_gate.check_triage_lines([GOOD, BAD_CLAIM])
    assert [r.finding_id for r in records] == ["Q-145-1"]
    assert len(errors) == 1 and "auditability" in errors[0]


def _pr(reviews: list[dict] | None = None) -> dict:
    return {
        "title": "t",
        "headRefOid": "abc1234",
        "statusCheckRollup": [{"name": "test", "conclusion": "SUCCESS"}],
        "files": [{"path": "src/f.py"}],
        "reviews": reviews or [],
        "comments": [],
    }


def test_the_gate_halts_on_a_triage_line_outside_the_vocabulary() -> None:
    diff = f"diff --git a/implementation-log.md b/implementation-log.md\n+`{BAD_CLAIM}`\n"
    with patch.object(pr_gate, "fetch_pr_data", return_value=_pr()), patch.object(
        pr_gate, "fetch_pr_diff", return_value=diff
    ):
        passed, reason, details = pr_gate.evaluate_pr(123, persist_episode=False)
    assert passed is False
    assert "Triage line outside the vocabulary" in reason and "auditability" in reason
    assert details["triage_errors"]


def test_a_declined_row_cancels_one_matching_defect_and_untriaged_ones_still_count() -> None:
    deltas = [_delta("REV1-CRIT-1"), _delta("REV1-CRIT-2")]
    kept, notes = pr_gate.reconcile_triage(deltas, [parse_triage_line(DECLINED)], 123)
    assert [d.finding_id for d in kept] == ["REV1-CRIT-2"]
    assert "declined" in notes[0]


def test_rows_for_other_prs_are_ignored() -> None:
    deltas = [_delta("REV1-CRIT-1")]
    kept, notes = pr_gate.reconcile_triage(deltas, [parse_triage_line(DECLINED)], 999)
    assert kept == deltas and notes == []


def test_an_accepted_row_keeps_the_review_defect_or_adds_the_rubric_delta() -> None:
    accepted = parse_triage_line(GOOD.replace("Q-145-1", "Q-123-1"))
    kept, _ = pr_gate.reconcile_triage([_delta("REV1-CRIT-1")], [accepted], 123)
    assert [d.finding_id for d in kept] == ["REV1-CRIT-1"]
    added, notes = pr_gate.reconcile_triage([], [accepted], 123)
    assert len(added) == 1 and added[0].finding_id == "Q-123-1" and added[0].delta < 0
    assert "added rubric delta" in notes[0]


def test_a_declined_triage_row_lifts_the_margin_a_review_defect_lowered() -> None:
    review = [
        {
            "author": {"login": "amazon-q[bot]"},
            "body": "Review Summary\n### Blocking issues found\n1. Logic error causing invalid state transitions.\n",
        }
    ]
    diff = f"diff --git a/implementation-log.md b/implementation-log.md\n+`{DECLINED}`\n"
    with patch.object(pr_gate, "fetch_pr_data", return_value=_pr(review)):
        with patch.object(pr_gate, "fetch_pr_diff", return_value=""):
            _, _, without = pr_gate.evaluate_pr(123, persist_episode=False)
        with patch.object(pr_gate, "fetch_pr_diff", return_value=diff):
            _, _, with_row = pr_gate.evaluate_pr(123, persist_episode=False)
    assert with_row["margin"] > without["margin"]
    assert with_row["triage_replay"] and not without["triage_replay"]


def test_fetch_pr_diff_decodes_as_utf8_and_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict = {}

    class Run:
        returncode = 1
        stdout = ""
        stderr = "boom"

    def fake(cmd, **kw):
        seen.update(kw)
        return Run()

    monkeypatch.setattr(pr_gate.subprocess, "run", fake)
    with pytest.raises(RuntimeError, match="boom"):
        pr_gate.fetch_pr_diff.real(1)  # type: ignore[attr-defined]
    assert seen["encoding"] == "utf-8" and seen["errors"] == "replace"


def test_a_declined_row_cannot_cancel_a_defect_an_accepted_row_kept() -> None:
    accepted = parse_triage_line(GOOD.replace("Q-145-1", "Q-123-1"))
    declined = parse_triage_line(DECLINED)
    kept, _ = pr_gate.reconcile_triage([_delta("REV1-CRIT-1")], [accepted, declined], 123)
    assert [d.finding_id for d in kept] == ["REV1-CRIT-1"]
    added, _ = pr_gate.reconcile_triage([], [accepted, declined], 123)
    assert [d.finding_id for d in added] == ["Q-123-1"]


def test_two_accepted_rows_each_stand_behind_their_own_defect() -> None:
    first = parse_triage_line(GOOD.replace("Q-145-1", "Q-123-1"))
    second = parse_triage_line(GOOD.replace("Q-145-1", "Q-123-2"))
    kept, _ = pr_gate.reconcile_triage([_delta("REV1-CRIT-1")], [first, second], 123)
    assert [d.finding_id for d in kept] == ["REV1-CRIT-1", "Q-123-2"]


def test_a_nested_implementation_log_is_not_the_triage_log() -> None:
    diff = f"diff --git a/docs/implementation-log.md b/docs/implementation-log.md\n+`{GOOD}`\n"
    assert pr_gate.added_triage_lines(diff) == []


def test_template_register_log_path_is_accepted() -> None:
    diff = (
        "diff --git a/docs/registers/Implementation-Log.md "
        f"b/docs/registers/Implementation-Log.md\n+`{GOOD}`\n"
    )
    assert pr_gate.added_triage_lines(diff) == [GOOD]


def test_unknown_claim_type_is_not_silently_mapped_to_correctness() -> None:
    """Q-7-2: claim type 'unknown' must not fall through to correctness."""
    from triage_replay import map_claim_to_criterion

    with pytest.raises(ValueError, match="no criterion mapping"):
        map_claim_to_criterion("unknown")


def test_reconcile_skips_unknown_claim_without_touching_correctness_deltas() -> None:
    """Q-7-2: an unknown claim must not cancel or reserve a correctness defect."""
    unknown = (
        "Q-7-2 | unknown | verified: yes | decision: declined | "
        "no criterion for this claim | fix: none"
    )
    deltas = [_delta("REV1-CRIT-1")]
    kept, notes = pr_gate.reconcile_triage(deltas, [parse_triage_line(unknown)], 7)
    assert kept == deltas
    assert any("skipped" in n and "unknown" in n for n in notes)
