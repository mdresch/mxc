---
governance_policy: "none (sync record)"
---

# SIDPA template sync

Last sync from **sidpa-template v1.2.0**.

## Paths updated

- `scripts/init_project.py`
- `scripts/init_management_plan_foundations.py`
- `scripts/orchestrate_pmbok.py`
- `scripts/execute_approve_gate.example.py`
- `scripts/complete-story.mjs`
- `scripts/run-contracts.mjs`
- `scripts/brain/ (20 files)`
- `templates/management-plans/ (32 files)`
- `.claude/skills/ (5 files)`
- `docs/second-brain-lifecycle-and-scripts.md`
- `docs/registers/Project-Status-Register.template.md`
- `docs/registers/Continuous-Improvement-Register.template.md`
- `docs/project-docs/Status-Reports/Stage-8-Implementation-Authorization-Notice.template.md`
- `docs/policy-shapes/decision-frames/charter-approval.json`
- `docs/policy-shapes/episodes/EXAMPLE-pmp-approval-episode.json`
- `.github/instructions/sidpa-governance-qa.instructions.md`
- `approve-subsidiary-plan policy + shape`
- `package.json (sidpa lifecycle scripts)`
- `tests/sidpa/ (21 files)`
- `docs/chain-coverage.md` (refreshed from template)
- `docs/sequence-and-lessons.md` (refreshed from template)
- `scripts/sync_from_sidpa_template.py` (repeatable sync entry point)
- Foundation packs instantiated via `init_management_plan_foundations.py` (31 files)
- `approve-subsidiary-plan` registered under `mxc-governance`
- `docs/project-docs/Stakeholder-Register.{template,}.md` (lifecycle I1)
- `pmbok/lifecycle/stages.py` — `approve-subsidiary-plan` in `EXTRA_POLICIES`

## Re-run sync

```bash
python scripts/sync_from_sidpa_template.py
python scripts/init_management_plan_foundations.py --target-root . --project-name mxc
```

Preserves existing `docs/project-docs/*.md` artifacts, gate records, and Hyper-V docs.
