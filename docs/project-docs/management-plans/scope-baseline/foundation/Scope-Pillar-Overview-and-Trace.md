---
artifact_id: scope-foundation-pillar-overview-trace
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.A-0P
depends_on: []
---

# Scope Pillar Overview and Trace — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a0p-pillar-overview-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-scope-7a0p-pillar-overview-2026-11-10.adjudication.json).

## Strategic outcomes and scope pillars

| Outcome / pillar | Authorized source | Measurable objective | Scope deliverables | Open gap |
|---|---|---|---|---|
| **TP-01 Isolation** | [ADR-001](../../../../07-architecture/ADR-001-type-1-hyperv-generation-2.md) Accepted; [BRD-001](../../../Business-Requirements/BRD-001-type-1-hyperv-generation-2.md); [epic-001](../../../../user-stories/epic-001-type-1-hyperv-generation-2.md) Approved | Confidential workloads on Gen2 guests, not shared-kernel containers | Hyper-V Gen2 guests; WMI/COM+/GPO in guest; Stories 1.1–1.2 | Suite monolith gaps named in ADR-001 consequences |
| **TP-02 Ingress** | [ADR-002](../../../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md); [epic-002](../../../../user-stories/epic-002-connection-buffering-ingress-gateway.md) | Buffer while Paused; ≤800 ms first byte; no wake 502/504 | `jit_ingress_gateway`; path + port routing (Stories 2.1–2.3) | Unnamed MFA product; Kerberos :88 with ADR-005 |
| **TP-03 Image supply** | [ADR-003](../../../../07-architecture/ADR-003-production-base-image.md); [epic-003](../../../../user-stories/epic-003-production-base-image.md) | Production image without dev toolchain; hot-ready checkpoint | `winserv2025-prod-adpa` pipeline; Stories 3.1–3.2 | `BEN-08` blocked until catalog VHDX exists (`Project-Details-Not-In-ADR.md`) |
| **TP-04 Paused footprint** | [ADR-004](../../../../07-architecture/ADR-004-paused-ram-standby.md); [epic-004](../../../../user-stories/epic-004-paused-ram-standby.md) | 0% idle CPU when Paused; trimmed RAM; resume <300 ms | Pre-suspend trim; Paused standby; Stories 4.1–4.3 | Dual RAM readings (700 MB vs 1.0–1.2 GB) still Formulated |
| **TP-05 Session sterility** | [ADR-005](../../../../07-architecture/ADR-005-transient-differencing-disk.md); [epic-005](../../../../user-stories/epic-005-transient-differencing-disk.md) | Transient diff disk + egress whitelist; discard after session | Differencing disk lifecycle; ACL egress; Stories 5.1–5.3 | Whole-guest discard horizon scoped in ADR, not in epic |
| **TP-06 Pool and wake hygiene** | [ADR-006](../../../../07-architecture/ADR-006-watermark-pool.md); [epic-006](../../../../user-stories/epic-006-watermark-pool.md) | Watermark pool, replenish, surge/cooldown hygiene | Pool config; replenish worker; Stories 6.1–6.4 | Live proof of dual surge + dual cooldown still observation-backed |

**Initiating context (not re-approved here):** [Spark-Capture.md](../../../Spark-Capture.md), [Business-Case.md](../../../Business-Case.md) Approved 2026-10-29.

## Trace to scope bands and milestones

| Outcome | WBS reference | Story WBS IDs | Milestone / gate | Acceptance source |
|---|---|---|---|---|
| TP-01 | 1.1 | 1.1.1, 1.1.2 | `approve-user-stories` 001 | Epic 001; BDR-03 |
| TP-02 | 1.2 | 1.2.1–1.2.3 | Gates 2026-10-30 | US-01 / AC-01.x |
| TP-03 | 1.3 | 1.3.1–1.3.2 | Gates 2026-10-30 | GOLDEN_IMAGE_REGISTRY |
| TP-04 | 1.4 | 1.4.1–1.4.3 | Gates 2026-10-30 | US-03 |
| TP-05 | 1.5 | 1.5.1–1.5.3 | Gates 2026-10-30 | US-02; AC-02.3 |
| TP-06 | 1.6 | 1.6.1–1.6.4 | Gates 2026-10-30 | US-05; AC-02.4 |
| Full product baseline | 1.0 | 1.1.1–1.6.4 (17) | `approve-subsidiary-plan` → `approve-pmp` | [Scope-WBS-Dictionary.md](Scope-WBS-Dictionary.md) |

Implementation authorization remains **Stage 8** (`Stage-8-Implementation-Authorization-Notice`); approved stories are not yet `implement-story` complete.

## Review checks

- Every pillar traces to an **Accepted** ADR and **Approved** BRD/FDD/epic (2026-10-30 gate records under `docs/project-docs/gates/`).
- Out-of-ADR hypotheses and benefits remain **Formulated** or open in [Project-Details-Not-In-ADR.md](../../../Project-Details-Not-In-ADR.md)—not treated as in-scope proof.
- Charter and benefits gates are not fully adjudicated; scope pack does not infer their approval.
