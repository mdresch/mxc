---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 7 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-02"
inputs:
  - "docs/hyperv/architecture/ADR.md"
  - "docs/07-architecture/ADR-002-connection-buffering-ingress-gateway.md"
  - "docs/project-docs/Ideation-Document.md"
  - "docs/project-docs/Benefits-Statement.md"
  - "docs/project-docs/Spark-Capture.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-008-authentication-gated-session-provisioning.md"
---

# ADR 008: Authentication-gated session provisioning and identity-bound VM leasing

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 7 (Requirement: Architecture)`  
> **Topic pillar:** `TP-02` Ingress. This is an opt-in leasing mode of the ADR-002 gateway, not a seventh pillar. Identity-bound leasing also touches `TP-05`.  
> **Inputs:** [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md), [ADR-002](ADR-002-connection-buffering-ingress-gateway.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md), [Spark-Capture.md](../project-docs/Spark-Capture.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-008-authentication-gated-session-provisioning.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

The accepted ingress decision wakes a guest on a path match, before anyone has authenticated. That is the right default for a stateless API. It is the wrong default for a personalized desktop, because the guest is already running before the gateway knows who asked. The decision adds a per-route `auth_gated` mode: hold the connection, take an assertion from the organization's existing identity provider, and only then lease a guest. A second, explicit option keeps that guest bound to the authenticated identity. Path-only leasing stays the default.

## 2. Status

**Accepted (2026-11-04)** — `approve-adr` accepted `approve_adr` on 2026-11-04 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-008-2026-11-04.adjudication.json](../project-docs/gates/approve-adr-008-2026-11-04.adjudication.json). No spark row, hypothesis id, or benefit id is advanced by this acceptance. `HYP-mxc-008` and `BEN-06` stay with `ADR-002`.

## 3. Context

1. Architecture-suite `ADR-002` issues `pool_lease` on a path match, before application-layer authentication. Routing in that record is pool-scoped by path. A released instance returns to the shared pool. Source: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-002` and `ADR-008`.
2. `ADR-005` erases differencing-disk state on release so the next session is not bound to the previous caller. Source: architecture-suite `ADR-005`.
3. `US-01` through `US-05` assume that path-routed, identity-agnostic lease. The suite record says none of them covers credential-triggered wake or a dedicated VM identity. Source: architecture-suite `ADR-008`, citing [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md).
4. The spark, `HYP-mxc-008`, and `BEN-06` describe a different sign-in. Username, password, and a second factor meet a guest that was already resumed for that request. Those rows stay with `ADR-002`. This decision does not claim them and does not move them. Sources: [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
5. No hypothesis id and no benefit id exist for credential-triggered wake or for identity-bound leasing. Those ideas are not `Formulated` in the ideation document, because they were never entered there.

## 4. Decision

1. A route may set `leasing_mode: "auth_gated"`. On that route the gateway still buffers the inbound connection, and it does not issue `pool_lease` when the connection arrives. It terminates TLS, proxies the request to the organization's existing OIDC or SAML identity provider, and leases a guest only after a successful assertion. A failed or abandoned login wakes nothing. MFA stays with that identity provider. MXC does not implement it.
2. Claims on the assertion (group, role, tenant) select the pool or golden-image variant through a configured claims-to-pool-target map. `ADR-003` already separates a production image from a developer image. This decision generalizes that split to more than two variants, chosen by claim rather than hardcoded per route.
3. Two leasing strategies stay named and separate.
   - **Pool-generic** is the `ADR-002` default and is unchanged. The next free instance is leased. On release it returns to the shared pool under `ADR-005`.
   - **Identity-bound** is opt-in. The control plane stores `(authenticated_identity, pool_target) → VM instance id`. A later assertion for that identity resolves to the same instance when it is still in the pool and not yet reaped past `StandbyPaused`. This is the only mode in which per-user state survives a release. Pool-generic leasing cannot do that, because `ADR-005` discards the differencing disk on every release.
4. The `Resume-VM` step (at most 300 ms, `ADR-004`) runs after the identity provider's round-trip, not in parallel with it. Added latency on top of that login is that resume plus the existing health-probe handshake of about 50 ms (`ADR-002`). This decision does not set a new user-visible budget.
5. Out of scope: how a person proves who they are; the expiry of an identity-bound mapping; a "disconnect, don't release" grace window. The mapping's expiry is named as a required follow-up FDD change. The grace window stays a future horizon on the suite record. Neither is decided here.
6. Guest credentials used by MXC's own automation (`hyperv-state-aware.md`) are unchanged.

### 4.1 Review triggers

Revisit before the first route is set to `auth_gated`, and before any identity-bound mapping is persisted. Revisit again when the follow-up FDD sets the binding expiry. Do not treat `HYP-mxc-008` as tested by this decision.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Keep path-only wake for a personalized desktop, and authenticate inside the guest after it is running | The guest becomes `ActiveRunning` before the gateway knows who asked. An anonymous scan, a bot, or an abandoned login still wakes a VM. That is the `ADR-002` default, and it stays the default for stateless API routes. It is rejected only for routes that need a person, not a path. |
| Identity-bind every release | That would silently drop `ADR-005`'s unconditional rollback. A route that only needs a clean next session would keep another caller's state. Binding is opt-in so the rollback stays the default. |
| MXC implements OIDC, SAML, or MFA | The organization already has an identity provider. This decision is when MXC wakes a guest and which guest it wakes, not how a person authenticates. |

## 6. Consequences

### Positive

A personalized session can run on the same paused pool, and no guest runs until an assertion succeeds. Path-only routes keep today's wake. Added latency sits after the identity provider's own wait.

### Negative

An identity-bound guest cannot fall back into the shared pool until someone decides how long the binding is held. This record names that expiry and does not set it. A compromised or over-broad claim can select a higher-privilege image (`ADR-003`) or rebind to another person's retained instance. The claims map is a new access-control surface. No hypothesis is advanced to `Formulated` or beyond, because no hypothesis id exists for this decision. `HYP-mxc-008` and `BEN-06` stay where `ADR-002` left them.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Architecture suite | ADR-008 | Credential-triggered wake and optional identity-bound leasing. | TP-02 | TP-05 |
| Architecture suite | ADR-002 | Path-only `pool_lease` stays the default. | TP-02 | — |
| Hypothesis | HYP-mxc-008 | Guest sign-in after wake. Not this decision. | TP-02 | ADR-002 |
| Benefit | BEN-06 | Sign-in does not wait on boot. Not this decision. | TP-02 | ADR-002 |
| Spark | Sign-in | Username, password, and MFA ride the ADR-002 wake. | TP-02 | — |

No spark row, hypothesis id, or benefit id states credential-triggered wake or identity-bound leasing.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-008`
- Path-only wake, not replaced here: [ADR-002](ADR-002-connection-buffering-ingress-gateway.md)
- Unconditional rollback, unchanged unless a route opts into identity-bound leasing: architecture-suite `ADR-005`
- Image variants selected by claim: architecture-suite `ADR-003`
- Resume ceiling, not decided here: architecture-suite `ADR-004`
