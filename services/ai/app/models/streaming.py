"""
services/ai/models/streaming.py
# 🔹 3. streaming.py → LIVE RESPONSE HANDLER

# 👉 Used when AI sends response piece by piece

# Instead of:

# FULL RESPONSE

# You get:

# word1 → word2 → word3 → ...

SSE streaming handler for OpenRouter responses.
Consumes an async token stream and yields structured ParsedStreamEvent objects,
then assembles the final complete text when the stream is exhausted.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

@dataclass
class TokenEvent:
    """A single content token delta."""
    token: str
    accumulated: str   # full text assembled so far


@dataclass
class StreamComplete:
    """Emitted once when the stream is fully consumed."""
    full_text: str
    token_count: int


# ---------------------------------------------------------------------------
# Public streaming handler
# ---------------------------------------------------------------------------

async def handle_stream(
    token_iterator: AsyncIterator[str],
) -> AsyncIterator[TokenEvent | StreamComplete]:
    """
    Wrap a raw token iterator (from OpenRouterClient.stream) and yield:
      - TokenEvent for every incremental token
      - StreamComplete once the iterator is exhausted

    Usage
    -----
    async for event in handle_stream(client.stream(...)):
        if isinstance(event, TokenEvent):
            send_to_websocket(event.token)
        elif isinstance(event, StreamComplete):
            store_result(event.full_text)
    """
    accumulated_parts: list[str] = []
    token_count = 0

    async for token in token_iterator:
        accumulated_parts.append(token)
        token_count += 1
        accumulated = "".join(accumulated_parts)
        logger.debug("Stream token #%d: %r", token_count, token[:40])
        yield TokenEvent(token=token, accumulated=accumulated)

    full_text = "".join(accumulated_parts)
    logger.debug("Stream complete | tokens=%d chars=%d", token_count, len(full_text))
    yield StreamComplete(full_text=full_text, token_count=token_count)


async def collect_stream(token_iterator: AsyncIterator[str]) -> str:
    """
    Convenience helper: consume a token stream and return the full text string.
    Does not yield intermediate events.
    """
    parts: list[str] = []
    async for token in token_iterator:
        parts.append(token)
    return "".join(parts)


async def collect_stream_as_json(token_iterator: AsyncIterator[str]) -> Optional[dict]:
    """
    Consume a token stream and parse the assembled text as JSON.
    Returns None and logs a warning on parse failure.
    """
    text = await collect_stream(token_iterator)
    text = text.strip()
    # Strip markdown code fences if the model wrapped the JSON
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines()
            if not line.strip().startswith("```")
        ).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Stream JSON parse failed: %s | raw=%s", exc, text[:200])
        return None