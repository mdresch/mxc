---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
  - "docs/project-docs/Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md"
process: "Specify zero-secret git bundle sync, outbound credential-injecting sidecar proxy, and protocol-aware MCP JSON-RPC firewall interfaces"
outputs:
  - "docs/project-docs/Functional-Design/FDD-013-zero-secret-sidecar-and-mcp-firewall.md"
status: "Approved"
---

# FDD-013: Zero-Secret Guest Git Sync, Credential-Injecting Sidecar Proxy & MCP Firewall

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-014](../../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md) | **Source BRD:** [BRD-013](../Business-Requirements/BRD-013-zero-secret-sidecar-and-mcp-firewall.md)  
> **Governing Baseline:** `PMP-BL-v3.0.0` | **Status:** Approved (2026-11-24)

---

## 1. Technical Architecture & Interfaces (`scripts/lib/zero_secret_mcp_gateway.py`)

```
[Airgapped Guest VM (0 NICs)] ──VMBus──▶ [MXC Host Zero-Secret Boundary]
   ├── Bare Repo (0 PATs) ◀──mxc-sync───▶ Host Git Vault + Upstream GitHub
   ├── API Call (Bearer __PLACEHOLDER__) ─▶ [CredentialSidecarProxy] ──▶ SaaS API
   └── MCP JSON-RPC (tools/call) ─────────▶ [McpFirewallPolicy PEP] ──▶ Approved MCP Server
```

### Core Types & Contracts
```python
@dataclass(frozen=True)
class GitBundleSyncPlan:
    repo_slug: str
    bundle_sha256: str
    guest_target_dir: str
    nic_count: int = 0
    secrets_present: bool = False

@dataclass(frozen=True)
class McpFirewallPolicy:
    allowed_servers: dict[str, str]      # server_id -> expected schema_sha256
    allowed_tools: dict[str, set[str]]   # server_id -> {tool_name, ...}
    blocked_arg_patterns: tuple[str, ...]

@dataclass(frozen=True)
class McpCallVerdict:
    allowed: bool
    reason_code: str  # "ALLOWED" | "ERR_MCP_SERVER_UNAPPROVED" | "ERR_MCP_SCHEMA_DRIFT" | "ERR_MCP_TOOL_BLOCKED" | "ERR_MCP_ARG_VIOLATION"
    server_id: str
    tool_name: str
```

---

## 2. Invariant Contracts & Error Codes

| Check | Error Code / Return | Invariant |
|---|---|---|
| Static PAT / private key detected in env or remote URL | `ERR_STATIC_SECRET_DETECTED` | Guest transfer aborted fail-closed. |
| Unknown secret placeholder or disallowed target domain | `ERR_SECRET_SCOPE_DENIED` | Host vault never substitutes real credential. |
| Unlisted `server_id` in MCP JSON-RPC envelope | `ERR_MCP_SERVER_UNAPPROVED` | Tool call dropped before upstream dispatch. |
| `server_id` schema SHA-256 mismatch ("rug-pull") | `ERR_MCP_SCHEMA_DRIFT` | Tool call blocked and server quarantined. |
| Disallowed tool name or blocked path/URI argument | `ERR_MCP_TOOL_BLOCKED` / `ERR_MCP_ARG_VIOLATION` | Fail-closed denial in `<= 2 ms` p95. |
