---
artifact_id: schedule-foundation-pillar-overview-trace
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-0P
depends_on:
  - scope-management
---

# Schedule Pillar Overview and Trace — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b0p-pillar-overview-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b0p-pillar-overview-2026-11-10.adjudication.json).

## Upstream schedule inputs (7.B-0)

| Input | Status | Schedule use |
|---|---|---|
| [Scope-Management-Plan.md](../../Scope-Management-Plan.md) | Approved 2026-11-10 | Authorized WBS **1.0–1.6** and 17 story packages |
| [Scope-Foundation-Pack-Manifest.md](../../scope-baseline/Scope-Foundation-Pack-Manifest.md) | `pack_status: approved` | Baseline id `PMP-BL-v1.0.0` |
| ADR/BRD/FDD/epic **001–006** | Accepted / Approved 2026-10-30 | Precedence and acceptance evidence |
| Observed benchmarks | Partial | Wake/resume harnesses cited in ADR-002/004; many ACs still **Formulated** |

## Strategic outcomes → schedule milestones

| Outcome / pillar | WBS | Story WBS | Phase-1 milestone | Gate / evidence | Schedule implication |
|---|---|---|---|---|---|
| **TP-01 Isolation** | 1.1 | 1.1.1, 1.1.2 | **MS-01** Gen2 guest path ready | Epic 001; provision checks | **Lead** — no image/pause work without Gen2 boundary |
| **TP-03 Image supply** | 1.3 | 1.3.1, 1.3.2 | **MS-02** Production image + warm checkpoint | Epic 003; `audit_production_image.ps1` | Blocks pause and pool scenarios needing gold image |
| **TP-04 Paused footprint** | 1.4 | 1.4.1–1.4.3 | **MS-03** Paused standby + resume proof | Epic 004; `benchmark_jit_wake.py` | Ingress buffering depends on credible wake/resume |
| **TP-02 Ingress** | 1.2 | 1.2.1–1.2.3 | **MS-04** Ingress path live | Epic 002; AC-01.x | After MS-03 — buffer assumes Paused guest |
| **TP-05 Session sterility** | 1.5 | 1.5.1–1.5.3 | **MS-05** Sterile session path | Epic 005; US-02 | After ingress — sessions traverse gateway |
| **TP-06 Pool hygiene** | 1.6 | 1.6.1–1.6.4 | **MS-06** Watermark pool operational | Epic 006; US-05 | Caps Phase-1 product implementation track |
| **Product baseline** | 1.0 | 1.1.1–1.6.4 | **MS-07** Phase-1 implementation schedule baseline | All stories `implement-story` + AC proof | **Not** a delivery commitment until schedule pack approved and Stage 8 issued |

## Pillar sequencing (authorized logic)

```text
TP-01 (1.1) → TP-03 (1.3) → TP-04 (1.4) → TP-02 (1.2) → TP-05 (1.5) → TP-06 (1.6)
```

Parallel work inside a pillar is allowed only when network rows in [Schedule-Network-Phase1.md](Schedule-Network-Phase1.md) show no hard FS predecessor.

## Review checks

- Schedule milestones match **scope** milestones, not invented scope.
- **MS-01…MS-07** remain planning targets until `approve-subsidiary-plan` on this pack and **`approve-pmp`**.
- Resource leveling and cost duration loads defer to **7.C / 7.D** packs.
