---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Monitoring & Controlling"
pmbok_process: "8.2 Manage Quality & 8.3 Control Quality Audits"
lifecycle_stage: "Stage 11 (Audit Record)"
governance_policy: "approve-audit-record"
inputs:
  - "Deliverables (Source code)"
  - "Verification Evidence (Contract test runs)"
  - "Telemetry"
process: "Perform compliance audits, identify drift or regressions, document corrective actions"
outputs:
  - "Audit-Register.md"
  - "Approved Audit Findings"
---

# Audit Register — <project>

> **PMBOK 8 Process:** `8.2 Manage Quality & 8.3 Control Quality Audits` (Monitoring & Controlling)  
> **Governance Policy:** `approve-audit-record` | **Lifecycle Stage:** `Stage 11 (Audit Record)`  
> **Inputs:** Deliverables (Source code), Verification Evidence (Contract test runs), Telemetry  
> **Process:** Perform compliance audits, identify drift or regressions, document corrective actions  
> **Outputs:** Audit-Register.md, Approved Audit Findings


| Field | Value |
|---|---|
| Version | 1.0 (live — accumulates as audits actually run) |
| Date | <date this project starts using it> |
| Status | Active, empty |
| Source | <this project's own audit-sampling rationale, once it has one> |

Centralized, not scattered. Every real audit finding (an ADR's accuracy checked against actual code) and every real Governance Exercise (a real-world prerequisite or claim checked against production reality) lives here once, with a stable ID — other documents **reference** the ID rather than copying the finding into their own text.

This register is conceptually distinct from governance-type documents (the policy/baseline itself) — this is the record of checking reality against that baseline.

## ADR-accuracy audits

| ID | ADR | Pillar | Finding | Verdict | Referenced by |
|---|---|---|---|---|---|
| *(empty — first real audit gets AUDIT-001)* | | | | | |

**Verdict taxonomy** (matches `classify-audit-finding`'s real action set, once this project has evidence to build that policy — see "Governance Exercises" below for the parallel reasoning): `confirmed_accurate`, `confirmed_with_drift`, `partially_confirmed`, `contradicted`, `stale_superseded`, `unauditable`, `flag_for_human_review`.

## Governance Exercises

A distinct sub-type from the ADR-accuracy audits above — these check a real-world prerequisite or claim against production reality, not an ADR's accuracy against code. This is also where a story that turns out not to be code-shaped gets reclassified to (see `Story-Execution-Register.template.md`), rather than forcing it into a lighter-weight story variant.

| ID | Checks | Status | Blocker |
|---|---|---|---|
| *(empty — first real exercise gets GOV-EX-001)* | | | |

## Building `classify-audit-finding` for this project

ADPA's own version of this policy was built only after a real finding (AUDIT-001) existed — not before. If this project accumulates more than one real audit finding and the verdict categories above start to feel repetitive rather than freshly reasoned each time, that's the real signal to build the policy — cite it in `docs/root-cause-log.md` when you do, the same way every other policy in this chain traces back to a real trigger.
