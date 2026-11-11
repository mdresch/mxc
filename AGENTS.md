## Learned User Preferences

- Take lifecycle document templates from the sibling `sidpa-template` repo (`D:\Source\repos\sidpa-template`), instantiate them in this repo (including the Spark Capture form), and keep MXC aligned with the latest sidpa-template governance policies and templates.
- Save architecture decision records to the designated folder `01 Architecture Decisions (ADR)` at `C:\Users\menno\Documents\Second Brain\wiki\Projects\MXC\01 Architecture Decisions (ADR)`.
- For GitHub pull requests, prefer on-demand PR Approval Agent runs via the project `approve-pr` skill over the always-on GitHub PR Reviewer when token use matters; invoke explicitly (for example `approve PR #N`). Run the SIDPA Bayesian gatekeeper first with `pr-gate` / `python scripts/pr_gate.py <N>` when checking merge readiness.
- In schedule and cost baselines, express planned work as human developer or engineering effort in days; do not pre-estimate agentic effort actuals—leave those for execution-time tracking.
- When a task needs multiple specialists, record a lead plus specialists reporting to that lead.
- Do not invent payroll hourly rates; use market-conform placeholders only when actual payroll rates are unavailable.

## Learned Workspace Facts

- SIDPA/PMBOK governance is initialized here from `sidpa-template` with `scripts/init_project.py --name mxc`. The policy agent id is `mxc-governance`. `agent-learning-governance` is separate and was left unchanged.
- Stage 1 working documents live in `docs/project-docs/`. The Spark Capture is `docs/project-docs/Spark-Capture.md`. The policy store is `data/agent-learning/store/`. `.claude/` is gitignored, so skills under `.claude/skills/` stay local. Project Cursor skills (for example on-demand PR approval) live under `.cursor/skills/`. GitHub PR approval policy files belong under `.cursor/approval-policies/` or as `APPROVAL_POLICY.md`.
- Project details and ADRs use topic pillars TP-01 Isolation, TP-02 Ingress, TP-03 Image supply, TP-04 Paused footprint, TP-05 Session sterility, and TP-06 Pool and wake hygiene. Each ADR has one primary pillar; a second pillar is optional. These are coverage categories, separate from the architecture suite document layers named Pillar I–IV.
- PMP subsidiary plans and Stage 7 foundation packs live under `docs/project-docs/management-plans/` (scope, schedule, cost, resource, and related baselines).
- Product WBS IDs follow `1.{pillar}.{story}` (17 story packages) aligned to epics 001–006 and pillars TP-01–TP-06.
- Agentic parallel coding (v1): `docs/project-docs/Agentic-Parallel-Execution-Policy.md`, live queue `docs/registers/Implementation-Story-Queue.md`, orientation `docs/registers/Project-Status-Register.md` §5, worktree claim `node scripts/provision-story-worktree.mjs <WBS>`, base branch `feat/hyperv-v2-rebased`. Tier A = one integration story (schedule CP order); Tier B = up to three scaffold lanes.
