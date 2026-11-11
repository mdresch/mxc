---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating"
pmbok_process: "13.1 Identify Stakeholders"
lifecycle_stage: "Stage 3 (Initiating)"
governance_policy: "approve-business-case"
inputs:
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "Spark-Capture.md"
process: "Identify stakeholders, roles, and engagement interest for charter and PMP inputs"
outputs:
  - "Stakeholder-Register.md"
---

# Stakeholder Register — MXC

> **PMBOK 8 Process:** `13.1 Identify Stakeholders` (Initiating)  
> **Governance Policy:** `approve-business-case` | **Lifecycle Stage:** `Stage 3 (Initiating)`  
> **Inputs:** [Business-Case.md](Business-Case.md), [Benefits-Statement.md](Benefits-Statement.md), [Spark-Capture.md](Spark-Capture.md)

| ID | Stakeholder | Role | Interest / influence | Notes |
|----|-------------|------|----------------------|-------|
| SH-01 | Menno Drescher | Product owner / architect | High / High | Named in BRD/epic approvals and spark. |
| SH-02 | SecOps consumers | Security operations | Medium / High | Isolation and egress posture per ADR-001/005. |
| SH-03 | SRE / platform operators | Operations | Medium / Medium | Pool, wake, and ingress reliability per ADR-002/006. |
| SH-04 | Project manager (governance) | PMBOK steward | High / Medium | Registers, subsidiary gates, Stage 8 prep. |
| SH-05 | R-QA / verification lead | Quality | Medium / Medium | Contract RED/GREEN; QG-02/03. |
| SH-06 | V-AGT (agentic lane) | Virtual implementer | Medium / Low | No approval authority — see engagement plan. |

**Status:** Draft — extended **2026-11-10** for [Stakeholder-Engagement-Plan.md](management-plans/Stakeholder-Engagement-Plan.md); refresh at **`approve-pmp`**.
