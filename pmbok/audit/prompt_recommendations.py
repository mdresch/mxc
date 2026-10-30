"""
Prompt Improvement Recommendation Engine

Analyzes audit findings to generate specific LLM prompt improvements
that will help regenerate artifacts with higher compliance scores.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from pmbok.models.audit import AuditFinding, AuditResult, AuditSeverity


class PromptEnhancementCategory(str, Enum):
    """Categories of prompt improvements."""
    COMPLETENESS = "completeness"           # Add missing fields/information
    CLARITY = "clarity"                     # Clarify ambiguous/vague content
    STRUCTURE = "structure"                 # Fix structural/format issues
    VALIDATION = "validation"               # Add validation/constraint guidance
    CONTEXT = "context"                     # Provide additional context
    EXAMPLES = "examples"                   # Add in-context examples
    CONSTRAINTS = "constraints"             # Add constraints/guardrails
    ALIGNMENT = "alignment"                 # Align with standards/references


@dataclass
class PromptImprovement:
    """Single prompt improvement recommendation."""
    
    category: PromptEnhancementCategory
    """Category of improvement."""
    
    finding_criterion: str
    """Audit criterion that triggered this improvement."""
    
    description: str
    """Description of what needs to improve."""
    
    prompt_enhancement: str
    """Specific text to add/modify in the prompt."""
    
    example: str = ""
    """Example of desired output."""
    
    priority: int = 1
    """Priority level (1=high, 2=medium, 3=low)."""


@dataclass
class PromptImprovementPlan:
    """Complete plan to improve artifact quality via prompt enhancement."""
    
    artifact_id: str
    """ID of the artifact."""
    
    artifact_type: str
    """Type of artifact."""
    
    current_score: float
    """Current compliance score."""
    
    target_score: float
    """Target compliance score."""
    
    improvements: List[PromptImprovement] = field(default_factory=list)
    """List of recommended improvements."""
    
    regeneration_command: str = ""
    """Suggested command/parameters to regenerate with improvements."""
    
    estimated_improvement: float = 0.0
    """Estimated score improvement from suggested changes (%)."""
    
    summary: str = ""
    """Executive summary of needed improvements."""


class PromptRecommendationEngine:
    """Generates prompt improvement recommendations based on audit findings."""
    
    # Mapping from finding characteristics to improvements
    FINDING_TO_IMPROVEMENT = {
        "REQUIRED_FIELDS_MISSING": {
            "category": PromptEnhancementCategory.COMPLETENESS,
            "suggestion": "Add field descriptions and requirements to prompt",
            "priority": 1,
        },
        "PLACEHOLDER_TEXT": {
            "category": PromptEnhancementCategory.CLARITY,
            "suggestion": "Instruct LLM to avoid placeholder text, provide real values",
            "priority": 1,
        },
        "VAGUE_DESCRIPTION": {
            "category": PromptEnhancementCategory.CLARITY,
            "suggestion": "Request more specific, detailed descriptions with examples",
            "priority": 2,
        },
        "INCOMPLETE_CONTENT": {
            "category": PromptEnhancementCategory.COMPLETENESS,
            "suggestion": "Define minimum content length/depth in prompt",
            "priority": 2,
        },
        "MISSING_STRUCTURE": {
            "category": PromptEnhancementCategory.STRUCTURE,
            "suggestion": "Provide explicit structure/format template in prompt",
            "priority": 1,
        },
        "NO_PMBOK_REFERENCE": {
            "category": PromptEnhancementCategory.ALIGNMENT,
            "suggestion": "Include PMBOK process/knowledge area in prompt context",
            "priority": 2,
        },
        "INVALID_PROCESS": {
            "category": PromptEnhancementCategory.VALIDATION,
            "suggestion": "Provide list of valid PMBOK processes to select from",
            "priority": 1,
        },
    }
    
    @staticmethod
    def analyze_findings(
        artifact_id: str,
        artifact_type: str,
        current_score: float,
        target_score: float,
        findings: List[AuditFinding],
    ) -> PromptImprovementPlan:
        """
        Generate prompt improvements based on audit findings.
        
        Args:
            artifact_id: ID of artifact
            artifact_type: Type of artifact
            current_score: Current compliance score
            target_score: Target compliance score
            findings: List of audit findings
        
        Returns:
            PromptImprovementPlan with recommendations
        """
        plan = PromptImprovementPlan(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            current_score=current_score,
            target_score=target_score,
        )
        
        # Group findings by criterion
        by_criterion = {}
        for finding in findings:
            if finding.criterion not in by_criterion:
                by_criterion[finding.criterion] = []
            by_criterion[finding.criterion].append(finding)
        
        # Generate improvements for each criterion
        seen_improvements = set()
        for criterion, finds in by_criterion.items():
            for finding in finds:
                # Determine improvement category
                improvement = PromptRecommendationEngine._finding_to_improvement(
                    finding, criterion
                )
                if improvement and improvement.prompt_enhancement not in seen_improvements:
                    plan.improvements.append(improvement)
                    seen_improvements.add(improvement.prompt_enhancement)
        
        # Sort by priority
        plan.improvements.sort(key=lambda x: x.priority)
        
        # Calculate estimated improvement
        plan.estimated_improvement = min(
            target_score - current_score,
            len(plan.improvements) * 3.0  # ~3% per improvement
        )
        
        # Generate summary
        high_priority = [i for i in plan.improvements if i.priority == 1]
        plan.summary = f"Implement {len(high_priority)} high-priority changes to improve from {current_score:.1f}% to {target_score:.1f}%"
        
        return plan
    
    @staticmethod
    def _finding_to_improvement(finding: AuditFinding, criterion: str) -> Optional[PromptImprovement]:
        """Convert a finding into a prompt improvement."""
        
        # Determine improvement type from finding message
        msg_lower = finding.message.lower()
        
        if "missing" in msg_lower or "required" in msg_lower:
            return PromptImprovement(
                category=PromptEnhancementCategory.COMPLETENESS,
                finding_criterion=criterion,
                description=f"Address missing/incomplete: {finding.message}",
                prompt_enhancement=f"Ensure all required fields are populated with complete, specific values: {', '.join(finding.affected_fields)}",
                priority=1 if finding.severity == AuditSeverity.CRITICAL else 2,
            )
        
        elif "placeholder" in msg_lower or "incomplete" in msg_lower:
            return PromptImprovement(
                category=PromptEnhancementCategory.CLARITY,
                finding_criterion=criterion,
                description=f"Replace vague content: {finding.message}",
                prompt_enhancement=f"Do not use placeholder text or generic descriptions. Provide detailed, specific content for: {', '.join(finding.affected_fields)}. Minimum 3-5 sentences per field.",
                priority=1,
            )
        
        elif "not found" in msg_lower or "invalid" in msg_lower:
            return PromptImprovement(
                category=PromptEnhancementCategory.VALIDATION,
                finding_criterion=criterion,
                description=f"Validate against standards: {finding.message}",
                prompt_enhancement=f"When generating {criterion}, verify against standard references. Use only valid values. For {finding.affected_fields[0]}, cross-reference the PMBOK process registry.",
                priority=1,
            )
        
        elif "structure" in msg_lower or "format" in msg_lower:
            return PromptImprovement(
                category=PromptEnhancementCategory.STRUCTURE,
                finding_criterion=criterion,
                description=f"Fix structural issues: {finding.message}",
                prompt_enhancement=f"Structure the output with clear sections, bullet points, and logical organization. Follow this template: [Provide detailed template structure]",
                priority=1,
            )
        
        elif "context" in msg_lower or "alignment" in msg_lower:
            return PromptImprovement(
                category=PromptEnhancementCategory.ALIGNMENT,
                finding_criterion=criterion,
                description=f"Improve PMBOK alignment: {finding.message}",
                prompt_enhancement=f"Reference the applicable PMBOK: {criterion}. Map outputs to standard frameworks and processes.",
                priority=2,
            )
        
        else:
            return PromptImprovement(
                category=PromptEnhancementCategory.CLARITY,
                finding_criterion=criterion,
                description=finding.message,
                prompt_enhancement=f"Address finding: {finding.message}",
                priority=2,
            )
    
    @staticmethod
    def format_prompt_enhancement(plan: PromptImprovementPlan) -> str:
        """Format improvement plan as a readable prompt enhancement guide."""
        
        lines = []
        lines.append(f"\n{'='*80}")
        lines.append(f"PROMPT IMPROVEMENT PLAN - {plan.artifact_type}")
        lines.append(f"{'='*80}\n")
        
        lines.append(f"Artifact: {plan.artifact_id}")
        lines.append(f"Current Score: {plan.current_score:.1f}%")
        lines.append(f"Target Score: {plan.target_score:.1f}%")
        lines.append(f"Estimated Improvement: +{plan.estimated_improvement:.1f}%\n")
        
        lines.append(f"SUMMARY: {plan.summary}\n")
        
        lines.append(f"{'IMPROVEMENTS':-^80}\n")
        
        # Group by category
        by_category = {}
        for imp in plan.improvements:
            if imp.category not in by_category:
                by_category[imp.category] = []
            by_category[imp.category].append(imp)
        
        for category in sorted(by_category.keys()):
            imprs = by_category[category]
            lines.append(f"\n[{category.value.upper()}] ({len(imprs)} changes)\n")
            
            for i, imp in enumerate(imprs, 1):
                pri_label = "HIGH" if imp.priority == 1 else "MED" if imp.priority == 2 else "LOW"
                lines.append(f"{i}. [{pri_label}] {imp.finding_criterion}")
                lines.append(f"   Issue: {imp.description}")
                lines.append(f"   Enhancement: {imp.prompt_enhancement}")
                if imp.example:
                    lines.append(f"   Example: {imp.example}")
                lines.append("")
        
        lines.append(f"{'='*80}\n")
        lines.append("REGENERATION STEPS:")
        lines.append("1. Update generation prompt with enhancements above")
        lines.append("2. Run artifact generator with new prompt")
        lines.append("3. Re-audit new artifact")
        lines.append("4. Compare scores and validate improvements\n")
        
        return "\n".join(lines)
