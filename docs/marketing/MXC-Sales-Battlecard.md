---
document_type: "Internal Sales Battlecard & Objection Handling Guide"
product: "MXC — Micro-Execution Container"
provider: "CBa Consult"
date: "2026-11-24"
---

# MXC Sales Battlecard — CIO / CISO / CTO Conversations

## 1. Ideal Customer Profile (ICP) & Buying Triggers

- **Target Accounts:** Mid-market & regulated enterprises (250–5,000+ seats) in Financial Services, Legal, Healthcare, Manufacturing, and B2B Software running **Microsoft / Windows-heavy estates** and adopting **AI Agents / Copilot Studio / custom agentic workflows**.
- **Economic Buyers:** CISO (isolation & zero-trust), CIO / VP Infrastructure (Hyper-V density & Windows fidelity), CTO / Head of AI (safe autonomous agent execution).
- **Top 2027 Buying Triggers:**
  1. **Security blocking AI agent rollouts** because agents need shell/filesystem access and Docker/shared hosts fail CISO review.
  2. **EU AI Act Annex III deadline (December 2, 2027 — Regulation (EU) 2026/1744)** requiring strict technical containment, auditability, and zero cross-tenant leakage.
  3. **Cloud sandbox lock-in / data residency:** Regulated EU buyers cannot send confidential source code, contracts, or financial data to third-party US cloud agent sandboxes.

---

## 2. Competitive Comparison Matrix

| Dimension | **MXC (CBa Consult)** | Docker / Kubernetes Containers | Traditional VMs / VDI | Cloud Linux Sandboxes *(E2B, Modal, Firecracker)* |
| :--- | :--- | :--- | :--- | :--- |
| **Isolation Boundary** | **Type-1 Hyper-V Gen2 Hardware VM** + Daemonless OS Sandboxes | Shared host kernel (namespace/cgroup escape risk) | Hardware VM | Linux micro-VM (cloud-hosted) |
| **Native Windows 11 / Server 2025** | **Full Native Support** (Win32, .NET, PowerShell, GUI/Prompt) | Headless build-pinned only; no GUI / Win11 | Yes, but slow & heavy | **Linux only** — no native Windows |
| **Wake / Dispatch Speed** | **≤ 5 ms Hot / ≤ 250 ms Warm / 9s Win11 Cold** | ~100–500 ms (cold app start) | 60–180+ seconds | ~150–500 ms (Linux only) |
| **Idle Memory Footprint** | **0 MB (ColdSaved)** / ~1.1 GB trimmed Warm + Host Page Combining | Full RAM while running | 4–16 GB static per idle VM | Billed per second in third-party cloud |
| **Airgapped Control Plane** | **Yes — VMBus PowerShell Direct (`0` NICs required)** | Requires `dockerd` + container network | Requires WinRM/SSH over network | Requires public internet + cloud API |
| **On-Prem / EU Sovereign** | **100% On-Prem / Private Hyper-V / Azure Local** | Yes | Yes | SaaS-first (data leaves perimeter) |

---

## 3. Top 8 Buyer Objections & Crisp Rebuttals

1. **"Why not just run everything in Docker containers?"**
   - *Rebuttal:* Docker shares the host kernel—great for trusted microservices, unacceptable for untrusted AI agents executing generated code. And Docker cannot run native Windows 11, Win32 desktop apps, or mismatched Windows Server builds. MXC gives you **hardware-enforced hypervisor isolation** at container-like speeds—and still supports OCI/Linux images via `wslc`/`lxc` when you need them.
2. **"Aren't Windows VMs way too slow and RAM-hungry for serverless/agent workloads?"**
   - *Rebuttal:* Traditional VMs are. MXC changes the physics with **three tiers**: `HotRunning` (≤ 5 ms), `WarmPaused` (≤ 250 ms unpause with trimmed RAM), and `ColdSaved` (0 MB RAM on NVMe), plus **Hyper-V Host Memory Combining** across identical golden images. Even a cold boot of our stripped Windows 11 Pro Lean Agent image hits Heartbeat + PowerShell Direct in **9 seconds**.
3. **"What if an AI agent deletes files, installs malware, or corrupts the OS?"**
   - *Rebuttal:* Every session runs on a **transient differencing disk** off a read-only golden parent, with **zero network adapter attached** by default. You can snapshot before risky steps (`checkpoint`), roll back in seconds (`restore`), and when the session ends, the entire differencing disk is erased—leaving the golden parent 100% byte-for-byte untouched.
4. **"How do you keep secrets and GitHub/API tokens safe from a compromised agent?"**
   - *Rebuttal:* Secrets never enter the guest VM or wire logs. MXC resolves guest credentials via Windows Credential Manager (`CredReadW`, zeroize-on-drop) and transfers files/git bundles over **Hyper-V VMBus (`copy-file`)**, keeping GitHub tokens, cloud keys, and corporate networks strictly outside the guest.
5. **"We already have an MSP and an MSSP — where does this sit?"**
   - *Rebuttal:* MXC runs cleanly on your existing Windows Server / Hyper-V hosts with zero daemon sprawl and pairs seamlessly with CBa Consult's **Managed Intelligence Provider (`OP-ITG-018`)** RACI—no helpdesk overlap with your MSP, no SOC overlap with your MSSP.
6. **"Is this just a slideware concept or does it actually work?"**
   - *Rebuttal:* It's live and verified today: **271/271 automated tests passing** (188 platform contracts + 83 Rust SDK Hyper-V unit tests) and a **5-Act live demo** that provisions an airgapped Windows 11 agent VM, transfers code over VMBus, runs Python/TypeScript/Git/Ruff/Pytest, simulates a destructive mutation, rolls back via Hyper-V checkpoint, and proves 100% parent sterility.
7. **"What does it cost in new software licenses?"**
   - *Rebuttal:* **€0 in third-party sandbox SaaS licenses.** MXC runs on Hyper-V infrastructure you already own (Windows Server / Azure Local / Windows 11 Pro/Enterprise).
8. **"How fast can we test this without a 6-month IT project?"**
   - *Rebuttal:* Start with a **2–4 week Phase 0 Live PoC** on one existing Hyper-V host: we bake a hardened golden image tailored to your stack, benchmark wake latency & density, and run your real agent/automation workload inside an airgapped sandbox.

---

## 4. High-Signal Discovery Questions
1. *"Where are your teams running AI-generated code or autonomous agent workflows today—and has your CISO signed off on that isolation boundary?"*
2. *"Do you have Windows-native workloads (Win32, .NET, PowerShell, M365/ERP automation) that can't move into Linux containers?"*
3. *"What happens today if a test or agent session mutates a VM—how long does it take to reset to a guaranteed sterile state?"*
4. *"Are you comfortable sending confidential source code or regulated EU data to third-party US cloud sandboxes ahead of the December 2, 2027 EU AI Act Annex III deadline?"*
