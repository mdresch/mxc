---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.4 Create WBS & Backlog Elaboration (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Story)"
governance_policy: "approve-user-stories"
inputs:
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/project-docs/Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/project-docs/Functional-Design/FDD-013-zero-secret-sidecar-and-mcp-firewall.md"
process: "Decompose Zero-Secret Git Sync, Credential Sidecar Proxy, and Protocol-Aware MCP Firewall into testable user stories"
outputs:
  - "docs/user-stories/epic-013-zero-secret-sidecar-and-mcp-firewall.md"
status: "Approved — Ready for Implementation"
---

# Epic 013: Zero-Secret Guest Git Sync, Credential-Injecting Sidecar Proxy & MCP Firewall

> **PMBOK 8 Process:** `5.4 Create WBS & Backlog Elaboration (Phase 3)` (Planning)  
> **Governance Policy:** `approve-user-stories` | **Lifecycle Stage:** `Stage 6 (Requirement: Story)`  
> **Source ADR:** [ADR-014](../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md) | **WBS:** `14.0` | **Topic Pillar:** `TP-12`  
> **Status:** Approved — Ready for Implementation (2026-11-24) (`IMP-MXC-017`, `024`, `026`)

---

## Story 13.1 — Host-Side Zero-Secret Git Bundle Sync (`mxc-sync`) & Credential Sidecar Proxy
- **WBS:** 14.1
- **Status:** Planned
- **As a** Platform Security Engineer,  
  **I want** `mxc-sync` to transfer clean bare repository bundles over airgapped VMBus and an outbound sidecar proxy to inject short-lived host credentials only on vetted requests,  
  **so that** `0` static tokens, PATs, or SSH keys ever exist inside guest sandboxes.
- **Acceptance Criteria:**
  - **AC-13.1.1:** Pre-transfer scanning rejects any repository remote URL or guest environment containing static PATs/private keys (`ERR_STATIC_SECRET_DETECTED`), while clean bundles verify with `nic_count == 0` and `secrets_present == False`.
  - **AC-13.1.2:** `CredentialSidecarProxy` substitutes declared placeholders strictly for allowlisted `(target_host, secret_scope)` pairs in `<= 5 ms`, redacting real secret values from all returned audit logs and rejecting empty/unknown/unscoped requests fail-closed (`ERR_SECRET_SCOPE_DENIED`).
  - **AC-13.1.3:** Passing `None`, empty strings, or empty config dictionaries safely fails closed without raising `AttributeError`.

---

## Story 13.2 — Protocol-Aware MCP JSON-RPC Firewall over VMBus
- **WBS:** 14.2
- **Status:** Planned
- **As a** CISO / AI Agent Governance Architect,  
  **I want** a protocol-aware MCP Firewall inspecting JSON-RPC requests across `server_id`, schema digest, `tool_name`, and arguments before dispatch,  
  **so that** rug-pull MCP servers, unauthorized tools, and path-traversal or exfiltration payloads are blocked deterministically.
- **Acceptance Criteria:**
  - **AC-13.2.1:** Allowlisted `(server_id, schema_sha256, tool_name)` calls with clean arguments return `McpCallVerdict(allowed=True, reason_code="ALLOWED")` within `<= 2 ms`.
  - **AC-13.2.2:** Unlisted servers (`ERR_MCP_SERVER_UNAPPROVED`), drifted schema hashes (`ERR_MCP_SCHEMA_DRIFT`), disallowed tools (`ERR_MCP_TOOL_BLOCKED`), and matched `blocked_arg_patterns` (`ERR_MCP_ARG_VIOLATION`) fail closed with `allowed=False`.
  - **AC-13.2.3:** Malformed, empty, or `None` JSON-RPC argument dictionaries return fail-closed denial without unhandled exceptions.
