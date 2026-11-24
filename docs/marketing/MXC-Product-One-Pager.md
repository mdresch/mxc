---
document_type: "Client Sales One-Pager"
product: "MXC — Micro-Execution Container"
provider: "CBa Consult (Menno Drescher)"
date: "2026-11-24"
status: "Sales-Ready"
---

# MXC — Micro-Execution Container

### Hardware-Isolated Windows & AI Agent Sandboxes at Container Speed
**For:** CIOs, CISOs, CTOs, Platform Engineering Leaders & Regulated Enterprises | **Provider:** CBa Consult

---

## The Enterprise AI Execution Gap

Organizations are racing to deploy autonomous AI agents, coding assistants, and automated document pipelines—yet **standard containers were never built to isolate untrusted AI agents or full Windows enterprise workloads**:

- **Shared-Kernel Risk:** Docker and Kubernetes containers share the host OS kernel; a single container escape or misconfigured privilege exposes the host and neighboring tenants.
- **Windows Fidelity Wall:** Standard containers cannot run native Windows 11 / Windows Server 2025 Desktop, Win32/COM, or mismatched OS builds cleanly without heavyweight VMs.
- **VM Speed & Density Penalty:** Traditional Hyper-V / VMware VMs take minutes to boot, waste gigabytes of idle RAM, and accumulate persistent drift across sessions.

**MXC eliminates the trade-off.** It delivers **Type-1 hardware-virtualized micro-VMs** and **daemonless OS sandboxes** under one unified policy contract—combining **sub-5 ms hot dispatch**, **airgapped VMBus control**, and **100% session sterility**.

---

## Verified Platform Benchmarks

| Capability | Verified MXC Result | Why It Matters |
| :--- | :--- | :--- |
| **Hot SLA Dispatch** | **≤ 5 ms** *(1.5 ms measured)* | Instantaneous Platinum-tier agent & API execution |
| **Warm Standby Unpause** | **≤ 250 ms** *(~215 ms)* | Near-instant wake with trimmed RAM (~1.0–1.2 GB) |
| **Cold NVMe Standby** | **0.0 MB host RAM** | Scale-to-zero economics for burst & batch workloads |
| **Lean Win11 Agent Cold Boot** | **9 seconds** *(Heartbeat + VMBus)* | Stripped Windows 11 Pro prompt-only shell (`Explorer: Off`), 12 pre-baked agent tools |
| **Session Sterility (ADR-005)** | **100% Parent Invariance** | Transient differencing VHDX + instant checkpoint rollback; zero drift |
| **Automated Assurance** | **271 / 271 Tests Passing** | 188 platform contracts + 83 Rust SDK Hyper-V unit tests |

---

## Core Architectural Features

1. **Multi-Tier Standby Pools (Hot, Warm, Cold):** Dynamically routes tenant requests across `HotRunning` (≤ 5 ms), `WarmPaused` (≤ 250 ms), and `ColdSaved` (0 MB RAM) pools with automatic idle demotion.
2. **Predictive Wake & Connection-Buffering Ingress:** Intercepts TLS `ClientHello` SNI and uses time-series activity forecasting to wake micro-VMs *before* traffic arrives—buffering TCP/HTTP connections so callers see zero dropped requests.
3. **Airgapped-by-Default VMBus Execution:** Runs commands (`wxc-exec`) and file transfers (`copy-file`) over Hyper-V **PowerShell Direct** with **zero network adapter attached** and **zero credentials stored inside the guest**.
4. **Speculative Execution & Instant Rollback:** Snapshot clean baselines (`checkpoint`), let an untrusted AI agent mutate code or run tests, and roll back destructive changes in seconds (`restore`) or discard the entire differencing disk on exit.
5. **Host Memory Combining & High Density:** Deduplicates identical Windows kernel and runtime pages across concurrent micro-VMs with verified Copy-on-Write (COW) tenant isolation.
6. **Unified 10-Backend Policy Contract:** One declarative JSON contract spanning `hyperv`, `processcontainer` (with UI isolation & `--audit` denial learning), `windows_sandbox`, `wslc`, `hyperlight`, `bubblewrap`, `lxc`, `seatbelt`, `isolation_session`, and `nanvix`.

---

## High-Impact Enterprise Use Cases

- **Autonomous AI Agent & Coding Sandboxes:** Give AI agents a full, sterile Windows 11 or Linux environment with Git, Python, Node/TS, and PowerShell—completely isolated from corporate networks and host credentials.
- **Regulated EU Sovereign Execution (EU AI Act Annex III — Dec 2, 2027):** Enforce hardware-level tenant separation, immutable golden images, and verifiable execution audit trails per Regulation (EU) 2026/1744.
- **Legacy & Native Windows Micro-Workloads:** Run Win32, .NET, Office/PDF automation, or ADPA document pipelines at serverless density without maintaining idle VDI fleets.
- **Zero-Drift CI/CD & Security Detonation:** Spin up clean Windows environments per test run and destroy all mutations automatically on teardown.

---

## Engagement Options

| Tier | Scope & Timeline | Ideal Starting Point |
| :--- | :--- | :--- |
| **Phase 0 — Architecture & Live PoC** | **2–4 weeks** · Deploy MXC Hyper-V sandbox + custom golden agent image on your host/cluster | Prove `<250 ms` warm wake & airgapped agent execution on a real workload |
| **Production Sandbox Fabric Rollout** | **6–10 weeks** · Multi-tier pools, ingress gateway, hardened golden image pipeline & audit telemetry | Scale to multi-tenant enterprise AI & automation workloads |
| **Managed Intelligence Provider (`OP-ITG-018`)** | **Ongoing Monthly Retainer** · Pool hygiene, image patching, FinOps & continuous EU AI Act compliance | Conflict-free ongoing stewardship alongside your MSP & MSSP |

**Next Step:** Book a 30-minute **Live MXC Micro-VM Architecture Demo** with **Menno Drescher (CBa Consult)** to see a 9-second airgapped Windows 11 Agent sandbox provision, execute, roll back, and sterilize live.
