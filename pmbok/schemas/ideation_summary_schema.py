"""
Ideation Summary JSON Schema Definition

This module defines the expected JSON structure for ideation summaries generated
by the PMBOK ideation engine.
"""

import json
from typing import Dict, Any


def get_ideation_summary_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for ideation summaries.

    The schema defines the structure that LLMs should follow when generating
    ideation summaries as JSON output. This ensures consistency and machine-readability
    while allowing flexible input processing.

    Returns:
        Dict containing the JSON schema definition
    """
    return {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Unique identifier for the ideation session"
            },
            "title": {
                "type": "string",
                "description": "Project title derived from inputs"
            },
            "problem_statement": {
                "type": "string",
                "description": "Consolidated problem statement from all inputs"
            },
            "proposed_solution": {
                "type": "string",
                "description": "Proposed solution approach"
            },
            "key_goals": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "List of key project goals (at least one required)"
            },
            "assumptions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of project assumptions"
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of project constraints"
            },
            "conflicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "source_a_id": {"type": "string"},
                        "value_a": {"type": "string"},
                        "source_b_id": {"type": "string"},
                        "value_b": {"type": "string"},
                        "resolved": {"type": "boolean"},
                        "resolution": {"type": ["string", "null"]}
                    },
                    "required": ["field", "source_a_id", "value_a", "source_b_id", "value_b"]
                },
                "description": "List of detected conflicts between inputs"
            },
            "version_history": {
                "type": "array",
                "items": {"$ref": "#"},
                "description": "History of previous versions (for revisions)"
            }
        },
        "required": ["session_id", "title", "problem_statement", "proposed_solution", "key_goals"]
    }


def get_ideation_summary_schema_as_json_string(indent: int = 2) -> str:
    """
    Returns the ideation summary schema as a formatted JSON string.

    Args:
        indent: Number of spaces for indentation

    Returns:
        JSON string representation of the schema
    """
    return json.dumps(get_ideation_summary_schema(), indent=indent)


if __name__ == "__main__":
    # Example usage
    schema = get_ideation_summary_schema()
    print("Ideation Summary JSON Schema:")
    print(json.dumps(schema, indent=2))