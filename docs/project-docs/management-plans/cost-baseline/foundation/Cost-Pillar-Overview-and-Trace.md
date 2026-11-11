---
artifact_id: cost-foundation-pillar-overview-trace
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.D-0P
depends_on:
  - scope-baseline approved
  - schedule-baseline approved
  - resource-baseline approved
---

# Cost Pillar Overview and Trace — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-cost-7d0p-pillar-overview-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-cost-7d0p-pillar-overview-2026-11-10.adjudication.json).

| Outcome / value driver | WBS / milestone | Cost category | Likely cost (EUR) | Financial boundary |
|---|---|---|---|---|
| Gen2 isolation ready | 1.1.x / MS-01 | CAT-LAB | €4,620 | Product Phase-1 charter |
| Reproducible image | 1.3.x / MS-02 | CAT-LAB | +€6,600 (cum. €11,220) | |
| Paused JIT proven | 1.4.x / MS-03 | CAT-LAB | +€11,240 (cum. €22,460) | |
| Ingress without wake errors | 1.2.x / MS-04 | CAT-LAB | +€9,900 (cum. €32,360) | |
| Sterile sessions | 1.5.x / MS-05 | CAT-LAB | +€10,350 (cum. €42,710) | |
| Watermark pool ops | 1.6.x / MS-06 | CAT-LAB | +€7,900 (cum. €50,610) | |
| Governance & quality overlay | — | CAT-LAB-OV | **€8,100** (incl. PM **€2,280**) | Sponsor/project pays; PM imputed at market rate |
| Risk / unknowns | RSV rows | CAT-CONT | €18k–€28k envelope | Not baseline until used |
| Agentic / IDE subscriptions | — | CAT-TOOL | **€71/mo** (**~€256** Phase-1) | Cursor, Gemini Antigravity, Claude Code, GitHub Basic |

## Review

Primary cost driver is **human integration labor** on approved schedule CP. Benefits (JIT savings) are **not** netted against estimates in this pack—see Business Case separately.
