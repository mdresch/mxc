---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.2 Collect Requirements & 5.3 Define Scope (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Business)"
governance_policy: "approve-brd"
inputs:
  - "docs/07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Benefits-Statement-Phase-4.md"
process: "Define business rules for compiled host-side credential sidecar, MCP firewall PEP, and EU Evidence Ledger daemon"
outputs:
  - "docs/project-docs/Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# BRD-019: Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service

> **PMBOK 8 Process:** `5.2 Collect Requirements & 5.3 Define Scope (Phase 4)` (Planning)  
> **Governance Policy:** `approve-brd` | **Lifecycle Stage:** `Stage 6 (Requirement: Business)`  
> **Source ADR:** [ADR-020](../../07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | **Topic Pillar:** `TP-18` | **Baseline:** `PMP-BL-v4.0.0-candidate`

---

## 1. Business Need

Regulated enterprise deployments require compiled, low-latency host services that inject scoped secrets without guest exposure, block unauthorized MCP tool calls before upstream dispatch, and emit tamper-evident EU AI Act / DORA / NIS2 audit chains paired with an instant operator kill switch.

---

## 2. Business Rules (BRU)

- **BRU-019-01 (Host-Only Secret Substitution & Redaction):** The compiled sidecar MUST inject credentials only for allowlisted `(target_host, secret_scope)` pairs in `<= 5 ms` p95 and scrub real secret values (`[REDACTED]`) from all logs on both allowed and denied paths (`ERR_SECRET_SCOPE_DENIED`).
- **BRU-019-02 (Deterministic MCP Firewall Precedence):** The compiled MCP PEP MUST evaluate `server_id` (`ERR_MCP_SERVER_UNAPPROVED`) $\rightarrow$ `schema_sha256` (`ERR_MCP_SCHEMA_DRIFT`) $\rightarrow$ `tool_name` (`ERR_MCP_TOOL_BLOCKED`) $\rightarrow$ `arguments` (`ERR_MCP_ARG_VIOLATION`) in `<= 2 ms` p95.
- **BRU-019-03 (EU AI Act Art. 19 Ledger & Entra Gate):** The host ledger MUST enforce `retention_days >= 180` (`ERR_RETENTION_BELOW_EU_FLOOR`), detect any historical chain tamper (`ERR_LEDGER_CHAIN_BROKEN`), and reject non-compliant/high-risk Entra postures (`ERR_CONDITIONAL_ACCESS_DENIED`).
- **BRU-019-04 (Sub-250ms Hit-L Containment):** `freeze-and-rollback` MUST halt guest execution, restore the clean checkpoint, and append a verified SHA-256 ledger event within `<= 250 ms`.

---

## 3. Traceability

- **Topic Pillar:** `TP-18` | **ADR:** [ADR-020](../../07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | **FDD:** [FDD-019](../Functional-Design/FDD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | **Epic:** [epic-019](../../user-stories/epic-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) (`WBS 20.0`, `HYP-mxc-032`, `BEN-26`)
