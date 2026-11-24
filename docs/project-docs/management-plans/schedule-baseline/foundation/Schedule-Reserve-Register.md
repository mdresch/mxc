---
artifact_id: schedule-foundation-reserve-register
parent_plan_id: schedule-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.B-3
depends_on:
  - 6.B-1
  - 6.B-4
---

# Schedule Reserve Register — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Quantifies contingency reserves for identified technical uncertainties and management reserves for unforeseen platform variance.

## 1. Schedule reserve allocations

| Reserve ID | Reserve type | Risk / uncertainty | Allocated amount | Trigger condition | Release authority | Source / basis |
|---|---|---|:---:|---|---|---|
| **CR-01** | Contingency | VHDX image bake sysprep / driver specialization latency | **3.0 hours** | ACT-04 bake runtime exceeds 45 minutes or requires image rebuild | Platform Lead | Benchmarked Windows sysprep variance on diverse SSDs |
| **CR-02** | Contingency | VM resume latency exceeding 300ms under host memory contention | **2.0 hours** | ACT-09 95th percentile unpause time > 300ms in benchmark | Platform Lead | Hyper-V memory paging benchmarks |
| **CR-03** | Contingency | Ingress HTTP socket hold timeout / connection drop under burst load | **2.0 hours** | ACT-12 or ACT-13 drops connections during $\ge 20\text{ req/s}$ test | Gateway Lead | Reverse proxy socket backlog profiling |
| **CR-04** | Contingency | Autonomous agent repair loop / turn limit exhaustion | **1.5 hours** (15 turns) | Agent reaches turn 20 without passing `spec_gate` or `pr_gate` | Dev Coordinator | Agentic workflow turn budget metrics |
| **MR-01** | Management | Host OS / Hyper-V cumulative update breaking VSwitch ACL cmdlets | **4.0 hours** | Host-level API breaking change or security patch failure | Project Sponsor | Historical Windows Server/Hyper-V update impacts |
| **MR-02** | Management | In-guest Windows subsystem COM+/WMI security descriptor incompatibility | **2.5 hours** | ACT-03 subsystem probe blocked by guest security hardening | Project Sponsor | Legacy enterprise Windows subsystem requirements |

---

## 2. Reserve consumption and governance rules

1. **Total Schedule Reserves**:
   - Total Contingency Reserve: **8.5 clock hours** ($\approx 27\%$ of critical path $31.0\text{ hours}$).
   - Total Management Reserve: **6.5 clock hours** ($\approx 21\%$ of critical path).
   - Total Buffered Project Duration: $31.0\text{h} + 8.5\text{h} = \mathbf{39.5\text{ clock hours}}$ (excluding management reserve).
2. **Drawdown Tracking**:
   - When an activity encounters a trigger condition, the worker logs a reserve drawdown entry in `docs/registers/Story-Execution-Register.md`.
   - Release of Contingency Reserves (CR-01 through CR-04) is approved by the assigned Lead role directly via gate comments.
   - Release of Management Reserves (MR-01, MR-02) requires a formal change request under `approve-pmp`.
