---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md"
  - "docs/project-docs/Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md"
process: "Specify SHA-256 hash-chained EvidenceLedger, Entra Conditional Access evaluator, FreezeRollbackCircuitBreaker, and ConfidentialEnclaveAttestor interfaces"
outputs:
  - "docs/project-docs/Functional-Design/FDD-015-eu-evidence-ledger-and-confidential-attestation.md"
status: "Proposed"
---

# FDD-015: Unified EU Regulatory Evidence Ledger, Kill Switch & Confidential Enclave Attestation

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-016](../../07-architecture/ADR-016-eu-evidence-ledger-and-confidential-attestation.md) | **Source BRD:** [BRD-015](../Business-Requirements/BRD-015-eu-evidence-ledger-and-confidential-attestation.md)  
> **Governing Baseline:** `PMP-BL-v3.0.0-candidate` | **Status:** Proposed

---

## 1. Technical Architecture & Interfaces (`scripts/lib/eu_evidence_and_enclave.py`)

```python
@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    timestamp_utc: str
    event_type: str
    session_id: str
    payload_sha256: str
    prev_hash: str
    entry_hash: str

class EvidenceLedger:
    def __init__(self, *, retention_days: int = 180) -> None: ...
    def append_event(self, *, event_type: str, session_id: str, payload: dict, timestamp_utc: str) -> LedgerEvent: ...
    def verify_chain(self) -> tuple[bool, str]: ...

def evaluate_entra_conditional_access(posture: dict | None) -> tuple[bool, str]: ...

class FreezeRollbackCircuitBreaker:
    def freeze_and_rollback(self, *, session_id: str, operator_id: str, checkpoint_id: str, ledger: EvidenceLedger) -> dict: ...

def verify_enclave_attestation(
    *,
    tee_type: str,             # "vtpm2" | "amd_sev_snp" | "intel_tdx"
    hardware_supported: bool,
    measured_pcr_hex: str | None,
    expected_pcr_hex: str,
) -> tuple[bool, str]: ...
```

---

## 2. Invariant Contracts & Error Codes

| Check | Error Code / Return | Invariant |
|---|---|---|
| `retention_days < 180` | Raises `ValueError` (`ERR_RETENTION_BELOW_EU_FLOOR`) | Enforces EU AI Act Art. 19 6-month minimum. |
| Empty ledger verification | Returns `(True, "OK")` | Handles 0-entry empty chain safely without index errors. |
| Corrupted historical `LedgerEvent` | Returns `(False, "ERR_LEDGER_CHAIN_BROKEN")` | Deterministic hash-chain verification. |
| `hardware_supported == False` | Returns `(False, "ERR_TEE_UNSUPPORTED")` | Never fakes confidential attestation on unsupported silicon. |
| `measured_pcr_hex != expected_pcr_hex` or `None` | Returns `(False, "ERR_PCR_ATTESTATION_FAILED")` | Fail-closed before releasing secrets. |
