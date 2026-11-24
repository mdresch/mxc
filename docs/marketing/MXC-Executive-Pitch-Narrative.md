---
document_type: "10-Slide Executive Pitch Deck Narrative & Storyboard"
product: "MXC — Micro-Execution Container"
provider: "CBa Consult"
date: "2026-11-24"
---

# MXC Executive Pitch Deck — 10-Slide Narrative & Storyboard

Use this 10-slide structure for 20–30 minute CIO / CISO / CTO executive briefings (pairs with the live 5-Act demo in [demo_win11_agent_sandbox.ps1](file:///c:/Users/MennoDrescher/source/repos/mxc/scripts/hyperv/demo_win11_agent_sandbox.ps1)).

---

### Slide 1 — Title: Hardware-Isolated Windows & AI Agent Sandboxes at Container Speed
- **Visual:** CBa Consult masthead + MXC architecture badge.
- **Speaker Hook:** *"Every enterprise wants autonomous AI agents executing real work—writing code, validating data, automating Windows workflows. The bottleneck isn't the LLM anymore; it's safe, sovereign, instant execution."*

### Slide 2 — The Execution Dilemma: Containers vs. Traditional VMs
- **Visual:** 2×2 quadrant showing **Security/Isolation** (Y-axis) vs. **Speed & Density** (X-axis). Docker sits bottom-right (fast, shared kernel); Traditional VMs sit top-left (isolated, slow/heavy); **MXC occupies the top-right**.
- **Key Proof:** Shared-kernel containers risk host escape and fail on native Windows 11/Win32 workloads; traditional VMs waste GBs of idle RAM and take minutes to boot.

### Slide 3 — Introducing MXC: Multi-Tier Hardware Containment Under One Policy
- **Visual:** Unified declarative JSON policy (`wxc-exec` / `mxc-sdk`) fanning out across **10 backends** (highlighting `Hyper-V Gen2`, `ProcessContainer`, `Windows Sandbox`, `WSLC`).
- **Key Message:** Not another Docker wrapper—a daemonless containment runtime built for zero-trust enterprise workloads.

### Slide 4 — Multi-Tier Standby Pools (Hot, Warm, Cold)
- **Visual:** 3-tier funnel diagram:
  - **HotRunning:** `≤ 5 ms` dispatch (`1.5 ms` measured) — Platinum SLA
  - **WarmPaused:** `≤ 250 ms` unpause (`~1.1 GB` trimmed RAM) — Standard SLA
  - **ColdSaved:** `0.0 MB` host RAM on NVMe (`2–4 s` restore) — Batch/Scale-to-Zero
- **Speaker Note:** Automatic idle demotion (`Hot → Warm → Cold`) plus **Host Memory Combining** lets a single host pack dense multi-tenant fleets without paying for idle VMs.

### Slide 5 — Predictive Wake & Zero-Drop Ingress
- **Visual:** Request timeline showing TLS `ClientHello` SNI interception overlapping the ~215 ms hypervisor unpause while the Connection-Buffering Ingress Gateway holds TCP connections cleanly.
- **Key Message:** Callers experience warm-like latency with zero dropped connections—and time-series forecasting pre-warms pools ahead of known shift/burst windows.

### Slide 6 — Airgapped-by-Default Security & Zero-Mutation Sterility
- **Visual:** Host ↔ Hyper-V VMBus (`PowerShell Direct` + `copy-file`) ↔ Gen2 Micro-VM (`ActiveNetLinks: 0`) ↔ Read-Only Golden VHDX + Transient Differencing Disk (`4 MB`).
- **Key Message:** Zero network adapter required, zero credentials stored inside the guest, and 100% immutable golden parents verified on every teardown.

### Slide 7 — Spotlight: The Lean Windows 11 Pro Agent Image
- **Visual:** Before/After comparison card:
  - **Stripped:** Explorer shell replaced with prompt-only PowerShell (`ExplorerRunning: false`), 90 AppX packages removed, 10 Optional Features & 23 background services disabled, CompactOS LZX.
  - **Pre-Baked:** `git`, `gh`, `pwsh 7`, `ripgrep`, `fd`, `jq`, `7zip`, `python 3.15`, `uv`, `ruff`, `pytest`, `pydantic`, `mcp`, `node 26`, `pnpm`, `typescript 7`, `tsx`.
  - **Measured:** **9-second cold boot** to Heartbeat + instant PowerShell Direct (`0` retries).

### Slide 8 — Live Proof: 5-Act Autonomous Agent Demo
- **Visual:** Screenshot/summary of `demo_win11_agent_sandbox.ps1` passing 5/5 acts live:
  1. Airgapped 9s boot (`Explorer: false`, `NICs: 0`)
  2. Zero-network VMBus file transfer + Git commit
  3. Full polyglot toolchain (`fd`, `ruff`, `pytest`, `pwsh 7`)
  4. Hyper-V Checkpoint → Destructive mutation (`PWNED.txt` + deleted code) → Instant Rollback (`2 passed in 0.12s`)
  5. Sterile teardown (`Parent Untouched: True`)

### Slide 9 — Built for Regulated EU Enterprises & Governance
- **Visual:** Traceability chain connecting MXC to **EU AI Act Annex III (Dec 2, 2027 per Regulation (EU) 2026/1744)**, **ISO/IEC 42001**, and **CBa Consult's MIP (`OP-ITG-018`)** & **ADPA (`OP-ITG-019`)** stack.
- **Key Proof:** **271 / 271 automated tests passing** (`188` platform contracts + `83` Rust SDK unit tests) with full SIDPA / PMBOK 8 audit trails.

### Slide 10 — Call to Action: 2–4 Week Phase 0 Live PoC
- **Visual:** 3-step roadmap: **Week 1** (Host & Golden Image Bake) → **Week 2–3** (Live Workload Integration & SLA Benchmark) → **Week 4** (CISO Security Sign-Off & Scale Plan).
- **Close:** *"Let's pick one high-risk AI agent or Windows automation workflow and prove sterile, sub-second execution on your own Hyper-V host in 14 days."*
