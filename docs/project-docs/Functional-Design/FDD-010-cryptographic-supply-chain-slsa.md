---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)"
pmp_baseline: "PMP-BL-v2.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-012-cryptographic-supply-chain-slsa.md"
  - "docs/project-docs/Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md"
process: "Specify SLSA provenance envelope schema, SBOM generator interface, offline Ed25519/Cosign verifier, and PoolRegistrationGuard fail-closed contracts"
outputs:
  - "docs/project-docs/Functional-Design/FDD-010-cryptographic-supply-chain-slsa.md"
status: "Approved"
---

# FDD-010: Cryptographic Image Supply Chain & Signed SBOM Attestation

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 2)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Inputs:** [ADR-012](../../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md), [BRD-010](../Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md)  
> **Outputs:** FDD-010-cryptographic-supply-chain-slsa.md

**Source ADR:** [ADR-012](../../07-architecture/ADR-012-cryptographic-supply-chain-slsa.md)  
**Source BRD:** [BRD-010](../Business-Requirements/BRD-010-cryptographic-supply-chain-slsa.md)  
**Governing Baseline:** `PMP-BL-v2.0.0`  
**Status:** Approved (2026-11-24)

---

## 1. Technical Architecture & Interfaces

### 1.1 Build-to-Runtime Attestation Pipeline
```
[Git Commit + Baker Script] + [ISO / Base VHDX]
                     │
                     ▼
   [1. Golden Image Factory (bake_golden_image / build_win11_agent)]
        ├── Outputs: <image>.vhdx (SHA-256)
        ├── Outputs: <image>.sbom.cdx.json (CycloneDX 1.5 SBOM)
        └── Outputs: <image>.intoto.jsonl (SLSA v1.0 Provenance + DSSE Signature)
                     │
                     ▼
   [2. PoolRegistrationGuard (scripts/lib/supply_chain_attestation.py)]
        ├── Verify DSSE signature against pinned offline trust root (Ed25519 / X.509)
        ├── Verify VHDX SHA-256 == provenance.subject[0].digest.sha256
        ├── Verify SBOM SHA-256 == provenance.predicate.sbomDigest
        ├── Check policy: image not revoked, not expired, zero forbidden packages
        └── Admit to golden_image_registry.json OR Quarantine (ERR_ATTESTATION_FAILED)
```

### 1.2 Core Interfaces (`scripts/lib/supply_chain_attestation.py`)
```python
@dataclass(frozen=True)
class AttestationBundle:
    image_id: str
    vhdx_path: str
    vhdx_sha256: str
    sbom_path: str
    sbom_sha256: str
    git_commit: str
    builder_id: str
    issued_at_utc: str
    expires_at_utc: str
    signature_b64: str
    key_id: str

@dataclass(frozen=True)
class AttestationDecision:
    admitted: bool
    image_id: str
    reason_code: str  # "ADMITTED" | "ERR_SIGNATURE_INVALID" | "ERR_DIGEST_MISMATCH" | "ERR_SBOM_INVALID" | "ERR_KEY_REVOKED" | "ERR_EXPIRED"
    verified_at_utc: str

def generate_sbom_and_provenance(
    image_id: str,
    vhdx_path: str,
    packages: list[dict[str, str]],
    git_commit: str,
    signing_key_bytes: bytes,
    key_id: str,
) -> AttestationBundle: ...

def verify_pool_admission(
    bundle: AttestationBundle,
    actual_vhdx_sha256: str,
    actual_sbom_sha256: str,
    trusted_public_keys: dict[str, bytes],
    revoked_key_ids: set[str],
    forbidden_packages: set[str],
    now_utc: str,
) -> AttestationDecision: ...
```

---

## 2. Invariant Contracts & Error Handling

| Check | Contract Invariant | Failure Mode |
|---|---|---|
| **Tampered VHDX** | `actual_vhdx_sha256 != bundle.vhdx_sha256` | Reject with `ERR_DIGEST_MISMATCH`; quarantine image. |
| **Forged / Missing Signature** | Signature fails Ed25519/HMAC-SHA256 verification against `trusted_public_keys[key_id]` | Reject with `ERR_SIGNATURE_INVALID`. |
| **Revoked Signing Key** | `bundle.key_id in revoked_key_ids` | Reject with `ERR_KEY_REVOKED`. |
| **Expired Attestation** | `now_utc > bundle.expires_at_utc` | Reject with `ERR_EXPIRED`. |
| **SBOM Policy Violation** | SBOM digest mismatch or any package in `forbidden_packages` (e.g., `dev-debugger`, `unapproved-tool`) | Reject with `ERR_SBOM_INVALID`. |
| **Airgap Guarantee** | Verifier performs zero network I/O | Verified by unit/contract test with network socket blocked. |
