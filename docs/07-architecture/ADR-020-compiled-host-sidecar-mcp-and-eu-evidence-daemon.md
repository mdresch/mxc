---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-18"
inputs:
  - "docs/project-docs/Project-Charter-Phase-4.md"
  - "docs/project-docs/Ideation-Document-Phase-4.md"
  - "docs/07-architecture/PILLARS-Phase-4.md"
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
process: "Specify compiled host-side credential sidecar proxy, MCP JSON-RPC firewall PEP, EU Evidence Ledger, and freeze-and-rollback daemon architecture"
outputs:
  - "docs/07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# ADR 020: Compiled Host Zero-Secret Sidecar, MCP Firewall PEP & EU Evidence Service

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 4)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-18` Compiled Host Zero-Secret Sidecar, MCP Firewall & EU Evidence Daemon. Also touches `TP-12`, `TP-14`.  
> **Inputs:** [PILLARS-Phase-4.md](PILLARS-Phase-4.md), [Ideation-Document-Phase-4.md](../project-docs/Ideation-Document-Phase-4.md) (`HYP-mxc-032`), [ADR-014](ADR-014-zero-secret-sidecar-and-mcp-firewall.md), [ADR-016](ADR-016-eu-evidence-ledger-and-confidential-attestation.md)  
> **Outputs:** ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md

---

## 1. Executive Summary

`ADR-020` compiles the Phase 3 host-side security and EU compliance control plane (`ADR-014` credential sidecar + MCP firewall and `ADR-016` SHA-256 hash-chained EU Evidence Ledger + Hit-L `freeze-and-rollback` kill switch) into `src/host/wxc_winhttp_proxy_shim/` (`proxy_policy.rs`) and a companion Rust host service module. All secret resolution, MCP inspection, and ledger chaining run strictly on the host partition with zero secrets crossing into guest RAM or disk.

---

## 2. Decision & Architectural Mechanics

1. **Compiled Host Credential Sidecar (`src/host/wxc_winhttp_proxy_shim/src/proxy_policy.rs`):**
   - Replaces declared placeholder headers (`__MXC_SECRET_*__`) strictly for allowlisted `(target_host, secret_scope)` pairs in `<= 5 ms` p95 using constant-time comparisons, redacting real secret values (`[REDACTED]`) from all structured audit events on both allowed and denied paths (`ERR_SECRET_SCOPE_DENIED`).
2. **Compiled MCP JSON-RPC Firewall PEP:**
   - Evaluates incoming `tools/call` envelopes in deterministic precedence (`ERR_MCP_SERVER_UNAPPROVED` $\rightarrow$ `ERR_MCP_SCHEMA_DRIFT` $\rightarrow$ `ERR_MCP_TOOL_BLOCKED` $\rightarrow$ `ERR_MCP_ARG_VIOLATION`) within `<= 2 ms` p95 before upstream dispatch.
3. **Host EU Evidence Ledger & Hit-L Circuit Breaker (`src/host/`):**
   - Persists append-only SHA-256 hash-chained `LedgerEvent` records enforcing `retention_days >= 180` (`ERR_RETENTION_BELOW_EU_FLOOR`) and Entra Conditional Access checks (`ERR_CONDITIONAL_ACCESS_DENIED`).
   - Exposes `freeze-and-rollback` completing in `<= 250 ms` and appending a tamper-evident `"FREEZE_AND_ROLLBACK"` entry to the chain.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Run MCP inspection and secret injection inside the guest OS | Compromised guest code or prompt injection can read in-guest memory and bypass in-guest filters. |
| Ship audit logs exclusively to an external cloud SIEM | Breaks airgapped sovereign deployments and EU AI Act Art. 19 local retention guarantees. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Native compiled performance (`<= 5 ms` sidecar, `<= 2 ms` MCP PEP, `<= 250 ms` rollback) with zero guest secret exposure (`BEN-26`).
- **Negative:** Requires explicit host-side policy configuration for new SaaS scopes and MCP servers.
- **Mitigation:** Provide declarative JSON policy schemas validated fail-closed on startup.
