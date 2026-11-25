---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
  - "docs/project-docs/Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
process: "Specify compiled host credential sidecar, MCP JSON-RPC firewall PEP, EU Evidence Ledger, and freeze-and-rollback interfaces"
outputs:
  - "docs/project-docs/Functional-Design/FDD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
status: "Approved"
---

# FDD-019: Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-020](../../07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | **Source BRD:** [BRD-019](../Business-Requirements/BRD-019-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md)

---

## 1. Technical Interfaces (`src/host/wxc_winhttp_proxy_shim/src/proxy_policy.rs` & `src/host/`)

```rust
pub struct SidecarInjectionResult {
    pub allowed: bool,
    pub reason_code: String, // "OK" | "ERR_SECRET_SCOPE_DENIED"
    pub outbound_headers: std::collections::BTreeMap<String, String>,
    pub redacted_audit_json: String,
}

pub struct McpCallVerdict {
    pub allowed: bool,
    pub reason_code: String, // "ALLOWED" | "ERR_MCP_SERVER_UNAPPROVED" | "ERR_MCP_SCHEMA_DRIFT" | "ERR_MCP_TOOL_BLOCKED" | "ERR_MCP_ARG_VIOLATION"
    pub server_id: String,
    pub tool_name: String,
}

pub struct EuEvidenceLedger { /* retention_days >= 180, SHA-256 chain */ }
impl EuEvidenceLedger {
    pub fn new(retention_days: u32) -> Result<Self, String>;
    pub fn append_event(&mut self, event_type: &str, session_id: &str, payload_json: &str, timestamp_utc: &str) -> Result<LedgerEvent, String>;
    pub fn verify_chain(&self) -> Result<(), String>;
}
```

---

## 2. Error Codes & Latency Budgets

| Check | Error Code | Latency / Invariant |
|---|---|---|
| Unscoped/missing placeholder in sidecar | `ERR_SECRET_SCOPE_DENIED` | `<= 5 ms` p95; real secret never in `redacted_audit_json` |
| Unapproved MCP server / schema drift / tool / arg | `ERR_MCP_SERVER_UNAPPROVED` / `ERR_MCP_SCHEMA_DRIFT` / `ERR_MCP_TOOL_BLOCKED` / `ERR_MCP_ARG_VIOLATION` | `<= 2 ms` p95 deterministic order |
| `retention_days < 180` or mutated chain | `ERR_RETENTION_BELOW_EU_FLOOR` / `ERR_LEDGER_CHAIN_BROKEN` | EU AI Act Art. 19 (`>= 180d`), empty chain verifies `Ok(())` |
| Hit-L `freeze_and_rollback()` | State `"FROZEN_ROLLED_BACK"` | `<= 250 ms` + appended `"FREEZE_AND_ROLLBACK"` event |
