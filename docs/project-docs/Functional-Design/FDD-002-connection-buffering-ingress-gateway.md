---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md"
  - "docs/project-docs/Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md"
process: "Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts"
outputs:
  - "FDD-002-connection-buffering-ingress-gateway.md"
---

# FDD-002: Connection-buffering ingress gateway

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md), [BRD-002](../Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md)  
> **Process:** Specify technical interfaces, data schemas, algorithmic logic, and invariant contracts  
> **Outputs:** FDD-002-connection-buffering-ingress-gateway.md

**Source ADR:** [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md) — Accepted.  
**Source BRD:** [BRD-002](../Business-Requirements/BRD-002-connection-buffering-ingress-gateway.md) — Approved (2026-10-30).
**Governing Baseline:** `PMP-BL-v1.0.0`  
**Status:** **Approved (2026-10-30)** — `approve-fdd` accepted `approve_fdd` on 2026-10-30 (policy `ada1bc73-753a-450b-b640-6b6fedd5493c`, human acceptance). Gate record: [approve-fdd-002-2026-10-30.adjudication.json](../gates/approve-fdd-002-2026-10-30.adjudication.json).

## Design

### JIT ingress gateway (`scripts/hyperv/dev_harness/jit_ingress_gateway.py`)
* Terminates TLS, matches `/api/v1/adpa/*` → `prod-adpa` and `/api/v1/sidpa/*` → `prod-sidpa`.
* Catalogued listen ports `:8090`, `:8091`, `:8092` select the bound image; guest service port `:8080`.
* On dormant target: hold buffer, call `pool_lease` / `resume`, poll `:8080/health`, flush request.
* `wake_timeout_ms` default 3000 → HTTP 503 with `Retry-After` (not 502/504 from wake).

### Route schema (suite `FDD.md` §2.1)
```json
{
  "match_path": "/api/v1/adpa/{**catch-all}",
  "target_pool": "prod-adpa",
  "guest_port": 8080,
  "wake_timeout_ms": 3000,
  "health_check_path": "/health"
}
```

## Error Handling / Compatibility

| Condition | Behavior |
|---|---|
| Resume exceeds wake_timeout_ms | HTTP 503 with Retry-After; do not drop TCP (`AC-01.3`) |
| Guest already Running | Forward immediately; warm path ≤ 15–25 ms proxy overhead (`AC-01.2`) |

## Out of Scope

- 300 ms `Resume-VM` measurement (`ADR-004`).
- Kerberos whitelist details (`ADR-005`).
- Clock step before sign-in (`ADR-006`).
