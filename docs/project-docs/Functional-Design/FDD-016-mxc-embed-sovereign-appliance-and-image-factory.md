---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)"
pmp_baseline: "PMP-BL-v3.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md"
  - "docs/project-docs/Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md"
process: "Specify ISO-to-Lean CI factory manifest builder, zero-cloud MXC Embed installer validator, and 5-Act HIL release gate"
outputs:
  - "docs/project-docs/Functional-Design/FDD-016-mxc-embed-sovereign-appliance-and-image-factory.md"
status: "Proposed"
---

# FDD-016: Turnkey "MXC Embed" Sovereign Appliance & Reproducible ISO-to-Lean Factory

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 3)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-017](../../07-architecture/ADR-017-mxc-embed-sovereign-appliance-and-image-factory.md) | **Source BRD:** [BRD-016](../Business-Requirements/BRD-016-mxc-embed-sovereign-appliance-and-image-factory.md)  
> **Governing Baseline:** `PMP-BL-v3.0.0-candidate` | **Status:** Proposed

---

## 1. Technical Architecture & Interfaces (`scripts/lib/mxc_embed_appliance.py`)

```python
@dataclass(frozen=True)
class ImageFactoryBuildSpec:
    image_id: str
    iso_sha256: str
    toolchain_packages: tuple[str, ...]
    explorer_stripped: bool = True
    compact_os_lzx: bool = True

def build_auto_registry_entry(spec: ImageFactoryBuildSpec, vhdx_sha256: str, size_bytes: int) -> dict: ...

def run_mxc_embed_preflight(
    *,
    hyperv_enabled: bool,
    base_image_present: bool,
    outbound_internet_required: bool,
    install_minutes_estimate: float,
) -> tuple[bool, str]: ...

def evaluate_five_act_hil_gate(
    *,
    act_results: list[dict],
    parent_sha_before: str,
    parent_sha_after: str,
) -> tuple[bool, str]: ...
```

---

## 2. Invariant Contracts & Error Codes

| Check | Error Code / Return | Invariant |
|---|---|---|
| Missing required `image_id` or empty `toolchain_packages` | Raises `ValueError` | No incomplete factory manifests permitted. |
| `outbound_internet_required == True` or duration `> 15.0` min | `(False, "ERR_NETWORK_EGRESS_ATTEMPTED")` / `ERR_INSTALL_BUDGET_EXCEEDED` | Guarantees zero-cloud `<= 15m` appliance SLA. |
| `parent_sha_before != parent_sha_after` | `(False, "ERR_PARENT_HASH_DRIFT")` | Immutable parent invariant across 5-Act rollback. |
| Fewer than 5 Acts or any Act `passed=False` | `(False, "ERR_HIL_ACT_FAILED")` | Fail-closed HIL release gate. |
