"""Streaming service for publishing clause results to Redis pub/sub."""

import json
import logging
import os
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "rediss://localhost:6379")
REDIS_CHANNEL_PREFIX = "scan:"


def _get_redis_client() -> redis.Redis:
    """Get a Redis client instance."""
    return redis.from_url(REDIS_URL, decode_responses=True)


def publish_clause_result(job_id: str, clause_result: Dict[str, Any]) -> None:
    """
    Publish a single clause result to the scan job's Redis channel.
    This is called by the Celery worker after each clause is processed.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps({"type": "clause", "data": clause_result})
    try:
        client = _get_redis_client()
        client.publish(channel, message)
        client.close()
        logger.debug("Published clause to channel %s", channel)
    except Exception as e:
        logger.error("Failed to publish clause to Redis: %s", e)


def publish_progress(job_id: str, progress_pct: int, step: str = "") -> None:
    """
    Publish a progress update to the scan job's Redis channel.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps({
        "type": "progress",
        "progress_pct": progress_pct,
        "step": step
    })
    try:
        client = _get_redis_client()
        client.publish(channel, message)
        client.close()
        logger.debug("Published progress %d%% to channel %s", progress_pct, channel)
    except Exception as e:
        logger.error("Failed to publish progress to Redis: %s", e)


def publish_complete(job_id: str, summary: Optional[Dict[str, Any]] = None) -> None:
    """
    Publish the terminal 'complete' event to signal scan completion.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps({
        "type": "complete",
        "summary": summary or {}
    })
    try:
        client = _get_redis_client()
        client.publish(channel, message)
        client.close()
        logger.info("Published complete event to channel %s", channel)
    except Exception as e:
        logger.error("Failed to publish complete to Redis: %s", e)


def publish_error(job_id: str, error_detail: str) -> None:
    """
    Publish an error event to signal scan failure.
    """
    channel = f"{REDIS_CHANNEL_PREFIX}{job_id}"
    message = json.dumps({
        "type": "error",
        "detail": error_detail
    })
    try:
        client = _get_redis_client()
        client.publish(channel, message)
        client.close()
        logger.error("Published error event to channel %s: %s", channel, error_detail)
    except Exception as e:
        logger.error("Failed to publish error to Redis: %s", e)