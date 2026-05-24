# Streaming service: the Redis pub/sub publisher layer.
# The Celery worker imports ``publish_clause`` and ``publish_complete`` here
# to push real-time updates into the channel that the SSE endpoint is reading.

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_CHANNEL_PREFIX = "scan:"

# ---------------------------------------------------------------------------
# Synchronous Redis client (used by Celery workers — no async event loop)
# ---------------------------------------------------------------------------


def _get_sync_client() -> redis.Redis:
    """Return a synchronous Redis client from the configured URL."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


# ---------------------------------------------------------------------------
# Public publisher functions
# ---------------------------------------------------------------------------


def publish_clause(job_id: str, clause_data: Dict[str, Any]) -> None:
    """
    Publish a single processed clause to the job's Redis channel.

    Called by the Celery task immediately after each clause finishes the
    full pipeline (rule engine + LLM risk + consequence + power + precedent).
    Results stream to the browser in real-time rather than all at once.

    Args:
        job_id:       UUID string of the ScanJob.
        clause_data:  Serialisable dict of the ClauseResult (to_dict()).
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps({"type": "clause", "data": clause_data})
    try:
        client = _get_sync_client()
        client.publish(channel, message)
        logger.debug("Published clause to %s", channel)
    except redis.RedisError as exc:
        # Non-fatal: SSE stream misses this clause update; DB still stores it.
        logger.error("Redis publish_clause failed for job %s: %s", job_id, exc)


def publish_progress(job_id: str, progress_pct: int, step_name: str = "") -> None:
    """
    Publish a progress update so the frontend progress bar can advance.

    Args:
        job_id:       UUID string of the ScanJob.
        progress_pct: Integer 0-100.
        step_name:    Human-readable pipeline step label (optional).
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps(
        {
            "type": "progress",
            "progress_pct": progress_pct,
            "step": step_name,
        }
    )
    try:
        client = _get_sync_client()
        client.publish(channel, message)
        logger.debug("Published progress %d%% to %s", progress_pct, channel)
    except redis.RedisError as exc:
        logger.error("Redis publish_progress failed for job %s: %s", job_id, exc)


def publish_complete(job_id: str, summary: Dict[str, Any] | None = None) -> None:
    """
    Publish the terminal ``complete`` event, signalling the SSE stream to close.

    The SSE endpoint generator returns on receipt of this message, cleanly
    ending the HTTP response body.  Must be the LAST message published.

    Args:
        job_id:   UUID string of the ScanJob.
        summary:  Optional high-level summary dict to send with the event.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps(
        {
            "type": "complete",
            "summary": summary or {},
        }
    )
    try:
        client = _get_sync_client()
        client.publish(channel, message)
        logger.info("Published complete event to %s", channel)
    except redis.RedisError as exc:
        logger.error("Redis publish_complete failed for job %s: %s", job_id, exc)


def publish_error(job_id: str, error_message: str) -> None:
    """
    Publish an error event so the frontend can display a failure state.

    Args:
        job_id:         UUID string of the ScanJob.
        error_message:  Human-readable description of what went wrong.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps(
        {
            "type": "error",
            "detail": error_message,
        }
    )
    try:
        client = _get_sync_client()
        client.publish(channel, message)
        logger.error("Published error event to %s: %s", channel, error_message)
    except redis.RedisError as exc:
        logger.error("Redis publish_error failed for job %s: %s", job_id, exc)
