"""
Tests for Step 6.4 — SSE Streaming Endpoint.
"""

import pytest
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'services', 'api'))

from app.api.v1.endpoints.streaming import (
    router,
    HEARTBEAT_INTERVAL,
    REDIS_CHANNEL_PREFIX,
)


class TestStreamingEndpoint:
    """Test streaming endpoint configuration."""

    def test_router_exists(self):
        assert router is not None

    def test_heartbeat_interval(self):
        assert HEARTBEAT_INTERVAL == 15

    def test_channel_prefix(self):
        assert REDIS_CHANNEL_PREFIX == "scan:"


class TestStreamingDependencies:
    """Test dependency functions exist."""

    def test_get_current_user_exists(self):
        from app.api.deps import get_current_user
        assert callable(get_current_user)

    def test_get_db_exists(self):
        from app.api.deps import get_db
        assert callable(get_db)


class TestStreamingResponseImport:
    """Verify required imports work."""

    def test_redis_import(self):
        import redis.asyncio as aioredis
        assert aioredis is not None

    def test_streaming_response_import(self):
        from fastapi.responses import StreamingResponse
        assert StreamingResponse is not None

    def test_fastapi_import(self):
        from fastapi import APIRouter
        assert APIRouter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])