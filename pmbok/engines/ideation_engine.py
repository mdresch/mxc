"""Ideation Engine — consolidates ParsedInputs into a structured IdeationSummary."""

from __future__ import annotations

import json
from itertools import combinations
from typing import Any, Protocol

from pmbok.exceptions import LLMParseError
from pmbok.llm.retry import call_with_retry
from pmbok.llm.validator import validate_llm_response
from pmbok.schemas import get_ideation_summary_schema_as_json_string
from pmbok.models.ideation import IdeationSummary, Conflict
from pmbok.models.inputs import ParsedInput

# Pairs with Jaccard similarity below this threshold are flagged as conflicts.
CONFLICT_THRESHOLD = 0.6

# Fields in the LLM output dict that are checked for cross-input conflicts.
_CONFLICT_FIELDS = ("key_goals", "assumptions", "constraints")


# ---------------------------------------------------------------------------
# Minimal protocol so the engine is not coupled to a concrete LLM client.
# ---------------------------------------------------------------------------

class AgentClient(Protocol):
    async def complete(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the raw response string."""
        ...


# ---------------------------------------------------------------------------
# Stub client used when no real LLM client is provided.
# ---------------------------------------------------------------------------

class _StubLLMClient:
    """Returns a hardcoded valid IdeationSummary JSON for testing."""

    async def complete(self, prompt: str) -> str:  # noqa: ARG002
        return json.dumps(
            {
                "session_id": "stub-session",
                "title": "Stub Project",
                "problem_statement": "A stub problem statement.",
                "proposed_solution": "A stub proposed solution.",
                "key_goals": ["Deliver on time"],
                "assumptions": ["Budget is available"],
                "constraints": ["6-month timeline"],
                "conflicts": [],
                "version_history": [],
            }
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jaccard(a: str, b: str) -> float:
    """Return Jaccard similarity (word-overlap) between two strings."""
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# IdeationEngine
# ---------------------------------------------------------------------------

class IdeationEngine:
    """Consolidates a list of ParsedInputs into a single IdeationSummary."""

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

    async def generate_summary(
        self,
        inputs: list[ParsedInput],
        session_id: str = "",
    ) -> IdeationSummary:
        """Consolidate *inputs* into a structured IdeationSummary.

        Steps:
        1. Build a structured prompt from all inputs.
        2. Call the LLM.
        3. Parse the JSON response into IdeationSummary.
        4. Detect conflicts and attach them.
        """
        prompt = self._build_prompt(inputs)
        raw_response = await call_with_retry(self._llm.complete, prompt)

        summary = self._parse_llm_response(raw_response, location="generate_summary")

        # Resolve session_id: prefer explicit arg, then first input id, then stub value.
        if not session_id:
            session_id = inputs[0].id if inputs else summary.session_id

        # Overwrite session_id with the resolved value.
        summary = summary.model_copy(update={"session_id": session_id})

        # Detect conflicts from the raw LLM output dict and attach.
        try:
            raw_dict = json.loads(raw_response)
        except json.JSONDecodeError:
            raw_dict = {}

        conflicts = self._detect_conflicts(raw_dict)
        summary = summary.model_copy(update={"conflicts": conflicts})

        return summary

    async def revise_summary(
        self,
        current: IdeationSummary,
        revision_instructions: str,
    ) -> IdeationSummary:
        """Incorporate *revision_instructions*; preserve *current* in version_history."""
        revision_prompt = self._build_revision_prompt(current, revision_instructions)
        raw_response = await call_with_retry(self._llm.complete, revision_prompt)

        new_summary = self._parse_llm_response(raw_response, location="revise_summary")

        # Prepend current to version_history and increment version.
        new_history = [current] + list(current.version_history)
        new_summary = new_summary.model_copy(
            update={
                "session_id": current.session_id,
                "version": current.version + 1,
                "version_history": new_history,
            }
        )

        # Re-run conflict detection on the revised output.
        try:
            raw_dict = json.loads(raw_response)
        except json.JSONDecodeError:
            raw_dict = {}

        conflicts = self._detect_conflicts(raw_dict)
        new_summary = new_summary.model_copy(update={"conflicts": conflicts})

        return new_summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, inputs: list[ParsedInput]) -> str:
        """Construct the LLM prompt from *inputs*."""
        if self._prompt_template:
            base = self._prompt_template
        else:
            schema_json = get_ideation_summary_schema_as_json_string()
            base = (
                "You are a project ideation assistant. "
                "Analyse the following inputs and return a JSON object that "
                "strictly matches the IdeationSummary schema below.\n\n"
                f"Schema:\n{schema_json}\n\n"
                "Return ONLY the JSON object — no markdown fences, no extra text.\n\n"
            )

        sections: list[str] = []
        for i, inp in enumerate(inputs, start=1):
            parts = [f"--- Input {i} (id={inp.id}, type={inp.source_type}) ---"]
            parts.append(inp.extracted_text)
            if inp.diagram_description:
                parts.append(f"[Diagram description: {inp.diagram_description}]")
            sections.append("\n".join(parts))

        return base + "\n\n".join(sections)

    def _build_revision_prompt(
        self,
        current: IdeationSummary,
        revision_instructions: str,
    ) -> str:
        """Build a prompt that asks the LLM to revise *current* per instructions."""
        current_json = current.model_dump_json(indent=2)
        return (
            "You are a project ideation assistant. "
            "Revise the IdeationSummary below according to the revision instructions "
            "and return a JSON object matching the same schema.\n\n"
            "Return ONLY the JSON object — no markdown fences, no extra text.\n\n"
            f"Current IdeationSummary:\n{current_json}\n\n"
            f"Revision instructions:\n{revision_instructions}\n"
        )

    def _detect_conflicts(self, raw_llm_output: dict[str, Any]) -> list[Conflict]:
        """Detect conflicts across goals, assumptions, and constraints.

        For each field, compute pairwise Jaccard similarity between items.
        Pairs with similarity < CONFLICT_THRESHOLD produce a Conflict record.
        """
        conflicts: list[Conflict] = []

        for field in _CONFLICT_FIELDS:
            items: list[str] = raw_llm_output.get(field, [])
            if not isinstance(items, list):
                continue

            # Compare every pair of items within the same field.
            for (idx_a, val_a), (idx_b, val_b) in combinations(
                enumerate(items), 2
            ):
                if not isinstance(val_a, str) or not isinstance(val_b, str):
                    continue
                similarity = _jaccard(val_a, val_b)
                if similarity < CONFLICT_THRESHOLD:
                    conflicts.append(
                        Conflict(
                            field=field,
                            source_a_id=str(idx_a),
                            value_a=val_a,
                            source_b_id=str(idx_b),
                            value_b=val_b,
                            resolved=False,
                        )
                    )

        return conflicts

    def _parse_llm_response(
        self,
        raw_response: str,
        location: str,
    ) -> IdeationSummary:
        """Parse and quality-check *raw_response* into IdeationSummary."""
        return validate_llm_response(
            raw_response,
            IdeationSummary,
            location=location,
        )
