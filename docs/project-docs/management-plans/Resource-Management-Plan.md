---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "9.1 Resource Management Plan"
lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"
governance_policy: "approve-pmp"
inputs:
  - "../Project-Charter.md"
  - "../Benefits-Statement.md"
  - "scope-baseline/Scope-Foundation-Pack-Manifest.md"
  - "schedule-baseline/Schedule-Foundation-Pack-Manifest.md"
  - "resource-baseline/Resource-Foundation-Pack-Manifest.md"
process: "Define human roles, agent worker capacities, physical host specifications, virtual infrastructure, and utilization control protocols"
outputs:
  - "Resource-Management-Plan.md"
  - "resource-baseline/foundation/Resource-Role-Catalogue.md"
  - "resource-baseline/foundation/Resource-Capacity-Estimates.md"
  - "resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md"
  - "resource-baseline/foundation/Resource-Team-Operating-Charter.md"
status: "Approved"
---

# Resource Management Plan — MXC Hyper-V for ADPA / SIDPA

**Status:** Approved. Formally approved by Menno Drescher (Project Sponsor / Project Manager) on 2026-11-20 under `approve-pmp`. Establishes the authorized Resource Baseline (`PMP-BL-v1.0.0`) detailing human engineering effort, contractor rate schedules, agent reasoning capacity, and material host sizing.

## 1. Executive summary and methodology

This Resource Management Plan establishes the framework for acquiring, allocating, monitoring, and controlling the resources required to deliver the 17 approved User Stories across the 6 Topic Pillars. 

The project employs a **Hybrid Delivery Model**:
- **Human Resources (90 person-hours)**: Provide architectural leadership, governance verification, security sign-off, risk escalation, and PR gate triage.
- **Autonomous Agent Workers (208.8 turns / $\approx 10.6\text{M}$ tokens)**: Execute unit/integration code, script automation, and documentation iterations within isolated story branches.
- **Material & Infrastructure Resources**: Dedicated Windows 11/Server Hyper-V host machine with high-speed NVMe storage, virtual switch networking, and clean OS image pipelines.

---

## 2. Resource foundation pack structure

Detailed specifications, capacity forecasts, and control mechanisms reside in the foundation pack:
1. **Pillar Overview and Trace**: [Resource-Pillar-Overview-and-Trace.md](resource-baseline/foundation/Resource-Pillar-Overview-and-Trace.md) traces TP-01–06 to physical and human requirements.
2. **Role Catalogue & RACI**: [Resource-Role-Catalogue.md](resource-baseline/foundation/Resource-Role-Catalogue.md) defines 8 human lead roles, 8 agent worker roles, decision authorities, and the WBS RACI matrix.
3. **Capacity Estimates & Contractor Rates**: [Resource-Capacity-Estimates.md](resource-baseline/foundation/Resource-Capacity-Estimates.md) details human labor (90h @ \$145–\$177/hr blended $\rightarrow$ \$13,020–\$15,890), agent turns ($208.8\text{ turns}$), host CPU (8–16 cores), host RAM (32–64 GB), and storage throughput ($\ge 2,500\text{ MB/s}$).
4. **Tooling & Assignment Register**: [Resource-Tooling-and-Assignment-Register.md](resource-baseline/foundation/Resource-Tooling-and-Assignment-Register.md) details the full inventory of physical, virtual, and developer tools.
5. **Team Operating Charter**: [Resource-Team-Operating-Charter.md](resource-baseline/foundation/Resource-Team-Operating-Charter.md) establishes working agreements, decision boundaries, and PR gate triage protocols.
6. **Utilization & Control Protocol**: [Resource-Utilization-and-Control-Protocol.md](resource-baseline/foundation/Resource-Utilization-and-Control-Protocol.md) establishes monitoring metrics, RAM/CPU/Turn thresholds, and corrective actions.
7. **Domain Checklist**: [Resource-Domain-Checklist.md](resource-baseline/foundation/Resource-Domain-Checklist.md) confirms PMBOK 8 Resource Performance Domain compliance (**PASS**).

---

## 3. Human resource requirements and governance boundaries

### Key Human Roles and Authority Limits
- **Project Sponsor & Project Manager (Menno Drescher)**: Dual role requiring Steering Committee co-approval for expenditures $> \$25,000$. Coordinates assignments and manages day-to-day execution.
- **Steering Committee**: Multi-disciplinary oversight (CFO, IT Engineering, HR, Analysis, L&D) providing independent governance for major adaptations.
- **Lead / System Architect**: Maintains ADR integrity across the 6 Topic Pillars and contract interfaces.
- **Platform / Hyper-V Engineering Lead**: Hypervisor configuration, Gen 2 VM automation, and performance benchmark sweeps.
- **Security & Compliance Officer**: Independent audit of virtual switch port ACLs and differencing disk sterility.
- **Gateway / Ingress Engineer**: Reverse proxy socket buffering and pool leasing.
- **SRE / Autoscaler Engineer**: Buffer replenish daemons and fleet reaper services.
- **Quality & Test Coordinator**: Acceptance test harness and PR triage verification.

---

## 4. Material resource requirements (physical and virtual infrastructure)

1. **Host Virtualization Hardware**:
   - **Processor**: 8 physical cores (16 logical threads), AMD-V / Intel VT-x with SLAT. (Suspended standby guests consume $0.0\%$ CPU/GPU).
   - **System Memory**: Minimum 32 GB (recommended 64 GB) DDR4/DDR5 ECC RAM. Suspended standby VMs consume $\le 700\text{MB}$ each.
   - **Solid-State Storage**: Dedicated NVMe PCIe Gen 4 SSD ($\ge 2,500\text{ MB/s}$ read, $\ge 500\text{K IOPS}$), minimum 150 GB unfragmented space for `C:\Hyper-V\MXC-Pool\`.
2. **Operating System & Licenses**:
   - Host: Windows 11 Enterprise (x64) with Hyper-V hypervisor role enabled.
   - Guest: Windows 11 Enterprise evaluation / volume license media for clean sysprep bake pipeline.
3. **Developer & Governance Tooling**:
   - PowerShell 7.4+ Core, Python 3.11+ environment (`pytest`), custom `wxc-exec` binary.
   - SIDPA governance scripts: `spec_gate.py`, `pr_gate.py`, `validate_lifecycle.py`.
   - Claude / Gemini AI reasoning API access.

---

## 5. Control protocols and thresholds

- **Effort Variance**: Escalation triggered if human hours exceed $+20\%$ ($> 108\text{h}$).
- **Agent Reasoning**: Escalation to human triage if an agent worker exceeds 25 turns on a story.
- **Host Resource Thresholds**:
  - Standby VM RAM $> 900\text{MB}$ triggers working set trimmer optimization.
  - Standby host CPU $> 0.1\%$ triggers kernel suspension probe.
  - Disk free space $< 30\text{GB}$ triggers immediate fleet reaper deallocation.
