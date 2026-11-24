---
artifact_id: cost-foundation-variance-control
parent_plan_id: cost-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.D-4
pmbok_process: Monitor and Control Finances
depends_on:
  - 6.D-3
---

# Cost Variance and Control Protocol — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Establishes Earned Value Management (EVM) tracking, variance thresholds, reserve drawdown governance, and corrective action protocols.

## 1. Cost monitoring metrics and EVM controls

Financial performance is tracked against the staged Cost Baseline (\$16,865) using standard Earned Value Management:

| Metric | Definition | Planned source | Actual source | Target / tolerance |
|---|---|---|---|---|
| **Planned Value (PV)** | Authorized budget assigned to scheduled work. | [Cost-Staged-Budget-and-Baseline.md](Cost-Staged-Budget-and-Baseline.md) | Cumulative planned baseline by wave | Reconciled with Schedule Gantt |
| **Earned Value (EV)** | Budget value of work actually completed and gate-approved. | Work packages passing `pr_gate.py` | Completed WBS items in `Implementation-Log.md` | $\text{EV} = \sum (\text{WBS Baseline Cost} \times \text{\% Complete})$ |
| **Actual Cost (AC)** | Incurred contractor hours and AI token spend. | Contractor timesheets & LLM API invoices | Recorded expenditure in `Story-Execution-Register.md` | $\text{AC} = \text{Labor Paid} + \text{AI Compute Incurred}$ |
| **Cost Variance (CV)** | $\text{CV} = \text{EV} - \text{AC}$ | Calculated weekly | Calculated weekly | Tolerance: $\ge -\$1,500$ |
| **Cost Performance Index (CPI)** | $\text{CPI} = \frac{\text{EV}}{\text{AC}}$ | Calculated weekly | Calculated weekly | Target: $\ge 0.95$; Trigger: $< 0.90$ |

---

## 2. Escalation triggers and corrective action protocol

| Variance trigger condition | Severity level | Decision authority | Mandatory corrective action |
|---|:---:|---|---|
| **$0.90 \le \text{CPI} < 0.95$** or $\text{CV} \in [-\$500, -\$1,500]$ | Yellow (Caution) | Project Manager | Review activity turn counts; adjust agent prompt guidance; monitor next story. |
| **$\text{CPI} < 0.90$** or $\text{CV} < -\$1,500$ | Orange (Warning) | Project Manager & Architect | Formal variance review; draw from Cost Contingency Reserve (\$2,200 max); audit code complexity. |
| **Forecast exceeds \$16,865 baseline** | Red (Critical) | Project Sponsor (Menno) | Release Management Reserve (\$3,500 max) via formal baseline change request. |
| **Total projected cost exceeds \$25,000** | Escalation (Breach) | Steering Committee | Halt execution; submit comprehensive Business Case amendment to Steering Committee. |

---

## 3. Reserve drawdown governance

1. **Contingency Reserve Drawdown**:
   - The Project Manager may approve draws from the **\$2,200 Cost Contingency Reserve** for documented scope complexity, test environment retries, or extra contractor review cycles.
   - Every drawdown must be recorded in the `Continuous-Improvement-Register.md` and referenced in the applicable PR gate adjudication.
2. **Management Reserve Drawdown**:
   - The **\$3,500 Management Reserve** is held separately for unforeseen external risks (e.g. host OS hypervisor breaking changes, license fee shifts).
   - Drawdown requires a formal change record approved by the Project Sponsor.
