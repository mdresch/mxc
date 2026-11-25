"""Contract tests for Story 17.1 — 640 MB Paused Floor, CrossGen2 Alignment, Disposable Trim Bypass & Local NUMA Pinning (ADR-018).

Spec Gate Episode: spec-17_1-4b2efa1e (Robust Utility Margin: +0.2102)
Contract Interpretations:
  I1 (Explicit Numeric Precision & Bounds): Floating-point assertions use exact
      comparisons or pytest.approx(..., abs=1e-9) rather than math.isclose (IMP-024).
      effective_ram_mb is rounded to 2 decimal places: round(paused_ram_mb * (1.0 - shared_page_ratio), 2).
  I2 (Fail-Closed Validation): Non-None, non-bool finite numeric checks reject
      NaN/inf, paused_ram_mb <= 0.0 or > 640.0 (ERR_PAUSED_FLOOR_EXCEEDED),
      shared_page_ratio outside [0.0, 1.0], and remote_numa_pages != 0
      (ERR_NUMA_REMOTE_PAGES on > 0) with ValueError.
"""

from __future__ import annotations

import pytest

from scripts.lib.frontier_density_and_gpu import evaluate_density_and_numa


# Story 17.1 — AC-17.1.1 (ADR-018)
def test_ac_17_1_1_sub_350mb_effective_density_crossgen2_and_trim_bypass():
    result = evaluate_density_and_numa(
        paused_ram_mb=640.0,
        shared_page_ratio=0.65,
        remote_numa_pages=0,
        disposable_discard=True,
    )

    assert result["paused_ram_mb"] == 640.0
    assert result["shared_page_ratio"] == pytest.approx(0.65, abs=1e-9)
    assert result["effective_ram_mb"] == pytest.approx(224.0, abs=1e-9)
    assert result["effective_ram_mb"] < 350.0
    assert result["trim_bypass_ms_saved"] == 50.0
    assert result["crossgen2_compliant"] is True
    assert result["numa_local_pinned"] is True
    assert result["remote_numa_pages"] == 0


# Story 17.1 — AC-17.1.1 (ADR-018)
def test_ac_17_1_1_recycled_guest_disables_trim_bypass_and_tracks_crossgen2_threshold():
    recycled = evaluate_density_and_numa(
        paused_ram_mb=512,
        shared_page_ratio=0.50,
        remote_numa_pages=0,
        disposable_discard=False,
    )

    assert recycled["paused_ram_mb"] == 512.0
    assert recycled["effective_ram_mb"] == pytest.approx(256.0, abs=1e-9)
    assert recycled["trim_bypass_ms_saved"] == 0.0
    assert recycled["crossgen2_compliant"] is False
    assert recycled["numa_local_pinned"] is True
    assert recycled["remote_numa_pages"] == 0

    full_share = evaluate_density_and_numa(
        paused_ram_mb=600.0,
        shared_page_ratio=1.0,
        remote_numa_pages=0,
        disposable_discard=True,
    )
    assert full_share["effective_ram_mb"] == 0.0
    assert full_share["crossgen2_compliant"] is True


# Story 17.1 — AC-17.1.2 (ADR-018)
@pytest.mark.parametrize(
    "kwargs,expected_substr",
    [
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": 0.65,
                "remote_numa_pages": 1,
                "disposable_discard": True,
            },
            "ERR_NUMA_REMOTE_PAGES",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": 0.65,
                "remote_numa_pages": -1,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.1,
                "shared_page_ratio": 0.70,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "ERR_PAUSED_FLOOR_EXCEEDED",
        ),
        (
            {
                "paused_ram_mb": 0.0,
                "shared_page_ratio": 0.70,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": -100.0,
                "shared_page_ratio": 0.70,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": -0.01,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": 1.01,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": float("nan"),
                "shared_page_ratio": 0.65,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": float("inf"),
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": None,
                "shared_page_ratio": 0.65,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": True,
                "shared_page_ratio": 0.65,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": False,
                "remote_numa_pages": 0,
                "disposable_discard": True,
            },
            "",
        ),
        (
            {
                "paused_ram_mb": 640.0,
                "shared_page_ratio": 0.65,
                "remote_numa_pages": False,
                "disposable_discard": True,
            },
            "",
        ),
    ],
)
def test_ac_17_1_2_rejects_remote_numa_non_finite_and_out_of_range_inputs(kwargs, expected_substr):
    with pytest.raises(ValueError) as exc_info:
        evaluate_density_and_numa(**kwargs)
    if expected_substr:
        assert expected_substr in str(exc_info.value)
