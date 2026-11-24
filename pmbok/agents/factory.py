"""ProcessAgentFactory — creates ProcessAgent instances for PMBOK processes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pmbok.agents.process_agent import AgentClient, ProcessAgent
from pmbok.models.pmbok import PMBOKProcess

if TYPE_CHECKING:
    from pmbok.storage.artifact_store import ArtifactStore


class ProcessAgentFactory:
    """Creates ProcessAgent instances wired with a shared LLM client and artifact store."""

    def __init__(
        self,
        llm_client: AgentClient | None = None,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._artifact_store = artifact_store

    def create(self, process: PMBOKProcess) -> ProcessAgent:
        """Create a new ProcessAgent for the given PMBOK process."""
        return ProcessAgent(
            process=process,
            llm_client=self._llm_client,
            artifact_store=self._artifact_store,
        )
