## Learned User Preferences

- Take lifecycle document templates from the sibling `sidpa-template` repo (`D:\Source\repos\sidpa-template`) and instantiate them in this repo, including the Spark Capture form.
- Save architecture decision records to the designated folder `01 Architecture Decisions (ADR)` at `C:\Users\menno\Documents\Second Brain\wiki\Projects\MXC\01 Architecture Decisions (ADR)`.

## Learned Workspace Facts

- SIDPA/PMBOK governance is initialized here from `sidpa-template` with `scripts/init_project.py --name mxc`. The policy agent id is `mxc-governance`. `agent-learning-governance` is separate and was left unchanged.
- Stage 1 working documents live in `docs/project-docs/`. The Spark Capture is `docs/project-docs/Spark-Capture.md`. The policy store is `data/agent-learning/store/`. `.claude/` is gitignored, so skills under `.claude/skills/` stay local.
- Project details and ADRs use topic pillars TP-01 Isolation, TP-02 Ingress, TP-03 Image supply, TP-04 Paused footprint, TP-05 Session sterility, and TP-06 Pool and wake hygiene. Each ADR has one primary pillar; a second pillar is optional. These are coverage categories, separate from the architecture suite document layers named Pillar I–IV.
