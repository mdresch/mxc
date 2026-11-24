# Management-Plan Foundation Templates

These are source templates for the four Stage 7 foundation packs. The initializer copies them to `docs/project-docs/management-plans/`, renders `{{PROJECT_NAME}}` and `{{BASELINE_ID}}`, and never overwrites an existing project file.

| Pack | Stage | Artifacts | Entry condition |
|---|---|---:|---|
| Scope | 7.A | 6 + manifest | Charter and approved Stage 6 Requirements |
| Schedule | 7.B | 8 + manifest | Scope baseline and credible duration evidence (from Stage 6 Stories) |
| Resource | 7.C | 7 + manifest | Scope and Schedule baselines approved |
| Cost | 7.D | 6 + manifest | Scope/Schedule baselines and required Resource/Procurement evidence |

Each manifest holds its checklist, prerequisites, artifact registry, and separate plan gate. The approved pack rolls into its parent management plan; the approved parent-plan baseline then rolls into the PMP register with its manifest/hash and approval references. Generated files start as drafts with `pending` approval status. A template copy is never approval evidence; reviewers must resolve project-specific questions, record decisions, and calculate hashes only after approval.

Initialize from a new project root:

```powershell
python scripts/init_project.py --name <project-name>
```

Add the pack structure to an existing project without running governance-policy initialization:

```powershell
python scripts/init_management_plan_foundations.py --target-root <project-root> --project-name <project-name>
```

The existing SIDPA project initializer also invokes this scaffold. To create only selected packs, pass `--packs scope schedule` (or any subset of `scope`, `schedule`, `resource`, and `cost`) to the standalone script.
