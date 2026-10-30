"""
LLM response quality validation layer.

Sits between the raw LLM string and Pydantic model_validate.
Handles four failure modes that Pydantic alone cannot catch:

  1. JSON buried in prose  — extract the first {...} or [...] block
  2. Structural invalidity — json.loads fails → LLMParseError
  3. Schema invalidity     — model_validate fails → LLMParseError
  4. Semantic emptiness    — valid JSON/schema but content is hollow → LLMQualityError

Usage (drop-in replacement for the inline parse blocks):

    from pmbok.llm.validator import validate_llm_response
    summary = validate_llm_response(raw, IdeationSummary, location="generate_summary")
"""

from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

from pydantic import BaseModel

from pmbok.exceptions import LLMParseError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Minimum non-whitespace characters a string field must contain to be
# considered non-empty.  Catches titles like "" or "N/A" or "...".
_MIN_STRING_LEN = 3


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validate_llm_response(
    raw: str,
    model_cls: type[T],
    *,
    location: str = "unknown",
    quality_checks: bool = True,
) -> T:
    """
    Parse *raw* into *model_cls* with structural + semantic validation.

    Steps:
      1. Strip markdown fences (redundant safety net alongside FoundryClient)
      2. Extract JSON from prose if the model added surrounding text
      3. json.loads  → LLMParseError on failure
      4. model_validate → LLMParseError on schema failure
      5. Semantic quality checks → LLMParseError on hollow content

    Args:
        raw:           Raw string returned by the LLM.
        model_cls:     Pydantic model class to validate into.
        location:      Human-readable call-site label for error messages.
        quality_checks: Set False to skip step 5 (useful in tests).

    Returns:
        A validated instance of *model_cls*.

    Raises:
        LLMParseError: On any structural or semantic failure.
    """
    snippet = raw[:500]

    # Step 1 — strip fences
    cleaned = _strip_fences(raw)

    # Step 2 — extract JSON from surrounding prose
    cleaned = _extract_json(cleaned, snippet, location)

    # Step 3 — parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMParseError(
            f"[{location}] JSON decode error after extraction: {exc}. "
            f"Raw (first 500 chars): {snippet!r}"
        ) from exc

    # Step 4 — Pydantic schema validation
    try:
        instance = model_cls.model_validate(data)
    except Exception as exc:
        raise LLMParseError(
            f"[{location}] {model_cls.__name__} schema failed validation: {exc}. "
            f"Raw (first 500 chars): {snippet!r}"
        ) from exc

    # Step 5 — semantic quality checks
    if quality_checks:
        issues = _check_quality(instance, model_cls.__name__)
        if issues:
            raise LLMParseError(
                f"[{location}] {model_cls.__name__} quality check failed — "
                f"{'; '.join(issues)}. Raw (first 500 chars): {snippet!r}"
            )

    return instance


# ---------------------------------------------------------------------------
# Step 1 — fence stripping
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    """Remove ```json / ``` wrappers."""
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1:] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return text.strip()


# ---------------------------------------------------------------------------
# Step 2 — JSON extraction from prose
# ---------------------------------------------------------------------------

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_JSON_ARRAY_RE  = re.compile(r"\[.*\]",  re.DOTALL)


def _extract_json(text: str, snippet: str, location: str) -> str:
    """
    If *text* is not directly parseable as JSON, try to extract the first
    JSON object or array embedded in it.  This handles models that prefix
    their response with "Here is the JSON:" or similar prose.
    """
    text = text.strip()
    # Fast path — already looks like JSON
    if (text.startswith("{") and text.endswith("}")) or \
       (text.startswith("[") and text.endswith("]")):
        return text

    # Try to find an embedded object first, then array
    for pattern in (_JSON_OBJECT_RE, _JSON_ARRAY_RE):
        match = pattern.search(text)
        if match:
            candidate = match.group(0)
            try:
                json.loads(candidate)   # validate it's actually parseable
                logger.warning(
                    "[%s] JSON was embedded in prose — extracted %d chars",
                    location, len(candidate),
                )
                return candidate
            except json.JSONDecodeError:
                continue

    # Nothing found — return as-is and let json.loads produce the error
    return text


# ---------------------------------------------------------------------------
# Step 5 — semantic quality checks
# ---------------------------------------------------------------------------

# Fields that must not be empty / too short, keyed by model class name.
# Each entry is (field_name, min_length, description).
_QUALITY_RULES: dict[str, list[tuple[str, int, str]]] = {
    "IdeationSummary": [
        ("title",              _MIN_STRING_LEN, "title is empty or too short"),
        ("problem_statement",  20,              "problem_statement is too short (< 20 chars)"),
        ("proposed_solution",  20,              "proposed_solution is too short (< 20 chars)"),
    ],
    "BusinessCase": [
        ("executive_summary",  20, "executive_summary is too short"),
        ("problem_statement",  20, "problem_statement is too short"),
        ("proposed_solution",  20, "proposed_solution is too short"),
        ("recommendation",     10, "recommendation is too short"),
    ],
}

# List fields that must be non-empty, keyed by model class name.
_REQUIRED_LISTS: dict[str, list[tuple[str, str]]] = {
    "IdeationSummary": [
        ("key_goals", "key_goals must have at least one item"),
    ],
    "BusinessCase": [
        ("expected_benefits", "expected_benefits must have at least one item"),
        ("key_risks",         "key_risks must have at least one item"),
        ("estimated_costs",   "estimated_costs must have at least one item"),
    ],
    "ProjectArtifact": [
        # content dict must not be empty
    ],
}

# For ProjectArtifact: content dict must not be empty
_ARTIFACT_MIN_CONTENT_KEYS = 1


def _check_quality(instance: BaseModel, class_name: str) -> list[str]:
    """Return a list of quality issue descriptions, empty if all pass."""
    issues: list[str] = []

    # String length checks
    for field, min_len, description in _QUALITY_RULES.get(class_name, []):
        value = getattr(instance, field, None)
        if not isinstance(value, str) or len(value.strip()) < min_len:
            issues.append(description)

    # Non-empty list checks
    for field, description in _REQUIRED_LISTS.get(class_name, []):
        value = getattr(instance, field, None)
        if not isinstance(value, list) or len(value) == 0:
            issues.append(description)

    # ProjectArtifact-specific: content must not be empty dict
    if class_name == "ProjectArtifact":
        content = getattr(instance, "content", {})
        if not isinstance(content, dict) or len(content) < _ARTIFACT_MIN_CONTENT_KEYS:
            issues.append("content dict is empty — artifact has no substance")

    return issues
