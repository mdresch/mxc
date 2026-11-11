---
artifact_id: scope-foundation-monitor-control
parent_plan_id: scope-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.A-3
pmbok_process: Monitor and Control Scope
depends_on:
  - 7.A-1
  - 7.A-2
---

# Monitor and Control Scope — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-scope-7a3-monitor-control-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-scope-7a3-monitor-control-2026-11-10.adjudication.json).

## Scope performance measures

| Measure | Evidence | Cadence | Reviewer |
|---|---|---|---|
| Requirements approval currency | BRD/FDD/epic status lines + gate JSON | Per gate | `mxc-governance` + human adjudication |
| ADR consistency | `docs/07-architecture` vs suite `ADR.md` | Per ADR change | Architect |
| Story AC regression | Contract tests; Bugbot on PRs | Per PR | CI + `approve-audit-record` (future) |
| Scope creep (side implementations) | [Project-Status-Register](../../../../registers/Project-Status-Register.template.md) (instantiate when live) | Weekly | PM |
| WBS ↔ epic mapping | This dictionary vs `docs/user-stories/epic-*.md` | Per scope pack revision | PM |

## Variance and change handling

| Condition | Required evidence | Impact analysis | Decision authority | Record |
|---|---|---|---|---|
| New pillar / ADR | Draft ADR + `approve-adr` | Scope, schedule, cost, risk, benefits | `approve-adr` + human accept | `docs/07-architecture/`; gates |
| BRD/FDD/story amendment | Revised pack + gate | Trace to ADR; WBS 1.x row | `approve-brd` / `approve-fdd` / `approve-user-stories` | `docs/project-docs/gates/` |
| Architectural scope in suite only | Diff vs lifecycle ADR | `classify-diff-type` → `escalate-diff-response` if material | Governance skill Stage 16 | `Adaptation-Plan.md` |
| Unplanned code outside epic | PR description + Bugbot | Map to WBS or quarantine | Human + optional `validate-intent-foundation` | Story register |
| Foundation pack edit | Manifest version bump | PMP roll-up | `approve-subsidiary-plan` | `Scope-Foundation-Pack-Manifest.md` |

## Traceability and staleness

- Changes to **Accepted** ADRs trigger review of matching BRD/FDD/epic **00N** and WBS **1.N**.
- Suite `docs/hyperv/architecture/*` updates require explicit lifecycle ADR or adaptation plan—suite-only drift does not silently expand WBS.
- `validate_lifecycle.py` run on meaningful merges (ordering invariants).

## Escalation and audit trail

- Unresolved scope conflicts → [Adaptation-Plan.md](../../../Adaptation-Plan.md) + `approve-adaptation-plan` (Stage 18 path).
- Gate artifacts are immutable JSON under `docs/project-docs/gates/`; post-adjudication status lines cite policy id.
- No numeric variance thresholds set for RAM/TTFB until hypotheses leave **Formulated**—do not invent SLO pass/fail here.
