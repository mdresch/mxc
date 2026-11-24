---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "11.1 Risk Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Business-Case.md"
  - "../Benefits-Statement.md"
  - "schedule-baseline/foundation/Schedule-Reserve-Register.md"
  - "cost-baseline/foundation/Cost-Variance-and-Control-Protocol.md"
process: "Define risk identification, probability/impact rating methodology, risk register, and reserve allocation"
outputs:
  - "Risk-Management-Plan.md"
status: "Approved"
---

# Risk Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the risk management methodology, probability/impact rating scale, active risk register, and reserve governance.

## 1. Risk management methodology and scoring criteria

Risks are evaluated using a standard 5x5 Probability and Impact matrix:
- **Probability ($P$)**: 1 (Very Low $< 10\%$), 2 (Low $10\text{–}25\%$), 3 (Moderate $25\text{–}50\%$), 4 (High $50\text{–}75\%$), 5 (Very High $> 75\%$).
- **Impact ($I$)**: 1 (Negligible), 2 (Minor schedule/cost variance $< 10\%$), 3 (Moderate variance $10\text{–}20\%$), 4 (Major variance $> 20\%$), 5 (Critical charter/security compromise).
- **Risk Score**: $\text{Score} = P \times I$ (1–6 Green/Low; 8–12 Yellow/Moderate; 15–25 Red/High).

---

## 2. Active risk register and response strategies

| Risk ID | Risk event and consequence | $P$ | $I$ | Score | Planned response strategy | Accountable owner | Reserve link |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-01** | **VHDX Image Bake Sysprep Latency**: Image bake runtime exceeds expected timebox on diverse host SSDs. | 3 | 2 | 6 (Low) | **Mitigate**: Cache intermediate sysprep layers and pre-install Windows updates in base image. | Release Lead | Schedule CR-01 (3.0h) |
| **RSK-02** | **Memory Contention Resume Latency**: `Resume-VM` exceeds 300ms target during concurrent host paging load. | 3 | 3 | 9 (Med) | **Mitigate**: Working set trimmer (ACT-08) clamps standby commit to $\le 700\text{MB}$; host lock-in-RAM. | Platform Lead | Schedule CR-02 (2.0h) |
| **RSK-03** | **Ingress Socket Hold Backlog Overflow**: HTTP socket buffers exhaust during sudden concurrency burst $> 20\text{ req/s}$. | 2 | 3 | 6 (Low) | **Mitigate**: Async queue holding; immediate dynamic surge trigger (ACT-17); structured 503 fallback. | Gateway Lead | Schedule CR-03 (2.0h) |
| **RSK-04** | **Autonomous Agent Repair Context Loops**: Agent worker consumes excessive turns without passing PR gate. | 3 | 2 | 6 (Low) | **Mitigate**: Hard turn limit at 20 turns; automated halt and human triage via `review_triage.py`. | Dev Coordinator | Schedule CR-04 (1.5h) / Cost Cont. (\$2,200) |
| **RSK-05** | **Host Hyper-V Cumulative Update Incompatibility**: Host Windows patch introduces breaking change to Port ACLs. | 2 | 4 | 8 (Med) | **Accept & Buffer**: Maintain host update freeze during active test sweeps; test on staging harness first. | Platform Lead | Cost MR-01 (\$3,500) |
| **RSK-06** | **In-Guest Subsystem COM+/WMI Hardening**: Enterprise security policy blocks in-guest WMI execution over KVP. | 2 | 3 | 6 (Low) | **Mitigate**: Pre-configured guest integration service descriptors baked into clean golden VHDX. | Security Lead | Cost MR-02 |
| **RSK-07** | **Dual-Role Sponsor/PM Conflict of Interest**: Combining PM and Sponsor could compromise expenditure oversight. | 2 | 3 | 6 (Low) | **Avoid**: Strict segregation of duties: Steering Committee holds sole authority for spending $> \$25,000$. | Project Sponsor | Charter Governance Limit |
| **RSK-08** | **Cross-Session Storage Contamination**: Differencing `.avhdx` fails to unmount on abnormal session termination. | 2 | 4 | 8 (Med) | **Mitigate**: Orphan differencing disk cleaner in Fleet Reaper (ACT-18); parent VHDX read-only filesystem lock. | Security Lead | Security Baseline |

---

## 3. Risk reserves and release governance

1. **Schedule Contingency Reserves**:
   - **8.5 clock hours** allocated across technical risks RSK-01 to RSK-04 (governed in [Schedule-Reserve-Register.md](schedule-baseline/foundation/Schedule-Reserve-Register.md)).
2. **Cost Contingency Reserves**:
   - **\$2,200 (15%)** allocated for technical iteration and retry loops (governed in [Cost-Staged-Budget-and-Baseline.md](cost-baseline/foundation/Cost-Staged-Budget-and-Baseline.md)).
3. **Management Reserves**:
   - **6.5 clock hours** and **\$3,500** allocated for unforeseen external risks (RSK-05, RSK-06), controlled exclusively by the Project Sponsor.
4. **Threshold Escalation**:
   - Any emergent risk threatening to breach the \$25,000 threshold or critical path by $> 20\%$ is immediately escalated to the Steering Committee.
