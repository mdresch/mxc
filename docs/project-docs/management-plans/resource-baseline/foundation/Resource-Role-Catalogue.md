---
artifact_id: resource-foundation-role-catalogue
parent_plan_id: resource-management
baseline_id: "PMP-BL-v1.0.0"
route: foundation_artifact
governance_policy: approve-pmp
version: "1.0.0"
approval_status: approved
substage: 6.C-1
pmbok_process: Plan Resource Management
depends_on:
  - 6.C-0P
---

# Resource Role Catalogue — MXC Hyper-V for ADPA / SIDPA

**Status:** Draft for review. Distinguishes human leadership/engineering roles and autonomous agent worker roles, mapping them to WBS work packages and decision rights.

## 1. Human resource roles and decision authority

| Role | Responsibilities | Decision authority | Required capability / skills | WBS / activity | Accountable owner |
|---|---|---|---|---|---|
| **Project Sponsor** | Strategic direction, business case ownership, charter authorization. | Approves charter changes, expenditures $> \$25,000$ (with Steering Committee). | Executive leadership, PMBOK governance, ADPA/SIDPA strategy. | All | Menno Drescher |
| **Project Manager** | Day-to-day project execution, schedule tracking, resource assignment, risk monitoring. | Approves task allocations, contingency releases ($\le \$25,000$), schedule adjustments within $20\%$. | PMBOK 8 project leadership, Agile/Agentic workflow coordination. | 1.0, 8.0 | Menno Drescher |
| **Steering Committee** | Independent governance oversight, baseline review, capital expenditure control. | Sole approval authority for expenditures exceeding $\$25,000$ and major scope pivots. | Multi-disciplinary leadership (CFO, IT Eng, HR, Analysis, L&D). | Governance gates | Steering Committee |
| **Lead / System Architect** | System architecture integrity, ADR compliance (TP-01–06), interface standards, contract gating. | Approves architectural decisions, contract schemas, gate criteria modifications. | Hyper-V internals, Windows kernel subsystems, reverse proxy networking. | 1.0, 8.0 | Lead Architect |
| **Platform / Hyper-V Engineering Lead** | Host OS configuration, Gen 2 VM automation, image bake pipelines, memory trimming, resume optimization. | Technical decisions on VM configurations, hypervisor cmdlets, VHDX partition layouts. | PowerShell 7+, Hyper-V cmdlets, Windows Server/11 sysprep, PerfMon profiling. | 2.1, 2.2, 4.1, 4.2, 5.1, 5.2, 5.3 | Platform Lead |
| **Security & Compliance Officer** | Network airgap verification, port ACL audit, ephemeral disk sterility, PRNG unpause validation. | Approves security compliance pass, firewall/ACL rules, data-at-rest sanitization. | Windows filtering platform, Hyper-V vSwitch ACLs, cryptographic RNG standards. | 6.1, 6.2, 6.3, 6.4, 7.3 | Security Lead |
| **Gateway / Ingress Engineer** | Reverse proxy architecture, HTTP connection hold, socket management, dynamic pool lease integration. | Approves ingress buffering thresholds, routing table schemas, HTTP 503 fallback headers. | Asynchronous HTTP proxying (Go/Python/Node), TCP socket multiplexing. | 3.1, 3.2, 3.3 | Gateway Lead |
| **SRE / Autoscaling Engineer** | Dynamic buffer replenishment daemon, velocity burst autoscaler, idle fleet reaper background service. | Approves capacity scaling algorithms, buffer pool thresholds ($K_{\text{base}}, K_{\text{max}}$), reaper cooldowns. | Systems reliability engineering, telemetry counters, daemon service design. | 7.1, 7.2, 7.4 | SRE Lead |
| **Quality & Test Coordinator** | Acceptance test harness execution, multi-session verification, regression test coverage, PR gate auditing. | Signs off on test suite integrity, determines whether acceptance criteria are satisfied. | Automated integration testing (`pytest`), synthetic load testing, PR triage. | 8.0, All PR gates | Test Coordinator |

---

## 2. Autonomous agent worker roles (agentic resource pool)

Autonomous agents operate under human guidance to execute stories via discrete, test-verified code iterations:

| Agent worker role | Assigned WBS activities | Tooling & capability profile | Primary validation contract |
|---|---|---|---|
| **Coordinator Agent** | ACT-01, ACT-19 | Repo governance tools, `validate_lifecycle.py`, milestone reconciliation. | `approve-pmp` verification |
| **Platform Worker** | ACT-02, ACT-03, ACT-07, ACT-08, ACT-09 | Hyper-V PowerShell, guest WMI/KVP data exchange, PerfMon counters. | `spec_gate.py` -> VM checks -> `pr_gate.py` |
| **Release Worker** | ACT-04, ACT-05 | Windows image bake runner, dism/sysprep, Hyper-V snapshot automation. | Clean image audit -> checkpoint validation |
| **Security Worker** | ACT-06, ACT-10, ACT-11 | Hyper-V VSwitch Port ACLs, differencing VHDX attach/detach, SHA-256 diffing. | Port block tests, hash identity verification |
| **Gateway Worker** | ACT-12, ACT-13 | HTTP socket hold proxy, connection queueing, structured 503 producer. | Latency probe ($\le 800\text{ms}$ TTFB), load test |
| **DevOps Worker** | ACT-14 | Reverse proxy URL rewriter, regex route dispatchers, port multiplexers. | Route dispatch unit tests |
| **SRE Worker** | ACT-15, ACT-16, ACT-17, ACT-18 | Background service loops, burst traffic generator, `Resume-VM` triggers, reaper. | Replenish latency ($\le 1.5\text{s}$), cooldown test |
| **Test Coordinator** | ACT-19 | End-to-end multi-agent test harness, synthetic user workload generator. | 12 Charter benefits full operational pass |

---

## 3. RACI matrix (WBS activities vs. roles)

R = Responsible (Executes), A = Accountable (Approves), C = Consulted (Provides input), I = Informed (Kept updated)

| Activity ID | WBS / Story | Human Lead Role | Agent Worker | Lead Architect | Security Lead | Test Lead | Project Manager |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **ACT-01** | WBS 1.0 (Baseline Reconcile) | PM (A) | Coordinator (R) | C | I | C | A |
| **ACT-02** | WBS 2.1 (Gen 2 Provisioning) | Platform Lead (A) | Platform Worker (R) | C | I | C | I |
| **ACT-03** | WBS 2.2 (In-Guest Subsystems) | Platform Lead (A) | Platform Worker (R) | C | I | C | I |
| **ACT-04** | WBS 4.1 (Clean VHDX Bake) | Platform Lead (A) | Release Worker (R) | C | C | C | I |
| **ACT-05** | WBS 4.2 (Warm Checkpoint) | Platform Lead (A) | Release Worker (R) | C | I | C | I |
| **ACT-06** | WBS 6.2 (Network Airgap ACLs) | Security Lead (A) | Security Worker (R) | C | A | C | I |
| **ACT-07** | WBS 5.1 (Zero CPU/GPU Suspend) | Platform Lead (A) | Platform Worker (R) | C | I | C | I |
| **ACT-08** | WBS 5.2 (RAM Pre-Trimming) | Platform Lead (A) | Platform Worker (R) | C | I | C | I |
| **ACT-09** | WBS 5.3 (Sub-300ms Resume) | Platform Lead (A) | Platform Worker (R) | C | I | C | I |
| **ACT-10** | WBS 6.1 (Ephemeral Diff Disk) | Security Lead (A) | Security Worker (R) | C | A | C | I |
| **ACT-11** | WBS 6.3 (Discard & Reproduce) | Security Lead (A) | Security Worker (R) | C | A | C | I |
| **ACT-12** | WBS 3.1 (Ingress Hold & Buffering)| Gateway Lead (A) | Gateway Worker (R) | C | I | C | I |
| **ACT-13** | WBS 3.2 (503 Saturation Fallback)| Gateway Lead (A) | Gateway Worker (R) | C | I | C | I |
| **ACT-14** | WBS 3.3 (Dual Route Rules) | Gateway Lead (A) | DevOps Worker (R) | C | I | C | I |
| **ACT-15** | WBS 7.3 (Wake Hygiene & PRNG) | SRE Lead (A) | SRE Worker (R) | C | C | C | I |
| **ACT-16** | WBS 7.1 (Buffer Replenishment) | SRE Lead (A) | SRE Worker (R) | C | I | C | I |
| **ACT-17** | WBS 7.2 (Concurrency Surge Scale) | SRE Lead (A) | SRE Worker (R) | C | I | C | I |
| **ACT-18** | WBS 7.4 (Fleet Reaper & Reclaim) | SRE Lead (A) | SRE Worker (R) | C | I | C | I |
| **ACT-19** | WBS 8.0 (Phase 1 Final Acceptance)| PM (A) | Test Coordinator (R) | C | C | A | A |
