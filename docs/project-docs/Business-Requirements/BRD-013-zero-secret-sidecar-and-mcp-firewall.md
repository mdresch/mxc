---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Benefits-Statement-Phase-3.md"
  - "docs/user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md"
process: "Define business requirements for zero-secret mxc-sync git bundles, outbound credential sidecar proxy, and protocol-aware MCP firewall"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md"
status: "Approved"
---

# BRD-013: Zero-Secret Guest Git Sync, Credential-Injecting Sidecar Proxy & MCP Firewall

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 3)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Inputs:** [ADR-014](../../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md), [Project-Charter-Phase-3.md](../Project-Charter-Phase-3.md), [Benefits-Statement-Phase-3.md](../Benefits-Statement-Phase-3.md)  
> **Outputs:** BRD-013-zero-secret-sidecar-and-mcp-firewall.md

**Source ADR:** [ADR-014](../../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md)  
**Governing Baseline:** `PMP-BL-v3.0.0` | **Topic Pillar:** `TP-12` | **Status:** Approved (2026-11-24)

---

## 1. Business Need

Enterprise CisOs approving autonomous AI coding and workflow agents cannot place live GitHub PATs, cloud keys, or privileged MCP server tokens inside guest VMs where unreviewed code executes. At the same time, blanket blocking blocks legitimate agent workflows. `BRD-013` defines the business rules ensuring secrets remain strictly host-resident and every MCP tool call is policy-checked at the protocol layer.

---

## 2. Business Rules (BRU)

- **BRU-013-01 (Zero Static Secrets in Guest Payload):** `mxc-sync` MUST strip or reject embedded PATs, SSH private keys, and authenticated remote URLs (`ERR_STATIC_SECRET_DETECTED`) so **0 bytes** of static credentials ever enter the guest VHDX or environment.
- **BRU-013-02 (Host-Side Secret Injection Only):** Real API tokens MUST exist exclusively in the host sidecar vault and never appear in guest-visible error messages or response bodies; placeholder-to-secret resolution MUST complete within **$\le 5\text{ ms}$** p95.
- **BRU-013-03 (Deny-by-Default MCP Protocol Inspection):** All MCP JSON-RPC calls MUST specify an allowlisted `server_id`, matching schema digest, and allowlisted `tool_name`, rejecting unknown/mutated servers or dangerous arguments (`ERR_MCP_SERVER_UNAPPROVED`, `ERR_MCP_TOOL_BLOCKED`, `ERR_MCP_ARG_VIOLATION`) within **$\le 2\text{ ms}$** p95.
- **BRU-013-04 (Airgap Compatibility):** Both `mxc-sync` bundle hydration/patch extraction and MCP gateway routing MUST operate over VMBus with **0** guest NICs attached.
- **BRU-013-05 (Defensive Null & Empty Input Handling):** Empty secret maps, malformed JSON-RPC envelopes, or `None` arguments MUST fail closed cleanly without uncaught exceptions.

---

## 3. Traceability

- **Topic Pillar:** `TP-12` | **ADR:** [ADR-014](../../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md) | **FDD:** [FDD-013](../Functional-Design/FDD-013-zero-secret-sidecar-and-mcp-firewall.md) | **Epic:** [epic-013](../../user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md) (`WBS 14.0`)
- **Hypotheses & Benefits:** `HYP-mxc-023`, `HYP-mxc-024`, `BEN-19` | **Improvements:** `IMP-MXC-017`, `IMP-MXC-024`, `IMP-MXC-026`
