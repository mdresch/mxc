"""Tests for ProcessAgent and ProcessAgentFactory."""

from __future__ import annotations

import json
import pytest
import anyio  # noqa: F401 — required for anyio backend

from pmbok.agents.process_agent import ProcessAgent, _StubLLMClient
from pmbok.agents.factory import ProcessAgentFactory
from pmbok.exceptions import LLMParseError, ProcessExecutionError
from pmbok.models.enums import KnowledgeArea, ProcessGroup
from pmbok.models.pmbok import PMBOKProcess, ProjectArtifact


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def charter_process() -> PMBOKProcess:
    return PMBOKProcess(
        process_id="4.1",
        name="Develop Project Charter",
        knowledge_area=KnowledgeArea.INTEGRATION,
        process_group=ProcessGroup.INITIATING,
        prerequisites=[],
        expected_outputs=["Project Charter"],
    )


@pytest.fixture()
def multi_output_process() -> PMBOKProcess:
    return PMBOKProcess(
        process_id="5.2",
        name="Collect Requirements",
        knowledge_area=KnowledgeArea.SCOPE,
        process_group=ProcessGroup.PLANNING,
        prerequisites=["5.1"],
        expected_outputs=["Requirements Documentation", "Requirements Traceability Matrix"],
    )


def _make_artifact(run_id: str = "run-1", process_id: str = "4.1") -> ProjectArtifact:
    return ProjectArtifact(
        run_id=run_id,
        process_id=process_id,
        artifact_type="Project Charter",
        version=1,
        content={"title": "Test Project"},
        produced_by=process_id,
    )


# ---------------------------------------------------------------------------
# _build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_includes_process_name(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        prompt = agent._build_system_prompt()
        assert "Develop Project Charter" in prompt

    def test_includes_knowledge_area(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        prompt = agent._build_system_prompt()
        assert "Integration" in prompt

    def test_includes_process_group(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        prompt = agent._build_system_prompt()
        assert "Initiating" in prompt

    def test_includes_expected_outputs(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        prompt = agent._build_system_prompt()
        assert "Project Charter" in prompt

    def test_instructs_json_array_return(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        prompt = agent._build_system_prompt()
        assert "JSON array" in prompt


# ---------------------------------------------------------------------------
# _parse_output
# ---------------------------------------------------------------------------

class TestParseOutput:
    def test_valid_single_artifact(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        payload = json.dumps([
            {
                "run_id": "run-1",
                "process_id": "4.1",
                "artifact_type": "Project Charter",
                "version": 1,
                "content": {"title": "My Project"},
                "produced_by": "4.1",
            }
        ])
        artifacts = agent._parse_output(payload)
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "Project Charter"

    def test_valid_multiple_artifacts(self, multi_output_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=multi_output_process)
        payload = json.dumps([
            {
                "run_id": "run-1",
                "process_id": "5.2",
                "artifact_type": "Requirements Documentation",
                "version": 1,
                "content": {"data": "sample"},
                "produced_by": "5.2",
            },
            {
                "run_id": "run-1",
                "process_id": "5.2",
                "artifact_type": "Requirements Traceability Matrix",
                "version": 1,
                "content": {"data": "sample"},
                "produced_by": "5.2",
            },
        ])
        artifacts = agent._parse_output(payload)
        assert len(artifacts) == 2

    def test_invalid_json_raises_llm_parse_error(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        with pytest.raises(LLMParseError, match="JSON decode error"):
            agent._parse_output("not valid json {{{")

    def test_non_array_raises_llm_parse_error(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        with pytest.raises(LLMParseError, match="Expected a JSON array"):
            agent._parse_output(json.dumps({"key": "value"}))

    def test_malformed_item_raises_llm_parse_error(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        # Missing required fields
        with pytest.raises(LLMParseError, match="failed validation"):
            agent._parse_output(json.dumps([{"artifact_type": "Charter"}]))


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------

class TestExecute:
    @pytest.mark.anyio
    async def test_returns_non_empty_list(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        artifacts = await agent.execute(run_id="run-1", input_artifacts=[])
        assert len(artifacts) >= 1

    @pytest.mark.anyio
    async def test_stamps_run_id_on_artifacts(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        artifacts = await agent.execute(run_id="my-run-id", input_artifacts=[])
        for artifact in artifacts:
            assert artifact.run_id == "my-run-id"

    @pytest.mark.anyio
    async def test_stamps_process_id_on_artifacts(self, charter_process: PMBOKProcess) -> None:
        agent = ProcessAgent(process=charter_process)
        artifacts = await agent.execute(run_id="run-1", input_artifacts=[])
        for artifact in artifacts:
            assert artifact.process_id == "4.1"
            assert artifact.produced_by == "4.1"

    @pytest.mark.anyio
    async def test_passes_input_artifacts_as_context(self, charter_process: PMBOKProcess) -> None:
        """Verify that input artifacts are serialized and included in the LLM prompt."""
        captured_prompts: list[str] = []

        class CapturingClient:
            async def complete(self, prompt: str) -> str:
                captured_prompts.append(prompt)
                return json.dumps([
                    {
                        "run_id": "run-1",
                        "process_id": "4.1",
                        "artifact_type": "Project Charter",
                        "version": 1,
                        "content": {"data": "sample"},
                        "produced_by": "4.1",
                    }
                ])

        agent = ProcessAgent(process=charter_process, llm_client=CapturingClient())
        input_art = _make_artifact()
        await agent.execute(run_id="run-1", input_artifacts=[input_art])
        assert len(captured_prompts) == 1
        assert "Input Evidence" in captured_prompts[0] or "Input artifacts" in captured_prompts[0]

    @pytest.mark.anyio
    async def test_raises_process_execution_error_on_llm_failure(
        self, charter_process: PMBOKProcess
    ) -> None:
        class FailingClient:
            async def complete(self, prompt: str) -> str:
                raise RuntimeError("LLM unavailable")

        agent = ProcessAgent(process=charter_process, llm_client=FailingClient())
        with pytest.raises(ProcessExecutionError):
            await agent.execute(run_id="run-1", input_artifacts=[])

    @pytest.mark.anyio
    async def test_raises_process_execution_error_on_empty_output(
        self, charter_process: PMBOKProcess
    ) -> None:
        class EmptyClient:
            async def complete(self, prompt: str) -> str:
                return json.dumps([])  # empty array

        agent = ProcessAgent(process=charter_process, llm_client=EmptyClient())
        with pytest.raises(ProcessExecutionError, match="no artifacts"):
            await agent.execute(run_id="run-1", input_artifacts=[])

    @pytest.mark.anyio
    async def test_llm_parse_error_propagates(self, charter_process: PMBOKProcess) -> None:
        class BadJsonClient:
            async def complete(self, prompt: str) -> str:
                return "not json"

        agent = ProcessAgent(process=charter_process, llm_client=BadJsonClient())
        with pytest.raises((LLMParseError, ProcessExecutionError)):
            await agent.execute(run_id="run-1", input_artifacts=[])


# ---------------------------------------------------------------------------
# ProcessAgentFactory
# ---------------------------------------------------------------------------

class TestProcessAgentFactory:
    def test_create_returns_process_agent(self, charter_process: PMBOKProcess) -> None:
        factory = ProcessAgentFactory()
        agent = factory.create(charter_process)
        assert isinstance(agent, ProcessAgent)

    def test_create_wires_process(self, charter_process: PMBOKProcess) -> None:
        factory = ProcessAgentFactory()
        agent = factory.create(charter_process)
        assert agent._process is charter_process

    def test_create_wires_llm_client(self, charter_process: PMBOKProcess) -> None:
        class MyClient:
            async def complete(self, prompt: str) -> str:
                return "[]"

        client = MyClient()
        factory = ProcessAgentFactory(llm_client=client)
        agent = factory.create(charter_process)
        assert agent._llm is client

    def test_create_wires_artifact_store(self, charter_process: PMBOKProcess, tmp_path) -> None:
        from pmbok.storage.artifact_store import ArtifactStore
        store = ArtifactStore(tmp_path)
        factory = ProcessAgentFactory(artifact_store=store)
        agent = factory.create(charter_process)
        assert agent._artifact_store is store

    def test_factory_default_no_llm_uses_stub(self, charter_process: PMBOKProcess) -> None:
        factory = ProcessAgentFactory()
        agent = factory.create(charter_process)
        assert isinstance(agent._llm, _StubLLMClient)

    @pytest.mark.anyio
    async def test_factory_agent_executes_successfully(
        self, charter_process: PMBOKProcess
    ) -> None:
        factory = ProcessAgentFactory()
        agent = factory.create(charter_process)
        artifacts = await agent.execute(run_id="run-42", input_artifacts=[])
        assert len(artifacts) >= 1
        assert all(a.run_id == "run-42" for a in artifacts)
