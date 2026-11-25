---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/project-docs/Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/project-docs/Functional-Design/FDD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
process: "Decompose compiled host credential sidecar, MCP firewall PEP, and EU Evidence Ledger daemon into testable user stories"
outputs:
  - "docs/user-stories/epic-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
status: "Approved — Ready for Implementation"
---

# Epic 019: Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 4)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-020](../07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | **WBS:** `20.0` | **Topic Pillar:** `TP-18`  
> **Status:** Approved — Ready for Implementation (2026-11-25) (`HYP-mxc-032`, `BEN-26`)

---

## Story 19.1 — Compiled Host Credential Sidecar Proxy & Protocol-Aware MCP JSON-RPC Firewall
- **WBS:** 20.1
- **Status:** Planned
- **As a** Platform Security Engineer,  
  **I want** compiled Rust host policy evaluators in `src/host/wxc_winhttp_proxy_shim/` for allowlisted secret substitution and ordered MCP JSON-RPC tool inspection,  
  **so that** real credentials never cross into guest memory and unauthorized MCP calls fail closed in `<= 2 ms`.
- **Acceptance Criteria:**
  - **AC-19.1.1:** Sidecar credential injection resolves allowlisted `(target_host, secret_scope)` placeholders in `<= 5 ms` while scrubbing real secrets (`[REDACTED]`) from `redacted_audit_json` on both allowed and denied paths, rejecting empty/`None` or unscoped requests with `ERR_SECRET_SCOPE_DENIED`.
  - **AC-19.1.2:** Compiled MCP JSON-RPC evaluation enforces deterministic precedence (`ERR_MCP_SERVER_UNAPPROVED` $\rightarrow$ `ERR_MCP_SCHEMA_DRIFT` $\rightarrow$ `ERR_MCP_TOOL_BLOCKED` $\rightarrow$ `ERR_MCP_ARG_VIOLATION`) in `<= 2 ms`, safely failing closed on empty, `None`, or malformed JSON envelopes.

---

## Story 19.2 — Compiled Host EU Evidence Ledger (`>= 180d`) & Hit-L `freeze-and-rollback` Circuit Breaker
- **WBS:** 20.2
- **Status:** Planned
- **As an** EU AI Act / DORA / NIS2 Compliance Lead,  
  **I want** a compiled host SHA-256 hash-chained `EuEvidenceLedger` (`retention_days >= 180`) paired with a `<= 250 ms` `freeze-and-rollback` circuit breaker,  
  **so that** live host sessions produce tamper-evident compliance chains and halt instantaneously on anomaly.
- **Acceptance Criteria:**
  - **AC-19.2.1:** `EuEvidenceLedger::new()` rejects `retention_days < 180` (`ERR_RETENTION_BELOW_EU_FLOOR`), verifies empty chains safely as `Ok(())`, and detects any historical mutation as `Err("ERR_LEDGER_CHAIN_BROKEN")`.
  - **AC-19.2.2:** `freeze_and_rollback()` rejects empty/`None` identifiers cleanly, returns `"FROZEN_ROLLED_BACK"` within `<= 250 ms`, and appends a verified `"FREEZE_AND_ROLLBACK"` entry to the hash chain.
