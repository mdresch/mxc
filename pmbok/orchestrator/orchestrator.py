"""PMBOK Orchestrator — state machine managing all 49 PMBOK processes."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pmbok.config import settings
from pmbok.exceptions import LLMError, LLMParseError, ProcessExecutionError
from pmbok.models.enums import ApprovalStatus, ProcessGroup, ProcessStatus, AuditMode
from pmbok.models.pmbok import ProcessMap, ProcessState, ProjectRun
from pmbok.process_registry import (
    PMBOK_PROCESSES,
    PROCESS_DEPENDENCY_MAP,
    get_processes_by_group,
)
from pmbok.audit.regression_thresholds import check_regression, get_threshold
from pmbok.audit.analytics import AuditAnalytics
from pmbok.audit.prompt_recommendations import PromptRecommendationEngine

if TYPE_CHECKING:
    from pmbok.agents.factory import ProcessAgentFactory
    from pmbok.models.approval import ApprovalDecision
    from pmbok.models.business_case import BusinessCase
    from pmbok.models.pmbok import PMBOKProcess
    from pmbok.storage.artifact_store import ArtifactStore
    from pmbok.storage.state_store import StateStore

logger = logging.getLogger(__name__)

# Tenacity retry configuration per design Section 7.1
# Retries on: agent execution failures, LLM API errors, and bad/hollow JSON responses.
# LLMParseError and LLMError are transient — the next call may produce valid output.
RETRY_CONFIG = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ProcessExecutionError, LLMParseError, LLMError)),
    reraise=False,
)

# Ordered sequence of process groups for gate advancement
_GROUP_ORDER: list[ProcessGroup] = [
    ProcessGroup.INITIATING,
    ProcessGroup.PLANNING,
    ProcessGroup.EXECUTING,
    ProcessGroup.MONITORING_CONTROLLING,
    ProcessGroup.CLOSING,
]

# Map process_id → PMBOKProcess for fast lookup
_PROCESS_BY_ID: dict[str, "PMBOKProcess"] = {p.process_id: p for p in PMBOK_PROCESSES}


def _build_reverse_dep_map() -> dict[str, list[str]]:
    """Build a reverse dependency map: process_id → list of processes that depend on it."""
    reverse: dict[str, list[str]] = defaultdict(list)
    for pid, prereqs in PROCESS_DEPENDENCY_MAP.items():
        for prereq in prereqs:
            reverse[prereq].append(pid)
    return dict(reverse)


_REVERSE_DEP_MAP: dict[str, list[str]] = _build_reverse_dep_map()


class PMBOKOrchestrator:
    """
    State machine that manages all 49 PMBOK processes, dispatches agents,
    and resolves dependencies.
    """

    def __init__(
        self,
        agent_factory: "ProcessAgentFactory",
        artifact_store: "ArtifactStore",
        state_store: "StateStore",
        enable_quality_gate: bool = True,
        max_regeneration_attempts: int = 3,
        project_context: dict[str, Any] | None = None,
    ) -> None:
        self._agent_factory = agent_factory
        self._artifact_store = artifact_store
        self._state_store = state_store
        self._enable_quality_gate = enable_quality_gate
        self._max_regeneration_attempts = max_regeneration_attempts
        self._regeneration_tracking: dict[str, int] = {}  # artifact_id → attempt count
        self._project_context = project_context
        self._semaphore = asyncio.Semaphore(3) # Limit concurrency to 3 to avoid 429

    # ── Public API ────────────────────────────────────────────────────────────

    async def start(self, business_case: "BusinessCase") -> ProjectRun:
        """Initialize a new project run from an approved BusinessCase."""
        session_id = str(uuid.uuid4())
        run = ProjectRun(
            business_case_id=business_case.id,
            current_process_group=ProcessGroup.INITIATING,
            gate_status={},
        )

        # Persist the run
        await self._state_store.save_run(run, session_id)
        
        # Formally persist the Business Case as a 'Phase 0' artifact for visibility
        from datetime import datetime
        from pmbok.models.pmbok import ProjectArtifact
        
        bc_artifact = ProjectArtifact(
            id=business_case.id,
            run_id=run.id,
            process_id="0.1", # Logical 'Phase 0' ID for Ideation/Strategy
            artifact_type="Business Case",
            version=1,
            content=business_case.dict(),
            produced_by="Strategy Ingestion",
            created_at=datetime.utcnow()
        )
        await self._artifact_store.save(bc_artifact, process_name="0.0 Project Inception")

        # Initialize all 49 process states as NOT_STARTED
        for process in PMBOK_PROCESSES:
            await self._state_store.set_status(
                run.id, process.process_id, ProcessStatus.NOT_STARTED
            )

        # Dispatch all Initiating-group processes (they have no prerequisites)
        initiating = get_processes_by_group(ProcessGroup.INITIATING)
        await asyncio.gather(
            *[self._dispatch_process(run.id, p) for p in initiating]
        )

        return run

    async def resume(self, run_id: str) -> ProjectRun:
        """Resume an existing run from its last persisted checkpoint."""
        run = await self._state_store.load_run(run_id)
        process_states = await self._state_store.load_all_process_states(run_id)
        status_map = {ps.process_id: ps.status for ps in process_states}

        ready = self._resolve_ready_processes(run_id, status_map)
        tasks = []
        for p in ready:
            current_status = status_map.get(p.process_id, ProcessStatus.NOT_STARTED)
            if current_status in (ProcessStatus.NOT_STARTED, ProcessStatus.IN_PROGRESS):
                tasks.append(self._dispatch_process(run_id, p))

        if tasks:
            await asyncio.gather(*tasks)

        return run

    async def advance_to_next_group(
        self, run_id: str, approval: "ApprovalDecision"
    ) -> None:
        """Called after user approves a process group gate."""
        run = await self._state_store.load_run(run_id)
        current_group = run.current_process_group

        # Load all process states to check group completion
        process_states = await self._state_store.load_all_process_states(run_id)
        status_map = {ps.process_id: ps.status for ps in process_states}

        if not self._is_group_complete(current_group, status_map):
            raise ValueError(
                f"Cannot advance: process group {current_group.value} is not complete."
            )

        if approval.status != ApprovalStatus.APPROVED:
            raise ValueError(
                f"Cannot advance: approval status is {approval.status.value}, not approved."
            )

        # Find the next group
        current_idx = _GROUP_ORDER.index(current_group)
        if current_idx >= len(_GROUP_ORDER) - 1:
            logger.info("run=%s All process groups complete.", run_id)
            return

        next_group = _GROUP_ORDER[current_idx + 1]

        # Update gate status and current group
        run.gate_status[current_group] = ApprovalStatus.APPROVED
        run.current_process_group = next_group

        # Persist updated run (use a dummy session_id since we're updating)
        await self._state_store.save_run(run, str(uuid.uuid4()))

        # Dispatch ready processes in the new group
        process_states_new = await self._state_store.load_all_process_states(run_id)
        status_map_new = {ps.process_id: ps.status for ps in process_states_new}
        ready = self._resolve_ready_processes(run_id, status_map_new)

        await asyncio.gather(
            *[self._dispatch_process(run_id, p) for p in ready]
        )

    async def get_process_map(self, run_id: str) -> ProcessMap:
        """Return current status of all 49 processes."""
        process_states = await self._state_store.load_all_process_states(run_id)
        status_map = {ps.process_id: ps.status for ps in process_states}

        # Build a complete list — include NOT_STARTED for any process not yet in the store
        all_states: list[ProcessState] = []
        for process in PMBOK_PROCESSES:
            if process.process_id in {ps.process_id for ps in process_states}:
                # Find the matching state
                state = next(
                    ps for ps in process_states if ps.process_id == process.process_id
                )
                all_states.append(state)
            else:
                all_states.append(
                    ProcessState(
                        process_id=process.process_id,
                        run_id=run_id,
                        status=status_map.get(
                            process.process_id, ProcessStatus.NOT_STARTED
                        ),
                    )
                )

        return ProcessMap(run_id=run_id, processes=all_states)

    async def retry_blocked_process(self, run_id: str, process_id: str) -> None:
        """Manual recovery: reset a BLOCKED process to NOT_STARTED to allow retry."""
        status = await self._state_store.get_status(run_id, process_id)
        if status != ProcessStatus.BLOCKED:
            raise ValueError(f"Process {process_id} is not BLOCKED (status={status.value}).")

        await self._state_store.set_status(run_id, process_id, ProcessStatus.NOT_STARTED)
        # We don't clear the error_log here (it's a history), but we could
        logger.info("run=%s process=%s UNBLOCKED via retry_blocked_process", run_id, process_id)

    # ── Internal dispatch ─────────────────────────────────────────────────────

    async def _invoke_agent_with_retry(
        self,
        run_id: str,
        process: "PMBOKProcess",
        input_artifacts: list,
        version: int = 1,
        system_message_override: str | None = None,
    ) -> list:
        """
        Invoke the process agent with tenacity exponential-backoff retry.

        Decorated with @retry so tenacity handles the backoff schedule:
          attempt 1→2: waits 2 s, attempt 2→3: waits 4 s.
        Raises ProcessExecutionError on each attempt; after 3 failures tenacity
        raises RetryError (reraise=False), which _dispatch_process catches.
        """
        async for attempt in AsyncRetrying(**RETRY_CONFIG):
            with attempt:
                async with self._semaphore: # Apply throttling here
                    agent = self._agent_factory.create(process)
                    try:
                        artifacts = await agent.execute(
                            run_id,
                            input_artifacts,
                            version=version,
                            system_message_override=system_message_override,
                            project_context=self._project_context,
                        )
                    except (ProcessExecutionError, LLMParseError, LLMError):
                        raise
                    except Exception as exc:
                        raise ProcessExecutionError(
                            f"process={process.process_id} run={run_id}: {exc}"
                        ) from exc
                return artifacts
        # AsyncRetrying exhausted — unreachable when reraise=False, but satisfies type checker
        raise ProcessExecutionError(  # pragma: no cover
            f"process={process.process_id} run={run_id}: all retries exhausted"
        )

    async def _dispatch_process(self, run_id: str, process: "PMBOKProcess") -> None:
        """Dispatch a single process to its ProcessAgent using tenacity retry."""
        await self._state_store.set_status(
            run_id, process.process_id, ProcessStatus.IN_PROGRESS
        )

        # Gather input artifacts from prerequisite processes
        input_artifacts = []
        for prereq_id in process.prerequisites:
            try:
                prereq_process = _PROCESS_BY_ID[prereq_id]
                for output_type in prereq_process.expected_outputs:
                    artifact = await self._artifact_store.get_latest(
                        run_id, prereq_id, output_type
                    )
                    input_artifacts.append(artifact)
            except FileNotFoundError:
                pass  # Prerequisite may not have produced this artifact type

        try:
            # Execute agent (returns artifacts and potentially qc_failure status)
            artifacts = await self._invoke_agent_with_retry(
                run_id, process, input_artifacts
            )
            
            # Quality Gate Hook: Check artifact quality and potentially regenerate (if BLOCKING)
            if self._enable_quality_gate:
                artifacts = await self._apply_quality_gate(
                    run_id, process, artifacts, input_artifacts
                )

            # Mark complete (or complete with warnings)
            final_status = ProcessStatus.COMPLETE
            
            # Refined Rule: If QC produced any warning/critical issue but execution completed,
            # and we are in ADVISORY mode, mark as COMPLETED_WITH_WARNINGS.
            if settings.AUDIT_MODE == AuditMode.ADVISORY:
                for a in artifacts:
                    if a.audit_result and (a.audit_result.critical_count > 0 or a.audit_result.warning_count > 0):
                        final_status = ProcessStatus.COMPLETED_WITH_WARNINGS
                        logger.warning(
                            "run=%s process=%s COMPLETED_WITH_WARNINGS due to QC findings in ADVISORY mode.",
                            run_id, process.process_id
                        )
                        break

            await self._state_store.set_status(
                run_id, process.process_id, final_status
            )
            logger.info(
                "run=%s process=%s %s",
                run_id,
                process.process_id,
                final_status.value
            )

            # Re-evaluate dependents
            await self._on_process_complete(run_id, process.process_id)

        except RetryError as exc:
            # All tenacity attempts exhausted — mark BLOCKED and propagate
            underlying_exc = exc.last_attempt.exception() if hasattr(exc, "last_attempt") else exc
            logger.error(
                "run=%s process=%s BLOCKED after all retry attempts. Last major error: %s",
                run_id,
                process.process_id,
                underlying_exc,
            )
            await self._state_store.append_error(
                run_id,
                process.process_id,
                f"BLOCKED after all retry attempts. Last major error: {underlying_exc}",
            )
            await self._state_store.set_status(
                run_id, process.process_id, ProcessStatus.BLOCKED
            )
            await self._propagate_blocked(run_id, process.process_id)

        except Exception as exc:
            # Unexpected non-ProcessExecutionError — log and mark BLOCKED
            logger.error(
                "run=%s process=%s BLOCKED due to unexpected error: %s",
                run_id,
                process.process_id,
                exc,
            )
            await self._state_store.append_error(
                run_id,
                process.process_id,
                f"Unexpected error: {exc}",
            )
            await self._state_store.set_status(
                run_id, process.process_id, ProcessStatus.BLOCKED
            )
            await self._propagate_blocked(run_id, process.process_id)

    async def _on_process_complete(self, run_id: str, completed_pid: str) -> None:
        """Re-evaluate readiness of dependents after a process completes."""
        run = await self._state_store.load_run(run_id)
        process_states = await self._state_store.load_all_process_states(run_id)
        status_map = {ps.process_id: ps.status for ps in process_states}

        # Only consider direct dependents of the completed process
        dependents = self._get_direct_dependents(completed_pid)
        newly_ready: list["PMBOKProcess"] = []

        for dep_id in dependents:
            dep_process = _PROCESS_BY_ID.get(dep_id)
            if dep_process is None:
                continue
            if dep_process.process_group != run.current_process_group:
                continue
            dep_status = status_map.get(dep_id, ProcessStatus.NOT_STARTED)
            if dep_status != ProcessStatus.NOT_STARTED:
                continue
            # Check all prerequisites are complete
            all_prereqs_complete = all(
                status_map.get(prereq, ProcessStatus.NOT_STARTED)
                in (ProcessStatus.COMPLETE, ProcessStatus.COMPLETED_WITH_WARNINGS)
                for prereq in dep_process.prerequisites
            )
            if all_prereqs_complete:
                newly_ready.append(dep_process)

        if newly_ready:
            await asyncio.gather(
                *[self._dispatch_process(run_id, p) for p in newly_ready]
            )

    # ── Dependency resolution ─────────────────────────────────────────────────

    def _resolve_ready_processes(
        self,
        run_id: str,
        status_map: dict[str, ProcessStatus],
    ) -> list["PMBOKProcess"]:
        """
        Topological sort: return processes whose all prerequisites are COMPLETE
        and which belong to the currently active ProcessGroup.

        Note: run_id is accepted for interface compatibility but current_group
        is derived from the status_map context. Callers must pass the correct
        status_map for the active group.
        """
        # We need the current group — load it from the status_map context.
        # Since this is synchronous, we derive the current group by checking
        # which group's processes are in NOT_STARTED/IN_PROGRESS state.
        # The caller is responsible for passing the correct status_map.
        ready: list["PMBOKProcess"] = []

        for process in PMBOK_PROCESSES:
            current_status = status_map.get(
                process.process_id, ProcessStatus.NOT_STARTED
            )
            if current_status != ProcessStatus.NOT_STARTED:
                continue

            # Check all prerequisites are complete
            all_prereqs_complete = all(
                status_map.get(prereq, ProcessStatus.NOT_STARTED)
                in (ProcessStatus.COMPLETE, ProcessStatus.COMPLETED_WITH_WARNINGS)
                for prereq in process.prerequisites
            )
            if all_prereqs_complete:
                ready.append(process)

        return ready

    def _resolve_ready_processes_for_group(
        self,
        current_group: ProcessGroup,
        status_map: dict[str, ProcessStatus],
    ) -> list["PMBOKProcess"]:
        """Return ready processes filtered to the given process group."""
        ready: list["PMBOKProcess"] = []

        for process in get_processes_by_group(current_group):
            current_status = status_map.get(
                process.process_id, ProcessStatus.NOT_STARTED
            )
            if current_status != ProcessStatus.NOT_STARTED:
                continue

            all_prereqs_complete = all(
                status_map.get(prereq, ProcessStatus.NOT_STARTED)
                in (ProcessStatus.COMPLETE, ProcessStatus.COMPLETED_WITH_WARNINGS)
                for prereq in process.prerequisites
            )
            if all_prereqs_complete:
                ready.append(process)

        return ready

    # ── Blocked propagation ───────────────────────────────────────────────────

    async def _propagate_blocked(
        self, run_id: str, blocked_process_id: str
    ) -> None:
        """BFS propagation of BLOCKED status to all transitively dependent processes."""
        queue = [blocked_process_id]
        visited: set[str] = set()

        while queue:
            pid = queue.pop(0)
            if pid in visited:
                continue
            visited.add(pid)

            dependents = self._get_direct_dependents(pid)
            for dep in dependents:
                dep_state = await self._state_store.get_status(run_id, dep)
                if dep_state == ProcessStatus.NOT_STARTED:
                    await self._state_store.set_status(
                        run_id, dep, ProcessStatus.BLOCKED
                    )
                    queue.append(dep)

    def _get_direct_dependents(self, pid: str) -> list[str]:
        """Return all process IDs that have *pid* in their prerequisites."""
        return _REVERSE_DEP_MAP.get(pid, [])

    # ── Quality Gate & Regeneration ───────────────────────────────────────────

    async def _apply_quality_gate(
        self,
        run_id: str,
        process: "PMBOKProcess",
        artifacts: list,
        input_artifacts: list,
    ) -> list:
        """
        Quality gate hook: Check artifact compliance and regenerate if needed.
        
        Returns the final list of artifacts (original or regenerated).
        """
        finalized_artifacts = []
        
        for artifact in artifacts:
            # Check if artifact needs regeneration
            should_regen = await self._should_regenerate(artifact)
            
            # Advisory Mode Rule: Skip regeneration entirely
            if should_regen and settings.AUDIT_MODE == AuditMode.ADVISORY:
                logger.info(
                    "artifact=%s Quality below threshold (score=%.1f%%) but skipping regeneration due to ADVISORY mode.",
                    artifact.id,
                    artifact.audit_result.compliance_score if artifact.audit_result else 0,
                )
                should_regen = False

            if should_regen:
                regen_count = self._regeneration_tracking.get(artifact.id, 0)
                
                if regen_count >= self._max_regeneration_attempts:
                    logger.warning(
                        "artifact=%s Max regeneration attempts (%d) reached. "
                        "Accepting current artifact.",
                        artifact.id,
                        self._max_regeneration_attempts,
                    )
                    finalized_artifacts.append(artifact)
                else:
                    logger.info(
                        "artifact=%s Quality below threshold (score=%.1f%%). "
                        "Regenerating (attempt %d/%d)...",
                        artifact.id,
                        artifact.audit_result.compliance_score if artifact.audit_result else 0,
                        regen_count + 1,
                        self._max_regeneration_attempts,
                    )
                    
                    # Regenerate with improvements
                    regenerated = await self._regenerate_with_improvements(
                        run_id, process, artifact, input_artifacts
                    )
                    
                    # Track regeneration attempt
                    self._regeneration_tracking[artifact.id] = regen_count + 1
                    
                    # Recursively apply gate to regenerated artifact
                    finalized = await self._apply_quality_gate(
                        run_id, process, [regenerated], input_artifacts
                    )
                    finalized_artifacts.extend(finalized)
            else:
                finalized_artifacts.append(artifact)
        
        return finalized_artifacts

    async def _should_regenerate(self, artifact) -> bool:
        """
        Determine if artifact's quality is below minimum threshold.
        
        Returns True if regeneration is recommended.
        """
        # No audit result = no quality check needed
        if artifact.audit_result is None:
            return False
        
        # Check if score is below minimum for this artifact type
        regression = check_regression(
            artifact.artifact_type,
            artifact.audit_result.compliance_score,
        )
        
        # Also check threshold config
        threshold = get_threshold(artifact.artifact_type)
        
        if not threshold.auto_regenerate:
            # Auto-regeneration not enabled for this type
            return False
        
        return (
            regression.get("recommendation") == "REGENERATE_REQUIRED"
            or artifact.audit_result.compliance_score < threshold.minimum_compliance_score
        )

    async def _regenerate_with_improvements(
        self,
        run_id: str,
        process: "PMBOKProcess",
        failed_artifact,
        input_artifacts: list,
    ) -> list:
        """
        Re-execute process with enhanced prompt based on audit findings.
        
        Returns regenerated artifact with improved quality.
        """
        # Generate improvement recommendations
        improvement_plan = PromptRecommendationEngine.analyze_findings(
            artifact_id=failed_artifact.id,
            artifact_type=failed_artifact.artifact_type,
            current_score=failed_artifact.audit_result.compliance_score,
            target_score=90.0, # Aim for high quality
            findings=failed_artifact.audit_result.findings
        )
        
        logger.info(
            "artifact=%s Generated %d improvement recommendations. "
            "Est. improvement: +%.1f%%",
            failed_artifact.id,
            len(improvement_plan.improvements),
            improvement_plan.estimated_improvement,
        )
        
        # Build enhanced system prompt
        enhanced_system_msg = self._build_enhanced_prompt(
            process, improvement_plan
        )
        
        # Execute with enhanced prompt and incremented version
        next_version = failed_artifact.version + 1
        try:
            regenerated_artifacts = await self._invoke_agent_with_retry(
                run_id,
                process,
                input_artifacts,
                version=next_version,
                system_message_override=enhanced_system_msg,
            )
        except Exception as exc:
            logger.error(
                "process=%s Regeneration failed: %s",
                process.process_id,
                exc,
            )
            return failed_artifact
        
        # Save regenerated artifacts (triggers audit hook)
        for regen_artifact in regenerated_artifacts:
            # Connect to previous version
            regen_artifact.previous_version_id = failed_artifact.id
            
            # Save with audit hook
            await self._artifact_store.save(regen_artifact)
            
            logger.info(
                "artifact=%s Regenerated: v%d saved. "
                "Compliance: %s%%",
                regen_artifact.id,
                regen_artifact.version,
                f"{regen_artifact.audit_result.compliance_score:.1f}"
                if regen_artifact.audit_result
                else "N/A",
            )
        
        # Return first regenerated artifact (or original if empty)
        return regenerated_artifacts[0] if regenerated_artifacts else failed_artifact

    def _build_enhanced_prompt(self, process: "PMBOKProcess", improvement_plan) -> str:
        """Build an enhanced system prompt with quality improvements."""
        base_system_msg = (
            f"You are a PMBOK project management expert specializing in "
            f"{process.name}. Generate high-quality, complete, and PMBOK-compliant "
            f"artifacts that meet all requirements.\n\n"
            f"Process name: {process.name}\n"
            f"Knowledge area: {process.knowledge_area.value}\n"
            f"Process group: {process.process_group.value}\n"
            f"Expected outputs: {json.dumps(process.expected_outputs)}\n"
        )
        
        improvements_section = "\n\n### CRITICAL QUALITY IMPROVEMENTS TO APPLY:\n"
        for i, improvement in enumerate(improvement_plan.improvements[:5], 1):
            improvements_section += (
                f"{i}. [{improvement.category.value.upper()}] "
                f"{improvement.description}\n"
                f"   REQUIRED ACTION: {improvement.prompt_enhancement}\n"
            )
        
        enhanced = (
            base_system_msg
            + improvements_section
            + f"\n\nTarget Compliance Score: {improvement_plan.target_score:.0f}%\n"
            + "\nYour task is to produce the expected outputs for this process with the above improvements applied.\n\n"
            "Return ONLY a JSON array of ProjectArtifact objects — no markdown fences, "
            "no extra text. Each object must have the following fields:\n"
            "[\n"
            "  {\n"
            '    "run_id": "<string>",\n'
            '    "process_id": "<string>",\n'
            '    "artifact_type": "<string>",\n'
            '    "version": 1,\n'
            '    "content": {<structured content>},\n'
            '    "produced_by": "<process_id>"\n'
            "  },\n"
            "  ...\n"
            "]\n\n"
            f"Produce one artifact per expected output: {process.expected_outputs}"
        )
        
        return enhanced

    # ── Gate helpers ──────────────────────────────────────────────────────────

    def _is_group_complete(
        self,
        group: ProcessGroup,
        status_map: dict[str, ProcessStatus],
    ) -> bool:
        """
        Return True only when ALL processes in *group* have finished.
        A process is finished if its status is either COMPLETE or BLOCKED.
        """
        for process in get_processes_by_group(group):
            status = status_map.get(process.process_id, ProcessStatus.NOT_STARTED)
            if status not in (ProcessStatus.COMPLETE, ProcessStatus.COMPLETED_WITH_WARNINGS):
                return False
        return True
