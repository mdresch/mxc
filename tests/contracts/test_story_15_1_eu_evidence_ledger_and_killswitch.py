"""Contract tests for Story 15.1 — Tamper-Evident EU Evidence Ledger, Entra Conditional Access & Hit-L Kill Switch (ADR-016).

Spec Gate Episode: spec-15_1-13a5d912 (Robust Utility Margin: +0.2153)
Contract Interpretations:
  I1 (Hash-Chained Retention & Tamper Detection): EvidenceLedger enforces retention_days >= 180
      (raising ValueError("ERR_RETENTION_BELOW_EU_FLOOR") on None, bool, or < 180), handles empty
      verify_chain() safely as (True, "OK"), and detects any single-field historical mutation across
      seq, timestamp_utc, event_type, session_id, payload_sha256, prev_hash, or entry_hash as
      (False, "ERR_LEDGER_CHAIN_BROKEN").
  I2 (Defensive None-Safety & Entra Conditional Access): evaluate_entra_conditional_access() guards
      None, non-dict, and empty dict postures without raising AttributeError, failing closed with
      (False, "ERR_CONDITIONAL_ACCESS_DENIED") when device_compliant is not True,
      agent_blueprint_verified is False, identity is missing, or risk_level is not in {"low", "none"}.
  I3 (Sub-250ms Hit-L Kill Switch): FreezeRollbackCircuitBreaker.freeze_and_rollback() validates
      inputs, transitions session state to "FROZEN_ROLLED_BACK" within <= 250 ms, appends a verified
      FREEZE_AND_ROLLBACK audit event to the ledger, and operates 100% offline.
"""

from __future__ import annotations

import hashlib
import json
import socket
import time

import pytest

from scripts.lib.eu_evidence_and_enclave import (
    EvidenceLedger,
    FreezeRollbackCircuitBreaker,
    LedgerEvent,
    evaluate_entra_conditional_access,
)


# Story 15.1 — AC-15.1.1 (ADR-016)
def test_ac_15_1_1_retention_floor_empty_chain_and_single_field_tamper_detection():
    # Retention floor >= 180 days (EU AI Act Art. 19 6-month minimum)
    default_ledger = EvidenceLedger()
    assert default_ledger.retention_days >= 180
    assert default_ledger.verify_chain() == (True, "OK")
    assert default_ledger.events == []

    custom_ledger = EvidenceLedger(retention_days=365)
    assert custom_ledger.retention_days == 365

    for invalid_retention in (179, 0, -30, None, True, False):
        with pytest.raises(ValueError, match="ERR_RETENTION_BELOW_EU_FLOOR"):
            EvidenceLedger(retention_days=invalid_retention)  # type: ignore[arg-type]

    # Append multiple events and verify deterministic hash-chain linkage
    p0 = {"route": "/agent/exec", "pool": "pool-win11-agent-lean"}
    p1 = {"entra_agent_id": "agent-eu-001", "decision": "OK"}
    p2 = {"vmbus_cmd": "git-bundle-apply", "bytes": 4096}

    e0 = default_ledger.append_event(
        event_type="DISPATCH",
        session_id="sess-eu-100",
        payload=p0,
        timestamp_utc="2026-11-25T00:10:00Z",
    )
    e1 = default_ledger.append_event(
        event_type="ENTRA_CA_CHECK",
        session_id="sess-eu-100",
        payload=p1,
        timestamp_utc="2026-11-25T00:10:01Z",
    )
    e2 = default_ledger.append_event(
        event_type="VMBUS_COMMAND",
        session_id="sess-eu-100",
        payload=p2,
        timestamp_utc="2026-11-25T00:10:02Z",
    )

    assert isinstance(e0, LedgerEvent)
    assert e0.seq == 0
    assert e0.prev_hash == "0" * 64
    assert e0.payload_sha256 == hashlib.sha256(
        json.dumps(p0, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert e1.seq == 1
    assert e1.prev_hash == e0.entry_hash
    assert e2.seq == 2
    assert e2.prev_hash == e1.entry_hash
    assert len(default_ledger.events) == 3
    assert default_ledger.verify_chain() == (True, "OK")

    # Mutating ANY single field of a historical LedgerEvent must fail closed with 100% detection
    mutations = {
        "seq": 99,
        "timestamp_utc": "2026-11-25T00:10:59Z",
        "event_type": "TAMPERED_EVENT",
        "session_id": "sess-rogue",
        "payload_sha256": "f" * 64,
        "prev_hash": "a" * 64,
        "entry_hash": "b" * 64,
    }
    original_e0 = default_ledger._events[0]
    for field_name, tampered_value in mutations.items():
        mutated_kwargs = {**original_e0.__dict__, field_name: tampered_value}
        default_ledger._events[0] = LedgerEvent(**mutated_kwargs)
        assert default_ledger.verify_chain() == (False, "ERR_LEDGER_CHAIN_BROKEN")
        default_ledger._events[0] = original_e0

    # Also verify middle-entry tamper detection and valid restoration
    assert default_ledger.verify_chain() == (True, "OK")
    original_e1 = default_ledger._events[1]
    default_ledger._events[1] = LedgerEvent(**{**original_e1.__dict__, "session_id": "sess-hijacked"})
    assert default_ledger.verify_chain() == (False, "ERR_LEDGER_CHAIN_BROKEN")
    default_ledger._events[1] = original_e1
    assert default_ledger.verify_chain() == (True, "OK")

    # Reject empty required strings or non-dict payloads on append_event
    with pytest.raises(ValueError):
        default_ledger.append_event(
            event_type="",
            session_id="sess-eu-100",
            payload={},
            timestamp_utc="2026-11-25T00:10:03Z",
        )
    with pytest.raises(ValueError):
        default_ledger.append_event(
            event_type="DISPATCH",
            session_id="sess-eu-100",
            payload="not-a-dict",  # type: ignore[arg-type]
            timestamp_utc="2026-11-25T00:10:03Z",
        )


# Story 15.1 — AC-15.1.2 (ADR-016)
def test_ac_15_1_2_entra_conditional_access_passes_compliant_and_fails_closed():
    # Compliant Entra Agent ID posture
    assert evaluate_entra_conditional_access(
        {
            "entra_agent_id": "entra-agent-blueprint-01",
            "device_compliant": True,
            "agent_blueprint_verified": True,
            "risk_level": "low",
            "approved_network": True,
        }
    ) == (True, "OK")

    # Compliant human/subject posture with risk_level="NONE" and optional blueprint field omitted
    assert evaluate_entra_conditional_access(
        {
            "subject_id": "compliance.lead@cba.eu",
            "device_compliant": True,
            "risk_level": "NONE",
        }
    ) == (True, "OK")

    # Fail-closed checks (including defensive None/empty/type guards)
    denied_postures = [
        None,
        {},
        "invalid-posture",
        {"entra_agent_id": "agent-1", "device_compliant": False, "risk_level": "low"},
        {"entra_agent_id": "agent-1", "device_compliant": None, "risk_level": "low"},
        {"entra_agent_id": "agent-1", "risk_level": "low"},  # missing device_compliant
        {
            "entra_agent_id": "agent-1",
            "device_compliant": True,
            "agent_blueprint_verified": False,
            "risk_level": "low",
        },
        {
            "entra_agent_id": "agent-1",
            "device_compliant": True,
            "agent_blueprint_verified": None,
            "risk_level": "low",
        },
        {"device_compliant": True, "risk_level": "low"},  # missing identity
        {"entra_agent_id": "   ", "subject_id": "", "device_compliant": True, "risk_level": "low"},
        {"entra_agent_id": "agent-1", "device_compliant": True, "risk_level": "medium"},
        {"entra_agent_id": "agent-1", "device_compliant": True, "risk_level": "high"},
        {"entra_agent_id": "agent-1", "device_compliant": True, "risk_level": ""},
        {"entra_agent_id": "agent-1", "device_compliant": True, "risk_level": None},
    ]
    for posture in denied_postures:
        assert evaluate_entra_conditional_access(posture) == (False, "ERR_CONDITIONAL_ACCESS_DENIED")  # type: ignore[arg-type]


# Story 15.1 — AC-15.1.3 (ADR-016)
def test_ac_15_1_3_freeze_and_rollback_sub_250ms_appends_verified_event_offline(monkeypatch):
    def _forbid_network(*args, **kwargs):
        raise AssertionError("Network access is strictly forbidden during offline ledger/kill-switch execution")

    monkeypatch.setattr(socket, "create_connection", _forbid_network)

    ledger = EvidenceLedger(retention_days=180)
    ledger.append_event(
        event_type="SESSION_START",
        session_id="sess-eu-kill-01",
        payload={"entra_agent_id": "agent-eu-09", "checkpoint": "baseline-hot-ready"},
        timestamp_utc="2026-11-25T00:20:00Z",
    )

    breaker = FreezeRollbackCircuitBreaker()
    t0 = time.perf_counter()
    result = breaker.freeze_and_rollback(
        session_id="sess-eu-kill-01",
        operator_id="dora-incident-lead@cba.eu",
        checkpoint_id="baseline-hot-ready",
        ledger=ledger,
        timestamp_utc="2026-11-25T00:20:05Z",
    )
    wall_ms = (time.perf_counter() - t0) * 1000.0

    assert wall_ms <= 250.0
    assert result["elapsed_ms"] <= 250.0
    assert result["session_id"] == "sess-eu-kill-01"
    assert result["state"] == "FROZEN_ROLLED_BACK"
    assert result["restored_checkpoint_id"] == "baseline-hot-ready"
    assert result["operator_id"] == "dora-incident-lead@cba.eu"

    assert len(ledger.events) == 2
    last_event = ledger.events[-1]
    assert last_event.event_type == "FREEZE_AND_ROLLBACK"
    assert last_event.session_id == "sess-eu-kill-01"
    assert result["ledger_entry_hash"] == last_event.entry_hash
    assert ledger.verify_chain() == (True, "OK")

    # Invalid arguments must raise ValueError cleanly
    with pytest.raises(ValueError):
        breaker.freeze_and_rollback(
            session_id="",
            operator_id="op-1",
            checkpoint_id="baseline-hot-ready",
            ledger=ledger,
        )
    with pytest.raises(ValueError):
        breaker.freeze_and_rollback(
            session_id="sess-1",
            operator_id="op-1",
            checkpoint_id="baseline-hot-ready",
            ledger="not-an-evidence-ledger",  # type: ignore[arg-type]
        )
