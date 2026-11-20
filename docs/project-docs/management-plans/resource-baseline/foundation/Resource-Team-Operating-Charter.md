---
artifact_id: resource-foundation-team-operating-charter
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-4
pmbok_process: Lead the Team
depends_on:
  - 6.C-1
  - 6.C-3
---

# Resource Team Operating Charter — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Establishes team collaboration agreements, human-agent interaction rules, authority limits, and escalation pathways.

## 1. Shared purpose and working agreements

1. **Human-Agent Synergy**:
   - Human leads own architectural direction, safety constraints, risk assessment, and governance sign-off.
   - Autonomous agent workers execute implementation, test coverage, and documentation tasks within strictly bounded user story scopes.
2. **Contract-First Development**:
   - No code is committed without passing pre-implementation specification criteria (`scripts/spec_gate.py`).
   - Every deliverable must be accompanied by automated verification tests passing `scripts/pr_gate.py`.
3. **Zero In-Guest Persistence Rule**:
   - All session data must reside on ephemeral differencing disks (`.avhdx`) discarded immediately upon session termination.
4. **Transparent Audit Trail**:
   - Every task claim, branch creation, reserve drawdown, and gate result must be recorded in the project registers (`Story-Execution-Register.md`, `Implementation-Log.md`).

---

## 2. Decision authority boundaries

| Role | May decide independently | Must escalate to Project Manager | Must escalate to Steering Committee |
|---|---|---|---|
| **Human Project Manager (Menno)** | Task scheduling within $\pm 20\%$, contingency reserve releases ($\le \$25,000$), role reassignments. | Baseline changes impacting charter objectives. | Capital expenditures $> \$25,000$, project cancellation/pause. |
| **Lead / System Architect** | Internal API contracts, test fixture designs, code modularity. | Cross-pillar design trade-offs, changes to Topic Pillars TP-01–06. | Scope changes that alter foundational architectural pillars. |
| **Platform / Security Leads** | Script optimizations, ACL rule structures, memory trimming routines. | Host OS configuration changes, hypervisor requirements shifts. | Security standard derogations or external compliance exceptions. |
| **Autonomous Agent Workers** | Code refactoring, test case generation, file edits within claimed story branch. | Ambiguous user story acceptance criteria, failing `spec_gate.py` checks. | Any change touching files outside the claimed work package scope. |

---

## 3. Communication, PR triage, and conflict resolution

1. **Conflict Resolution Hierarchy**:
   - Technical disagreements between leads $\rightarrow$ resolved by Lead Architect.
   - Schedule or resource priority conflicts $\rightarrow$ resolved by Project Manager.
   - Governance policy, budget, or charter conflicts $\rightarrow$ resolved by Steering Committee.
2. **Asynchronous PR Gate Triage**:
   - When an agent completes a story on `feat/story-<num>`, it executes `python scripts/pr_gate.py --pr <pr_num>`.
   - If defects or critique findings are raised, the agent attempts up to 2 automated repair turns.
   - If unresolved after 2 turns, the issue is flagged for human lead triage via `review_triage.py`.
