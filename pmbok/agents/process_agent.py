"""Process Agent — executes a single PMBOK process via an LLM agent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Protocol

from pmbok.audit.prompt_optimizer import prompt_optimizer, PromptOptimization
from pmbok.audit.quality_control import quality_controller
from pmbok.exceptions import ProcessExecutionError, LLMParseError, LLMError
from pmbok.config import settings
from pmbok.models.enums import AuditMode
from pmbok.models.pmbok import PMBOKProcess, ProjectArtifact
from pmbok.llm.validator import _strip_fences, _extract_json, validate_llm_response

if TYPE_CHECKING:
    from pmbok.storage.artifact_store import ArtifactStore


# ---------------------------------------------------------------------------
# Protocol — keeps the agent decoupled from a concrete LLM client.
# ---------------------------------------------------------------------------

class AgentClient(Protocol):
    async def complete(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the raw response string."""
        ...


# ---------------------------------------------------------------------------
# Stub client — returns a valid JSON array with one artifact per expected output.
# ---------------------------------------------------------------------------

class _StubLLMClient:
    """Returns a minimal valid JSON array of ProjectArtifact objects for testing."""

    async def complete(self, prompt: str) -> str:  # noqa: ARG002
        # Extract expected outputs from the prompt to build realistic stubs.
        # The prompt contains a line like: "Expected outputs: ['Output A', 'Output B']"
        outputs: list[str] = []
        for line in prompt.splitlines():
            if line.startswith("Expected outputs:"):
                try:
                    outputs = json.loads(line.split(":", 1)[1].strip().replace("'", '"'))
                except (json.JSONDecodeError, IndexError):
                    pass
                break

        if not outputs:
            outputs = ["Artifact"]

        artifacts = [
            {
                "run_id": "stub-run",
                "process_id": "0.0",
                "artifact_type": output,
                "version": 1,
                "content": {"description": f"Stub content for {output}"},
                "produced_by": "0.0",
            }
            for output in outputs
        ]
        return json.dumps(artifacts)


# ---------------------------------------------------------------------------
# ProcessAgent
# ---------------------------------------------------------------------------

class ProcessAgent:
    """Executes a single PMBOK process using an LLM agent."""

    def __init__(
        self,
        process: PMBOKProcess,
        llm_client: AgentClient | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self._process = process
        self._llm = llm_client if llm_client is not None else _StubLLMClient()
        self._artifact_store = artifact_store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        run_id: str,
        input_artifacts: list[ProjectArtifact],
        system_message_override: str | None = None,
        version: int = 1,
        project_context: dict[str, Any] | None = None,
    ) -> list[ProjectArtifact]:
        """Run the PMBOK process.

        Steps:
        1. Build the system prompt (or use override if provided).
        2. Serialize input artifacts as context and append to the prompt.
        3. Save the raw prompt (versioned).
        4. Call the LLM.
        5. Parse the response into ProjectArtifact objects.
        6. Run quality control audit on generated content.
        7. Set run_id, process_id, and version on each artifact.
        8. Return the non-empty list.

        Parameters
        ----------
        run_id : str
            The project run ID.
        input_artifacts : list[ProjectArtifact]
            Input artifacts from prerequisite processes.
        system_message_override : str | None
            Optional enhanced system prompt for regeneration/quality improvement.
            When provided, overrides the standard system prompt.
        version : int
            The artifact version (defaults to 1).
        project_context : dict | None
            Project context (ideation, business case, charter) for quality control.

        Raises ProcessExecutionError on any unrecoverable failure.
        """
        try:
            # Project context fallback for unanchored testing / callers
            if project_context is None:
                project_context = {"title": "Default PMBOK Project", "objectives": ["Standard PMBOK Execution"]}
            elif not project_context.get("title"):
                project_context["title"] = "Default PMBOK Project" 

            # Use override if provided (regeneration), else standard prompt
            system_prompt = (
                system_message_override
                if system_message_override is not None
                else self._build_system_prompt(project_context)
            )
            context = self._serialize_input_artifacts(input_artifacts)
            full_prompt = f"{system_prompt}\n\n{context}" if context else system_prompt

            # Save the prompt before processing
            if self._artifact_store is not None:
                await self._artifact_store.save_prompt(
                    run_id, self._process.process_id, full_prompt, version=version, process_name=self._process.name
                )

            raw_response = await self._llm.complete(full_prompt)
            artifacts = self._parse_output(raw_response)

            # Stamp artifacts with metadata (run_id, process_id, version)
            stamped = self._stamp_artifacts(run_id, artifacts, version)

            # Preliminary Save: Always persist what was generated for traceability
            if self._artifact_store is not None:
                for artifact in stamped:
                    await self._artifact_store.save(artifact, process_name=self._process.name)

            # Run quality control audit if project context is available
            if project_context is not None:
                qc_result = quality_controller.audit_output_quality(
                    input_artifacts, stamped, project_context
                )

                # Log quality control results
                if self._artifact_store is not None:
                    await self._artifact_store.save_quality_audit(
                        run_id, self._process.process_id, qc_result, version=version, process_name=self._process.name
                    )

                # If quality control fails, handle based on AuditMode
                if not qc_result.is_passing:
                    error_msg = f"Quality control failed for process {self._process.process_id}: {qc_result.issues}"
                    
                    # Generate optimized prompt for potential regeneration
                    optimization = prompt_optimizer.generate_optimized_prompt(
                        full_prompt, qc_result, project_context
                    )
                    
                    # Save optimization details
                    await self._save_optimization_details(
                        run_id, self._process.process_id, optimization, version, process_name=self._process.name
                    )
                    
                    if settings.AUDIT_MODE == AuditMode.BLOCKING:
                        # Raise error - artifacts are already persisted but won't be "finalized" by orchestrator
                        raise ProcessExecutionError(
                            f"{error_msg}\nOptimized prompt available for regeneration."
                        )
                    else:
                        # Advisory mode: just log a warning and continue
                        import logging
                        logging.getLogger(__name__).warning(
                            f"QC failed for process {self._process.process_id} — "
                            f"continuing due to ADVISORY mode. Issues: {qc_result.issues}"
                        )

            if not stamped:
                raise ProcessExecutionError(
                    f"Process {self._process.process_id} produced no artifacts."
                )

            return stamped

        except (ProcessExecutionError, LLMParseError):
            raise
        except Exception as exc:
            raise ProcessExecutionError(
                f"Process {self._process.process_id} failed: {exc}"
            ) from exc

    def _stamp_artifacts(
        self, run_id: str, artifacts: list[ProjectArtifact], version: int
    ) -> list[ProjectArtifact]:
        """Inject metadata into generated artifacts."""
        stamped = []
        for artifact in artifacts:
            s_artifact = artifact.model_copy(
                update={
                    "run_id": run_id,
                    "process_id": self._process.process_id,
                    "produced_by": self._process.process_id,
                    "version": version,
                }
            )
            stamped.append(s_artifact)
        return stamped

    async def _save_optimization_details(
        self, run_id: str, process_id: str, optimization: PromptOptimization, version: int, process_name: str | None = None
    ) -> None:
        """Save prompt optimization details to the artifact store."""
        if self._artifact_store is not None:
            from datetime import datetime
            optimization_data = {
                "original_prompt_preview": optimization.original_prompt[:200] + "...",
                "optimized_prompt_preview": optimization.optimized_prompt[:200] + "...",
                "improvements": optimization.improvements,
                "expected_quality_improvement": optimization.expected_quality_improvement,
                "optimization_reason": optimization.optimization_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._artifact_store.save_optimization_details(
                run_id, process_id, optimization_data, version, process_name=process_name
            )

    def _render_project_overview(self, project_context: dict[str, Any] | None) -> str:
        """Render a canonical project overview block to anchor the LLM."""
        if not project_context:
            return ""

        title = project_context.get("title", "Unknown Project")
        objectives = project_context.get("objectives", [])

        lines = [
            "### Project Overview",
            f"- **Project Title**: {title}",
        ]

        if objectives:
            lines.append("- **Key Objectives**:")
            for i, obj in enumerate(objectives, 1):
                lines.append(f"  {i}. {obj}")

        lines.extend([
            "- **Domain / Initiative**: ADPA",
            "- **Thematic Alignment**: lifecycle templates, governance, auditability, traceability, PMBOK-aligned outputs",
            ""
        ])

        return "\n".join(lines)

    def _build_system_prompt(self, project_context: dict[str, Any] | None = None) -> str:
        """Construct agent instructions specific to this PMBOK process."""
        p = self._process
        outputs_str = json.dumps(p.expected_outputs)

        overview = self._render_project_overview(project_context)

        from datetime import datetime
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        prompt = [
            "# Role & Behaviour",
            "You are a PMBOK project management assistant executing a specific process.",
            f"**Current Date**: {now}",
            "**Identity Anchor**: You must ensure all generated content remains strictly within the project context defined below.",
            "",
            overview,
            "# Process Task",
            f"- **Process Name**: {p.name}",
            f"- **Knowledge Area**: {p.knowledge_area.value}",
            f"- **Process Group**: {p.process_group.value}",
            f"- **Expected Outputs**: {outputs_str}",
            "",
            "# Instructions & Negative Guardrails",
            "- **DO NOT** produce generic content unrelated to the named project.",
            "- **DO NOT** substitute generic software/system examples (like ERP or generic HR systems) unless explicitly present in source inputs.",
            "- All outputs must align with the Project Title and Key Objectives.",
            "- If input artifacts are sparse, remain project-specific rather than inventing unrelated domains.",
            "",
            "# Output Expectations & Schema",
            "Return ONLY a JSON array of ProjectArtifact objects — no markdown fences, no extra text.",
            "Each object must follow this structure:",
            "[",
            "  {",
            '    "run_id": "<string>",',
            '    "process_id": "<string>",',
            '    "artifact_type": "<string>",',
            '    "version": 1,',
            '    "content": {<dictionary - MUST be a JSON object, NEVER a raw list>},',
            '    "produced_by": "<process_id>"',
            "  },",
            "  ...",
            "]",
            "",
            "**CRITICAL**: The 'content' field MUST be a JSON object (dictionary). Wrap lists in a key (e.g., {\"items\": [...]}).",
            f"Produce exactly one artifact per expected output: {p.expected_outputs}"
        ]

        return "\n".join(prompt)

    def _parse_output(self, llm_response: str) -> list[ProjectArtifact]:
        """
        Extract and quality-check ProjectArtifact objects from the LLM response.

        Raises LLMParseError on structural or semantic failures.
        Also verifies that every expected output has a corresponding artifact.
        """
        snippet = llm_response[:500]

        # Extract JSON array (handles prose wrapping and fences)
        cleaned = _strip_fences(llm_response)
        cleaned = _extract_json(cleaned, snippet, "_parse_output")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMParseError(
                f"[_parse_output] JSON decode error: {exc}. "
                f"Raw (first 500 chars): {snippet!r}"
            ) from exc

        if not isinstance(data, list):
            raise LLMParseError(
                f"[_parse_output] Expected a JSON array, got {type(data).__name__}. "
                f"Raw (first 500 chars): {snippet!r}"
            )

        artifacts: list[ProjectArtifact] = []
        for i, item in enumerate(data):
            # validate_llm_response handles per-item quality checks
            artifact = validate_llm_response(
                json.dumps(item),
                ProjectArtifact,
                location=f"_parse_output[{i}]",
            )
            artifacts.append(artifact)

        # Completeness check: every expected output should be present
        produced_types = {a.artifact_type for a in artifacts}
        missing = [o for o in self._process.expected_outputs if o not in produced_types]
        if missing:
            import logging
            logging.getLogger(__name__).warning(
                "process=%s missing expected outputs: %s",
                self._process.process_id, missing,
            )
            # Not a hard failure — the LLM may use slightly different names.
            # Log the gap; the orchestrator will still store what was produced.

        return artifacts

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _serialize_input_artifacts(
        self, input_artifacts: list[ProjectArtifact]
    ) -> str:
        """Serialize input artifacts as a JSON context block."""
        if not input_artifacts:
            return "# Input Artifacts\nNo prerequisite artifacts available for this process. Rely strictly on the Project Overview and Process Task."

        items = [a.model_dump(mode="json") for a in input_artifacts]
        return (
            "# Input Evidence from Prerequisite Processes\n"
            + json.dumps(items, indent=2)
        )
