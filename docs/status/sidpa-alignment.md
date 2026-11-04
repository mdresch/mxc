# SIDPA alignment check

Checked 4 Nov 2026, 10:41 Europe/Amsterdam, against `mdresch/sidpa-template` @ `5fb4f20` (4 Nov 2026, 09:14 Europe/Amsterdam) and the MXC tree `feat/hyperv-v2-rebased` @ `06a630d4`, plus unmerged `cursor/approve-adr-008-73a6`.

MXC is on an earlier copy of the scaffold. It is not aligned to that template commit. `main` (`3d0d9dd0`) does not contain the chain at all.

Stage numbers below are the template's `docs/chain-coverage.md` at `5fb4f20`. MXC's own `docs/chain-coverage.md` still uses an older map: PMP as stage 6, requirements as stage 7, readiness as stage 8. `pmbok/lifecycle/stages.py` on the Hyper-V branch is a third map (ADR 5, BRD 6, FDD 7, TDS 8, stories 9, PMP 10) and is not in the template commit. The policy table in MXC's chain file still names `template-governance`. The live store is `mxc-governance`.

| Template stage | What the template requires | What MXC has |
|---|---|---|
| 1 Intent | Approved `Spark-Capture.md` and ideation under `approve-ideation` | Spark is written. The 29 Oct 2026 decision recommends `approve_ideation` and is still `needs_user_feedback`. No adjudication file. |
| 2 Objective | `Project-Charter.md` under `approve-charter` | Charter file is section headings only. No gate file. |
| 3 Hypothesis | `classify-hypothesis-status` on real outcomes | Every hypothesis in `Ideation-Document.md` is `Formulated`. The policy shape exists. It is not in `active-policies`, and no gate was run. |
| 4 Benefit | Approved business case and benefits statement | Business case accepted `approve_business_case` on 29 Oct 2026. Benefits statement is still Draft. Its 30 Oct decision recommends approval and has no adjudication. |
| 5 Pillars | `PILLARS-EXERCISE.md` and ADRs covering every pillar | No pillars file. `TP-01` through `TP-06` are named inside ADR-001–006. |
| 6 Requirement | Approved ADR, BRD, FDD, and user stories | Packs 001–006 accepted on 30 Oct 2026. ADR-008 is accepted only on unmerged `cursor/approve-adr-008-73a6` (4 Nov 2026) and has no BRD, FDD, or epic. |
| 7 Project | Approved PMP, nine subsidiary plans, foundation packs 7.A–7.D, `approve-subsidiary-plan` and `approve-pmp` | `PMP-BL-v1.0.0` is printed on the PMP and on packs 001–006. `approve-pmp` has no gate file. The PMP title is still "SIDPA Project". All nine subsidiary plans are scaffold sentences for "SIDPA Project". No foundation packs. No `approve-subsidiary-plan` shape. |
| 8 Readiness | `Stage-8-Implementation-Authorization-Notice.md` via `validate-intent-foundation` | Policy is installed. No notice, no gate file, no story sign-off. |
| 9 Deliverable | `implement-story`, rows in `Story-Execution-Register.md` | Skill is not tracked (`.claude/` is gitignored). Register is the empty template. Hyper-V code on this branch was built outside that loop. |
| 10 Verification | Contract tests and `heal-contract-failure` | Product tests exist. No story contract row. Skill is not tracked. |
| 11 Audit | Approved `Audit-Register.md` | Register is the empty template. Title is still `<project>`. |
| 12–15 Outcome through lesson | Observation, insight, and lessons registers | Not instantiated. `docs/hyperv/architecture/LESSONS_LEARNED.md` is outside this chain. |
| 16 Governance change | A real `classify-diff-type` / `escalate-diff-response` case | Shapes and active policies exist. No change record has been run. |
| 17 Adaptation | Approved `Adaptation-Plan.md` | File is still the template, including angle-bracket placeholders. |
| 18 Intent refinement | Approved `Intent-Refinement-Proposal.md` | Same. `docs/policy-shapes/decision-frames/adr-009-approval.json` cites `docs/adr/ADR-009-intent-refinement-and-cognitive-feedback-loop.md`, which is not in this repo. |

Template invariants that this tree does not meet:

1. Requirements are approved before the PMP baseline is locked. MXC prints `PMP-BL-v1.0.0` on approved requirements, and the PMP itself says `approve-pmp` must run before those requirements are finalized. Neither order has an `approve-pmp` adjudication.
2. A pillars exercise with full pillar coverage before detailed requirements. The six pillars are inside the ADRs. There is no pillars exercise document.
3. No implementation until the Stage 8 authorization notice. The Hyper-V control plane, pool, and ingress harness are already on the branch. The story register has no row.
4. Every approved artifact records the governing baseline. Packs 001–006 do. The baseline they record has not been through `approve-pmp`.

What does match the template's shape: policy JSON for the core `approve-*` gates, the local `mxc-governance` store, the ADR → BRD → FDD → epic folder layout for 001–006, and human-adjudicated gate files for those four requirement policies plus the business case.
