---
artifact_id: schedule-foundation-wbs-forecast
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-4
depends_on:
  - 7.B-1
  - scope-management
---

# WBS Duration Forecast — mxc (Phase 1)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b4-wbs-forecast-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b4-wbs-forecast-2026-11-10.adjudication.json).

**Estimate basis:** **Low / Likely / High** columns are **human developer WD only** (see [Schedule-Basis-of-Estimates.md](Schedule-Basis-of-Estimates.md)). Do not interpret as agent or automation effort.

| WBS ID | Work package | Human WD actual | Low / Likely / High (human WD) | Confidence | Source / sample | Dependency |
|---|---|---|---|---|---|---|
| 1.1.1 | Gen2 isolation boundary | — | 2 / 4 / 5 | Medium | ADR-001; analogous provision | — |
| 1.1.2 | Windows subsystems on guest | — | 2 / 3 / 4 | Medium | Epic 001 | 1.1.1 |
| 1.3.1 | Clean production VHDX | — | 4 / 7 / 10 | Low | `BEN-08`; RSV-002 | 1.1.2 |
| 1.3.2 | Warm baseline checkpoint | — | 2 / 4 / 6 | Medium | Epic 003 | 1.3.1 |
| 1.4.1 | Zero idle CPU at Paused | — | 2 / 4 / 6 | Low | Formulated meter | 1.3.2 |
| 1.4.2 | Trimmed paused footprint | — | 3 / 5 / 7 | Low | Formulated RAM | 1.4.1 |
| 1.4.3 | Sub-300 ms resume | — | 3 / 5 / 8 | Medium | `benchmark_jit_wake.py` | 1.4.2 |
| 1.2.1 | Cold wake TTFB | — | 4 / 6 / 8 | Medium | AC-01.1 | 1.4.3 |
| 1.2.2 | No wake 502/504 | — | 2 / 4 / 5 | Medium | AC-01.3 | 1.2.1 |
| 1.2.3 | Dual routing rules | — | 3 / 5 / 7 | Low | HYP-mxc-004; RSV-003 | 1.2.2 |
| 1.5.1 | Ephemeral session disk | — | 3 / 5 / 6 | Medium | ADR-005 | 1.2.3 |
| 1.5.2 | Egress whitelist | — | 4 / 6 / 8 | Medium | AC-02.3 | 1.5.1 |
| 1.5.3 | Discard and reproduce | — | 2 / 4 / 5 | Medium | Story 5.3 | 1.5.2 |
| 1.6.1 | Buffer replenishment | — | 2 / 4 / 5 | Medium | Epic 006 | 1.5.3 |
| 1.6.2 | Surge expansion | — | 2 / 4 / 5 | Medium | Story 6.2 | 1.6.1 |
| 1.6.3 | Wake hygiene | — | 2 / 3 / 5 | Medium | Story 6.3 | 1.6.2 |
| 1.6.4 | Scale down | — | 2 / 4 / 5 | Medium | Story 6.4 | 1.6.3 |
| **1.0** | **Product roll-up** | — | **~62 / ~78 / ~102** | Low–Med | Sum likely on CP | Chain 1.1.1→1.6.4 |

## Roll-up method

- **Work-package likely** values sum along the critical path (no overlap assumed).
- **Milestone dates** derive from cumulative WD converted to **relative weeks** in [Schedule-Gantt-Phase1.md](Schedule-Gantt-Phase1.md) (data date **T0** = schedule pack draft, not execution start).
- **Reserves** in [Schedule-Reserve-Register.md](Schedule-Reserve-Register.md) add contingency outside the **likely** sum.
- **Human WD actuals** from `implement-story` (people time) may replace analogous cells on rebaseline.
- **Agentic actuals** are logged separately below — **not** estimated in this approved baseline.

## Agentic effort actuals (fill on execution — not estimated)

No prior input exists for agent sessions, Tier B parallelism, or agent calendar compression. **Do not add numbers here during planning.**

| WBS ID | Metric (define when first observed) | Actual | Period / story | Source (register, log) |
|---|---|---|---|---|
| *all* | *e.g. agent-sessions, wall-clock with Tier A+B* | — | — | [Story-Execution-Register.md](../../../registers/Story-Execution-Register.md); Project-Status-Register §5 |
