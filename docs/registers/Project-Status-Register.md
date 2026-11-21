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
| **Current Phase** | Phase 1 (Core Foundation & Standby Fleet) |
| **Current PMP Baseline** | `PMP-BL-v1.0.0` |
| **Session close-off checkpoint** | Phase 1, Stage 10 (Execution: Epic 002 Stories 2.1..2.3 completed, contracts verified, merged to `feat/hyperv-v2-rebased`) |
| **Current macro Stage** | Stage 10 (Execution & Verification) |
| **Last Epic/unit of work fully completed** | Epic 002: Connection-buffering ingress gateway (`LL-003`, `IMP-MXC-002`) |
| **Next Epic/unit of work to implement** | Epic 003: Production base image and warm checkpoint (Story 3.1 — Clean production VHDX image bake) |
| **Last commit on the base branch** | `ece4a280` (docs(US-02.3): update story execution register merge status) |
| **Open side-thread outside the formal loop** | None |
| **Stage-label overload caveat (if this project's docs exhibit it)** | Standard SIDPA convention: Stage 6 decomposes ADR/BRD/FDD/Stories, Stage 7 ratifies subsidiary plans & PMP, Stage 10 tracks execution. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Phase 1 | `PMP-BL-v1.0.0` | Active (Epic 001 & Epic 002 complete, Epic 003 in flight) | — |

## 3. Epic/Unit-of-Work Status (all phases)

| Epic | Title | Phase | Status | Stories Executed |
|---|---|---|---|---|
| Epic 001 | Type-1 Hyper-V Generation 2 instead of a container namespace | Phase 1 | Complete | Story 1.1, Story 1.2 (2/2) |
| Epic 002 | Connection-buffering ingress gateway | Phase 1 | Complete | Story 2.1, Story 2.2, Story 2.3 (3/3) |
| Epic 003 | Production base image and warm checkpoint | Phase 1 | Ready | Story 3.1, Story 3.2 (0/2) |
| Epic 004 | Paused RAM standby and footprint readings | Phase 1 | Ready | Story 4.1, Story 4.2, Story 4.3 (0/3) |
| Epic 005 | Transient differencing disk and session sterility | Phase 1 | Ready | Story 5.1, Story 5.2, Story 5.3 (0/3) |
| Epic 006 | Watermark pool and wake hygiene | Phase 1 | Ready | Story 6.1, Story 6.2, Story 6.3, Story 6.4 (0/4) |

## 4. How to keep this current

- **After every Epic's Step 9 breakout/recap** (`implement-story` SKILL.md): update §1 ("Last … completed" / "Next … to implement" / "Session close-off checkpoint") and flip that Epic's row in §3.
- **Before starting a new Epic's first story:** confirm §1's "Next … to implement" still matches what's about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and append the new Phase's row.
- **At any natural pause, not only at Epic boundaries** — a decision made, a correction applied, before starting work that will take many steps. Session/model cutoffs do not always announce themselves in advance; treat this update as cheap, frequent insurance, not a formal gate.
- **Any out-of-loop work** (built directly, no ADR/BRD/FDD/Story) gets one line in §1's "Open side-thread" field, not a fabricated Epic/Story entry elsewhere.
- This register is **not** append-only and carries **no version bump on every edit** — same convention as `Story-Execution-Register.template.md`'s "live" framing. Only `last_updated` changes.
