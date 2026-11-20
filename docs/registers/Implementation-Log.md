---
register: "implementation-log"
governed_by: "implement-story skill, Step 7"
---

# Implementation Log — <project name>

Append-only. One entry per completed story, written after the implementation commit exists. Never edited once merged. A mistake is fixed by a new dated **Correction** entry that names the entry it corrects, not by rewriting the old one.

**Commit hash rule.** Commit the implementation first, then record that commit's hash in the log in a separate follow-up commit. Do not amend the implementation commit after logging it: an amend changes the hash and leaves the log pointing at a commit that is not in the base branch.

<!--
Copy this block per story.

## Story <N.M> — <title>
- **Commit:** `<hash of the implementation commit>`
- **Date:** <date>
- **Branch:** `feat/story-<N.M>`
- **Source ADR / BRD / FDD:** ADR-<NNN>, BRD-<NNN>, FDD-<NNN>
- **Files Modified/Created:**
  - `<path>` (<what changed>)
- **Validation:**
  - AC_0 ... AC_n: <how each criterion is met>
  - Observed RED first: <how many contract tests failed before implementation>
  - Story contract: <file> <n> passed
  - Full suite: <command, passed/skipped counts>. Name every path excluded and why; never call a partial run the entire suite.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - I1: <reading chosen, and where it is recorded>
- **Open for a human:** <approvals or decisions still needed>
- **Breakout recap:** <LL-### entries, a no-new-lessons sign-off, or "pending, last story of the epic">
-->
