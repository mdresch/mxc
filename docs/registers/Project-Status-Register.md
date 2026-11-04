---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Cross-Cutting (All Process Groups)"
pmbok_process: "4.3 Direct & Manage Project Work (Orientation Snapshot)"
lifecycle_stage: "Live — tracks whichever stage is currently active"
governance_policy: "none (orientation snapshot, not a governed approval artifact)"
artifact_id: "project-status-register"
version: "1.0 (live — overwritten in place, not re-versioned, every time orientation changes)"
owner: "Menno Drescher"
last_updated: "2026-11-04"
---

# Project Status Register — MXC Hyper-V JIT (ADPA / SIDPA)

> **Purpose:** The single place to answer, in under a minute, "which Phase and which Stage is this project
> at right now, what just finished, and what's next." Every other register answers a narrower question
> (risks, audits, lessons, improvements, story steps) — this one is the index into all of them.
>
> Read this file for the active phase, stage, and epic. Story-by-story implementation evidence stays in
> [`Story-Execution-Register.md`](Story-Execution-Register.md) on `feat/hyperv-v2-rebased` (still the empty
> template there) and in the point-in-time audit [`docs/status/adr-story-audit.md`](../status/adr-story-audit.md).
> Do not re-audit every story to answer the orientation question.
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
| **Current Phase** | Initial phase. One open phase under `PMP-BL-v1.0.0`. The delivery slices in `docs/hyperv/architecture/IMPLEMENTATION_PLAN.md` (Phase 1–4) are inside this phase. They are not separate SIDPA phases and have no Stage 17 or Stage 18 close. |
| **Current PMP Baseline** | `PMP-BL-v1.0.0`, printed on the PMP and on ADR/BRD/FDD/epic 001–006. No `approve-pmp` gate file is in `docs/project-docs/gates/`. |
| **Session close-off checkpoint** | Initial phase. Requirement packs 001–006 are approved. Readiness gate not entered. No story in flight. This numbering is MXC's older `docs/chain-coverage.md` (requirements = 7, readiness = 8). Current `sidpa-template` @ `5fb4f20` calls that requirement band Stage 6 and the PMP Stage 7. Alignment evidence: `docs/status/sidpa-alignment.md` (4 Nov 2026, 10:41 Europe/Amsterdam). Story evidence remains `docs/status/adr-story-audit.md`. |
| **Current macro Stage** (MXC's older chain on `feat/hyperv-v2-rebased`, not the 4 Nov 2026 template) | **Requirement band for Epics 001–006.** Those epics have accepted ADRs and approved BRDs, FDDs, and story packs (gate files dated 30 Oct 2026). `validate-intent-foundation` is not recorded on any story. `implement-story` has no row in the Story Execution Register. The current template's chain (`5fb4f20`) places this band at Stage 6, the PMP at Stage 7, and readiness at Stage 8. MXC has not reached the template's Stage 7: `approve-pmp` has no gate file. |
| **Last Epic/unit of work fully completed** | None. No epic has a Step 9 breakout. `Lessons-Learned-Register.md` and `Continuous-Improvement-Register.md` are not instantiated. |
| **Next Epic/unit of work to implement** | **Epic 001 — Type-1 Hyper-V Generation 2.** Story packs are approved. Stage 8 is still open: run `validate-intent-foundation` and write the sign-off on the story status line before `implement-story`. First story after that gate is **1.1 Generation 2 isolation boundary**, then 1.2. Rust contracts use `cargo test` as recorded in `.github/instructions/rust.instructions.md`. Story worktrees branch from `feat/hyperv-v2-rebased`, not `main`. |
| **Last commit on the base branch** | Story base `feat/hyperv-v2-rebased` @ `06a630d4` (30 Oct 2026, 15:44 Europe/Amsterdam), `feat(hyperv): Server Core WebDev golden image, ADR-008, and harness tooling`. Repository default `main` @ `3d0d9dd0` (15 Oct 2026, 16:17 Europe/Amsterdam) has no Hyper-V ADR chain. |
| **Open side-thread outside the formal loop** | Hyper-V control plane, warm pool, JIT ingress harness, image bake/audit scripts, and the implementation plan's "complete" marks were built on `feat/hyperv-v2-rebased` with no `implement-story` row. Leave them in this cell. Do not invent epic or story paperwork to match that code. A later story run re-walks the code with `heal-contract-failure` and shows the new contract failing before trusting it. ADR-008 (authentication-gated leasing) was accepted under `approve-adr` on 4 Nov 2026, Europe/Amsterdam (gate `approve-adr-008-2026-11-04` on `cursor/approve-adr-008-73a6`, off `feat/hyperv-v2-rebased`). It still has no BRD, FDD, or epic, and no spark, hypothesis, or benefit id. ADR-007 stays inside accepted ADR-006 as story 6.3. |
| **Stage-label overload caveat (if this project's docs exhibit it)** | Confirmed. ADR frontmatter says `Stage 7 (Requirement: Architecture)`, BRD says `Stage 7 (Requirement: Business)`, FDD says `Stage 7 (Requirement: Solution)`, and each epic says `Stage 7 (Requirement: Story)`. The PMP frontmatter says `Stage 6 (Project)`. Those labels follow MXC's older chain file. `pmbok/lifecycle/stages.py` numbers the same documents differently again. Use the macro Stage cell above, and `docs/status/sidpa-alignment.md` when comparing with `sidpa-template`. |

## 2. Phase Status

| Phase | Baseline | Status | Closed via |
|---|---|---|---|
| Initial | `PMP-BL-v1.0.0` | Open. Stage 7 packs 001–006 approved on 30 Oct 2026. Stage 8 not entered. Stage 6 `approve-pmp` and Stage 2 `approve-charter` have no gate file under `docs/project-docs/gates/`. | Not closed. No approved Stage 17 Adaptation Plan and no approved Stage 18 Intent Refinement. |

## 3. Epic/Unit-of-Work Status (all phases)

Story counts below are pack size only. Executed counts stay 0 until `Story-Execution-Register.md` gains a row. Per-story step detail belongs in that register, not here.

| Epic | Title | Phase | Status | Stories Executed |
|---|---|---|---|---|
| 001 | Type-1 Hyper-V Generation 2 | Initial | Approved 30 Oct 2026. Next to implement after Stage 8. | 0 / 2 |
| 002 | Connection-buffering ingress gateway | Initial | Approved 30 Oct 2026. Waits on Epic 004 and Epic 006. | 0 / 3 |
| 003 | Production base image | Initial | Approved 30 Oct 2026. Image `winserv2025-prod-adpa.vhdx` is not in the catalog. | 0 / 2 |
| 004 | Paused RAM standby | Initial | Approved 30 Oct 2026. Follows Epic 001. | 0 / 3 |
| 005 | Transient differencing disk and egress whitelist | Initial | Approved 30 Oct 2026. Follows Epic 003. | 0 / 3 |
| 006 | Watermark pool, replenish, and wake hygiene | Initial | Approved 30 Oct 2026. Follows Epics 004 and 005. ADR-007 has no epic of its own; its behavior is story 6.3. | 0 / 4 |

## 4. How to keep this current

- **After every Epic's Step 9 breakout/recap** (`implement-story` SKILL.md): update §1 ("Last … completed" / "Next … to implement" / "Session close-off checkpoint") and flip that Epic's row in §3.
- **Before starting a new Epic's first story:** confirm §1's "Next … to implement" still matches what's about to be worked on.
- **At every Stage 17/18 Phase close:** update §2 and append the new Phase's row.
- **At any natural pause, not only at Epic boundaries** — a decision made, a correction applied, before starting work that will take many steps. Session/model cutoffs do not always announce themselves in advance; treat this update as cheap, frequent insurance, not a formal gate.
- **Any out-of-loop work** (built directly, no ADR/BRD/FDD/Story) gets one line in §1's "Open side-thread" field, not a fabricated Epic/Story entry elsewhere.
- This register is **not** append-only and carries **no version bump on every edit** — same convention as `Story-Execution-Register.template.md`'s "live" framing. Only `last_updated` changes.
- When `validate-intent-foundation` clears an epic, record that on the story status line and move the macro Stage cell to Stage 8 for that epic only. The other epics stay at Stage 7 until their own gate.
- When `npm run story:done` (or the Rust equivalent, a `cargo test` contract plus a Story Execution Register row) finishes a story, increment that epic's executed count here and leave the step grid in `Story-Execution-Register.md`.
