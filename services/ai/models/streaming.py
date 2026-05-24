"""
SSE (Server-Sent Events) streaming handler for OpenRouter.
"""

import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


async def stream_sse(response) -> AsyncGenerator[dict, None]:
    """
    Parse streaming response from OpenRouter and yield JSON events.

    Parameters
    ----------
    response : httpx.Response
        The streaming response object.

    Yields
    ------
    dict
        Parsed JSON content from each SSE chunk.
    """
    async for line in response.aiter_lines():
        if not line.strip():
            continue

        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break

            try:
                chunk = json.loads(data)
                yield chunk
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse SSE chunk: {e}, data: {data[:100]}")
                continue