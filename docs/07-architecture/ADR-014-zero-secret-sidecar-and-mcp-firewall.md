---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-12"
inputs:
  - "docs/project-docs/Project-Charter-Phase-3.md"
  - "docs/project-docs/Ideation-Document-Phase-3.md"
  - "docs/07-architecture/PILLARS-Phase-3.md"
  - "docs/07-architecture/ADR-005-transient-differencing-disk.md"
process: "Formulate architectural decisions for host-side mxc-sync git bundles, outbound credential-injecting sidecar proxy, and protocol-aware MCP firewall over VMBus"
outputs:
  - "docs/07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md"
status: "Approved"
---

# ADR 014: Zero-Secret Guest Git Sync, Credential-Injecting Sidecar Proxy & Protocol-Aware MCP Firewall

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning (Phase 3)` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic Pillar:** `TP-12` Zero-Secret Agentic Execution & MCP Protocol Containment. Also touches `TP-01` (Isolation) and `TP-05` (Session Sterility).  
> **Inputs:** [PILLARS-Phase-3.md](PILLARS-Phase-3.md), [Ideation-Document-Phase-3.md](../project-docs/Ideation-Document-Phase-3.md) (`HYP-mxc-023`, `024`), [ADR-005](ADR-005-transient-differencing-disk.md)  
> **Outputs:** ADR-014-zero-secret-sidecar-and-mcp-firewall.md

---

## 1. Executive Summary

Phase 1 (`ADR-005`) enforced default-deny internet egress with port whitelists, while Phase 2 fieldwork (`mxc-hv-6b34439e`) proved that cloning private Git repositories on the host and shipping bare bundles/patches over VMBus keeps GitHub PATs completely out of untrusted guests. Meanwhile, late-2026 agent security architecture (E2B *Managed Secrets*, Modal *Sandbox Sidecars*, and Microsoft *Global Secure Access MCP Firewall*) established two mandatory primitives: **zero static secrets inside the sandbox** and **protocol-level Model Context Protocol (MCP) inspection**.

`ADR-014` formalizes MXC's **Zero-Secret Host-Side Boundary**: `mxc-sync` handles authenticated Git operations solely on the host, a **Credential-Injecting Sidecar Proxy** attaches short-lived tokens only to vetted outbound host requests, and a **Protocol-Aware MCP Firewall PEP** inspects every MCP JSON-RPC tool call crossing VMBus before execution.

---

## 2. Decision & Architectural Mechanics

1. **Host-Side Zero-Secret Git Primitive (`mxc-sync`, `IMP-MXC-017`):**
   - Private repository authentication (`gh` / GitHub App / SSH) lives exclusively on the Hyper-V host.
   - The host creates a bare git bundle or archive and transfers it over VMBus `copy-file` into the guest workspace; after guest work completes, diffs/patches return over VMBus for host-side commit/PR creation.
   - Pre-flight scanner verifies **0 static PATs, private keys, or `.git/config` token URLs** exist in the transferred guest artifact (`ERR_STATIC_SECRET_DETECTED`).
2. **Credential-Injecting Outbound Sidecar Proxy (`IMP-MXC-024`):**
   - Inside an airgapped guest (`0` NICs), agent HTTP/API calls route across VMBus to a host-side sidecar holding placeholder headers (e.g., `Bearer __MXC_SECRET_GITHUB__`).
   - The sidecar resolves only allowlisted host-scoped credentials, stamps them after policy check, and enforces `<= 5 ms` p95 injection latency without exposing secret values in guest memory, disk, or stdout.
3. **Protocol-Aware MCP Firewall PEP (`IMP-MXC-026`):**
   - Every MCP JSON-RPC request crossing VMBus is parsed and checked against a deny-by-default `McpFirewallPolicy`:
     - Allowed MCP `server_id` and pinned manifest/schema digest (preventing rug-pull tool mutations),
     - Allowed `tool_name` allowlist per agent policy,
     - Restricted path/argument regex/deny guards (`..` traversal, secret exfiltration URIs).
   - Unapproved calls fail closed immediately (`ERR_MCP_SERVER_UNAPPROVED`, `ERR_MCP_TOOL_BLOCKED`, `ERR_MCP_ARG_VIOLATION`) within `<= 2 ms` p95 overhead.

---

## 3. Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| Mount scoped GitHub PATs or API `.env` files inside guest VMs | Prompt injection or compromised npm/PyPI build scripts inside the sandbox can read environment variables or disk files and exfiltrate tokens. |
| Rely solely on L4 IP/port egress rules (`ADR-005`) for MCP | Port `:443` rules cannot distinguish benign read-only MCP tool calls from destructive shell/mutation tools or rug-pull schema changes on an approved server hostname. |
| Build a custom in-guest secret broker daemon | Any credential decrypted inside guest memory remains vulnerable to peer guest processes under jailbreak; holding real secrets exclusively on the host partition eliminates guest exposure. |

---

## 4. Consequences & Trade-Offs

- **Positive:** Achieves true zero-secret guest execution (`BEN-19`), prevents rug-pull MCP tool attacks, and works natively on `0`-NIC airgapped Hyper-V micro-VMs.
- **Negative:** Requires host-side sidecar configuration and declarative MCP tool allowlists before onboarding new SaaS endpoints; adds `<= 5 ms` sidecar + `<= 2 ms` MCP inspection latency per proxied call.
- **Mitigation:** Pre-seed common `McpFirewallPolicy` templates for read-only vs. PR-creation workflows and run static secret scans as a fast pre-transfer invariant.
