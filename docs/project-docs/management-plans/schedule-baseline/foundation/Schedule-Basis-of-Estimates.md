---
artifact_id: schedule-foundation-basis-of-estimates
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-1
pmbok_process: Plan Schedule Management
depends_on:
  - 6.B-0P
---

# Schedule Basis of Estimates — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Tailored specifically for autonomous agent operations, tool invocation latencies, and local test verification cycles.

## 1. Estimating methodology for autonomous agent workers

In autonomous agentic execution environments, activity duration is composed of three distinct operational factors:

$$T_{\text{activity}} = T_{\text{reasoning \& tool turns}} + T_{\text{execution \& test runtime}} + T_{\text{gate review latency}}$$

1. **Agent Reasoning & Tool Turns ($T_{\text{turns}}$)**:
   - Evaluated as discrete LLM context interactions (file reads, edits, bash commands).
   - Historical baseline from MXC project setup and governance integration shows:
     - Simple unit/configuration task: 3–6 turns.
     - Feature implementation with test authoring: 8–15 turns.
     - Complex architectural component with integration tests: 15–25 turns.
2. **Execution & Test Runtime ($T_{\text{runtime}}$)**:
   - VM provisioning and image bake operations: 10–25 minutes per run.
   - `pytest` unit/governance test suites: 10–30 seconds per run.
   - Hyper-V `Suspend-VM` / `Resume-VM` timing benchmark sweeps: 2–5 minutes per cycle.
3. **Gate Review Latency ($T_{\text{review}}$)**:
   - Automated gates (`spec_gate.py`, `pr_gate.py`): 30–90 seconds.
   - Human adjudication gates: modeled as asynchronous queue steps (1–4 hours buffer in calendar models, zero critical-path hold during batch automation).

---

## 2. Activity estimating basis and historical benchmarks

| Work type | Representative activities | Estimating method | Assumptions & parameters | Confidence |
|---|---|---|---|:---:|
| **Governance & Baseline** | ACT-01 | Parametric / Historical | Based on Stage 1–6 SIDPA template instantiation actuals in this repository. | High |
| **Hyper-V Platform & Scripting** | ACT-02, ACT-07, ACT-08, ACT-09 | Analogous / Engineering benchmark | Hyper-V PowerShell cmdlets executed on Windows 11 host with NVMe storage. | High |
| **Guest OS & Subsystems** | ACT-03, ACT-15 | Parametric | In-guest PowerShell / WMI queries over Hyper-V Data Exchange (KVP). | Medium |
| **VHDX Image Bake Pipeline** | ACT-04, ACT-05 | Measured benchmark | Windows image sysprep and dism capture on host hardware; bake runtime $\approx 25\text{ mins}$. | High |
| **Security & Port ACLs** | ACT-06, ACT-10, ACT-11 | Parametric | Hyper-V VSwitch Port ACL cmdlets and VHDX parent-child differential disk commands. | High |
| **Ingress & Proxy Networking** | ACT-12, ACT-13, ACT-14 | Engineering build & test | Python/Go lightweight reverse proxy with HTTP socket holding and pooling API. | Medium |
| **Fleet Autoscaler & Reaper** | ACT-16, ACT-17, ACT-18 | Parametric | Background daemon loop with synthetic traffic burst generator. | High |
| **Integrated Acceptance** | ACT-19 | Synthetic load benchmark | End-to-end multi-agent orchestration exercising full lifecycle across all 17 stories. | Medium |

---

## 3. Data limitations and uncertainty handling

1. **Hardware Specifics**: Benchmarks assume Windows 11 Pro/Enterprise with virtualization extensions enabled and minimum 32GB RAM / 1TB NVMe. Running on constrained hardware will increase $T_{\text{runtime}}$.
2. **LLM Context Limits**: Activities exceeding 25 turns risk context degradation; decomposed activities are scoped strictly to individual user stories to stay within optimal turn budgets.
3. **Flaky Test Retries**: Flaky timing in VM suspension/resume benchmarks is mitigated through 3-run median scoring in the test harness.
