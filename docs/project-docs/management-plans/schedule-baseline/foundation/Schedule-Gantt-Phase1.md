---
artifact_id: schedule-foundation-gantt
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-2B
pmbok_process: Develop Schedule — develop schedule model
depends_on:
  - 7.B-2
  - 7.B-2A
  - 7.B-4
---

# Schedule Model / Gantt — mxc (Phase 1, relative)

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b2b-gantt-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b2b-gantt-2026-11-10.adjudication.json).

| Activity ID | Early start (Wk) | Early finish (Wk) | Late start | Late finish | Float | Milestone / constraint |
|---|---|---|---|---|---|---|
| 1.1.1 | 0 | 0.8 | 0 | 0.8 | 0 | MS-01 path |
| 1.1.2 | 0.8 | 1.4 | 0.8 | 1.4 | 0 | MS-01 **Gen2 ready** (~W1.4) |
| 1.3.1 | 1.4 | 2.8 | 1.4 | 2.8 | 0 | MS-02 path |
| 1.3.2 | 2.8 | 3.6 | 2.8 | 3.6 | 0 | MS-02 **Image baseline** (~W3.6) |
| 1.4.1 | 3.6 | 4.4 | 3.6 | 4.4 | 0 | MS-03 path |
| 1.4.2 | 4.4 | 5.4 | 4.4 | 5.4 | 0 | |
| 1.4.3 | 5.4 | 6.4 | 5.4 | 6.4 | 0 | MS-03 **Paused proven** (~W6.4) |
| 1.2.1 | 6.4 | 7.6 | 6.4 | 7.6 | 0 | MS-04 path |
| 1.2.2 | 7.6 | 8.4 | 7.6 | 8.4 | 0 | |
| 1.2.3 | 8.4 | 9.4 | 8.4 | 9.4 | 0 | MS-04 **Ingress live** (~W9.4) |
| 1.5.1 | 9.4 | 10.4 | 9.4 | 10.4 | 0 | MS-05 path |
| 1.5.2 | 10.4 | 11.6 | 10.4 | 11.6 | 0 | |
| 1.5.3 | 11.6 | 12.4 | 11.6 | 12.4 | 0 | MS-05 **Sterile path** (~W12.4) |
| 1.6.1 | 12.4 | 13.2 | 12.4 | 13.2 | 0 | MS-06 path |
| 1.6.2 | 13.2 | 14.0 | 13.2 | 14.0 | 0 | |
| 1.6.3 | 14.0 | 14.6 | 14.0 | 14.6 | 0 | |
| 1.6.4 | 14.6 | 15.4 | 14.6 | 15.4 | 0 | MS-06 **Pool ops** (~W15.4) |
| MS-07 | 15.4 | 15.4 | 15.4 | 15.4 | 0 | **Phase-1 CP ~15.6 wks** (+ reserves) |

*Week fractions: likely WD ÷ 5 per activity; see forecast for raw WD.*

## Model assumptions

| Assumption | Value |
|---|---|
| Calendar | 5 WD/week, no holidays modeled |
| Critical path | Single FTE on FS chain (see network) |
| Tool / source | Planning spreadsheet derived from forecast |
| Confidence | Low until first **human WD** `implement-story` actual; agentic metrics tracked separately |
| Constraint | **No start before Stage 8** execution authorization |

## Reconciliation

Early/late columns match **zero float** on the draft critical path. When resource pack assigns >1 FTE, regenerate this model and expect float on non-CP branches.
