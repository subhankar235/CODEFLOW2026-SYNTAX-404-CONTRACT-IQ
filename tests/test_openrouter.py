"""
Tests for OpenRouter client.
"""

import os
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from services.ai.models.openrouter_client import (
    OpenRouterClient,
    OpenRouterError,
    AuthenticationError,
    RateLimitError,
    APIError,
)
from services.ai.models.model_config import PRIMARY_MODEL, FAST_MODEL


os.environ["OPENROUTER_API_KEY"] = "test_api_key"


class TestModelConfig:
    """Test model configuration constants."""

    def test_primary_model(self):
        assert PRIMARY_MODEL == "meta-llama/llama-3.3-70b-instruct"

    def test_fast_model(self):
        assert FAST_MODEL == "google/gemini-2.0-flash-001"


class TestOpenRouterClient:
    """Test OpenRouter client functionality."""

    @pytest.fixture
    def client(self):
        return OpenRouterClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_non_streaming_primary_model(self, client):
        """Test non-streaming call to PRIMARY_MODEL returns valid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"result": "test"}'}}
            ]
        }

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.chat(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say hello",
                model=PRIMARY_MODEL,
                stream=False,
            )

            assert "choices" in result
            assert len(result["choices"]) > 0
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            assert "result" in parsed

    @pytest.mark.asyncio
    async def test_non_streaming_fast_model(self, client):
        """Test non-streaming call to FAST_MODEL returns valid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"result": "fast test"}'}}
            ]
        }

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.chat(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say hello",
                model=FAST_MODEL,
                stream=False,
            )

            assert "choices" in result
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            assert "result" in parsed

    @pytest.mark.asyncio
    async def test_streaming_yields_tokens(self, client):
        """Test streaming call yields tokens progressively."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: {"choices": [{"delta": {"content": " World"}}]}'
            yield 'data: [DONE]'

        mock_response.aiter_lines = mock_aiter_lines

        async def mock_request(*args, **kwargs):
            return mock_response

        client._client.request = mock_request

        result = await client.chat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say hello",
            model=PRIMARY_MODEL,
            stream=True,
        )

        chunks = []
        async for chunk in result:
            chunks.append(chunk)

        assert len(chunks) >= 2
        assert "choices" in chunks[0]

    @pytest.mark.asyncio
    async def test_rate_limit_triggers_retry(self, client):
        """Test simulated 429 response triggers retry with backoff."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response_429, mock_response_success]

            result = await client.chat(
                system_prompt="Test",
                user_prompt="Test",
                model=PRIMARY_MODEL,
            )

            assert mock_request.call_count == 2
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_error(self, client):
        """Test invalid API key returns clear error message."""
        client.api_key = "invalid_key"

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(AuthenticationError) as exc_info:
                await client.chat(
                    system_prompt="Test",
                    user_prompt="Test",
                    model=PRIMARY_MODEL,
                )

            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_error(self):
        """Test missing API key raises AuthenticationError."""
        client = OpenRouterClient(api_key="")

        with pytest.raises(AuthenticationError) as exc_info:
            await client.chat(
                system_prompt="Test",
                user_prompt="Test",
                model=PRIMARY_MODEL,
            )

        assert "API key is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_server_error_triggers_retry(self, client):
        """Test 5xx errors trigger retry."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_response_500, mock_response_success]

            result = await client.chat(
                system_prompt="Test",
                user_prompt="Test",
                model=PRIMARY_MODEL,
            )

            assert mock_request.call_count == 2
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_chat_json_method(self, client):
        """Test chat_json returns parsed JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": '{"key": "value", "number": 42}'}}
            ]
        }

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.chat_json(
                system_prompt="You are a JSON generator.",
                user_prompt='Generate {"key": "value"}',
                model=PRIMARY_MODEL,
            )

            assert result == {"key": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client can be used as async context manager."""
        async with OpenRouterClient(api_key="test") as client:
            assert client.api_key == "test"


async def run_manual_test():
    """Manual test to verify actual API calls work (requires valid API key)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("SKIP: No OPENROUTER_API_KEY set")
        return

    async with OpenRouterClient(api_key=api_key) as client:
        print("\n=== Test 1: Non-streaming PRIMARY_MODEL ===")
        result = await client.chat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, world!' in exactly those words.",
            model=PRIMARY_MODEL,
            stream=False,
        )
        print(f"Response: {result['choices'][0]['message']['content']}")

        print("\n=== Test 2: Non-streaming FAST_MODEL ===")
        result = await client.chat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, world!' in exactly those words.",
            model=FAST_MODEL,
            stream=False,
        )
        print(f"Response: {result['choices'][0]['message']['content']}")

        print("\n=== Test 3: Streaming ===")
        async for chunk in client.chat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Count from 1 to 3.",
            model=PRIMARY_MODEL,
            stream=True,
        ):
            if chunk.get("choices") and chunk["choices"][0].get("delta"):
                content = chunk["choices"][0]["delta"].get("content", "")
                print(content, end="", flush=True)
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(run_manual_test())
    else:
        pytest.main([__file__, "-v"])