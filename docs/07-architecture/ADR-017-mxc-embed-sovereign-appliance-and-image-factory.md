---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-15"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
process: "Formulate architectural decisions for turnkey zero-cloud MXC Embed single-host sovereign installer, reproducible ISO-to-Lean CI factory, and gated 5-Act HIL release check"
outputs:
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
status: "Proposed"
---

# ADR 017: Turnkey "MXC Embed" Sovereign On-Premises Appliance & Reproducible ISO-to-Lean Factory

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-15` Turnkey Sovereign On-Premises Appliance ("MXC Embed") & Reproducible Image Factory. Also touches `TP-03` & `TP-10`.  
> **Inputs:** [PILLARS-Phase-3.md](PILLARS-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md) (`HYP-mxc-028`), [ADR-012](ADR-012-cryptographic-supply-chain-slsa.md)  
> **Outputs:** ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md

---

## 1. Executive Summary

Market developments in late 2026 (highlighted by **E2B Embed**) confirmed strong enterprise demand for single-machine, self-hosted sandboxes in regulated sectors that reject SaaS control planes. Phase 2 fieldwork also created `build_win11_agent_from_iso.ps1` + `bake_win11_agent_lean.ps1` (producing the 9s boot `win11-agent-lean.vhdx`) and `demo_win11_agent_sandbox.ps1` (5-Act verification showcase).

`ADR-017` productizes these three capabilities into **Phase 3 `TP-15`**:
1. A parameterized **ISO-to-Lean Agent CI Factory & Auto-Registry Hasher** (`IMP-MXC-018`),
2. A zero-cloud single-host **"MXC Embed" Sovereign Appliance Installer** (`IMP-MXC-031`), and
3. A gated **5-Act Hardware-in-the-Loop (HIL) Release Verification Gate** (`IMP-MXC-023`).

---

## 2. Decision & Architectural Mechanics

1. **Automated ISO-to-Lean CI Image Factory (`IMP-MXC-018`):**
   - Parameterizes ISO path, edition (`Windows 11 Pro`), 12-tool polyglot manifest, AppX/Explorer stripping, CompactOS LZX, and `Optimize-VHD`.
   - Automatically computes SHA-256 digest, updates `golden_image_registry.json`, and emits an `ADR-012` CycloneDX SBOM + SLSA attestation bundle without manual hash editing.
2. **Turnkey "MXC Embed" Sovereign Single-Host Appliance (`IMP-MXC-031`):**
   - Offline installer bundle (`wxc-exec` binary + golden image + `PoolRegistrationGuard` trust root + local firewall/credential bootstrap) executing end-to-end on a single Windows 11 Pro or Windows Server 2025 host in `<= 15 minutes` with **0 outbound internet calls** (`ERR_NETWORK_EGRESS_ATTEMPTED`).
3. **Gated 5-Act HIL Release & PoC Runner (`IMP-MXC-023`):**
   - Automates all 5 verification Acts (9s airgapped boot $\rightarrow$ VMBus `copy-file` $\rightarrow$ polyglot toolchain execution $\rightarrow$ rogue mutation & instant Hyper-V checkpoint rollback $\rightarrow$ bit-identical parent SHA-256 verification) as a deterministic pass/fail release & customer-PoC gate (`ERR_HIL_ACT_FAILED`, `ERR_PARENT_HASH_DRIFT`).

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Ship bespoke PowerShell runbooks per customer PoC | Slow, error-prone onboarding cannot compete with turnkey `E2B Embed` single-host installation. |
| Require cloud package downloads during host provisioning | Fails completely on airgapped banking, defense, and healthcare Hyper-V hosts. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Turns MXC into an installable on-premises product (`BEN-23`), eliminates manual SHA-256 registry updates, and makes 5-minute CISO live demos continuously regression-tested.
- **Negative:** Offline installer bundle size must hold the compacted base image + signed bundles.
- **Mitigation:** CompactOS LZX + `Optimize-VHD -Mode Full` keeps `win11-agent-lean.vhdx` compact and verifiable via streaming SHA-256 checks.
