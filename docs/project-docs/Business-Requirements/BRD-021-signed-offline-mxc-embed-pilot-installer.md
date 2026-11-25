---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md"
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
process: "Define business rules for turnkey zero-cloud MXC Embed pilot bundle packaging, integrity verification, and unattended 5-Act self-test"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# BRD-021: Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 4)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-022](../../07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md) | **Topic Pillar:** `TP-20` | **Baseline:** `PMP-BL-v4.0.0-candidate`

---

## 1. Business Need

Regulated EU enterprises evaluating MXC on airgapped Windows 11 Pro or Windows Server 2025 hosts need a turnkey, integrity-checked offline pilot installer that verifies all bundled binaries and golden image digests locally and proves end-to-end containment via the 5-Act HIL self-test within 15 minutes.

---

## 2. Business Rules (BRU)

- **BRU-021-01 (Zero-Cloud Offline Integrity):** The MXC Embed pilot bundle MUST verify every packaged artifact's SHA-256 digest offline (`ERR_BUNDLE_INTEGRITY_FAILED` on any missing or tampered file) with `0` outbound internet requests (`ERR_NETWORK_EGRESS_ATTEMPTED`).
- **BRU-021-02 (Supply-Chain & Time Budget Enforcement):** Installer preflight MUST validate `ADR-012` SLSA registry entries offline and enforce `install_minutes_estimate <= 15.0` (`ERR_INSTALL_BUDGET_EXCEEDED`).
- **BRU-021-03 (Gated Unattended 5-Act Self-Test):** Installation MUST complete with a passing 5-Act HIL verification gate asserting bit-for-bit parent VHDX SHA-256 invariance (`ERR_PARENT_HASH_DRIFT` / `ERR_HIL_ACT_FAILED` on any failure).

---

## 3. Traceability

- **Topic Pillar:** `TP-20` | **ADR:** [ADR-022](../../07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md) | **FDD:** [FDD-021](../Functional-Design/FDD-021-signed-offline-mxc-embed-pilot-installer.md) | **Epic:** [epic-021](../../user-stories/epic-021-signed-offline-mxc-embed-pilot-installer.md) (`WBS 22.0`, `HYP-mxc-034`, `BEN-28`)
