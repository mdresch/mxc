---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md"
  - "docs/project-docs/Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md"
process: "Specify bare-metal Hyper-V silicon HIL probe, benchmark evaluator, and protected-VM exclusion interfaces"
outputs:
  - "docs/project-docs/Functional-Design/FDD-020-bare-metal-silicon-hil-verification-harness.md"
status: "Approved"
---

# FDD-020: Bare-Metal Silicon HIL Verification Harness

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-021](../../07-architecture/ADR-021-bare-metal-silicon-hil-verification-harness.md) | **Source BRD:** [BRD-020](../Business-Requirements/BRD-020-bare-metal-silicon-hil-verification-harness.md)

---

## 1. Technical Interfaces (`scripts/lib/silicon_hil_harness.py` & `scripts/hyperv/run_silicon_hil_probe.ps1`)

```python
@dataclass(frozen=True)
class HostHardwareCapabilities:
    hyperv_enabled: bool
    numa_node_count: int
    vtpm_supported: bool
    sev_snp_or_tdx_supported: bool
    gpup_supported: bool
    ramdisk_available_mb: int

def evaluate_silicon_capabilities(
    caps: HostHardwareCapabilities | None,
    *,
    require_tee: bool = False,
    require_gpup: bool = False,
    require_multisocket_numa: bool = False,
) -> dict: ...

def verify_hil_benchmark_report(
    report: dict | None,
    *,
    protected_vm_names: tuple[str, ...] = ("Windows 11 Pro Dev",),
) -> tuple[bool, str]: ...
```

---

## 2. Error Codes & Guardrails

| Condition | Return / Error Code | Invariant |
|---|---|---|
| `require_tee=True` on non-TEE host | `tee_verdict == "ERR_TEE_UNSUPPORTED"` | Never fakes confidential enclave support |
| `require_gpup=True` on CPU-only host | `gpup_verdict == "ERR_GPUP_UNSUPPORTED"` | Honest hardware gating |
| `parent_sha_before != parent_sha_after` | `(False, "ERR_PARENT_HASH_DRIFT")` | Immutable golden parent invariant |
| Any protected VM in `touched_vms` | `(False, "ERR_PROTECTED_VM_TOUCHED")` | Protects user dev VM and active sandboxes |
