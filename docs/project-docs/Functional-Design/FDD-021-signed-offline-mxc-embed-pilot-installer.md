---
pmbok_edition: "PMBOK 8"
pmbok_process_group: "Planning"
pmbok_process: "5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)"
pmp_baseline: "PMP-BL-v4.0.0-candidate"
lifecycle_stage: "Stage 6 (Requirement: Solution)"
governance_policy: "approve-fdd"
inputs:
  - "docs/07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md"
  - "docs/project-docs/Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md"
process: "Specify offline MXC Embed pilot bundle packager, SHA-256 manifest verifier, and post-install 5-Act HIL gate interfaces"
outputs:
  - "docs/project-docs/Functional-Design/FDD-021-signed-offline-mxc-embed-pilot-installer.md"
status: "Draft — Ready for Stage 5/6 Approval"
---

# FDD-021: Signed Offline "MXC Embed" Sovereign Enterprise Pilot Installer

> **PMBOK 8 Process:** `5.3 Define Scope & Detailed Interface/Solution Design (Phase 4)` (Planning)  
> **Governance Policy:** `approve-fdd` | **Lifecycle Stage:** `Stage 6 (Requirement: Solution)`  
> **Source ADR:** [ADR-022](../../07-architecture/ADR-022-signed-offline-mxc-embed-pilot-installer.md) | **Source BRD:** [BRD-021](../Business-Requirements/BRD-021-signed-offline-mxc-embed-pilot-installer.md)

---

## 1. Technical Interfaces (`scripts/lib/mxc_embed_packager.py` & `scripts/hyperv/install_mxc_embed.ps1`)

```python
@dataclass(frozen=True)
class EmbedBundleManifest:
    bundle_version: str
    offline_only: bool
    artifacts: dict[str, str]  # relative_path -> lowercase 64-hex sha256
    golden_vhdx_sha256: str

def build_embed_bundle_manifest(
    bundle_version: str,
    file_hashes: dict[str, str] | None,
    golden_vhdx_sha256: str,
) -> EmbedBundleManifest: ...

def verify_embed_bundle_offline(
    manifest: EmbedBundleManifest | None,
    actual_file_hashes: dict[str, str] | None,
    *,
    outbound_internet_attempted: bool = False,
    install_minutes_estimate: float = 10.0,
) -> tuple[bool, str]: ...
```

---

## 2. Error Codes & Guardrails

| Condition | Return / Error Code | Invariant |
|---|---|---|
| `outbound_internet_attempted == True` | `(False, "ERR_NETWORK_EGRESS_ATTEMPTED")` | Strict zero-cloud offline guarantee |
| Missing, extra, or mismatched file digest | `(False, "ERR_BUNDLE_INTEGRITY_FAILED")` | Constant-time `hmac.compare_digest` verification |
| `install_minutes_estimate <= 0` or `> 15.0` or non-finite | `(False, "ERR_INSTALL_BUDGET_EXCEEDED")` | `<= 15 min` sovereign deployment SLA |
| Empty/`None` manifest or invalid SHA-256 | Raises `ValueError` or returns `(False, "ERR_BUNDLE_INTEGRITY_FAILED")` | Fail-closed defensive handling |
