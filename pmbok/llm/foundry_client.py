"""
Azure AI Foundry LLM client — implements the AgentClient protocol used by
IdeationEngine, BusinessCaseGenerator, and ProcessAgent.

Supports two modes (controlled by env vars):
  - Cloud:  Azure AI Foundry project endpoint  (USE_LOCAL_FOUNDRY=false)
  - Local:  Local AI Foundry / Phi-4 endpoint  (USE_LOCAL_FOUNDRY=true)

Usage:
    from pmbok.llm import create_llm_client

    client = create_llm_client()          # reads env vars automatically
    engine = IdeationEngine(llm_client=client)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from pmbok.exceptions import LLMError

logger = logging.getLogger(__name__)

# ── Environment variable names ────────────────────────────────────────────────
_PROJECT_ENDPOINT      = "PROJECT_ENDPOINT"       # e.g. https://<project>.services.ai.azure.com
_MODEL_DEPLOYMENT_NAME = "MODEL_DEPLOYMENT_NAME"  # e.g. gpt-4.1-mini
_AZURE_OPENAI_API_KEY  = "AZURE_OPENAI_API_KEY"
_LOCAL_FOUNDRY_URL     = "LOCAL_FOUNDRY_URL"      # e.g. http://127.0.0.1:50268
_LOCAL_MODEL_NAME      = "LOCAL_MODEL_DEPLOYMENT_NAME"  # e.g. phi-4
_USE_LOCAL_FOUNDRY     = "USE_LOCAL_FOUNDRY"      # "true" / "false"


def _use_local() -> bool:
    return os.getenv(_USE_LOCAL_FOUNDRY, "false").strip().lower() in ("1", "true", "yes")


class FoundryClient:
    """
    Thin async wrapper around the Azure AI Foundry / OpenAI-compatible chat API.

    Implements the AgentClient protocol:
        async def complete(self, prompt: str) -> str

    The response is expected to be a raw JSON string (the LLM is instructed
    to return only JSON in every prompt).  If the model wraps the JSON in
    markdown fences (```json ... ```) those are stripped automatically.
    """

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        use_local: bool | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        system_message: str = "You are a helpful project management assistant.",
    ) -> None:
        self._use_local = use_local if use_local is not None else _use_local()
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._system_message = system_message

        if self._use_local:
            self._endpoint = (endpoint or os.getenv(_LOCAL_FOUNDRY_URL, "http://127.0.0.1:50268")).rstrip("/")
            self._model    = model or os.getenv(_LOCAL_MODEL_NAME, "phi-4")
            self._api_key  = api_key or "local"
            self._mode     = "local"
        else:
            self._endpoint = (endpoint or os.getenv(_PROJECT_ENDPOINT, "")).rstrip("/")
            self._model    = model or os.getenv(_MODEL_DEPLOYMENT_NAME, "gpt-4.1-mini")
            self._api_key  = api_key or os.getenv(_AZURE_OPENAI_API_KEY)  # None → use DefaultAzureCredential
            self._mode     = "azure"

        logger.debug(
            "FoundryClient mode=%s endpoint=%s model=%s",
            self._mode, self._endpoint, self._model,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    async def complete(self, prompt: str) -> str:
        """
        Send *prompt* to the LLM and return the raw response string.

        The prompt already contains the full instruction (system + user content
        merged), so we send it as the user message and rely on the system
        message only for persona framing.
        """
        if self._use_local:
            return await self._complete_openai_compat(prompt)
        else:
            return await self._complete_azure_foundry(prompt)

    # ── Local Foundry (OpenAI-compatible /v1/chat/completions) ───────────────

    async def _complete_openai_compat(self, prompt: str) -> str:
        """Call a local OpenAI-compatible endpoint (Local AI Foundry / Ollama)."""
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise LLMError(
                "openai package not installed. Run: pip install openai"
            ) from exc

        client = AsyncOpenAI(
            base_url=f"{self._endpoint}/v1",
            api_key=self._api_key,
        )
        try:
            if "mistral" in self._model.lower():
                messages = [
                    {"role": "user", "content": f"{self._system_message}\n\n{prompt}"}
                ]
            else:
                messages = [
                    {"role": "system", "content": self._system_message},
                    {"role": "user",   "content": prompt},
                ]

            response = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            raw = response.choices[0].message.content or ""
            return self._strip_fences(raw)
        except Exception as exc:
            raise LLMError(f"Local Foundry call failed: {exc}") from exc

    # ── Azure AI Foundry ──────────────────────────────────────────────────────

    async def _complete_azure_foundry(self, prompt: str) -> str:
        """
        Call Azure AI Foundry using the OpenAI SDK.
        
        The project inference endpoint is OpenAI-compatible.
        """
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise LLMError(
                "openai package not installed. Run: pip install openai"
            ) from exc

        if not self._endpoint:
            raise LLMError(
                f"PROJECT_ENDPOINT env var is not set."
            )

        # Build the models endpoint URL for OpenAI client
        # If it's the project endpoint, we use it as base_url
        base_url = self._endpoint
        if not base_url.endswith("/v1"):
            # The project endpoint usually needs /openai/v1 for the OpenAI-compatible API
            if "/api/projects/" in base_url and not base_url.endswith("/openai"):
                 base_url = base_url.rstrip("/") + "/openai/v1"
            elif not base_url.endswith("/v1"):
                 base_url = base_url.rstrip("/") + "/v1"

        client = AsyncOpenAI(
            base_url=base_url,
            api_key=self._api_key,
        )

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._system_message},
                    {"role": "user",   "content": prompt},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            raw = response.choices[0].message.content or ""
            return self._strip_fences(raw)
        except Exception as exc:
            raise LLMError(f"Azure AI Foundry (OpenAI mode) call failed: {exc}") from exc

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences that some models wrap JSON in."""
        import re
        text = text.strip()
        
        # Try to find exactly {...} or [...] blocks
        obj_match = re.search(r'\{.*\}', text, re.DOTALL)
        arr_match = re.search(r'\[.*\]', text, re.DOTALL)
        
        if obj_match and arr_match:
            return obj_match.group(0) if obj_match.start() < arr_match.start() else arr_match.group(0)
        elif obj_match:
            return obj_match.group(0)
        elif arr_match:
            return arr_match.group(0)
            
        if text.startswith("```"):
            # strip opening fence (```json or ```)
            text = text[text.index("\n") + 1:] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        return text.strip()


# ── Factory function ──────────────────────────────────────────────────────────

def create_llm_client(
    *,
    endpoint: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    use_local: bool | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    system_message: str = "You are a helpful project management assistant.",
) -> FoundryClient:
    """
    Factory that creates a FoundryClient from env vars (with optional overrides).

    Environment variables (see .env):
        USE_LOCAL_FOUNDRY          true/false
        LOCAL_FOUNDRY_URL          http://127.0.0.1:50268
        LOCAL_MODEL_DEPLOYMENT_NAME  phi-4
        PROJECT_ENDPOINT           https://<project>.services.ai.azure.com
        MODEL_DEPLOYMENT_NAME      gpt-4.1-mini

    Example — use whatever the .env says:
        client = create_llm_client()

    Example — force cloud with a specific model:
        client = create_llm_client(use_local=False, model="gpt-4.1")

    Example — force local Phi-4:
        client = create_llm_client(use_local=True)
    """
    return FoundryClient(
        endpoint=endpoint,
        model=model,
        api_key=api_key,
        use_local=use_local,
        temperature=temperature,
        max_tokens=max_tokens,
        system_message=system_message,
    )
