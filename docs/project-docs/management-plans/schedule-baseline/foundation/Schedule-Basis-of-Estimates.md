---
artifact_id: schedule-foundation-basis-of-estimates
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-subsidiary-plan
version: "1.0.0"
approval_status: approved
substage: 7.B-1
pmbok_process: Plan Schedule Management
depends_on:
  - 7.B-0P
---

# Schedule Basis of Estimates — mxc

**Status:** **Approved (2026-11-10)** — `approve-subsidiary-plan` accepted `approve_plan` on 2026-11-10 (policy `1c0b25f8-af6e-4573-a101-9f5568f28792`, human acceptance). Gate record: [approve-subsidiary-plan-schedule-7b1-basis-estimates-2026-11-10.adjudication.json](../../../gates/approve-subsidiary-plan-schedule-7b1-basis-estimates-2026-11-10.adjudication.json).

## Estimating standards

| Element | Rule |
|---|---|
| **Unit** | Working day (WD); 1 WD = 6 h **human** developer / engineer effort (planning assumption) |
| **Out of scope for WD baseline** | **Agentic** effort (agent sessions, tokens, parallel Tier B lanes, calendar compression) — **no estimate** without observed data; record **actuals only** after execution (see forecast § Agentic actuals) |
| **Calendar** | Mon–Fri; holidays not modeled in Phase-1 draft |
| **Method** | **Analogous** (similar Hyper-V/Rust integration stories) + **parametric** where harness exists (wake/resume) |
| **Triangular default** | Low / likely / high WD per WBS row in [Schedule-Baseline-WBS-Forecast.md](Schedule-Baseline-WBS-Forecast.md) |
| **Governance latency** | +1 WD per artifact that must pass `approve-audit-record` before closure (not double-counted in story ranges) |
| **Update rule** | **Human WD:** first `implement-story` human-effort actuals may replace analogous priors; rebaseline via change control. **Agentic:** log only — do not fold into WD ranges until a rebaseline decision with evidence |

## Work-type basis

| Work type | Historical / project evidence | Method | Typical range (WD) | Owner |
|---|---|---|---|---|
| Gen2 provision + guest subsystem proof | ADR-001; partial suite scripts | Analogous | 2–5 | Platform |
| Production image pipeline | ADR-003; `BEN-08` blocked | Analogous + risk widen | 5–10 | Release |
| Paused trim + resume | ADR-004; lesson doc ≤300 ms target | Parametric + benchmark harness | 3–8 | Platform |
| Ingress gateway integration | ADR-002; AC-01.x | Analogous | 4–8 | Platform |
| Diff disk + egress ACL | ADR-005; US-02 | Analogous | 4–8 | SecOps |
| Pool watermark / surge | ADR-006; observational SRE notes | Analogous | 3–5 per story | SRE |
| Contract / AC verification | Epics Approved | Fixed append | +1–2 per story | Story owner |

## Uncertainty and data limits

- **No story-point ledger** and **no agentic throughput baseline** exist; human WD ranges are analogous placeholders only.
- **Agentic parallel execution** ([Agentic-Parallel-Execution-Policy.md](../../Agentic-Parallel-Execution-Policy.md)) affects **calendar** and operations, not approved WD math, until actuals are recorded.
- **Formulated** metrics (epic 004 RAM/CPU meters) widen ranges and link to [Schedule-Reserve-Register.md](Schedule-Reserve-Register.md).
- **BEN-08** / production VHDX catalog may idle **1.3.1** — schedule shows dependency, not fake progress.
- Single-threaded critical path assumed; **resource pack** may compress calendar after leveling.

## Data limitations

Do not convert **likely** column to a committed finish date without **7.B-7** approval and Stage 8 notice.
