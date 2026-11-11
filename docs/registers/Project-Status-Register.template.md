---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "<project sponsor / lead>"
last_updated: "<date this project starts using it>"
---

# Project Status Register — <project>

> **Purpose:** The single place to answer, in under a minute, "which Phase and which Stage is this project
> at right now, what just finished, and what's next." Every other register answers a narrower question
> (risks, audits, lessons, improvements, story steps) — this one is the index into all of them.
>
> **This is not a governed approval artifact** (no `approve-*` policy gates it) and it is not append-only.
> It is overwritten in place whenever the project's orientation changes.

## Why this register exists (lesson, not speculation)

Confirmed real case (Enterprise Work Hierarchy): a human sponsor picked the project back up and asked
"which Phase and Stage are we at?" The first answer was wrong — it quoted an Epic document's own
`lifecycle_stage` frontmatter (`Stage 7`), which turned out to be that document's *authoring-time* label,
not the project's actual current position. By the time the question was asked, the project had already
cleared Stage 7 (Integrated PMP) *and* Stage 8 (Implementation Readiness Gate) for that same Epic — the
correct answer was one stage ahead of what the Epic's own frontmatter still said. Two separate problems
caused this, both worth guarding against here:

1. **Different document types in this methodology independently overload the same stage number.** A BRD,
   an FDD, an Epic, and the PMP can each claim "Stage 7" while meaning something different by it. Don't
   resolve "what stage are we at" by reading any single artifact's own frontmatter.
2. **Model/session cutoffs can happen abruptly, mid-story, without a clean announcement that a limit is
   close.** Reconstructing project position after an unannounced cutoff, from scattered documents, is
   slow and error-prone exactly when you can least afford it. A single, deliberately-maintained snapshot
   avoids both problems — but only if it is kept current more often than "once per Epic."

## 1. Current Orientation (read this first)

| Field | Value |
|---|---|
| **Current Phase** | *(e.g. "Phase 2")* |
| **Current PMP Baseline** | *(e.g. `PMP-BL-v2.0.0`)* |
| **Session close-off checkpoint** | *(Phase, Stage, and Epic/Story in flight right now — cite the `GOV-EX-###` gate-closure entries in `Audit-Register.md` that establish it, not any single document's own `lifecycle_stage` frontmatter. This is the line to re-read first when resuming work, or if a session ends without a clean handoff.)* |
| **Current macro Stage** (this methodology's lifecycle chain, see `docs/chain-coverage.md`) | *(state both the aggregate project-level stage AND whether the specific Epic/Story in flight has actually reached it yet — they can differ.)* |
| **Last Epic/unit of work fully completed** | *(what, and its closing evidence — breakout recap register entries, audit record ID)* |
| **Next Epic/unit of work to implement** | *(what, and its current readiness — which gates are already cleared, which story is first)* |
| **Last commit on the base branch** | *(hash + one-line summary)* |
| **Open side-thread outside the formal loop** | *(anything implemented directly without a dedicated ADR/BRD/FDD/Story — name it here so it isn't lost, don't retroactively fabricate governance paperwork for it)* |
| **Stage-label overload caveat (if this project's docs exhibit it)** | *(if more than one document type in this project reuses the same stage number for different meanings — confirmed true in Enterprise Work Hierarchy — record which document types do it and what each means by it, so a future reader doesn't repeat the Why-this-exists mistake above.)* |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| *(row per phase)* | | | *(cite the Stage 17 Adaptation Plan / Stage 18 Intent Refinement gate records that closed it, if closed)* |

## 3. Epic/Unit-of-Work Status (all phases)

| Epic | Title | Phase | Status | Stories Executed |
|---|---|---|---|---|
| *(one row per Epic or equivalent unit of work; keep this in sync with `Story-Execution-Register.md`, don't duplicate its per-story detail — just the completion status)* | | | | |

## 4. How to keep this current

- **After every Epic's Step 9 breakout/recap** (`implement-story` SKILL.md): update §1 ("Last … completed" / "Next … to implement" / "Session close-off checkpoint") and flip that Epic's row in §3.
- **Before starting a new Epic's first story:** confirm §1's "Next … to implement" still matches what's about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and append the new Phase's row.
- **At any natural pause, not only at Epic boundaries** — a decision made, a correction applied, before starting work that will take many steps. Session/model cutoffs do not always announce themselves in advance; treat this update as cheap, frequent insurance, not a formal gate.
- **Any out-of-loop work** (built directly, no ADR/BRD/FDD/Story) gets one line in §1's "Open side-thread" field, not a fabricated Epic/Story entry elsewhere.
- This register is **not** append-only and carries **no version bump on every edit** — same convention as `Story-Execution-Register.template.md`'s "live" framing. Only `last_updated` changes.
