---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Systems Architecture Planning"
pmp_baseline: "PMP-BL-v1.0.0"
lifecycle_stage: "Stage 6 (Requirement: Architecture)"
governance_policy: "approve-adr"
topic_pillar: "TP-02"
inputs:
  - "Spark-Capture.md"
  - "Ideation-Document.md"
  - "Business-Case.md"
  - "Benefits-Statement.md"
  - "docs/hyperv/architecture/ADR.md"
process: "Formulate architectural decisions, evaluate trade-off alternatives, specify consequences"
outputs:
  - "ADR-002-connection-buffering-ingress-gateway.md"
---

# ADR 002: Connection-buffering ingress gateway

> **PMBOK 8 Process:** `5.3 Define Scope & Systems Architecture Planning` (Planning)  
> **Governance Policy:** `approve-adr` | **Lifecycle Stage:** `Stage 6 (Requirement: Architecture)`  
> **Topic pillar:** `TP-02` Ingress. The 300 ms unpause stays with `TP-04`. Kerberos stays with `TP-05`. The clock step stays with `TP-06`.  
> **Inputs:** [Spark-Capture.md](../project-docs/Spark-Capture.md), [Ideation-Document.md](../project-docs/Ideation-Document.md), [Business-Case.md](../project-docs/Business-Case.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md)  
> **Process:** Formulate architectural decisions, evaluate trade-off alternatives, specify consequences  
> **Outputs:** ADR-002-connection-buffering-ingress-gateway.md

**Governing Baseline:** `PMP-BL-v1.0.0` (the identifier printed on [Project-Management-Plan.md](../project-docs/Project-Management-Plan.md)). This lifecycle ADR is **Accepted** under `approve-adr`. It does not by itself replace the approved Project Management Plan baseline.

## 1. Executive Brief

Callers send an ordinary HTTPS request while the guest is paused and its socket is unreachable. Turning the guest off would make them wait through a 14–45 second boot. The decision is a connection-buffering ingress gateway that holds the request, wakes the guest, returns the first byte within 800 ms, and delivers the request to the image that owns it. Username, password, and a second factor ride that same wake. The architecture suite already states the gateway in [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md). This file is the lifecycle copy.

## 2. Status

**Accepted (2026-10-30)** — `approve-adr` accepted `approve_adr` on 2026-10-30 (policy `0063adbf-5659-426d-950b-b2eaab87fb34`, human acceptance). Gate record: [approve-adr-002-2026-10-30.adjudication.json](../project-docs/gates/approve-adr-002-2026-10-30.adjudication.json).

## 3. Context

1. Spark bad choice 2 and business-case Alternative 2 turn the server off. The next caller waits through a 14–45 second boot, and webhooks time out. That alternative is rejected if the wake ceilings hold. Sources: [Spark-Capture.md](../project-docs/Spark-Capture.md), [Business-Case.md](../project-docs/Business-Case.md).
2. While the guest is `Paused`, its TCP socket is unreachable. The spark holds the request and routes the port to the correct image. Source: [Spark-Capture.md](../project-docs/Spark-Capture.md).
3. `HYP-mxc-003` and `BEN-02` require the first byte within 800 ms from a paused guest, together with a 300 ms unpause. Warm traffic does not pass the first-byte check. The unpause measurement stays with `ADR-004` (`TP-04`). Sources: [Ideation-Document.md](../project-docs/Ideation-Document.md), [Benefits-Statement.md](../project-docs/Benefits-Statement.md).
4. `HYP-mxc-004` and `BEN-04` are two routes. A path selects the pool. A catalogued listen port selects the image. The gateway in tree routes by URL path on one listen port, then proxies to guest port `:8080`. The image catalog maps `:8090` to the dev image, `:8091` to the ADPA proof-of-concept image, and `:8092` to the SIDPA dev image. Passing one rule does not pass the other. Sources: [Ideation-Document.md](../project-docs/Ideation-Document.md), [GOLDEN_IMAGE_REGISTRY.md](../hyperv/GOLDEN_IMAGE_REGISTRY.md).
5. `HYP-mxc-010` and `BEN-03` require a held request to wake the guest with no HTTP 502 or 504. User story `US-01` already returns HTTP 503 with `Retry-After` when wake exceeds `wake_timeout_ms` (3000 ms). That 503 is a different case. Source: [USER_STORIES.md](../hyperv/architecture/USER_STORIES.md).
6. `HYP-mxc-008` and `BEN-06` require username, password, and a second factor to meet a guest that was paused. The second-factor product is still unnamed. Kerberos `:88` stays with `ADR-005` (`TP-05`). The clock step to host UTC stays with `ADR-006` (`TP-06`).
7. `HYP-mxc-016` is the future horizon already on the suite record: a long-lived stream survives an idle pause. It stays `Formulated`.

## 4. Decision

1. Deploy a connection-buffering ingress reverse proxy (YARP / Envoy / FastMCP Gateway) in front of the VM cluster. The client opens TLS to the proxy. No custom wake SDK is required.
2. If the guest is dormant, the proxy holds the request open and dispatches `pool_lease` / `resume`.
3. The first byte of the HTTP response, from request arrival on a paused guest to the header flush, is within 800 ms. Warm keep-alive traffic is a separate check. `Resume-VM` at most 300 ms is `ADR-004` and is not restated as a measurement here. The 800 ms ceiling includes that resume.
4. The proxy probes `:8080/health` (about 50 ms) and then flushes the held request. The response is not HTTP 502 or 504 because of the wake. A 503 after `wake_timeout_ms` is a different case.
5. Both routing rules are in force. A path starting with `/api/v1/adpa` leases pool `prod-adpa`. A path starting with `/api/v1/sidpa` leases pool `prod-sidpa`. A catalogued listen port selects the image: `:8090` the dev image, `:8091` the ADPA proof-of-concept image, `:8092` the SIDPA dev image. After either route the guest service port is `:8080`. A check records which rule fired.
6. Username, password, and a second factor ride that same wake. The guest was `Paused` when the request arrived. The person does not watch a 25–45 second boot. Time spent typing is outside the 300 ms and 800 ms ceilings. The second-factor product is still unnamed, so the check cannot be scripted until that name exists.
7. This decision does not set paused RAM, CPU, GPU, or disk (`ADR-004`), the Kerberos whitelist (`ADR-005`), or the clock step, entropy reseed, database-pool purge, and pool refill (`ADR-006`).

### 4.1 Review triggers

Revisit before the first paused-guest first-byte measurement named in `BEN-02`, before scripting `BEN-06` once the second factor is named, and before any claim that `HYP-mxc-016` has left `Formulated`.

## 5. Alternatives Considered

| Alternative | Reason for rejection |
|---|---|
| Turn the server off | The next caller waits through a 14–45 second boot. Spark bad choice 2 and business-case Alternative 2. Rejected if the 300 ms unpause and the 800 ms first byte hold (`BEN-02`). |
| Leave the guest running | The idle machine keeps executing. That comparison belongs to `ADR-001` (`TP-01`) and the footprint readings to `ADR-004`. |
| A custom wake SDK in every client | Ordinary HTTPS callers, including webhooks, cannot be rewritten. The gateway holds the buffer instead. |

## 6. Consequences

### Positive

A standard client gets the first byte without a cold boot and without a wake-caused 502 or 504. The request reaches the image that owns it. Sign-in uses the same wake.

### Negative

The 800 ms ceiling includes the resume. If `Resume-VM` misses 300 ms, this decision fails even when a later byte still arrives. The two routing rules must both be tested. `BEN-06` cannot pass until the second factor has a product name. `HYP-mxc-003`, `HYP-mxc-004`, `HYP-mxc-008`, and `HYP-mxc-010` stay `Formulated`.

## 7. References

| Source | Item | Detail | Pillar | Also |
|---|---|---|---|---|
| Spark | Bad choice 2 | Turn it off and make the caller wait through a 14–45 s boot. | TP-02 | TP-04 |
| Spark | Held request | The request is held and the port is routed to the correct image. | TP-02 | — |
| Spark | 800 ms first byte | The first byte is back in under 800 ms. | TP-02 | TP-04 |
| Spark | Sign-in | Username, password, and MFA ride the same wake. | TP-02 | TP-05, TP-06 |
| Hypothesis | HYP-mxc-003 | First byte within 800 ms from a paused guest. | TP-02 | TP-04 |
| Hypothesis | HYP-mxc-004 | Path selects the pool. Listen port selects the catalogued image. | TP-02 | — |
| Hypothesis | HYP-mxc-008 | Username, password, and MFA meet a guest that was paused. | TP-02 | TP-05, TP-06 |
| Hypothesis | HYP-mxc-010 | A held request wakes the guest with no HTTP 502 or 504. | TP-02 | — |
| Hypothesis | HYP-mxc-016 | Future: a long-lived stream survives an idle pause. | TP-02 | ADR-002 horizon |
| Benefit | BEN-02 | Wake without a cold boot: 300 ms unpause and 800 ms first byte. | TP-02 | TP-04 |
| Benefit | BEN-03 | No wake-caused HTTP 502 or 504. | TP-02 | — |
| Benefit | BEN-04 | The request lands on the owning image. | TP-02 | — |
| Benefit | BEN-06 | Sign-in does not wait on boot. | TP-02 | TP-05, TP-06 |
| Business case | Alternative 2 | Turn the server off. Rejected if the wake ceilings hold. | TP-02 | TP-04 |

`HYP-mxc-016` is the future horizon already noted on the architecture-suite ADR: a WebSocket or Server-Sent Events connection stays held across an idle pause. No stream hold has been tested.

Related records:

- Architecture suite: [docs/hyperv/architecture/ADR.md](../hyperv/architecture/ADR.md) `ADR-002`
- Gap note: [Project-Details-Not-In-ADR.md](../project-docs/Project-Details-Not-In-ADR.md)
- Unpause measurement, not decided here: architecture-suite `ADR-004`
- Kerberos whitelist, not decided here: architecture-suite `ADR-005`
- Clock step before sign-in, not decided here: architecture-suite `ADR-006`
