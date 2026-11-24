---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Initiating / Planning"
pmbok_process: "5.3 Define Scope & Architectural Strategy Formulation"
lifecycle_stage: "Stage 5 (Pillars & Architecture)"
governance_policy: "approve-adr"
status: "Approved"
inputs:
  - "docs/project-docs/Project-Charter.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Benefits-Statement.md"
process: "Decompose Project Charter objectives into mutually exclusive, collectively exhaustive architectural and functional topic pillars"
outputs:
  - "docs/07-architecture/PILLARS-EXERCISE.md"
  - "Pillar-to-ADR Coverage Matrix"
---

# Pillars Exercise — MXC Micro-Execution Platform

> **PMBOK 8 Process:** `5.3 Define Scope & Architectural Strategy Formulation` (Initiating / Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 5 (Pillars & Architecture)`  
> **Inputs:** [Project-Charter.md](../project-docs/Project-Charter.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Decompose Project Charter into mutually exclusive, collectively exhaustive topic pillars  
> **Outputs:** PILLARS-EXERCISE.md, Pillar-to-ADR Full-Coverage Matrix

**Source:** [Project-Charter.md](../project-docs/Project-Charter.md)

---

## 1. Executive Purpose & Strategic Mandate

The MXC Micro-Execution Platform provides instantaneous, isolated serverless execution for Windows Server 2025 micro-workloads. To eliminate architectural gaps, the technical domain is structured across six mutually exclusive, collectively exhaustive (MECE) Topic Pillars (**TP-01** through **TP-06**). Each topic pillar represents a distinct architectural foundation, owns specific operational invariants, and governs downstream Architectural Decision Records (ADRs).

---

## 2. Core Topic Pillars (TP-01 through TP-06)

### Topic Pillar 1: TP-01 Isolation
- **Domain Focus:** Hardware-enforced kernel and hypervisor boundary virtualization.
- **Strategic Alignment:** Objectives 1 & 2 in Project Charter; `HYP-mxc-001`, `HYP-mxc-002`.
- **Key Architectural Responsibilities:**
  - Type-1 Hyper-V Generation 2 VM topology.
  - VMBus synthetic device isolation; disable COM/LPT legacy hardware.
  - UEFI Secure Boot and hardware virtualization barriers.
- **Governing ADR:** [ADR-001-type-1-hyperv-generation-2.md](ADR-001-type-1-hyperv-generation-2.md)

### Topic Pillar 2: TP-02 Ingress
- **Domain Focus:** Gateway routing, zero-wake-drop buffering, and TLS session handoff.
- **Strategic Alignment:** Objective 3 in Project Charter; `HYP-mxc-003`, `HYP-mxc-004`.
- **Key Architectural Responsibilities:**
  - Reverse proxy request holding buffer during VM resume.
  - Zero client-facing 502/504 errors during wake transitions.
  - Dynamic route table registration and fast loopback proxy forwarding.
- **Governing ADR:** [ADR-002-connection-buffering-ingress-gateway.md](ADR-002-connection-buffering-ingress-gateway.md)

### Topic Pillar 3: TP-03 Image Supply
- **Domain Focus:** Base OS hygiene, deterministic image compilation, and clean state immutability.
- **Strategic Alignment:** Objective 4 in Project Charter; `HYP-mxc-005`, `HYP-mxc-006`.
- **Key Architectural Responsibilities:**
  - Golden VM base bake separation from development clutter.
  - Deterministic staging scripts, service disabling, and pre-warm execution.
  - SHA-256 parent image digest verification and cryptographic sealing.
- **Governing ADR:** [ADR-003-production-base-image.md](ADR-003-production-base-image.md)

### Topic Pillar 4: TP-04 Paused Footprint
- **Domain Focus:** Memory trimming, working set compaction, and sub-second resume mechanics.
- **Strategic Alignment:** Objective 5 in Project Charter; `HYP-mxc-007`, `HYP-mxc-008`.
- **Key Architectural Responsibilities:**
  - Pre-suspend RAM ballooning/compaction to ~1.0–1.2 GB working set.
  - Hyper-V `Suspend-VM` / `Resume-VM` lifecycle orchestration.
  - 0.0% idle host CPU consumption during paused state.
- **Governing ADR:** [ADR-004-paused-ram-standby.md](ADR-004-paused-ram-standby.md)

### Topic Pillar 5: TP-05 Session Sterility
- **Domain Focus:** Storage isolation, zero cross-tenant contamination, and transient disk rollback.
- **Strategic Alignment:** Objective 6 in Project Charter; `HYP-mxc-009`, `HYP-mxc-010`.
- **Key Architectural Responsibilities:**
  - Ephemeral child `.avhdx` differencing disk mounting per session.
  - Immediate teardown and disk purge upon session conclusion.
  - 100% immutable parent `.vhdx` base integrity across all runs.
- **Governing ADR:** [ADR-005-transient-differencing-disk.md](ADR-005-transient-differencing-disk.md)

### Topic Pillar 6: TP-06 Pool & Wake Hygiene
- **Domain Focus:** Watermark pool replenishment, surge auto-scaling, and tenant wake sanitization.
- **Strategic Alignment:** Objective 7 in Project Charter; `HYP-mxc-011` through `HYP-mxc-014`.
- **Key Architectural Responsibilities:**
  - Standby pool buffer management ($K_{\min}$ low watermark, $K_{\max}$ ceiling).
  - Velocity and queue-depth surge expansion.
  - Post-wake hygiene gate: PRNG reseed, clock drift sync ($\le 50\text{ ms}$), DB pool purge.
- **Governing ADR:** [ADR-006-watermark-pool.md](ADR-006-watermark-pool.md)

---

## 3. Pillar-to-ADR Full-Coverage Matrix (100% Invariant)

| Pillar ID | Pillar Name | Primary ADR | Secondary ADR | Scope / Deliverable | Status |
|---|---|---|---|---|:---:|
| **TP-01** | Isolation | `ADR-001` | `ADR-008` | Type-1 Hyper-V Gen2 VM Topology & Auth Gate | **Active / Approved** |
| **TP-02** | Ingress | `ADR-002` | — | Connection-Buffering Reverse Proxy Gateway | **Active / Approved** |
| **TP-03** | Image Supply | `ADR-003` | — | Production Base Image Clean Bake Pipeline | **Active / Approved** |
| **TP-04** | Paused Footprint | `ADR-004` | — | Trimmed Paused RAM Standby Mechanics | **Active / Approved** |
| **TP-05** | Session Sterility | `ADR-005` | — | Transient Differencing Disk Discard Rollback | **Active / Approved** |
| **TP-06** | Pool & Wake Hygiene | `ADR-006` | — | Watermark Standby Pool, Refill & Wake Gate | **Active / Approved** |

---

## 4. Downstream Work Package Derivation Chain

$$\text{Topic Pillar (TP-01..06)} \longrightarrow \text{Governing ADR} \longrightarrow \text{BRD} \longrightarrow \text{FDD} \longrightarrow \text{Epics 001..006} \longrightarrow \text{Stories 1.1..6.4}$$

1. **Architecture Decisions:** Formalized in `docs/07-architecture/ADR-001` through `ADR-006`.
2. **Business Requirements:** Documented in `docs/project-docs/Business-Requirements/`.
3. **Functional Designs:** Detailed in `docs/project-docs/Functional-Design/`.
4. **Implementation Stories:** 17 validated stories under Epics 001–006 with 162 passing contract tests.
