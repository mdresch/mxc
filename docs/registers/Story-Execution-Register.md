# Story Execution Register — <project>

| Field | Value |
|---|---|
| Version | 1.0 (live — accumulates as stories actually run) |
| Date | <date this project starts using it> |
| Status | Active, empty — no story has run through `implement-story` yet |
| Source | `.claude/skills/implement-story/SKILL.md` |

Centralized, structured record of which `implement-story` steps (0–8) actually completed for each story — not inferred after the fact from scattered artifacts (a contract's header comment, a `SKILL.md` field), each logged here as it happens. This is what a future step-confirmation TaskPolicy would need as real evidence to be built on anything but speculation — it does not exist yet because no story has run even once. Don't build one preemptively; let this register accumulate real cases first (see `docs/root-cause-log.md`'s own framing of this exact trade-off).

## Register

| Story | Step 0 Worktree | Step 1 Spec pyramid read | Step 2 Intent stated | Step 3 Contract (RED) | Step 4 SKILL.md | Step 5 Implement (GREEN) | Step 6 Validate | Step 7 Log | Step 8 Merge |
|---|---|---|---|---|---|---|---|---|---|
| Story 1.1 | Complete (`feat/story-1.1`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-001 / WBS 2.1) | Complete (`test_story_1_1_gen2_isolation.py`) | Complete (`hyperv-isolation/SKILL.md`) | Complete (`hyperv_isolation.py`) | Complete (3 contracts + 56 suite pass) | Complete (`9e454974`) | Merged (`e64bb1b0`) |
| Story 1.2 | Complete (`feat/story-1.2`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-001 / WBS 2.2) | Complete (`test_story_1_2_windows_subsystems.py`) | Complete (`hyperv-isolation/SKILL.md`) | Complete (`hyperv_subsystems.py`) | Complete (2 contracts + 58 suite pass) | Complete (`17c924e2`) | Merged (`a994569e`) |

## When a story's steps don't match this template's own assumed shape

Confirmed, twice, in the source projects: a drafted story can turn out to have no code deliverable at all, or an epic can turn out to have zero story-shaped entries in it. Neither is a flaw in `implement-story` — it's the loop correctly refusing to force a template onto work that doesn't have that shape. Reclassify into the Audit Register's Governance Exercises section (`Audit-Register.template.md`) rather than inventing a lighter-weight story variant for a category of one, or leaving a row half-filled here.

## Why no TaskPolicy exists for this register yet

Every real TaskPolicy in this methodology followed at least one real case (see `docs/root-cause-log.md`). A "did this story's steps actually complete correctly" policy has zero real cases to ground it on day one — building one now would mean inventing the decision shape, not deriving it. This register exists so that the *first* real story run produces exactly that case, the same pattern every policy in this chain has followed.

## Trigger for building that TaskPolicy

The moment a story's real run here surfaces a repeating judgment call (not just a one-off), log it, cite it in `docs/root-cause-log.md`, and build the policy from that real evidence — not before.
