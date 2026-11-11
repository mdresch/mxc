---
artifact_id: resource-foundation-team-operating-charter
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-4
pmbok_process: Lead the Team
depends_on:
  - 7.C-1
  - 7.C-3
---

# Resource Team Operating Charter — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c4-charter-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c4-charter-2026-11-10.adjudication.json).

## Shared purpose and working agreements

- Deliver **17** story packages **1.1.1–1.6.4** through **`implement-story`** with contract tests green on the integration branch.
- **Tier A:** one integration story at a time; **lead specialist** claims in [Project-Status-Register.md](../../../../registers/Project-Status-Register.md) §5 before work.
- **Reporting specialists** coordinate through the lead for that WBS (daily or per-stand-up); deliver partial PRs or branches to the lead for integration.
- **Human WD** is the performance unit for capacity; agents (**V-AGT**) report to the active **lead** for the WBS.
- Escalate cross-pillar design conflicts to **R-ARC** within 1 WD; if lead vs reporting role boundary is unclear, **R-PM** decides within 1 WD.

## Roles and authority boundaries

| Role | May decide | Must escalate | Evidence |
|---|---|---|---|
| **R-PLT** | Story technical approach, sandbox runs, Tier B lane scope | Cross-pillar sequencing change, reserve consume | PR + contracts |
| **R-REL** | Image pipeline, checkpoint naming | Platform API breaking change | VHDX manifest |
| **R-SEC** | Egress / sterility implementation | Weakening default-deny posture | Sec AC sign-off |
| **R-SRE** | Pool thresholds in story scope | Shared host capacity beyond charter | Metrics / runbooks |
| **R-QA** | Contract structure for story | Scope creep AC | RED/GREEN log |
| **R-PM** | Queue order per schedule CP | Stage 8 issuance | Registers, gates |
| **R-ARC** | Architecture guidance | Baseline rebaseline | ADR trail |

## Conflict and performance response

1. **Over-allocation:** PM rebaselines capacity or shifts WBS primary per [Resource-Utilization-and-Control-Protocol.md](Resource-Utilization-and-Control-Protocol.md).
2. **Skills gap:** Contractor SOW or training spike—record in Q-RES register on manifest.
3. **Tooling unavailable:** Halt Tier A claim; update Project-Status-Register §5 bake lock.
