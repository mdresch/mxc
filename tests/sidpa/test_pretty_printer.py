"""Tests for PrettyPrinter markdown serializer."""

from __future__ import annotations

from datetime import datetime

import pytest

from pmbok.models.business_case import BusinessCase, CostItem
from pmbok.models.enums import ApprovalStatus, KnowledgeArea, ProcessGroup, ProcessStatus
from pmbok.models.ideation import Conflict, IdeationSummary
from pmbok.models.pmbok import ProcessMap, ProcessState, ProjectArtifact
from pmbok.models.reporting import ProgressReport, StatusCounts
from pmbok.output.pretty_printer import PrettyPrinter


@pytest.fixture
def printer() -> PrettyPrinter:
    return PrettyPrinter()


@pytest.fixture
def ideation_summary() -> IdeationSummary:
    return IdeationSummary(
        session_id="sess-001",
        title="Smart Irrigation Controller",
        problem_statement="Farmers waste 40% of water due to manual irrigation.",
        proposed_solution="IoT sensor network with AI-driven scheduling.",
        key_goals=["Reduce water usage by 30%", "Automate scheduling"],
        assumptions=["Farmers have basic smartphone access"],
        constraints=["Budget under $500k"],
        conflicts=[
            Conflict(
                field="goals",
                source_a_id="src-1",
                value_a="Reduce water by 30%",
                source_b_id="src-2",
                value_b="Reduce water by 50%",
                resolved=False,
            )
        ],
    )


@pytest.fixture
def business_case() -> BusinessCase:
    return BusinessCase(
        ideation_summary_id="sum-001",
        executive_summary="This project will reduce water waste.",
        problem_statement="Manual irrigation wastes water.",
        proposed_solution="Deploy IoT sensors.",
        expected_benefits=["30% water reduction", "Cost savings"],
        estimated_costs=[
            CostItem(label="Hardware", amount=100000.0, currency="USD"),
            CostItem(label="Software", amount=None, currency="USD", is_placeholder=True),
        ],
        key_risks=["Adoption risk", "Technical risk"],
        recommendation="Proceed with pilot phase.",
    )


@pytest.fixture
def project_artifact() -> ProjectArtifact:
    return ProjectArtifact(
        run_id="run-001",
        process_id="4.1",
        artifact_type="Project Charter",
        version=1,
        content={"project_title": "Smart Irrigation", "sponsor": "[PLACEHOLDER]"},
        produced_by="4.1",
        created_at=datetime(2025, 1, 15, 11, 0, 0),
    )


@pytest.fixture
def process_map() -> ProcessMap:
    return ProcessMap(
        run_id="run-001",
        processes=[
            ProcessState(process_id="4.1", run_id="run-001", status=ProcessStatus.COMPLETE),
            ProcessState(process_id="13.1", run_id="run-001", status=ProcessStatus.IN_PROGRESS),
            ProcessState(process_id="4.2", run_id="run-001", status=ProcessStatus.NOT_STARTED),
        ],
    )


@pytest.fixture
def progress_report() -> ProgressReport:
    return ProgressReport(
        run_id="run-001",
        by_knowledge_area={
            KnowledgeArea.INTEGRATION: StatusCounts(not_started=1, in_progress=2, complete=3, blocked=0),
            KnowledgeArea.SCOPE: StatusCounts(not_started=2, in_progress=0, complete=1, blocked=1),
        },
        total=StatusCounts(not_started=3, in_progress=2, complete=4, blocked=1),
    )


# ── render_ideation_summary ────────────────────────────────────────────────

class TestRenderIdeationSummary:
    def test_returns_non_empty_string(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_title(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "Smart Irrigation Controller" in result

    def test_contains_problem_statement_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Problem Statement" in result

    def test_contains_proposed_solution_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Proposed Solution" in result

    def test_contains_key_goals_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Key Goals" in result

    def test_contains_assumptions_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Assumptions" in result

    def test_contains_constraints_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Constraints" in result

    def test_contains_conflicts_heading(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "## Conflicts" in result

    def test_contains_approval_status(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "pending" in result

    def test_contains_version(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "Version" in result

    def test_goals_rendered_as_list(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "- Reduce water usage by 30%" in result
        assert "- Automate scheduling" in result

    def test_conflict_data_present(self, printer, ideation_summary):
        result = printer.render_ideation_summary(ideation_summary)
        assert "src-1" in result
        assert "src-2" in result

    def test_no_conflicts_message(self, printer):
        summary = IdeationSummary(
            session_id="sess-002",
            title="Test",
            problem_statement="A problem.",
            proposed_solution="A solution.",
            key_goals=["Goal 1"],
        )
        result = printer.render_ideation_summary(summary)
        assert "No conflicts detected" in result


# ── render_business_case ──────────────────────────────────────────────────

class TestRenderBusinessCase:
    def test_returns_non_empty_string(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_executive_summary_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Executive Summary" in result

    def test_contains_problem_statement_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Problem Statement" in result

    def test_contains_proposed_solution_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Proposed Solution" in result

    def test_contains_expected_benefits_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Expected Benefits" in result

    def test_contains_estimated_costs_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Estimated Costs" in result

    def test_contains_key_risks_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Key Risks" in result

    def test_contains_recommendation_heading(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "## Recommendation" in result

    def test_costs_table_has_correct_columns(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "| Label | Amount | Currency | Placeholder |" in result

    def test_costs_table_contains_items(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "Hardware" in result
        assert "Software" in result

    def test_placeholder_cost_marked(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "Yes" in result  # is_placeholder=True for Software

    def test_benefits_rendered_as_list(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "- 30% water reduction" in result

    def test_risks_rendered_as_list(self, printer, business_case):
        result = printer.render_business_case(business_case)
        assert "- Adoption risk" in result


# ── render_project_artifact ───────────────────────────────────────────────

class TestRenderProjectArtifact:
    def test_returns_non_empty_string(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_artifact_type(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "Project Charter" in result

    def test_contains_process_id(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "4.1" in result

    def test_contains_version(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "Version" in result

    def test_contains_content_heading(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "## Content" in result

    def test_content_rendered_as_json_block(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "```json" in result
        assert "Smart Irrigation" in result

    def test_contains_created_at(self, printer, project_artifact):
        result = printer.render_project_artifact(project_artifact)
        assert "2025-01-15" in result


# ── render_process_map ────────────────────────────────────────────────────

class TestRenderProcessMap:
    def test_returns_non_empty_string(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_processes_heading(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "## Processes" in result

    def test_table_has_correct_columns(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "| Process ID | Name | Knowledge Area | Process Group | Status |" in result

    def test_process_ids_present(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "4.1" in result
        assert "13.1" in result
        assert "4.2" in result

    def test_process_names_resolved(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "Develop Project Charter" in result
        assert "Identify Stakeholders" in result

    def test_knowledge_areas_present(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "Integration" in result
        assert "Stakeholder" in result

    def test_statuses_present(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "complete" in result
        assert "in_progress" in result
        assert "not_started" in result

    def test_summary_count_present(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "Total" in result
        assert "3" in result  # 3 processes total

    def test_run_id_present(self, printer, process_map):
        result = printer.render_process_map(process_map)
        assert "run-001" in result


# ── render_progress_report ────────────────────────────────────────────────

class TestRenderProgressReport:
    def test_returns_non_empty_string(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_status_heading(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert "## Status by Knowledge Area" in result

    def test_table_has_correct_columns(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert "| Knowledge Area | Not Started | In Progress | Complete | Blocked |" in result

    def test_knowledge_areas_present(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert "Integration" in result
        assert "Scope" in result

    def test_counts_present(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        # Integration: not_started=1, in_progress=2, complete=3, blocked=0
        assert "| Integration | 1 | 2 | 3 | 0 |" in result

    def test_totals_row_present(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert "Total" in result
        # total: not_started=3, in_progress=2, complete=4, blocked=1
        assert "3" in result
        assert "4" in result

    def test_run_id_present(self, printer, progress_report):
        result = printer.render_progress_report(progress_report)
        assert "run-001" in result


# ── _section helper ───────────────────────────────────────────────────────

class TestSectionHelper:
    def test_default_level_2(self, printer):
        result = printer._section("My Title", "Some content")
        assert result == "## My Title\n\nSome content\n\n"

    def test_custom_level(self, printer):
        result = printer._section("Sub", "body", level=3)
        assert result == "### Sub\n\nbody\n\n"
