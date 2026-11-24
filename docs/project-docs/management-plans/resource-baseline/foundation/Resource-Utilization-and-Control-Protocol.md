---
artifact_id: resource-foundation-utilization-control
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-5
pmbok_process: Monitor and Control Resourcing
depends_on:
  - 6.C-2
  - 6.C-4
---

# Resource Utilization and Control Protocol — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Establishes monitoring controls and escalation thresholds for human effort, agent computation, and material hardware consumption.

## 1. Resource monitoring metrics and control thresholds

| Resource dimension | Planned baseline | Measurement source | Review cadence | Escalation trigger threshold | Corrective action |
|---|---|---|---|---|---|
| **Human Engineering Hours** | 90 total person-hours across Phase 1 | Time logs / PR reviews in `Implementation-Log.md` | Weekly / Wave boundary | Cumulative effort variance $> +20\%$ ($> 108\text{h}$) | Re-evaluate story scope or increase agent delegation. |
| **Agent AI Turns / Tokens** | 208.8 turns / $\approx 10.6\text{M}$ tokens | Agent session turn counts in `Story-Execution-Register.md` | Per story completion | Single story exceeds 25 turns without passing gate | Draw on Reserve CR-04; invoke human triage via `review_triage.py`. |
| **Host Standby Memory Commit** | $\le 700\text{MB}$ per suspended guest | Host PerfMon: `Hyper-V Dynamic Memory \ Current Pressure` | Continuous during test runs | Suspended guest RAM commit $> 900\text{MB}$ | Tune memory working set trimmer script (ACT-08). |
| **Host Idle CPU Consumption** | $0.0\%$ CPU across suspended pool | Host PerfMon: `Hyper-V Hypervisor Virtual Processor \ % Total Run Time` | Continuous during test runs | CPU usage $> 0.1\%$ in standby | Verify guest background tasks and kernel suspend states (ACT-07). |
| **NVMe Disk Storage Capacity** | Minimum 150 GB free for differencing pool | Host filesystem monitor: `Get-PSDrive` | Daily | Free space $< 30\text{GB}$ on VM drive | Trigger Fleet Reaper (ACT-18) or prune orphan `.avhdx` files. |
| **Guest OS License Pool** | Maximum 10 concurrent standby + 10 active VMs | Hyper-V inventory: `Get-VM` | Real-time via pool lease API | Active pool requests exceed license capacity | Return HTTP 503 Retry-After (ACT-13). |

---

## 2. Corrective action and escalation process

1. **Hardware Resource Saturation**:
   - If host memory or disk IOPS saturate during test execution, the SRE Lead clamps the pool size ($K_{\text{base}}$ lowered from 2 to 1) until physical host capacity is upgraded.
2. **Agent Stalling or Context Loop**:
   - If an autonomous agent enters a repair loop consuming $> 15$ turns on a single story, the subagent is paused, context is dumped, and the Dev Coordinator reviews the failure mode.
3. **Budgetary Expenditure Thresholds**:
   - Any hardware upgrade or license purchase exceeding USD 25,000 must be submitted to the Steering Committee with an updated Business Case.
