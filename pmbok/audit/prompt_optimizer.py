"""
Prompt Optimization Engine

Analyzes quality control findings and generates optimized prompts to improve LLM output quality.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict

from pmbok.audit.quality_control import QualityControlResult


@dataclass
class PromptOptimization:
    """Optimization recommendations for a prompt."""
    original_prompt: str
    optimized_prompt: str
    improvements: List[str]
    expected_quality_improvement: float  # 0.0 to 1.0
    optimization_reason: str


class PromptOptimizer:
    """
    Analyzes quality control results and generates optimized prompts.
    """

    def __init__(self):
        self.issue_patterns = {
            "low_relevance": self._optimize_for_relevance,
            "hallucination": self._optimize_for_hallucination,
            "title_mismatch": self._optimize_for_title,
            "generic_content": self._optimize_for_specificity
        }

    def generate_optimized_prompt(
        self,
        original_prompt: str,
        qc_result: QualityControlResult,
        project_context: Dict[str, Any]
    ) -> PromptOptimization:
        """
        Generate an optimized prompt based on quality control findings.
        """
        issues = qc_result.issues
        audit_details = qc_result.audit_details

        # Identify primary issues
        primary_issues = self._identify_primary_issues(issues, audit_details)

        # Start with original prompt
        optimized_prompt = original_prompt
        improvements = []
        total_improvement = 0.0

        # Apply optimizations for each issue
        for issue_type in primary_issues:
            if issue_type in self.issue_patterns:
                optimization = self.issue_patterns[issue_type](
                    optimized_prompt, audit_details, project_context
                )
                optimized_prompt = optimization["prompt"]
                improvements.extend(optimization["improvements"])
                total_improvement += optimization["improvement_score"]

        # Calculate expected quality improvement
        expected_improvement = min(total_improvement, 1.0)

        return PromptOptimization(
            original_prompt=original_prompt,
            optimized_prompt=optimized_prompt,
            improvements=improvements,
            expected_quality_improvement=expected_improvement,
            optimization_reason=f"Addressing {len(primary_issues)} quality issues: {', '.join(primary_issues)}"
        )

    def _identify_primary_issues(
        self, issues: List[str], audit_details: Dict[str, Any]
    ) -> List[str]:
        """Identify the primary issues from quality control results."""
        issue_types = []

        # Check for specific issue patterns
        if any("hallucination" in issue.lower() for issue in issues):
            issue_types.append("hallucination")

        if any("relevance" in issue.lower() for issue in issues):
            issue_types.append("low_relevance")

        if any("title" in issue.lower() and "similarity" in issue.lower() for issue in issues):
            issue_types.append("title_mismatch")

        if any("generic" in issue.lower() for issue in issues):
            issue_types.append("generic_content")

        # Check audit details for additional patterns
        if audit_details.get("overall_score", 0) < 0.5:
            if "low_relevance" not in issue_types:
                issue_types.append("low_relevance")

        # If no specific issues found, use general optimization
        if not issue_types:
            issue_types.append("generic_content")

        return issue_types

    def _optimize_for_relevance(
        self, prompt: str, audit_details: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize prompt to improve relevance to input terms."""
        key_terms = audit_details.get("input_analysis", {}).get("key_terms", [])
        improvements = []
        modified_prompt = prompt

        # Add emphasis on key terms
        if key_terms:
            terms_section = "\n\nKEY TERMS TO INCLUDE:\n" + "\n".join(f"- {term}" for term in key_terms[:10])
            if "KEY TERMS TO INCLUDE" not in prompt:
                modified_prompt += terms_section
                improvements.append(f"Added emphasis on {len(key_terms[:10])} key terms")

        # Add context about project
        project_title = project_context.get("title", "")
        if project_title and f"project titled '{project_title}'" not in prompt.lower():
            context_section = f"\n\nPROJECT CONTEXT:\nThis is for a project titled '{project_title}'. "
            context_section += "Ensure all outputs are relevant to this specific project."
            modified_prompt += context_section
            improvements.append("Added specific project context")

        return {
            "prompt": modified_prompt,
            "improvements": improvements,
            "improvement_score": 0.3
        }

    def _optimize_for_hallucination(
        self, prompt: str, audit_details: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize prompt to prevent hallucination."""
        improvements = []
        modified_prompt = prompt

        # Add strict instructions about content boundaries
        if "STRICT CONTENT BOUNDARIES" not in prompt:
            boundaries_section = "\n\nSTRICT CONTENT BOUNDARIES:\n"
            boundaries_section += "- Only use information provided in the input artifacts\n"
            boundaries_section += "- Do not invent or assume information not explicitly provided\n"
            boundaries_section += "- If information is missing, use [PLACEHOLDER] and note what's needed\n"
            boundaries_section += "- Never generate content about unrelated domains or projects"
            modified_prompt += boundaries_section
            improvements.append("Added strict content boundaries to prevent hallucination")

        # Add examples of good vs bad outputs
        if "EXAMPLES" not in prompt:
            examples_section = "\n\nEXAMPLES:\n"
            examples_section += "GOOD: 'Implement template versioning as described in the ideation document'\n"
            examples_section += "BAD: 'Implement ERP system for supply chain management' (unrelated to templates)"
            modified_prompt += examples_section
            improvements.append("Added examples of appropriate vs inappropriate content")

        return {
            "prompt": modified_prompt,
            "improvements": improvements,
            "improvement_score": 0.4
        }

    def _optimize_for_title(
        self, prompt: str, audit_details: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize prompt to ensure project title is referenced."""
        project_title = project_context.get("title", "")
        improvements = []
        modified_prompt = prompt

        if project_title:
            # Add explicit instruction to reference project title
            title_section = f"\n\nPROJECT IDENTIFICATION:\n"
            title_section += f"- This project is titled: '{project_title}'\n"
            title_section += f"- All outputs must explicitly reference this project title\n"
            title_section += f"- Never use different project names or titles"
            modified_prompt += title_section
            improvements.append(f"Added explicit project title reference: '{project_title}'")

        return {
            "prompt": modified_prompt,
            "improvements": improvements,
            "improvement_score": 0.25
        }

    def _optimize_for_specificity(
        self, prompt: str, audit_details: Dict[str, Any], project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize prompt to improve specificity and reduce generic content."""
        improvements = []
        modified_prompt = prompt

        # Add instructions for specific, detailed outputs
        if "SPECIFICITY REQUIREMENTS" not in prompt:
            specificity_section = "\n\nSPECIFICITY REQUIREMENTS:\n"
            specificity_section += "- Provide detailed, specific outputs\n"
            specificity_section += "- Avoid generic statements and buzzwords\n"
            specificity_section += "- Include concrete examples and implementation details\n"
            specificity_section += "- Reference specific elements from input artifacts"
            modified_prompt += specificity_section
            improvements.append("Added specificity requirements to reduce generic content")

        return {
            "prompt": modified_prompt,
            "improvements": improvements,
            "improvement_score": 0.2
        }


# Global prompt optimizer instance
prompt_optimizer = PromptOptimizer()