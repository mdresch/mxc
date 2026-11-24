"""
Business Case JSON Schema Definition

This module defines the expected JSON structure for business cases generated
by the PMBOK business case generator.
"""

import json
from typing import Dict, Any


def get_business_case_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for business cases.

    The schema defines the structure that LLMs should follow when generating
    business cases as JSON output. This ensures consistency and machine-readability
    while allowing flexible input processing from ideation summaries.

    Returns:
        Dict containing the JSON schema definition
    """
    return {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Unique identifier for the business case"
            },
            "ideation_summary_id": {
                "type": "string",
                "description": "ID of the ideation summary this business case is based on"
            },
            "version": {
                "type": "integer",
                "minimum": 1,
                "default": 1,
                "description": "Version number of the business case"
            },
            "executive_summary": {
                "type": "string",
                "description": "High-level summary of the business case"
            },
            "problem_statement": {
                "type": "string",
                "description": "Detailed problem statement"
            },
            "proposed_solution": {
                "type": "string",
                "description": "Description of the proposed solution"
            },
            "expected_benefits": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of expected benefits from implementing the solution"
            },
            "estimated_costs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "amount": {"type": ["number", "null"]},
                        "currency": {"type": "string", "default": "USD"},
                        "is_placeholder": {"type": "boolean", "default": False}
                    },
                    "required": ["label"]
                },
                "description": "List of estimated costs with details"
            },
            "key_risks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key risks associated with the project"
            },
            "recommendation": {
                "type": "string",
                "description": "Recommendation on whether to proceed with the project"
            },
            "placeholders": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of placeholder items that need further detail"
            },
            "version_history": {
                "type": "array",
                "items": {"$ref": "#"},
                "description": "History of previous versions (for revisions)"
            }
        },
        "required": [
            "ideation_summary_id",
            "executive_summary",
            "problem_statement",
            "proposed_solution",
            "expected_benefits",
            "estimated_costs",
            "key_risks",
            "recommendation"
        ]
    }


def get_business_case_schema_as_json_string(indent: int = 2) -> str:
    """
    Returns the business case schema as a formatted JSON string.

    Args:
        indent: Number of spaces for indentation

    Returns:
        JSON string representation of the schema
    """
    return json.dumps(get_business_case_schema(), indent=indent)


if __name__ == "__main__":
    # Example usage
    schema = get_business_case_schema()
    print("Business Case JSON Schema:")
    print(json.dumps(schema, indent=2))