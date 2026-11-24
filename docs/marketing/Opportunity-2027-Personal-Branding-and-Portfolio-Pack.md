---
document_type: "Opportunity 2027 — Personal Branding & Portfolio Integration Pack"
product: "MXC — Micro-Execution Container (OP-ITG-017)"
opportunity_links:
  - "mdresch/oppurtunities-2027 :: OP-ITG-017 (MXC Hyper-V JIT Scale-to-Zero)"
  - "mdresch/oppurtunities-2027 :: OP-MKT-007 (Personal Branding Consultancy)"
  - "mdresch/oppurtunities-2027 :: OP-MKT-006 (LinkedIn Ghostwriting / Executive Thought Leadership)"
portfolio_target: "mdresch/my-portfolio-menno (https://my-portfolio-menno.vercel.app)"
owner: "Menno Drescher (Director, CBa Consult)"
date: "2026-11-24"
---

# Opportunity 2027: Personal Branding (`OP-MKT-007`) & `my-portfolio-menno` Showcase Pack for MXC

## 1. Strategic Purpose (Proof-by-Building Authority)

In CBa Consult's **2027 Opportunity Portfolio** (`mdresch/oppurtunities-2027`), **`OP-MKT-007` (Personal Branding Consultancy)** and **`OP-MKT-006` (Executive Thought Leadership)** position executives and technical principals for **inbound advisory and speaking opportunities** with **\$0 working capital**.

**MXC (`OP-ITG-017`)** is Menno Drescher's flagship **"Proof-by-Building"** personal-brand anchor:
- Instead of generic AI commentary, Menno demonstrates **live, working, hardware-isolated Hyper-V micro-VM engineering** (`271/271` passing tests, `≤ 5 ms` hot dispatch, `9s` stripped Windows 11 Lean Agent cold boot, zero-network VMBus execution, and live checkpoint rollback).
- Publishing MXC on **[my-portfolio-menno.vercel.app](https://my-portfolio-menno.vercel.app)** directly fuels inbound discovery for CBa Consult's Core Tier A Flagships (**`OP-ITG-013`** Agent Governance, **`OP-RSK-004`** EU AI Act / ISO 42001 Readiness, **`OP-ITG-018`** Managed Intelligence Provider) and serves as a live reference case for `OP-MKT-007` clients.

---

## 2. Ready-to-Import `mdresch/my-portfolio-menno` Project Entry (JSON)

Drop this entry into `data/` or `content/` in **`mdresch/my-portfolio-menno`** (Next.js + Tailwind portfolio):

```json
{
  "id": "mxc-micro-execution-container",
  "slug": "mxc-hyperv-agent-sandboxes",
  "title": "MXC — Micro-Execution Container (Hyper-V & AI Agent Sandboxes)",
  "tagline": "Hardware-isolated Windows 11, Windows Server 2025 & AI Agent micro-VMs at container speed.",
  "category": "Enterprise Architecture & Sovereign AI Execution",
  "status": "Active — Phase 1 Complete & Phase 2 Epics 007–009 Verified",
  "date": "2026-11",
  "repoUrl": "https://github.com/mdresch/mxc",
  "featured": true,
  "metrics": [
    { "label": "Hot SLA Dispatch", "value": "≤ 5 ms (1.5 ms measured)" },
    { "label": "Warm Standby Unpause", "value": "≤ 250 ms (~215 ms)" },
    { "label": "Win11 Lean Agent Boot", "value": "9 sec (Heartbeat + VMBus)" },
    { "label": "Automated Tests", "value": "271 / 271 Passing" },
    { "label": "Session Sterility", "value": "100% Immutable Golden Parent" }
  ],
  "techStack": [
    "Rust (mxc-sdk / wxc-exec)",
    "Python 3.15",
    "Hyper-V Gen2 (VMBus / PowerShell Direct)",
    "Windows 11 Pro & Server 2025",
    "Multi-Tier Standby Pools",
    "TLS SNI Predictive Wake",
    "SIDPA / PMBOK 8 Governance"
  ],
  "summary": "MXC bridges the gap between shared-kernel Docker containers and slow traditional VMs. Built for untrusted autonomous AI agents and regulated EU enterprises, it delivers Type-1 Hyper-V Generation 2 micro-VMs controlled over airgapped VMBus (zero network adapter required), multi-tier Hot/Warm/Cold standby pools, predictive TLS wake, host memory combining, and instant checkpoint rollback.",
  "highlights": [
    "9/9 Epics delivered across Phase 1 (Isolation, Buffering Ingress, Golden Images, Paused RAM Trimming, Differencing Sterility, Watermark Pools) and Phase 2 (Multi-Tier Pools, Predictive Wake, Host Memory Combining).",
    "Custom ISO-to-Lean Windows 11 Pro Agent image: 90 consumer AppX packages & Explorer stripped, 12-tool polyglot agent stack pre-baked, 9-second cold boot.",
    "Live 5-Act verification: airgapped VMBus file transfer, Git/Python/TypeScript/Ruff/Pytest execution, simulated rogue mutation, instant Hyper-V checkpoint rollback, and zero-mutation parent verification.",
    "Aligned with EU AI Act Annex III (December 2, 2027 per Regulation (EU) 2026/1744) and ISO/IEC 42001 technical containment."
  ],
  "cta": {
    "primaryLabel": "View Repository on GitHub",
    "primaryUrl": "https://github.com/mdresch/mxc",
    "secondaryLabel": "Request 15-Min Live Demo (CBa Consult)",
    "secondaryUrl": "/contact?topic=mxc-demo"
  }
}
```

---

## 3. Ready-to-Ingest RAG Knowledge Chunk (`my-portfolio-menno` AI Chatbot)

Add this Markdown block to `content/` and run `node load-rag-content.js` in **`mdresch/my-portfolio-menno`** so visitors querying the portfolio AI assistant get accurate, grounded answers:

```markdown
# Project: MXC (Micro-Execution Container) — Built by Menno Drescher (CBa Consult)

Menno Drescher architected and built **MXC (Micro-Execution Container)** (`github.com/mdresch/mxc`), a multi-tier hardware containment and micro-VM execution fabric designed for untrusted autonomous AI agents, native Windows 11 / Windows Server 2025 workloads, and regulated EU enterprises.

## What Makes MXC Different from Docker
Unlike Docker containers—which share the host OS kernel and struggle with native Windows 11 or Win32 workloads—MXC unifies 10 containment backends (including Type-1 Hyper-V Gen2 micro-VMs, Windows ProcessContainer, Windows Sandbox, and WSLC) under a single declarative Rust CLI/SDK (`wxc-exec` / `mxc-sdk`). Hyper-V sandboxes run airgapped by default (`0` network adapters), execute commands and file transfers over VMBus (`PowerShell Direct`), store zero credentials inside the guest, and guarantee 100% session sterility via immutable golden VHDX parents and transient differencing disks.

## Verified Engineering Milestones
- **9 Epics Delivered** across Phase 1 and Phase 2 with **271/271 automated tests passing** (188 Python contract tests + 83 Rust SDK Hyper-V unit tests).
- **Multi-Tier Standby Pools:** `HotRunning` (≤ 5 ms dispatch), `WarmPaused` (≤ 250 ms unpause), `ColdSaved` (0.0 MB host RAM on NVMe), plus TLS SNI predictive wake and Hyper-V host memory combining.
- **Lean Windows 11 Pro Agent Image:** Built unattended from ISO with Explorer bypassed (prompt-only PowerShell shell), 90 consumer AppX packages removed, CompactOS LZX compression, and a 12-tool polyglot agent stack (`git`, `gh`, `pwsh 7`, `python 3.15`, `uv`, `ruff`, `pytest`, `node 26`, `pnpm`, `typescript 7`, `tsx`), achieving a **9-second cold boot**.
- **Governance & EU Compliance:** Governed end-to-end under SIDPA / PMBOK 8 and aligned with the **EU AI Act Annex III** compliance deadline (**December 2, 2027**, per Regulation (EU) 2026/1744) and **ISO/IEC 42001**.
```

---

## 4. 4-Week Personal Branding Distribution Plan (`OP-MKT-007` Cadence)

| Week | Channel & Asset | Goal & CTA |
| :--- | :--- | :--- |
| **Week 1** | Publish MXC project card + RAG chunk on **`my-portfolio-menno.vercel.app`** | Permanent flagship proof page for all inbound profile visits |
| **Week 2** | LinkedIn Post #1 (*Why Docker Isn't Enough for Enterprise AI Agents*) from [MXC-LinkedIn-and-Outreach-Kit.md](MXC-LinkedIn-and-Outreach-Kit.md) | Spark CISO/CTO discussion; link to `my-portfolio-menno` case study |
| **Week 3** | LinkedIn Post #2 (*9-Second Prompt-Only Windows 11 Agent Micro-VM*) + attach [MXC-Product-One-Pager.pdf](MXC-Product-One-Pager.pdf) | Demonstrate hands-on engineering authority; invite 15-min live demos |
| **Week 4** | LinkedIn Post #3 (*EU AI Act Annex III — Dec 2, 2027 & Hardware Sterility*) + targeted CIO/CISO emails (Emails A & B) | Convert readers into Phase 0 PoC / `OP-ITG-013` / `OP-ITG-018` discovery calls |
