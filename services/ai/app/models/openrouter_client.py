"""
services/ai/models/openrouter_client.py
# 🔹 1. openrouter_client.py → THE CALLER (main thing)

👉 This file is the one that talks to AI
Async OpenRouter API client built on httpx.
Supports standard (non-streaming) and streaming (SSE) request modes.
Implements exponential-backoff retry on 429 / 5xx responses.
"""

from __future__ import annotations
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)
import asyncio
import json
import logging
import os
from typing import Any, AsyncIterator, Optional

import httpx

from .model_config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    MAX_RETRIES,
    BACKOFF_BASE,
    RETRYABLE_STATUS_CODES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHAT_ENDPOINT = f"{OPENROUTER_BASE_URL}/chat/completions"

_API_KEY_ENV = "OPENROUTER_API_KEY"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OpenRouterError(Exception):
    """Base error for all OpenRouter client failures."""


class AuthenticationError(OpenRouterError):
    """Raised when the API key is missing or rejected (401/403)."""


class RateLimitError(OpenRouterError):
    """Raised when the rate limit is exceeded and retries are exhausted."""


class ServerError(OpenRouterError):
    """Raised when the server returns 5xx after all retries."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    key = os.getenv(_API_KEY_ENV, "").strip()
    if not key:
        raise AuthenticationError(
            f"OpenRouter API key not found. "
            f"Set the {_API_KEY_ENV!r} environment variable."
        )
    return key


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("APP_BASE_URL", "https://localhost"),
        "X-Title": os.getenv("APP_NAME", "ContractScan"),
    }


def _build_payload(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    stream: bool,
    json_mode: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    return payload


# ---------------------------------------------------------------------------
# Core client
# ---------------------------------------------------------------------------

class OpenRouterClient:
    """
    Async client for the OpenRouter chat-completions endpoint.

    Parameters
    ----------
    timeout   : httpx timeout in seconds (default: 60)
    api_key   : override the env-var lookup (useful in tests)
    """

    def __init__(
        self,
        timeout: float = 60.0,
        api_key: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or _get_api_key()
        self._timeout = httpx.Timeout(timeout)

    # ------------------------------------------------------------------
    # Non-streaming call
    # ------------------------------------------------------------------

    async def complete(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        json_mode: bool = False,
    ) -> dict[str, Any]:
        """
        Send a non-streaming completion request.

        Returns the raw OpenRouter response dict.
        Raises OpenRouterError subclasses on unrecoverable failure.
        """
        payload = _build_payload(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
            json_mode=json_mode,
        )

        logger.debug(
            "OpenRouter request | model=%s json_mode=%s payload_size=%d",
            model,
            json_mode,
            len(json.dumps(payload)),
        )

        last_exc: Exception = RuntimeError("No attempts made")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(MAX_RETRIES + 1):
                try:
                    response = await client.post(
                        CHAT_ENDPOINT,
                        headers=_build_headers(self._api_key),
                        json=payload,
                    )
                except httpx.RequestError as exc:
                    logger.warning("OpenRouter network error (attempt %d): %s", attempt + 1, exc)
                    last_exc = exc
                    await self._backoff(attempt)
                    continue

                logger.debug(
                    "OpenRouter response | status=%d attempt=%d",
                    response.status_code,
                    attempt + 1,
                )

                # Auth errors – do not retry
                if response.status_code in (401, 403):
                    raise AuthenticationError(
                        f"Authentication failed (HTTP {response.status_code}). "
                        "Check your OPENROUTER_API_KEY."
                    )

                # Retryable errors
                if response.status_code in RETRYABLE_STATUS_CODES:
                    logger.warning(
                        "OpenRouter retryable error %d (attempt %d/%d)",
                        response.status_code,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    last_exc = self._status_exc(response)
                    if attempt < MAX_RETRIES:
                        await self._backoff(attempt)
                        continue
                    raise last_exc

                response.raise_for_status()

                data: dict[str, Any] = response.json()
                logger.debug(
                    "OpenRouter success | model=%s usage=%s",
                    data.get("model"),
                    data.get("usage"),
                )
                return data

        raise last_exc  # exhausted retries via network errors

    # ------------------------------------------------------------------
    # Streaming call
    # ------------------------------------------------------------------

    async def stream(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> AsyncIterator[str]:
        """
        Send a streaming completion request.

        Yields raw content-delta strings as they arrive from the SSE stream.
        The caller is responsible for assembling the full response.
        """
        payload = _build_payload(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            json_mode=False,   # streaming + json_object not supported by all models
        )

        logger.debug("OpenRouter stream request | model=%s", model)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                CHAT_ENDPOINT,
                headers=_build_headers(self._api_key),
                json=payload,
            ) as response:
                if response.status_code in (401, 403):
                    raise AuthenticationError(
                        f"Authentication failed (HTTP {response.status_code})."
                    )
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        raw = line[len("data: "):]
                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            logger.debug("Non-JSON SSE line: %s", raw)
                            continue

                        delta = (
                            event.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if delta:
                            yield delta

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    async def _backoff(attempt: int) -> None:
        wait = BACKOFF_BASE ** attempt
        logger.debug("Backoff %.2fs before retry attempt %d", wait, attempt + 2)
        await asyncio.sleep(wait)

    @staticmethod
    def _status_exc(response: httpx.Response) -> OpenRouterError:
        if response.status_code == 429:
            return RateLimitError(
                f"Rate limit exceeded (HTTP 429). "
                f"Retry-After: {response.headers.get('Retry-After', 'unknown')}"
            )
        return ServerError(f"Server error HTTP {response.status_code}: {response.text[:200]}")


# ---------------------------------------------------------------------------
# Module-level convenience helpers (mirrors boto3 / openai SDK style)
# ---------------------------------------------------------------------------

_default_client: Optional[OpenRouterClient] = None


def _client() -> OpenRouterClient:
    global _default_client
    if _default_client is None:
        _default_client = OpenRouterClient()
    return _default_client


async def complete(**kwargs: Any) -> dict[str, Any]:
    """Module-level shortcut for non-streaming completion."""
    return await _client().complete(**kwargs)


async def stream(**kwargs: Any) -> AsyncIterator[str]:
    """Module-level shortcut for streaming completion."""
    return _client().stream(**kwargs)