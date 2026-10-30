"""
Project Charter JSON Schema Definition

This module defines the expected JSON structure for project charters generated
by the PMBOK lifecycle orchestration.
"""

import json
from typing import Dict, Any


def get_project_charter_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for project charters.

    The schema defines the structure that LLMs should follow when generating
    project charters as JSON output. This ensures consistency and machine-readability.

    Returns:
        Dict containing the JSON schema definition
    """
    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The project title"
            },
            "objectives": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of project objectives"
            },
            "stakeholders": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "responsibilities": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["name", "role"]
                },
                "description": "List of key stakeholders with their roles and responsibilities"
            },
            "requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "High-level requirements"
            },
            "deliverables": {
                "type": "array",
                "items": {"type": "string"},
                "description": "High-level deliverables"
            },
            "success_criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Success criteria and metrics"
            },
            "assumptions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Project assumptions"
            },
            "constraints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Project constraints"
            },
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "mitigation": {"type": "string"}
                    },
                    "required": ["description"]
                },
                "description": "High-level risks and mitigation strategies"
            },
            "timeline": {
                "type": "object",
                "properties": {
                    "milestones": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "date": {"type": "string"}
                            },
                            "required": ["name"]
                        }
                    }
                },
                "description": "Timeline with milestones"
            },
            "budget": {
                "type": "object",
                "properties": {
                    "total": {"type": "number"},
                    "breakdown": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "description": "Budget and resource requirements"
            },
            "resources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Resource requirements"
            }
        },
        "required": ["title", "objectives"]
    }


def get_project_charter_schema_as_json_string(indent: int = 2) -> str:
    """
    Returns the project charter schema as a formatted JSON string.

    Args:
        indent: Number of spaces for indentation

    Returns:
        JSON string representation of the schema
    """
    return json.dumps(get_project_charter_schema(), indent=indent)


if __name__ == "__main__":
    # Example usage
    schema = get_project_charter_schema()
    print("Project Charter JSON Schema:")
    print(json.dumps(schema, indent=2))