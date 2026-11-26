---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Monitoring & Controlling"
pmbok_process: "8.2 Manage Quality & 8.3 Control Quality Audits"
lifecycle_stage: "Stage 11 (Audit Record)"
governance_policy: "approve-audit-record"
inputs:
  - "Deliverables (Source code)"
  - "Verification Evidence (Contract test runs)"
  - "Telemetry"
process: "Perform compliance audits, identify drift or regressions, document corrective actions"
outputs:
  - "Audit-Register.md"
  - "Approved Audit Findings"
---

# Audit Register — <project>

> **PMBOK 8 Process:** `8.2 Manage Quality & 8.3 Control Quality Audits` (Monitoring & Controlling)  
> **Governance Policy:** `approve-audit-record` | **Lifecycle Stage:** `Stage 11 (Audit Record)`  
> **Inputs:** Deliverables (Source code), Verification Evidence (Contract test runs), Telemetry  
> **Process:** Perform compliance audits, identify drift or regressions, document corrective actions  
> **Outputs:** Audit-Register.md, Approved Audit Findings


| Field | Value |
|---|---|
| Version | 1.4 (Phases 1–4 Complete Baseline Conformance Audit) |
| Date | 2026-11-25 |
| Status | Complete — All Phase 1–4 ADRs (`ADR-001..006`, `ADR-008..022`) and Governance Exercises Verified |
| Source | 460/460 Python Contract Tests + 18/18 Phase 4 Compiled Rust Tests across Epics 001..021 |

Centralized, not scattered. Every real audit finding (an ADR's accuracy checked against actual code) and every real Governance Exercise (a real-world prerequisite or claim checked against production reality) lives here once, with a stable ID — other documents **reference** the ID rather than copying the finding into their own text.

This register is conceptually distinct from governance-type documents (the policy/baseline itself) — this is the record of checking reality against that baseline.

## ADR-accuracy audits

| ID | ADR | Pillar | Finding | Verdict | Referenced by |
|---|---|---|---|---|---|
| `AUDIT-001` | [ADR-001](../../07-architecture/ADR-001-type-1-hyperv-generation-2.md) | `TP-01` | Hyper-V Gen2 Type-1 micro-VM isolation instead of Windows container namespace verified across all Win32, COM+, WMI, and kernel drivers (`scripts/lib/hyperv_v2.py`). | `confirmed_accurate` | `Story 1.1`, `Story 1.2` |
| `AUDIT-002` | [ADR-002](../../07-architecture/ADR-002-connection-buffering-ingress-gateway.md) | `TP-02` | JIT connection-buffering reverse proxy holding incoming sockets with zero wake-caused 502/504 errors and dual routing rules verified (`scripts/lib/ingress_gateway.py`). | `confirmed_accurate` | `Story 2.1`, `Story 2.2`, `Story 2.3` |
| `AUDIT-003` | [ADR-003](../../07-architecture/ADR-003-production-base-image.md) | `TP-03` | Production base image verified clean of dev tooling, non-prod registration rejected (`BRU-003-01`), warm baseline checkpoint `baseline-hot-ready` verified (`scripts/lib/production_image.py`). | `confirmed_accurate` | `Story 3.1`, `Story 3.2` |
| `AUDIT-004` | [ADR-004](../../07-architecture/ADR-004-paused-ram-standby.md) | `TP-04` | Paused standby guest consumes 0.0% host CPU, working set trimmed to 1024–1228.8 MB prior to suspend, sub-300ms Hyper-V resume verified (`scripts/lib/paused_ram.py`). | `confirmed_accurate` | `Story 4.1`, `Story 4.2`, `Story 4.3` |
| `AUDIT-005` | [ADR-005](../../07-architecture/ADR-005-transient-differencing-disk.md) | `TP-05` | Session writes strictly isolated to child `.avhdx` purged on release/300s idle, parent SHA-256 intact, default-deny egress whitelist enforced (`scripts/lib/session_sterility.py`). | `confirmed_accurate` | `Story 5.1`, `Story 5.2`, `Story 5.3` |
| `AUDIT-006` | [ADR-006](../../07-architecture/ADR-006-watermark-pool.md) | `TP-06` | Standby pool buffer refill in ~1.5s, velocity/queue surge expansion up to $K_{\max}$, 3-step wake hygiene on `/health`, surplus cooldown scale down verified (`scripts/lib/watermark_pool.py`). | `confirmed_accurate` | `Story 6.1`, `Story 6.2`, `Story 6.3`, `Story 6.4` |
| `AUDIT-007` | [ADR-009](../../07-architecture/ADR-009-multi-tier-standby-pools.md) | `TP-07` | Multi-tier standby hierarchy (Hot <=5ms, Warm ~200ms, Cold 2-4s), SLA dispatch routing, and dynamic promotion/demotion lifecycle verified (`scripts/lib/watermark_pool.py`). | `confirmed_accurate` | `Story 7.1`, `Story 7.2`, `Story 7.3` |
| `AUDIT-008` | [ADR-010](../../07-architecture/ADR-010-predictive-wake-interception.md) | `TP-08` | Early TLS SNI extraction within <= 5ms, concurrent async unpause during TLS handshake, and time-series workload forecasting >=60s in advance verified (`scripts/lib/tls_snooper.py`, `scripts/lib/workload_forecaster.py`). | `confirmed_accurate` | `Story 8.1`, `Story 8.2` |
| `AUDIT-009` | [ADR-011](../../07-architecture/ADR-011-hyperv-memory-combining-deduplication.md) | `TP-09` | Hyper-V memory combining configuration, diagnostic performance counters, effective host RAM <= 450 MB floor, and COW hardware page isolation verified (`scripts/lib/memory_combining_probe.py`). | `confirmed_accurate` | `Story 9.1`, `Story 9.2` |
| `AUDIT-010` | [ADR-012](../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md) | `TP-10` | Airgapped SLSA v1.0 provenance, CycloneDX 1.5 SBOM, fail-closed `PoolRegistrationGuard`, and O(1) hot-path admission cache verified (`scripts/lib/supply_chain_attestation.py`). | `confirmed_accurate` | `Story 10.1`, `Story 10.2` |
| `AUDIT-011` | [ADR-013](../07-architecture/ADR-013-autonomous-fleet-economics-scheduler.md) | `TP-11` | Autonomous RAM pressure autotuner (`<75%`/`75-85%`/`>85%`), critical hysteresis override, and `desktop_gui >= 4096 MB` archetype floor guard verified (`scripts/lib/fleet_economics.py`). | `confirmed_accurate` | `Story 11.1`, `Story 11.2` |
| `AUDIT-012` | [ADR-008](../07-architecture/ADR-008-authentication-gated-session-provisioning.md) | `TP-02` | Opt-in `auth_gated` ingress (0 unauthenticated wakes), deny-by-default OIDC/SAML & Entra Agent ID claims mapping, and TTL-bounded identity binding (`[300s, 86400s]`) verified (`scripts/lib/auth_gated_leasing.py`). | `confirmed_accurate` | `Story 12.1`, `Story 12.2` |
| `AUDIT-013` | [ADR-014](../07-architecture/ADR-014-zero-secret-sidecar-and-mcp-firewall.md) | `TP-12` | Zero-secret host git bundle sync (`mxc-sync`), credential-injecting sidecar proxy (`<= 5 ms`, `[REDACTED]` logs), and ordered MCP JSON-RPC firewall (`<= 2 ms`) verified (`scripts/lib/zero_secret_mcp_gateway.py`). | `confirmed_accurate` | `Story 13.1`, `Story 13.2` |
| `AUDIT-014` | [ADR-015](../07-architecture/ADR-015-snapshot-forking-vmbus-streaming-and-ide-workers.md) | `TP-13` | Bounded parallel `.avhdx` snapshot forking (`max_depth <= 4`, `max_parallel <= 5`), SHA-256 chunked VMBus streaming, BOM-tolerant manifest parsing, and zero-secret IDE worker validation verified (`scripts/lib/snapshot_fork_and_vmbus.py`). | `confirmed_accurate` | `Story 14.1`, `Story 14.2`, `Story 14.3` |
| `AUDIT-015` | [ADR-016](../07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | `TP-14` | Tamper-evident EU Evidence Ledger (`>= 180d` retention), Entra Conditional Access gate, `<= 250 ms` freeze-and-rollback circuit breaker, and offline vTPM 2.0 / SEV-SNP / TDX attestation with O(1) cache verified (`scripts/lib/eu_evidence_and_enclave.py`). | `confirmed_accurate` | `Story 15.1`, `Story 15.2` |
| `AUDIT-016` | [ADR-017](../07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | `TP-15` | Reproducible ISO-to-Lean auto-registry builder, zero-cloud `<= 15m` MXC Embed preflight validator, and immutable parent 5-Act HIL release gate verified (`scripts/lib/mxc_embed_appliance.py`). | `confirmed_accurate` | `Story 16.1`, `Story 16.2` |
| `AUDIT-017` | [ADR-018](../07-architecture/ADR-018-ultra-density-ramdisk-ebpf-and-gpu-sandboxes.md) | `TP-16` | 640 MB paused floor / CrossGen2 `< 350 MB` effective RAM / local NUMA pinning, RAM-disk/DAX overlay, kernel TLS safe pass-through, WMI/COM+/Services/GPO telemetry matrix, and `GPU-P` capability/SLA gate verified (`scripts/lib/frontier_density_and_gpu.py`). | `confirmed_accurate` | `Story 17.1`, `Story 17.2`, `Story 17.3` |
| `AUDIT-018` | [ADR-019](../07-architecture/ADR-019-native-rust-wxc-exec-phase3-parity.md) | `TP-17` | Compiled Rust UTF-8 BOM manifest parsing, CLI override precedence, SHA-256 chunked VMBus framing, bounded `.avhdx` snapshot forking, and token-boundary secret scanning verified offline (`src/tools/wxc/src/phase3_parity.rs`, `10/10` Rust tests). | `confirmed_accurate` | `Story 18.1`, `Story 18.2` |
| `AUDIT-019` | [ADR-020](../07-architecture/ADR-020-compiled-host-sidecar-mcp-and-eu-evidence-daemon.md) | `TP-18` | Compiled Rust host credential sidecar (`<= 5 ms`, `[REDACTED]`), deterministic MCP JSON-RPC firewall (`<= 2 ms`), `>= 180d` EU Evidence Ledger, and `<= 250 ms` freeze-and-rollback verified offline (`src/host/wxc_winhttp_proxy_shim/src/phase4_security_ledger.rs`, `8/8` Rust tests). | `confirmed_accurate` | `Story 19.1`, `Story 19.2` |
| `AUDIT-020` | [ADR-021](../07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md) | `TP-19` | Honest fail-closed silicon capability probing (`NO_FAKED_HARDWARE_PASS`), protected-VM exclusion (`Windows 11 Pro Dev`), parent SHA-256 invariance, and read-only PowerShell probe verified (`scripts/lib/silicon_hil_harness.py`, `scripts/hyperv/run_silicon_hil_probe.ps1`, `45/45` tests). | `confirmed_accurate` | `Story 20.1`, `Story 20.2` |
| `AUDIT-021` | [ADR-022](../07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md) | `TP-20` | Deterministic offline pilot bundle manifest builder, constant-time SHA-256 verifier, zero-egress `<= 15m` preflight, and offline PowerShell installer verified (`scripts/lib/mxc_embed_packager.py`, `scripts/hyperv/install_mxc_embed.ps1`, `57/57` tests). | `confirmed_accurate` | `Story 21.1`, `Story 21.2` |

**Verdict taxonomy** (matches `classify-audit-finding`'s real action set, once this project has evidence to build that policy — see "Governance Exercises" below for the parallel reasoning): `confirmed_accurate`, `confirmed_with_drift`, `partially_confirmed`, `contradicted`, `stale_superseded`, `unauditable`, `flag_for_human_review`.

## Governance Exercises

A distinct sub-type from the ADR-accuracy audits above — these check a real-world prerequisite or claim against production reality, not an ADR's accuracy against code. This is also where a story that turns out not to be code-shaped gets reclassified to (see `Story-Execution-Register.template.md`), rather than forcing it into a lighter-weight story variant.

| ID | Checks | Status | Blocker |
|---|---|---|---|
| `GOV-EX-001` | Phase 1 Integrated Acceptance & Verification Coverage (162/162 contract tests passing across 6 Epics, 0 regressions, lifecycle invariants verified). | `confirmed_accurate` | None |
| `GOV-EX-002` | Phase 2 Integrated Acceptance & Verification Coverage (204/204 Python contracts + 83 Rust Hyper-V unit tests passing across Epics 007..012, live 9s Windows 11 Lean boot & 5-Act verification). | `confirmed_accurate` | None |
| `GOV-EX-003` | Phase 3 Integrated Acceptance & Verification Coverage (358/358 Python tests passing across Epics 001..017, 12/12 Phase 3 `spec_gate.py` episodes passed, 5/5 Tier-2 skills citing `LL-014..018`, 31/31 Continuous Improvements Delivered, `validate_lifecycle.py` `Invariants: PASS`). | `confirmed_accurate` | None |
| `GOV-EX-004` | Phase 4 Integrated Acceptance & Verification Coverage (460/460 Python tests + 18/18 Phase 4 compiled Rust offline tests passing across Epics 001..021, 8/8 Phase 4 `spec_gate.py` episodes passed, 4/4 Tier-2 skills citing `LL-019..022`, 2/2 PowerShell scripts `0` AST parse errors, `validate_lifecycle.py` `Invariants: PASS`). | `confirmed_accurate` | None |

## Building `classify-audit-finding` for this project

ADPA's own version of this policy was built only after a real finding (AUDIT-001) existed — not before. If this project accumulates more than one real audit finding and the verdict categories above start to feel repetitive rather than freshly reasoned each time, that's the real signal to build the policy — cite it in `docs/root-cause-log.md` when you do, the same way every other policy in this chain traces back to a real trigger.
