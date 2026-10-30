"""Business Case Generator — drafts and revises formal BusinessCase documents."""

from __future__ import annotations

import json
import re
from typing import Protocol

from pmbok.exceptions import LLMParseError
from pmbok.llm.retry import call_with_retry
from pmbok.llm.validator import validate_llm_response
from pmbok.models.business_case import BusinessCase, CostItem
from pmbok.models.ideation import IdeationSummary


# ---------------------------------------------------------------------------
# Minimal protocol so the generator is not coupled to a concrete LLM client.
# ---------------------------------------------------------------------------

class AgentClient(Protocol):
    async def complete(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the raw response string."""
        ...


# ---------------------------------------------------------------------------
# Stub client used when no real LLM client is provided.
# ---------------------------------------------------------------------------

class _StubLLMClient:
    """Returns a hardcoded valid BusinessCase JSON for testing."""

    async def complete(self, prompt: str) -> str:  # noqa: ARG002
        return json.dumps(
            {
                "ideation_summary_id": "stub-summary-id",
                "executive_summary": "This project aims to deliver a robust solution.",
                "problem_statement": "The current process is inefficient and costly.",
                "proposed_solution": "Implement an automated system to streamline operations.",
                "expected_benefits": [
                    "Reduce operational costs by 20%",
                    "Improve throughput by 30%",
                ],
                "estimated_costs": [
                    {"label": "Development", "amount": 150000.0, "currency": "USD", "is_placeholder": False},
                    {"label": "Infrastructure", "amount": 50000.0, "currency": "USD", "is_placeholder": False},
                ],
                "key_risks": [
                    "Scope creep may delay delivery",
                    "Resource availability is uncertain",
                ],
                "recommendation": "Proceed with the project given the strong ROI.",
                "placeholders": [],
                "version_history": [],
            }
        )


# ---------------------------------------------------------------------------
# BusinessCaseGenerator
# ---------------------------------------------------------------------------

# Regex pattern to detect cost/budget figures in text.
_COST_PATTERN = re.compile(r"\$[\d,]+|\d+[kKmMbB]\b|\bbudget\b|\bcost\b|\bprice\b", re.IGNORECASE)


class BusinessCaseGenerator:
    """Drafts and revises formal BusinessCase documents from an IdeationSummary."""

    def __init__(
        self,
        llm_client: AgentClient | None = None,
        prompt_template: str = "",
    ) -> None:
        self._llm = llm_client if llm_client is not None else _StubLLMClient()
        self._prompt_template = prompt_template

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(self, summary: IdeationSummary) -> BusinessCase:
        """Draft a BusinessCase from the approved IdeationSummary."""
        placeholder_fields = self._identify_placeholders(summary)
        prompt = self._build_prompt(summary, placeholder_fields)
        raw_response = await call_with_retry(self._llm.complete, prompt)
        business_case = self._parse_llm_response(raw_response, location="generate")

        # Ensure placeholder fields are reflected in the returned BusinessCase.
        if placeholder_fields:
            # Inject placeholder CostItem if estimated_costs is missing/empty
            # and "estimated_costs" is in placeholder_fields.
            costs = list(business_case.estimated_costs)
            if "estimated_costs" in placeholder_fields and not any(
                c.is_placeholder for c in costs
            ):
                costs.insert(
                    0,
                    CostItem(
                        label="[PLACEHOLDER] Cost estimate",
                        amount=None,
                        is_placeholder=True,
                    ),
                )

            business_case = business_case.model_copy(
                update={
                    "ideation_summary_id": summary.id,
                    "estimated_costs": costs,
                    "placeholders": placeholder_fields,
                }
            )
        else:
            business_case = business_case.model_copy(
                update={"ideation_summary_id": summary.id}
            )

        return business_case

    async def revise(
        self,
        current: BusinessCase,
        revision_instructions: str,
    ) -> BusinessCase:
        """Produce a new BusinessCase version incorporating revision_instructions."""
        revision_prompt = self._build_revision_prompt(current, revision_instructions)
        raw_response = await call_with_retry(self._llm.complete, revision_prompt)
        new_case = self._parse_llm_response(raw_response, location="revise")

        new_history = [current] + list(current.version_history)
        new_case = new_case.model_copy(
            update={
                "ideation_summary_id": current.ideation_summary_id,
                "version": current.version + 1,
                "version_history": new_history,
            }
        )
        return new_case

    def _identify_placeholders(self, summary: IdeationSummary) -> list[str]:
        """Return list of field names that lack data and need placeholders."""
        placeholders: list[str] = []

        # Check if assumptions or constraints are empty — signals missing context.
        missing_context = not summary.assumptions or not summary.constraints

        # Check if the summary text mentions any cost/budget figures.
        combined_text = " ".join(
            [
                summary.problem_statement,
                summary.proposed_solution,
                *summary.key_goals,
                *summary.assumptions,
                *summary.constraints,
            ]
        )
        has_cost_info = bool(_COST_PATTERN.search(combined_text))

        if missing_context or not has_cost_info:
            placeholders.append("estimated_costs")

        if missing_context:
            placeholders.append("expected_benefits")

        return placeholders

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        summary: IdeationSummary,
        placeholder_fields: list[str],
    ) -> str:
        """Construct the LLM prompt from the IdeationSummary."""
        if self._prompt_template:
            base = self._prompt_template
        else:
            base = (
                "You are a business analyst. "
                "Draft a formal BusinessCase from the IdeationSummary below and return "
                "a JSON object that strictly matches the BusinessCase schema.\n\n"
                "Schema:\n"
                "{\n"
                '  "ideation_summary_id": "<string>",\n'
                '  "executive_summary": "<string>",\n'
                '  "problem_statement": "<string>",\n'
                '  "proposed_solution": "<string>",\n'
                '  "expected_benefits": ["<string>", ...],\n'
                '  "estimated_costs": [{"label": "<string>", "amount": <number|null>, '
                '"currency": "USD", "is_placeholder": <bool>}, ...],\n'
                '  "key_risks": ["<string>", ...],\n'
                '  "recommendation": "<string>",\n'
                '  "placeholders": ["<field_name>", ...],\n'
                '  "version_history": []\n'
                "}\n\n"
                "Return ONLY the JSON object — no markdown fences, no extra text.\n\n"
            )

        summary_json = summary.model_dump_json(indent=2)
        hint = ""
        if placeholder_fields:
            hint = (
                f"\nNote: The following fields lack sufficient data and should use "
                f"[PLACEHOLDER] labels: {placeholder_fields}. "
                "For estimated_costs, include at least one CostItem with "
                'label="[PLACEHOLDER] Cost estimate", amount=null, is_placeholder=true.\n'
            )

        return f"{base}IdeationSummary:\n{summary_json}\n{hint}"

    def _build_revision_prompt(
        self,
        current: BusinessCase,
        revision_instructions: str,
    ) -> str:
        """Build a prompt that asks the LLM to revise *current* per instructions."""
        current_json = current.model_dump_json(indent=2)
        return (
            "You are a business analyst. "
            "Revise the BusinessCase below according to the revision instructions "
            "and return a JSON object matching the same schema.\n\n"
            "Return ONLY the JSON object — no markdown fences, no extra text.\n\n"
            f"Current BusinessCase:\n{current_json}\n\n"
            f"Revision instructions:\n{revision_instructions}\n"
        )

    def _parse_llm_response(
        self,
        raw_response: str,
        location: str,
    ) -> BusinessCase:
        """Parse and quality-check *raw_response* into BusinessCase."""
        return validate_llm_response(
            raw_response,
            BusinessCase,
            location=location,
        )
