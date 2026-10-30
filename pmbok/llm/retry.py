"""
Shared tenacity retry helper for LLM calls in engines and agents.

Retries on LLMError (network/auth/rate-limit) and LLMParseError
(bad JSON, hollow content) — both are transient and worth retrying.
ProcessExecutionError is also included so the orchestrator's retry
config stays consistent with the engine-level retry.
"""

from __future__ import annotations

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pmbok.exceptions import LLMError, LLMParseError, ProcessExecutionError

# Same schedule as the orchestrator: 2 s → 4 s → give up
LLM_RETRY_CONFIG = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((LLMParseError, LLMError, ProcessExecutionError)),
    reraise=True,   # re-raise the original exception after exhausting retries
)


async def call_with_retry(coro_fn, *args, **kwargs):
    """
    Call an async function with LLM retry logic.

    Usage:
        result = await call_with_retry(self._llm.complete, prompt)

    On the third failure the original LLMParseError / LLMError is re-raised
    so the caller (engine or orchestrator) can handle it.
    """
    async for attempt in AsyncRetrying(**LLM_RETRY_CONFIG):
        with attempt:
            return await coro_fn(*args, **kwargs)
