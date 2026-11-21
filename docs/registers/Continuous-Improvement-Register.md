---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Executing & Continuous Adaptation"
pmbok_process: "4.3 Direct & Manage Project Work / 4.5 Continuous Improvement & Innovation"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 10 (Execution) & Stage 18 (Intent Refinement Feeder)"
governance_policy: "approve-pmp"
inputs:
  - ".claude/skills/implement-story/SKILL.md (Step 9 Breakout & Recap)"
  - "docs/registers/Story-Execution-Register.md"
process: "After each Epic completes, prompt the positive posture cadence question to harvest improvement ideas, record dispositions, and roll deferred ideas into Stage 18 Intent Refinement"
outputs:
  - "docs/registers/Continuous-Improvement-Register.md"
  - "docs/project-docs/Intent-Refinement-Proposal.md (Phase Next Catalyst Feed)"
---

# Continuous Improvement & Idea Register — MXC Hyper-V for ADPA / SIDPA

| Field | Value |
|---|---|
| **Version** | `1.0.0` (Active — Ratified under `PMP-BL-v1.0.0`) |
| **Date** | 2026-11-21 |
| **Status** | Active — Continuous In-Flight Idea & Innovation Backlog |
| **Governance Authority** | `approve-pmp` / PMBOK 8 Continuous Improvement & Organizational Learning |
| **Trigger Cadence** | Executed at the end of every Epic during `implement-story` Step 9 |
| **Downstream Feed** | Stage 16/17 (In-Flight Fast-Path CCB) & Stage 18 (`Intent-Refinement-Proposal.md`) |

---

## 1. Executive Purpose & Governance Protocol

While the **Lessons Learned Register** (`LL-###`) adopts a *defensive posture* to analyze traps, regressions, and root causes, the **Continuous Improvement & Idea Register** (`IMP-###`) establishes a **positive, generative posture**. It ensures that as engineers and agents develop user stories, high-value technical simplifications, architectural enhancements, and product opportunities are captured while tacit knowledge is fresh.

### The Mandatory Per-Epic Cadence Question

Upon verification of the final story of each Epic (Stage 10, Step 9):
> *"What improvement ideas, architectural simplifications, developer-experience boosts, or product opportunities emerged during this Epic that could add value to upcoming Epics or roll into the Intent Refinement Proposal for the next phase?"*

- **If ideas emerge:** Logged below as `IMP-###`.
- **If no new ideas emerge:** A brief sign-off entry is recorded in the Epic Recap Log (`"Epic [N] Recap: No new improvement ideas identified."`).

### Idea Disposition & Lifecycle Routing

1. **`In-Flight Candidate` (Stages 16–17 Fast-Path):** Enhancements that can be introduced within the active phase to accelerate subsequent Epics without expanding baseline scope (e.g. algorithm memoization, test runner optimizations). Evaluated and ratified via `GC-###` in `Adaptation-Plan.md`.
2. **`Rolled into Phase Next Intent Refinement` (Stage 18 Feed):** Valuable opportunities beyond the current baseline scope. These entries are automatically harvested at Phase Close by `Intent-Refinement-Proposal.md` to form the initial work breakdown structure and catalyst for `SPARK-vNext`.

---

## 2. Continuous Improvement Register

| ID | Originating Epic | Idea Title | Category | Description & Technical Value | Target Benefit / Outcome | Disposition & Status |
|---|---|---|---|---|---|---|
| `IMP-MXC-001` | Epic 01 | Automated Subsystem Differential Telemetry Matrix | Architecture / Verification | Generalize the differential subsystem probe from Story 1.2 into an automated telemetry probe executed during JIT guest provisioning to stream structured WMI, COM+, Services, and GPO health directly to the pool controller. | Instantaneous detection of guest image degradation or missing Windows subsystem prerequisites prior to session dispatch (`BEN-05`). | 🔵 `Rolled into Phase Next Intent Refinement` |
| `IMP-MXC-002` | Epic 02 | Early TLS ClientHello Interception for Predictive Hyper-V Resume | Performance / Architecture | Trigger hypervisor `Resume-VM` upon TCP connection establishment and receipt of TLS SNI hostname during the TLS handshake, overlapping the ~220ms hypervisor wake latency with TLS negotiation. | Reduces observed cold wake TTFB from ~350ms down to near-warm latency (~120ms total TTFB), accelerating sub-800ms margins (`BEN-02`). | 🔵 `Rolled into Phase Next Intent Refinement` |
| `IMP-MXC-003` | Epic 03 | Automated Image Cryptographic Signature & SBOM Attestation Gate | Security / Supply Chain | Implement a cryptographic signing and in-toto / cosign attestation check into `PoolRegistrationGuard` for production images, pairing the existing offline VHDX compliance audit with signed SBOM validation (`HYP-mxc-017` horizon). | Guarantees verifiable provenance, zero tampering, and complete supply-chain attestation before allowing any VHDX parent into the standby pool (`BEN-08`). | 🔵 `Rolled into Phase Next Intent Refinement` |
| `IMP-MXC-004` | Epic 04 | Dynamic Host Memory Pressure-Sensitive Standby Density Autotuner | Resource Optimization | Introduce a feedback control loop between host committed physical RAM pressure and the standby fleet controller, dynamically shuttling idle guests between Paused RAM (~1.1 GB, ~215ms wake) and deep compressed NVMe saved state (`HYP-mxc-018` horizon). | Prevents host swapping or commit limit exhaustion during standby fleet scaling beyond 16+ concurrent guests while retaining sub-800ms cold wake margins (`BEN-01`, `BEN-10`). | 🔵 `Rolled into Phase Next Intent Refinement` |
| `IMP-MXC-005` | Epic 04 | Lifecycle Discard Decoupling: In-Session Trim Bypass for Disposable Guests | Architecture / Efficiency | Selectively bypass in-session working set trimming when operating under ADR-005 §4.3 (Whole-Guest Discard). In a disposable model, memory is reclaimed instantly by hypervisor VM teardown, so post-request trim is redundant and skipping it eliminates ~50–100ms teardown overhead. | Streamlines session release latency and CPU overhead while preserving pre-suspend trimming strictly for golden bake and recycled standby replenishment (`BEN-07`, `BEN-12`). | 🔵 `Rolled into Phase Next Intent Refinement` |
| `IMP-MXC-006` | Epic 04 | Ultra-Lean Golden Bake Memory Compression Floor (~512MB–640MB) | Sizing / Density | Challenge the 1.0–1.2 GB paused baseline by integrating prompt-centric OS stripping (`shrink_to_prompt.ps1`), disabling non-essential background daemons (Search, Update, Spooler), and applying Win32 `EmptyWorkingSet` at bake time with Dynamic Memory `MinimumRAM = 512MB`. | Squeezes warm paused baseline from ~1100 MB down to ~640 MB, unlocking an ~80% increase in host standby fleet density (~80 VMs on a 64 GB host) with zero wake page thrashing (`BEN-01`, `BEN-10`). | 🔵 `Rolled into Phase Next Intent Refinement` |

---

## 3. Epic-by-Epic Recap Log

### Epic 01: Type-1 Hyper-V Generation 2 instead of a container namespace
- **Cadence Date:** 2026-11-21
- **Defensive Review (`LL-###`):** `LL-001` (zero-padded epic file matching in `spec_gate.py`), `LL-002` (local store dir process environment isolation for pytest).
- **Positive Improvement Harvest:** Identified `IMP-MXC-001` (Automated Subsystem Differential Telemetry Matrix).

### Epic 02: Connection-buffering ingress gateway
- **Cadence Date:** 2026-11-21
- **Defensive Review (`LL-###`):** `LL-003` (Ingress gateway buffer holding and timeout decoupling).
- **Positive Improvement Harvest:** Identified `IMP-MXC-002` (Early TLS ClientHello Interception for Predictive Hyper-V Resume).

### Epic 03: Production base image separate from the developer image
- **Cadence Date:** 2026-11-21
- **Defensive Review (`LL-###`):** `LL-004` (Pre-checkpoint connection pool sterilization & JIT warm-up decoupling).
- **Positive Improvement Harvest:** Identified `IMP-MXC-003` (Automated Image Cryptographic Signature & SBOM Attestation Gate).

### Epic 04: Paused RAM standby, trimmed before suspend
- **Cadence Date:** 2026-11-21
- **Defensive Review (`LL-###`):** `LL-005` (Pre-suspend working set trimming sequence & vCPU execution state).
- **Positive Improvement Harvest:**
  - `IMP-MXC-004`: Dynamic Host Memory Pressure-Sensitive Standby Density Autotuner (`HYP-mxc-018` horizon).
  - `IMP-MXC-005`: Lifecycle Discard Decoupling (In-session trim bypass for disposable whole-guest teardown).
  - `IMP-MXC-006`: Ultra-Lean Golden Bake Memory Compression Floor (~512MB–640MB target, ~80% density boost).

---

## 4. Phase Close Synthesis (Stage 18 Closed-Loop Link)

All improvement ideas designated as `Rolled into Phase Next Intent Refinement` are systematically harvested during **Stage 18** by `Intent-Refinement-Proposal.md` and mapped directly into the **Phase 2 Work Breakdown Structure** of `SPARK-{PROJECT_PREFIX}-vNext.md`.

