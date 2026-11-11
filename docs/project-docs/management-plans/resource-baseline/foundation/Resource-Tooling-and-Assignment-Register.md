---
artifact_id: resource-foundation-tooling-assignment-register
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.C-3
pmbok_process: Acquire Resources
depends_on:
  - 7.C-2
---

# Resource Tooling and Assignment Register — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-resource-7c3-tooling-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-resource-7c3-tooling-2026-11-10.adjudication.json).

| Resource / tool | Type | Assigned role(s) | WBS use | Availability | Constraint |
|---|---|---|---|---|---|
| Hyper-V Type-1 host (Gen2) | Physical / infra | R-PLT, R-REL, R-SEC, R-SRE | 1.1–1.6 integration | Org-owned; pool standby | One sandbox session per agent; serial integration per policy |
| MXC Hyper-V sandbox (MCP / pool VM) | Virtual | R-PLT, R-QA, V-AGT | `implement-story`, contract tests | Lease from warm pool | Airgap default; `set_network` for crate fetch |
| Windows guest golden image workspace | Virtual / storage | R-REL | 1.3.x | On host storage | VHDX bake lock when publishing |
| Rust toolchain (stable) | Virtual | R-PLT, R-SRE, R-QA | Rust deliverables | Repo-pinned | Sandbox builds only per `.cursorrules` |
| Node.js + contract test runner | Virtual | R-PLT, R-QA | JS contracts | Dev + CI | Align with `tests/contracts/` |
| PowerShell 7+ | Virtual | R-PLT, R-REL | Host automation | Windows | Elevated ops escalated to sponsor |
| **GitHub** Basic (subscription) | Virtual | All human roles | All stories | **€10/mo** | CAT-TOOL; branch `feat/hyperv-v2-rebased`; worktrees per WBS |
| **Cursor** (subscription) | Virtual | V-AGT, R-PLT | Tier A/B | **€16/mo** | CAT-TOOL; Q-CST-002 |
| **Gemini Antigravity** (subscription) | Virtual | V-AGT | Agent assist | **€25/mo** | CAT-TOOL; Q-CST-002 |
| **Claude Code** (subscription) | Virtual | V-AGT | Agentic coding | **€20/mo** | CAT-TOOL; Q-CST-002 |
| Benchmark harness `benchmark_jit_wake.py` | Virtual | R-PLT | 1.4.3, 1.6.3 | Repo | Evidence for parametric schedule |
| Observability / metrics (TBD product) | Virtual | R-SRE | 1.6.x | TBD at implement | Q-RES-004 |

## Human assignment placeholder (names TBD at Stage 8)

| Role ID | Named resource | Engagement | Backup | Notes |
|---|---|---|---|---|
| R-PLT | TBD | Payroll or contractor | TBD | **Lead** on 1.1, 1.2, 1.4; **reports to** R-REL lead on 1.3.x; **reports to** R-SEC lead on 1.5.x; etc. |
| R-REL | TBD | Payroll or contractor | R-PLT | **Lead** on 1.3.x |
| R-SEC | TBD | Payroll or contractor | R-ARC | **Lead** on 1.5.x |
| R-SRE | TBD | Payroll or contractor | R-PLT | **Lead** on 1.6.x |
| R-QA | TBD | Payroll or contractor | R-PLT | **Reporting** on all stories to active lead |
| R-PM | Menno Drescher (draft) | Payroll | Sponsor | **Lead** MS-07; **reporting** on 1.6.4 only |
| R-ARC | TBD | Fractional contractor | ADR authors | **Reporting** on 1.2.3 to R-PLT lead |

At Stage 8, fill a second table **per WBS**: lead name, each reporting specialist name (see [Resource-Role-Catalogue.md](Resource-Role-Catalogue.md) staffing matrix).

## Gaps and acquisition decisions

| Gap | Make / buy | Decision owner | Status |
|---|---|---|---|
| Dedicated SecOps FTE vs contractor SOW | Buy option open | PM + Procurement | open (Q-RES-003) |
| Second Hyper-V host for parallel Tier B | Use existing pool | R-PLT | assumed available |
| Production metrics backend for 1.6.x | Make in-story | R-SRE | defer to 1.6.1 |
