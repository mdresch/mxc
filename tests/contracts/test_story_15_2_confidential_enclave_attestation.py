"""Contract tests for Story 15.2 — vTPM 2.0 & Confidential VM (AMD SEV-SNP / Intel TDX) Remote Attestation Gate (ADR-016).

Spec Gate Episode: spec-15_2-8cf6474a (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1 (Hardware Capability Honesty): verify_enclave_attestation() checks hardware_supported is True
      first and explicitly returns (False, "ERR_TEE_UNSUPPORTED") on unsupported silicon rather than
      fabricating compliance—even if measured_pcr_hex is None or mismatched.
  I2 (Fail-Closed Quote Verification & Offline Execution): Supported TEE profiles ("vtpm2",
      "amd_sev_snp", "intel_tdx") verify non-empty valid hex measured_pcr_hex against expected_pcr_hex
      100% offline using constant-time hmac.compare_digest, returning (True, "ATTESTED") on match
      and (False, "ERR_PCR_ATTESTATION_FAILED") on unknown tee_type, None, empty, non-hex, or
      mismatched measurements.
  I3 (Zero Hot-Dispatch Overhead): EnclaveAttestationCache executes quote verification strictly at
      admission via admit() and exposes is_admitted() as an O(1) in-memory lookup incurring 0.0 ms
      cryptographic overhead on post-admission dispatch.
"""

from __future__ import annotations

import socket
import time

import scripts.lib.eu_evidence_and_enclave as enclave_mod
from scripts.lib.eu_evidence_and_enclave import (
    EnclaveAttestationCache,
    verify_enclave_attestation,
)

GOLDEN_PCR_HEX = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"


# Story 15.2 — AC-15.2.1 (ADR-016)
def test_ac_15_2_1_supported_enclaves_attest_offline_and_cache_has_zero_dispatch_overhead(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise AssertionError("Network access is strictly forbidden during offline enclave attestation")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    for tee_type in ("vtpm2", "amd_sev_snp", "intel_tdx"):
        assert verify_enclave_attestation(
            tee_type=tee_type,
            hardware_supported=True,
            measured_pcr_hex=GOLDEN_PCR_HEX,
            expected_pcr_hex=GOLDEN_PCR_HEX,
        ) == (True, "ATTESTED")

    # Case-insensitive hex matching
    assert verify_enclave_attestation(
        tee_type="amd_sev_snp",
        hardware_supported=True,
        measured_pcr_hex=GOLDEN_PCR_HEX.upper(),
        expected_pcr_hex=GOLDEN_PCR_HEX.lower(),
    ) == (True, "ATTESTED")

    # Admission cache stores verified (image_or_vm_id, tee_type, pcr_hex) once
    cache = EnclaveAttestationCache()
    assert cache.admit(
        image_or_vm_id="vm-confidential-eu-01",
        tee_type="amd_sev_snp",
        hardware_supported=True,
        measured_pcr_hex=GOLDEN_PCR_HEX,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (True, "ATTESTED")

    # Ensure hot-path lookup does NOT re-invoke quote verification or network I/O
    def _forbid_reverification(*args, **kwargs):
        raise AssertionError("is_admitted() must not invoke verify_enclave_attestation() on dispatch path")

    monkeypatch.setattr(enclave_mod, "verify_enclave_attestation", _forbid_reverification)

    t0 = time.perf_counter()
    for _ in range(1000):
        assert cache.is_admitted("vm-confidential-eu-01", "amd_sev_snp", GOLDEN_PCR_HEX.upper()) is True
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 5.0  # O(1) set lookup => ~0.0 ms per dispatch

    assert cache.is_admitted("vm-confidential-eu-01", "intel_tdx", GOLDEN_PCR_HEX) is False
    assert cache.is_admitted("vm-unregistered", "amd_sev_snp", GOLDEN_PCR_HEX) is False


# Story 15.2 — AC-15.2.2 (ADR-016)
def test_ac_15_2_2_mismatched_empty_none_nonhex_or_unknown_tee_fails_closed():
    tampered_pcr = "f" * 64

    # Mismatched measurement
    assert verify_enclave_attestation(
        tee_type="vtpm2",
        hardware_supported=True,
        measured_pcr_hex=tampered_pcr,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (False, "ERR_PCR_ATTESTATION_FAILED")

    # None / empty / non-hex / unknown TEE type
    invalid_cases = [
        ("vtpm2", None, GOLDEN_PCR_HEX),
        ("amd_sev_snp", GOLDEN_PCR_HEX, None),
        ("intel_tdx", "", GOLDEN_PCR_HEX),
        ("intel_tdx", "   ", GOLDEN_PCR_HEX),
        ("vtpm2", GOLDEN_PCR_HEX, ""),
        ("amd_sev_snp", "not-valid-hex-zzzz", GOLDEN_PCR_HEX),
        ("intel_tdx", "0x" + GOLDEN_PCR_HEX, GOLDEN_PCR_HEX),
        ("sgx_unsupported_profile", GOLDEN_PCR_HEX, GOLDEN_PCR_HEX),
        ("", GOLDEN_PCR_HEX, GOLDEN_PCR_HEX),
    ]
    for tee_type, measured, expected in invalid_cases:
        assert verify_enclave_attestation(
            tee_type=tee_type,
            hardware_supported=True,
            measured_pcr_hex=measured,
            expected_pcr_hex=expected,  # type: ignore[arg-type]
        ) == (False, "ERR_PCR_ATTESTATION_FAILED")

    # Failed re-admission must evict stale cached entry and never admit compromised enclaves
    cache = EnclaveAttestationCache()
    assert cache.admit(
        image_or_vm_id="vm-confidential-eu-02",
        tee_type="vtpm2",
        hardware_supported=True,
        measured_pcr_hex=GOLDEN_PCR_HEX,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (True, "ATTESTED")
    assert cache.is_admitted("vm-confidential-eu-02", "vtpm2", GOLDEN_PCR_HEX) is True

    assert cache.admit(
        image_or_vm_id="vm-confidential-eu-02",
        tee_type="vtpm2",
        hardware_supported=True,
        measured_pcr_hex=tampered_pcr,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (False, "ERR_PCR_ATTESTATION_FAILED")
    assert cache.is_admitted("vm-confidential-eu-02", "vtpm2", GOLDEN_PCR_HEX) is False
    assert cache.is_admitted(None, "vtpm2", GOLDEN_PCR_HEX) is False  # type: ignore[arg-type]


# Story 15.2 — AC-15.2.3 (ADR-016)
def test_ac_15_2_3_unsupported_hardware_returns_err_tee_unsupported_without_faking():
    # Precedence: hardware_supported != True ALWAYS returns ERR_TEE_UNSUPPORTED
    for tee_type in ("vtpm2", "amd_sev_snp", "intel_tdx", "unknown"):
        assert verify_enclave_attestation(
            tee_type=tee_type,
            hardware_supported=False,
            measured_pcr_hex=GOLDEN_PCR_HEX,
            expected_pcr_hex=GOLDEN_PCR_HEX,
        ) == (False, "ERR_TEE_UNSUPPORTED")
        assert verify_enclave_attestation(
            tee_type=tee_type,
            hardware_supported=False,
            measured_pcr_hex=None,
            expected_pcr_hex=GOLDEN_PCR_HEX,
        ) == (False, "ERR_TEE_UNSUPPORTED")

    # Non-bool truthy value must not pass as hardware_supported=True
    assert verify_enclave_attestation(
        tee_type="amd_sev_snp",
        hardware_supported="yes",  # type: ignore[arg-type]
        measured_pcr_hex=GOLDEN_PCR_HEX,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (False, "ERR_TEE_UNSUPPORTED")

    cache = EnclaveAttestationCache()
    assert cache.admit(
        image_or_vm_id="vm-host-no-tee",
        tee_type="amd_sev_snp",
        hardware_supported=False,
        measured_pcr_hex=None,
        expected_pcr_hex=GOLDEN_PCR_HEX,
    ) == (False, "ERR_TEE_UNSUPPORTED")
    assert cache.is_admitted("vm-host-no-tee", "amd_sev_snp", GOLDEN_PCR_HEX) is False
