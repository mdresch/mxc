"""
Audit Analytics and Regression Tracking

Tracks audit history, detects regressions, and recommends prompt improvements.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from pmbok.models.pmbok import ProjectArtifact
from pmbok.models.audit import AuditResult
from pmbok.audit.regression_thresholds import (
    check_regression,
    get_threshold,
    RegressionThreshold,
)
from pmbok.audit.prompt_recommendations import (
    PromptRecommendationEngine,
    PromptImprovementPlan,
)
from pmbok.storage.audit_store import AuditStore


@dataclass
class AuditComparison:
    """Comparison between two audit results."""
    
    artifact_id: str
    current_result: AuditResult
    previous_result: Optional[AuditResult]
    
    score_change: float = 0.0
    confidence_change: float = 0.0
    finding_delta: Dict[str, int] = None  # New, resolved, unchanged
    
    is_regression: bool = False
    regression_severity: str = "NONE"  # CRITICAL, WARNING, INFO
    
    def __post_init__(self):
        if self.finding_delta is None:
            self.finding_delta = {}
        
        if self.previous_result:
            self.score_change = (
                self.current_result.compliance_score - 
                self.previous_result.compliance_score
            )
            self.confidence_change = (
                self.current_result.confidence_score - 
                self.previous_result.confidence_score
            )


class AuditAnalytics:
    """Analyzes audit trends and detects quality regressions."""
    
    def __init__(self, audit_store: AuditStore | Path):
        if isinstance(audit_store, (str, Path)):
            self.audit_store = AuditStore(Path(audit_store))
        else:
            self.audit_store = audit_store
    
    def compare_audits(
        self,
        artifact_id: str,
    ) -> Optional[AuditComparison]:
        """
        Compare current audit against previous version.
        
        Args:
            artifact_id: Artifact to compare
        
        Returns:
            AuditComparison with trend analysis
        """
        history = self.audit_store.get_history(artifact_id)
        
        if not history or len(history) < 2:
            return None
        
        current = history[-1]
        previous = history[-2] if len(history) >= 2 else None
        
        comparison = AuditComparison(
            artifact_id=artifact_id,
            current_result=current,
            previous_result=previous,
        )
        
        # Analyze changes
        if previous:
            comparison.score_change = (
                current.compliance_score - previous.compliance_score
            )
            comparison.confidence_change = (
                current.confidence_score - previous.confidence_score
            )
            
            # Compare findings
            prev_findings = {f.code: f for f in previous.findings}
            curr_findings = {f.code: f for f in current.findings}
            
            new_codes = set(curr_findings.keys()) - set(prev_findings.keys())
            resolved_codes = set(prev_findings.keys()) - set(curr_findings.keys())
            
            comparison.finding_delta = {
                "new": len(new_codes),
                "resolved": len(resolved_codes),
                "unchanged": len(set(curr_findings.keys()) & set(prev_findings.keys())),
            }
        
        # Check for regression
        threshold = get_threshold(current.artifact_type)
        if current.compliance_score < threshold.minimum_compliance_score:
            comparison.is_regression = True
            comparison.regression_severity = "CRITICAL"
        elif previous and comparison.score_change < -5.0:
            comparison.is_regression = True
            comparison.regression_severity = "WARNING"
        
        return comparison
    
    def get_regression_report(
        self,
        artifact_ids: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Generate regression report for artifacts.
        
        Args:
            artifact_ids: Specific artifacts to check, or None for all
        
        Returns:
            Report with regressions detected
        """
        artifacts_to_check = (
            artifact_ids or self.audit_store.list_artifacts()
        )
        
        regressions = []
        compliant = []
        
        for artifact_id in artifacts_to_check:
            comparison = self.compare_audits(artifact_id)
            if not comparison:
                continue
            
            if comparison.is_regression:
                regressions.append(comparison)
            else:
                compliant.append(comparison)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_artifacts": len(artifacts_to_check),
            "regressions_detected": len(regressions),
            "compliant": len(compliant),
            "regressions": regressions,
            "compliant_artifacts": compliant,
        }
    
    def get_improvement_recommendations(
        self,
        artifact_id: str,
        target_score: float = 90.0,
    ) -> Optional[PromptImprovementPlan]:
        """
        Generate prompt improvement plan for an artifact.
        
        Args:
            artifact_id: Artifact to improve
            target_score: Target compliance score
        
        Returns:
            PromptImprovementPlan with specific recommendations
        """
        latest_audit = self.audit_store.get(artifact_id)
        if not latest_audit:
            return None
        
        # Don't recommend improvements if already meeting target
        if latest_audit.compliance_score >= target_score:
            return None
        
        plan = PromptRecommendationEngine.analyze_findings(
            artifact_id=artifact_id,
            artifact_type=latest_audit.artifact_type,
            current_score=latest_audit.compliance_score,
            target_score=target_score,
            findings=latest_audit.findings,
        )
        
        return plan
    
    def get_batch_improvement_plan(
        self,
        artifact_ids: List[str],
        target_score: float = 85.0,
    ) -> List[PromptImprovementPlan]:
        """
        Generate improvement plans for multiple artifacts.
        
        Args:
            artifact_ids: List of artifacts to improve
            target_score: Target compliance score
        
        Returns:
            List of PromptImprovementPlan objects
        """
        plans = []
        for artifact_id in artifact_ids:
            plan = self.get_improvement_recommendations(artifact_id, target_score)
            if plan:
                plans.append(plan)
        
        return plans
    
    def format_analytics_report(
        self,
        artifact_ids: Optional[List[str]] = None,
    ) -> str:
        """Format analytics and regression report."""
        report_data = self.get_regression_report(artifact_ids)
        
        lines = []
        lines.append(f"\n{'='*80}")
        lines.append("AUDIT ANALYTICS & REGRESSION DETECTION REPORT")
        lines.append(f"{'='*80}\n")
        
        lines.append(f"Timestamp: {report_data['timestamp']}")
        lines.append(f"Total Artifacts Tracked: {report_data['total_artifacts']}")
        lines.append(f"Regressions Detected: {report_data['regressions_detected']}")
        lines.append(f"Compliant: {report_data['compliant']}\n")
        
        if report_data['regressions']:
            lines.append(f"{'REGRESSIONS DETECTED':-^80}\n")
            for i, comp in enumerate(report_data['regressions'], 1):
                lines.append(f"{i}. {comp.artifact_id}")
                lines.append(f"   Severity: {comp.regression_severity}")
                lines.append(f"   Score: {comp.current_result.compliance_score:.1f}%")
                if comp.previous_result:
                    lines.append(f"   Change: {comp.score_change:+.1f}%")
                    lines.append(f"   Findings Delta: New={comp.finding_delta.get('new', 0)}, Resolved={comp.finding_delta.get('resolved', 0)}")
                lines.append("")
        
        if report_data['compliant']:
            lines.append(f"\n{'COMPLIANT ARTIFACTS':-^80}\n")
            for i, comp in enumerate(report_data['compliant'][:5], 1):  # Show first 5
                lines.append(f"{i}. {comp.artifact_id}: {comp.current_result.compliance_score:.1f}%")
            if len(report_data['compliant']) > 5:
                lines.append(f"... and {len(report_data['compliant']) - 5} more compliant artifacts")
        
        lines.append(f"\n{'='*80}\n")
        return "\n".join(lines)

    async def generate_comprehensive_report(self, run_id: str) -> str:
        """
        Generate a comprehensive project report for a specific project run.
        Includes process status, artifact quality, and audit analytics.
        """
        # We need the state data to show process status
        from pmbok.storage.state_store import StateStore
        # state.db is expected to be in the same base path
        state_db_path = self.audit_store.base_path / "state.db"
        state_store = StateStore(str(state_db_path))
        
        run_data = await state_store.load_run(run_id)
        process_states = await state_store.load_all_process_states(run_id)
        
        # Gather all artifacts for this run
        from pmbok.storage.artifact_store import ArtifactStore
        artifact_store = ArtifactStore(self.audit_store.base_path)
        all_artifacts = await artifact_store.list_artifacts(run_id)
        
        lines = []
        lines.append(f"# ADPA COMPREHENSIVE PROJECT REPORT")
        lines.append(f"**Run ID:** {run_id}")
        lines.append(f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Phases Completed:** {run_data.current_process_group.value}")
        lines.append(f"\n## 1. Project Execution Overview")
        
        status_counts = {}
        for ps in process_states:
            status_counts[ps.status.value] = status_counts.get(ps.status.value, 0) + 1
            
        lines.append(f"- **Total Processes:** {len(process_states)}")
        for status, count in status_counts.items():
            lines.append(f"- **{status.capitalize()}:** {count}")
            
        lines.append(f"\n## 2. Artifact Quality Summary")
        
        # Calculate average score
        scores = [a.audit_result.compliance_score for a in all_artifacts if a.audit_result]
        if scores:
            avg_score = sum(scores) / len(scores)
            lines.append(f"- **Average Compliance Score:** {avg_score:.1f}%")
            lines.append(f"- **Artifacts Audited:** {len(scores)}")
        else:
            lines.append("- No audit results found for generated artifacts.")
            
        lines.append(f"\n## 3. Detailed Process Findings")
        
        # Group artifacts by process
        from collections import defaultdict
        process_artifacts = defaultdict(list)
        for a in all_artifacts:
            process_artifacts[a.process_id].append(a)
            
        for ps in sorted(process_states, key=lambda x: x.process_id):
            status_symbol = "✅" if ps.status.value == "complete" else "⚠️" if ps.status.value == "blocked" else "⏳"
            lines.append(f"\n### {status_symbol} {ps.process_id} Status: {ps.status.value.upper()}")
            
            if ps.error_log:
                lines.append("#### Errors Tracked:")
                for error in ps.error_log:
                    lines.append(f"- {error}")
            
            artifacts = process_artifacts.get(ps.process_id, [])
            if artifacts:
                lines.append("#### Generated Artifacts:")
                for a in artifacts:
                    score = f"({a.audit_result.compliance_score:.1f}%)" if a.audit_result else "(No Audit)"
                    lines.append(f"- {a.artifact_type} v{a.version} {score}")
                    if a.audit_result and a.audit_result.findings:
                        for f in a.audit_result.findings[:3]: # Top 3 findings
                            lines.append(f"  - [{f.severity.value}] {f.message}")
                            
        lines.append(f"\n---")
        lines.append(f"*Report generated by ADPA AuditAnalytics Module.*")
        
        return "\n".join(lines)
