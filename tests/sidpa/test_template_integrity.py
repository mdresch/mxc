"""
Template integrity and lifecycle sequence tests for SIDPA template.

Enforces:
1. Stage 6: Requirements (ADRs, BRDs, FDDs, User Stories)
2. Stage 7: Integrated PMP & 9 Subsidiary Management Plans (PMP-BL-v1.0.0, Foundation Packs 7.A-7.D)
3. Stage 8: Implementation Readiness Gate & Implementation Authorization Notice
4. Valid JSON structure across all policy declarations and decision frames
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

NINE_PLANS = [
    "Scope-Management-Plan.md",
    "Schedule-Management-Plan.md",
    "Cost-Management-Plan.md",
    "Resource-Management-Plan.md",
    "Quality-Management-Plan.md",
    "Communications-Management-Plan.md",
    "Risk-Management-Plan.md",
    "Procurement-Management-Plan.md",
    "Stakeholder-Engagement-Plan.md",
]


def test_nine_subsidiary_plans_are_generated_not_shipped() -> None:
    """The 9 subsidiary plans are Stage 7 outputs of orchestrate_pmbok.py --mode full
    against a real project's own Charter -- they must never ship pre-filled in the
    template itself (that was a real regression: self-hosted "SIDPA Project" plans
    leaking into every project scaffolded from this template)."""
    plans_dir = REPO_ROOT / "docs" / "project-docs" / "management-plans"
    for plan_name in NINE_PLANS:
        plan_path = plans_dir / plan_name
        assert not plan_path.exists(), (
            f"{plan_name} must not be pre-shipped in the template -- it is a generated "
            "Stage 7 output. Delete it and let orchestrate_pmbok.py produce it per project."
        )

    orchestrator_src = (REPO_ROOT / "scripts" / "orchestrate_pmbok.py").read_text(encoding="utf-8")
    for plan_name in NINE_PLANS:
        plan_stem = plan_name.removesuffix(".md")
        assert plan_stem in orchestrator_src, (
            f"orchestrate_pmbok.py no longer appears to generate {plan_name}"
        )


def test_project_management_plan_template_has_stage_7_frontmatter() -> None:
    template_path = REPO_ROOT / "docs" / "project-docs" / "Project-Management-Plan.template.md"
    assert template_path.is_file(), "Missing Project-Management-Plan.template.md"
    content = template_path.read_text(encoding="utf-8")
    assert 'lifecycle_stage: "Stage 7 (Planning: Integrated PMP & Baselines)"' in content
    assert 'pmbok_process: "4.2 Develop Project Management Plan"' in content

    active_path = REPO_ROOT / "docs" / "project-docs" / "Project-Management-Plan.md"
    assert not active_path.exists(), (
        "Project-Management-Plan.md must not be pre-shipped in the template -- it is a "
        "generated Stage 7 output, approved per project, not template content."
    )


def test_requirements_templates_have_stage_6_frontmatter() -> None:
    req_templates = [
        (REPO_ROOT / "docs" / "07-architecture" / "ADR-TEMPLATE.md", "Stage 6 (Requirement: Architecture)"),
        (REPO_ROOT / "docs" / "project-docs" / "Business-Requirements" / "BRD-TEMPLATE.md", "Stage 6 (Requirement: Business)"),
        (REPO_ROOT / "docs" / "project-docs" / "Functional-Design" / "FDD-TEMPLATE.md", "Stage 6 (Requirement: Solution)"),
        (REPO_ROOT / "docs" / "user-stories" / "EPIC-TEMPLATE.md", "Stage 6 (Requirement: Story)"),
    ]
    for path, expected_stage in req_templates:
        assert path.is_file(), f"Missing {path}"
        content = path.read_text(encoding="utf-8")
        assert f'lifecycle_stage: "{expected_stage}"' in content, (
            f"{path.name} does not declare {expected_stage}"
        )


def test_stage_8_authorization_notice_template_exists_but_not_pre_authorized() -> None:
    reports_dir = REPO_ROOT / "docs" / "project-docs" / "Status-Reports"
    assert reports_dir.is_dir()

    template_notice = reports_dir / "Stage-8-Implementation-Authorization-Notice.template.md"
    active_notice = reports_dir / "Stage-8-Implementation-Authorization-Notice.md"

    assert template_notice.is_file(), "Missing Stage 8 notice template"
    content = template_notice.read_text(encoding="utf-8")
    assert 'artifact_type: "execution_authorization_notice"' in content
    assert "Stage 8 (Implementation Readiness Gate" in content
    assert "AUTHORIZED_TO_EXECUTE" in content

    # The active notice certifies that a real project has actually completed every
    # upstream gate and been authorized to execute. The template itself has not --
    # shipping this pre-filled was a real regression (a false execution-authorization
    # claim for whatever project got scaffolded from this template).
    assert not active_notice.exists(), (
        "Stage-8-Implementation-Authorization-Notice.md must not be pre-shipped in the "
        "template -- it asserts real execution authorization that only a real project's "
        "own Stage 8 gate can grant."
    )


def test_foundation_packs_have_stage_7_manifests() -> None:
    pack_checks = [
        ("scope-baseline", "Scope-Foundation-Pack-Manifest.template.md", "Stage 7.A"),
        ("schedule-baseline", "Schedule-Foundation-Pack-Manifest.template.md", "Stage 7.B"),
        ("resource-baseline", "Resource-Foundation-Pack-Manifest.template.md", "Stage 7.C"),
        ("cost-baseline", "Cost-Foundation-Pack-Manifest.template.md", "Stage 7.D"),
    ]
    for pack_dir, manifest_name, expected_stage in pack_checks:
        path = REPO_ROOT / "templates" / "management-plans" / pack_dir / manifest_name
        assert path.is_file(), f"Missing {path}"
        content = path.read_text(encoding="utf-8")
        assert f"## {expected_stage} process" in content, (
            f"{manifest_name} does not reference {expected_stage}"
        )


def test_continuous_improvement_register_not_pre_shipped() -> None:
    template_path = REPO_ROOT / "docs" / "registers" / "Continuous-Improvement-Register.template.md"
    active_path = REPO_ROOT / "docs" / "registers" / "Continuous-Improvement-Register.md"
    assert template_path.is_file(), "Missing Continuous-Improvement-Register.template.md"
    assert not active_path.exists(), (
        "Continuous-Improvement-Register.md must not be pre-shipped in the template -- "
        "a real project's register starts empty and is populated per Epic, not seeded "
        "with another project's worked example rows."
    )


def test_policy_shapes_contain_no_project_specific_identifiers() -> None:
    """Regression guard: decision-frames/episodes shipped in the template must be
    either generic (no real project name/codebase baked in) or explicitly marked
    illustrative_example. Real project governance history does not belong here."""
    policy_dir = REPO_ROOT / "docs" / "policy-shapes"
    banned_substrings = ["enterprise-work-hierarchy", "EWH-", "Menno Drescher", "wiki/Projects/"]
    for jf in policy_dir.rglob("*.json"):
        content = jf.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, dict) and data.get("illustrative_example"):
            continue
        for banned in banned_substrings:
            assert banned not in content, f"{jf.relative_to(REPO_ROOT)} contains project-specific identifier {banned!r}"


def test_policy_shapes_and_frames_are_valid_json() -> None:
    policy_dir = REPO_ROOT / "docs" / "policy-shapes"
    assert policy_dir.is_dir()
    json_files = list(policy_dir.rglob("*.json"))
    assert len(json_files) >= 10, "Found fewer policy JSON files than expected"
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            assert isinstance(data, (dict, list)), f"{jf.name} did not load as dict or list"
        except Exception as e:
            pytest.fail(f"Invalid JSON in {jf}: {e}")
