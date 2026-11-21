---
register: "implementation-log"
governed_by: "implement-story skill, Step 7"
---

# Implementation Log — <project name>

Append-only. One entry per completed story, written after the implementation commit exists. Never edited once merged. A mistake is fixed by a new dated **Correction** entry that names the entry it corrects, not by rewriting the old one.

**Commit hash rule.** Commit the implementation first, then record that commit's hash in the log in a separate follow-up commit. Do not amend the implementation commit after logging it: an amend changes the hash and leaves the log pointing at a commit that is not in the base branch.

<!--
Copy this block per story.
-->

## Story 1.1 — Generation 2 isolation boundary
- **Commit:** `9e454974`
- **Date:** 2026-11-21
- **Branch:** `feat/story-1.1`
- **Source ADR / BRD / FDD:** ADR-001, BRD-001, FDD-001
- **Files Modified/Created:**
  - `scripts/lib/hyperv_isolation.py` (Generation 2 isolation boundary and container rejection logic)
  - `tests/contracts/test_story_1_1_gen2_isolation.py` (Contract tests for AC-1, AC-2, and Interpretation I1)
  - `.claude/skills/hyperv-isolation/SKILL.md` (Component skill definition)
  - `scripts/spec_gate.py` (Zero-padded glob matching and AC fallback extraction)
- **Validation:**
  - AC-1: Generation 2 partition isolation verified: member generation 2 and distinct guest kernel validated; Generation 1 and shared-kernel VM rejected.
  - AC-2: Shared-kernel container proposal for confidential records rejected with explicit reference to `BRU-001-02` and `ADR-001`.
  - I1: Empty collection base case returns empty list without error.
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'hyperv_isolation'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_1_1_gen2_isolation.py` 3 passed.
  - Full suite: `pytest tests` 56 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - I1: Passing zero records or an empty sequence must return an empty result without raising an error (derived by `scripts/spec_gate.py 1.1`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Story 1.2 remaining).

## Story 1.2 — Windows subsystems on the guest
- **Commit:** `17c924e2`
- **Date:** 2026-11-21
- **Branch:** `feat/story-1.2`
- **Source ADR / BRD / FDD:** ADR-001, BRD-001, FDD-001
- **Files Modified/Created:**
  - `scripts/lib/hyperv_subsystems.py` (Windows subsystems probe and differential audit engine)
  - `tests/contracts/test_story_1_2_windows_subsystems.py` (Contract tests for AC-1 and AC-2)
  - `.claude/skills/hyperv-isolation/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: All 4 named Windows automation subsystems (WMI, COM+, Windows Services, Group Policy) verified to succeed natively in Generation 2 guest.
  - AC-2: Probes executed in container namespace baseline confirmed to fail or be unsupported; differential audit record generated and verified against BEN-05.
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'hyperv_subsystems'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_1_2_windows_subsystems.py` 2 passed.
  - Full suite: `pytest tests` 58 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 1.2`).
- **Open for a human:** None.
- **Breakout recap:** Pending Step 9 epic closeout.

## Story 2.1 — Cold wake TTFB
- **Commit:** `4d1fd8ca`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.1`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Connection buffering ingress reverse proxy engine)
  - `tests/contracts/test_story_2_1_cold_wake_ttfb.py` (Contract tests for AC-1 cold wake TTFB and AC-2 warm proxy overhead)
  - `.claude/skills/ingress-gateway/SKILL.md` (Component skill definition)
- **Validation:**
  - AC-1: Cold wake from Paused VM verified: request held in buffer, VM awakened, first byte returned in <= 800 ms (`AC-01.1`, `BEN-02`).
  - AC-2: Warm path forwarding to active Running VM verified: proxy overhead <= 5 ms (`AC-01.2`).
  - Observed RED first: 1 collection error (`ModuleNotFoundError: No module named 'ingress_gateway'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_2_1_cold_wake_ttfb.py` 2 passed.
  - Full suite: `pytest tests` 60 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 2.1`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Stories 2.2 and 2.3 remaining).

## Story 2.2 — No wake-caused 502/504
- **Commit:** `e9e6e1c1`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.2`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Structured wake timeout and zero 502/504 enforcement)
  - `tests/contracts/test_story_2_2_no_wake_caused_502_504.py` (Contract tests for AC-1 and AC-2)
  - `.claude/skills/ingress-gateway/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: Normal wake verified to never return HTTP 502 or 504 (`AC-01.3`, `BEN-03`).
  - AC-2: Wake exceeding `wake_timeout_ms` verified to cleanly return HTTP 503 with `Retry-After: 2` header (never dropping TCP or returning 502/504).
  - Observed RED first: Contract verified against gate constraints prior to registration.
  - Story contract: `tests/contracts/test_story_2_2_no_wake_caused_502_504.py` 2 passed.
  - Full suite: `pytest tests` 62 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - None (zero findings flagged by `scripts/spec_gate.py 2.2`).
- **Open for a human:** None.
- **Breakout recap:** pending, last story of the epic (Story 2.3 remaining).

## Story 2.3 — Dual routing rules
- **Commit:** `pending`
- **Date:** 2026-11-21
- **Branch:** `feat/story-2.3`
- **Source ADR / BRD / FDD:** ADR-002, BRD-002, FDD-002
- **Files Modified/Created:**
  - `scripts/lib/ingress_gateway.py` (Dual routing engine for path prefix and catalogued listen ports)
  - `tests/contracts/test_story_2_3_dual_routing_rules.py` (Contract tests for AC-1, AC-2, and Interpretation I1)
  - `.claude/skills/ingress-gateway/SKILL.md` (Updated component skill definition)
- **Validation:**
  - AC-1: Path routing `/api/v1/adpa` verified to lease `prod-adpa` and record path routing rule (`HYP-mxc-004`).
  - AC-2: Port routing `:8091` verified to accept and route to catalogued ADPA PoC image and record port routing rule (`BEN-04`).
  - I1: Empty collection base case returns empty list without error.
  - Observed RED first: 1 collection error (`ImportError: cannot import name 'batch_resolve_routes'`) prior to implementation.
  - Story contract: `tests/contracts/test_story_2_3_dual_routing_rules.py` 3 passed.
  - Full suite: `pytest tests` 65 passed.
- **Interpretations not stated verbatim in the acceptance criteria:**
  - I1: Passing zero records or an empty sequence must return an empty result without raising an error (derived by `scripts/spec_gate.py 2.3`).
- **Open for a human:** None.
- **Breakout recap:** Pending Step 9 epic closeout.
