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
| Story 2.1 | Complete (`feat/story-2.1`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-002 / WBS 3.1) | Complete (`test_story_2_1_cold_wake_ttfb.py`) | Complete (`ingress-gateway/SKILL.md`) | Complete (`ingress_gateway.py`) | Complete (2 contracts + 60 suite pass) | Complete (`4d1fd8ca`) | Merged (`dc7ab685`) |
| Story 2.2 | Complete (`feat/story-2.2`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-002 / WBS 3.2) | Complete (`test_story_2_2_no_wake_caused_502_504.py`) | Complete (`ingress-gateway/SKILL.md`) | Complete (`ingress_gateway.py`) | Complete (2 contracts + 62 suite pass) | Complete (`e9e6e1c1`) | Merged (`f3ea4b37`) |
| Story 2.3 | Complete (`feat/story-2.3`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-002 / WBS 3.3) | Complete (`test_story_2_3_dual_routing_rules.py`) | Complete (`ingress-gateway/SKILL.md`) | Complete (`ingress_gateway.py`) | Complete (3 contracts + 65 suite pass) | Complete (`12659be9`) | Merged (`a96850b8`) |
| Story 3.1 | Complete (`feat/story-3.1`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-003 / WBS 4.1) | Complete (`test_story_3_1_production_image_audit.py`) | Complete (`production-image/SKILL.md`) | Complete (`production_image.py`) | Complete (23 contracts + 88 suite pass) | Complete (`836aadcc`) | Merged (`68fdf047`) |
| Story 3.2 | Complete (`feat/story-3.2`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-003 / WBS 4.2) | Complete (`test_story_3_2_warm_baseline_checkpoint.py`) | Complete (`production-image/SKILL.md`) | Complete (`production_image.py`) | Complete (5 contracts + 93 suite pass) | Complete (`af0b7bc3`) | Merged (`18892234`) |
| Story 4.1 | Complete (`feat/story-4.1`) | Complete (ADR/BRD/FDD/Story) | Complete (ADR-004 / WBS 5.1) | Complete (`test_story_4_1_zero_idle_cpu.py`) | Complete (`paused-ram-standby/SKILL.md`) | Complete (`paused_ram.py`) | Complete (5 contracts + 98 suite pass) | Pending commit | Pending merge |

## When a story's steps don't match this template's own assumed shape

Confirmed, twice, in the source projects: a drafted story can turn out to have no code deliverable at all, or an epic can turn out to have zero story-shaped entries in it. Neither is a flaw in `implement-story` — it's the loop correctly refusing to force a template onto work that doesn't have that shape. Reclassify into the Audit Register's Governance Exercises section (`Audit-Register.template.md`) rather than inventing a lighter-weight story variant for a category of one, or leaving a row half-filled here.

## Why no TaskPolicy exists for this register yet

Every real TaskPolicy in this methodology followed at least one real case (see `docs/root-cause-log.md`). A "did this story's steps actually complete correctly" policy has zero real cases to ground it on day one — building one now would mean inventing the decision shape, not deriving it. This register exists so that the *first* real story run produces exactly that case, the same pattern every policy in this chain has followed.

## Trigger for building that TaskPolicy

The moment a story's real run here surfaces a repeating judgment call (not just a one-off), log it, cite it in `docs/root-cause-log.md`, and build the policy from that real evidence — not before.
