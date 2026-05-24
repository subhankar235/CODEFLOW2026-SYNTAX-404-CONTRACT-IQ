# Streaming endpoint: serves the GET /scan/{jobId}/stream route.
# Validates the JWT, confirms job ownership, then opens a Redis pub/sub
# subscription and pushes each clause result to the browser as Server-Sent Events.

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.repositories.scan_job_repo import ScanJobRepository
from app.core.config import settings
from app.core.security import get_current_user_from_query
logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 15  # seconds
REDIS_CHANNEL_PREFIX = "scan:"


# ---------------------------------------------------------------------------
# Helper: async SSE generator
# ---------------------------------------------------------------------------

from uuid import UUID


async def _fetch_scan_data(
    job_uuid: UUID,
    user_id: str,
) -> tuple[str, str | None, list[str] | None]:
    """
    Do all DB queries upfront, return a result tuple.
    No ``yield`` here — avoids SQLAlchemy async greenlet-context corruption.

    Returns one of:
      ("error", "message", None)
      ("complete", None, [clause_event_strings])
      ("realtime", None, None)
    """
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.scan_job import ScanJob
    from app.models.contract import Contract
    from app.models.clause import Clause

    db = AsyncSessionLocal()
    try:
        from app.repositories import user_repo
        user = await user_repo.get_user_by_clerk_id(db, user_id)
        if not user:
            return ("error", "User not found", None)

        query = (
            select(ScanJob)
            .where(ScanJob.id == job_uuid)
            .join(Contract, ScanJob.contract_id == Contract.id)
            .where(Contract.user_id == user.id)
        )
        result = await db.execute(query)
        job = result.scalars().first()

        if not job:
            return ("error", "Job not found or access denied", None)

        if job.status == "complete":
            clause_query = (
                select(Clause)
                .where(Clause.contract_id == job.contract_id)
                .order_by(Clause.position_index)
            )
            clause_result = await db.execute(clause_query)
            events: list[str] = []
            for clause in clause_result.scalars().all():
                clause_dict = {
                    "clause_index": clause.position_index,
                    "clause_text": clause.text,
                    "risk_severity": clause.risk_level,
                    "safety_rating": clause.risk_level,
                    "risk_categories": [clause.risk_category] if clause.risk_category else [],
                    "explanation": clause.plain_english,
                    "recommendation": clause.worst_case_scenario,
                    "financial_exposure": clause.financial_exposure,
                    "negotiable": clause.negotiable,
                    "confidence": clause.confidence,
                }
                payload = json.dumps({"type": "clause", "data": clause_dict})
                events.append(f"data: {payload}\n\n")
            return ("complete", None, events)

        return ("realtime", None, None)
    finally:
        await db.close()


async def _sse_generator(
    job_id: str,
    user_id: str,
    contract_id: str,
) -> AsyncGenerator[str, None]:
    """
    Core generator that drives the SSE stream for one scan job.

    DB work is entirely separated into ``_fetch_scan_data`` so that
    no ``yield`` ever appears while an ``AsyncSession`` is open (avoiding
    ``MissingGreenlet`` errors).
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        yield 'event: error\ndata: {"detail": "Invalid job ID format"}\n\n'
        return

    kind, error_msg, clause_events = await _fetch_scan_data(job_uuid, user_id)

    # ── Error ──────────────────────────────────────────────────────────────────
    if kind == "error":
        yield f'event: error\ndata: {{"detail": "{error_msg}"}}\n\n'
        return

    # ── Job already complete — stream stored clauses ───────────────────────────
    if kind == "complete":
        for line in clause_events or []:
            yield line
        yield "event: complete\ndata: {}\n\n"
        return

    # ── Real-time — subscribe to Redis pub/sub ─────────────────────────────────
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    channel_name = f"{REDIS_CHANNEL_PREFIX}{contract_id}"

    try:
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(channel_name)
            logger.info("SSE: subscribed to channel %s", channel_name)

            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                now = asyncio.get_event_loop().time()

                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield "event: heartbeat\ndata: {}\n\n"
                    last_heartbeat = now

                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=0.1,
                )

                if message is None:
                    await asyncio.sleep(0.05)
                    continue

                raw = message.get("data", "")
                if not isinstance(raw, str):
                    continue

                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning(
                        "SSE: invalid JSON on channel %s: %r", channel_name, raw
                    )
                    continue

                msg_type = payload.get("type", "")

                if msg_type == "clause":
                    yield f"data: {raw}\n\n"

                elif msg_type == "progress":
                    yield f"event: progress\ndata: {raw}\n\n"

                elif msg_type == "complete":
                    yield f"event: complete\ndata: {raw}\n\n"
                    logger.info("SSE: job %s complete — closing stream", job_id)
                    return

                elif msg_type == "error":
                    yield f"event: error\ndata: {raw}\n\n"
                    return

    except asyncio.CancelledError:
        logger.info("SSE: client disconnected for job %s", job_id)
    finally:
        await redis_client.aclose()


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "/scan/{job_id}/stream",
    summary="Stream clause results for a scan job via SSE",
    responses={
        200: {"description": "text/event-stream"},
        401: {"description": "Invalid or missing JWT"},
        404: {"description": "Job not found or does not belong to user"},
    },
)
async def stream_scan_results(
    job_id: str,
    request: Request,
    token: str = None,
) -> StreamingResponse:
    # Validate token from query param
    user_id = await get_current_user_from_query(token)
    """
    Opens a persistent SSE connection for ``job_id``.

    Security:
    - ``get_current_user`` validates the JWT from the ``Authorization`` header.
    - Ownership of the job is verified inside ``_sse_generator`` against the DB.

    The client receives:
    - ``data: {...}``           — clause result events (default event type)
    - ``event: progress``       — progress_pct updates
    - ``event: complete``       — signals the scan is done; client should close
    - ``event: error``          — unrecoverable pipeline failure
    - ``: heartbeat``           — SSE comment every 15 s (no browser event fired)
    """
    # Verify job exists before streaming (own session — generator creates its own)
    from app.db.session import AsyncSessionLocal
    from app.models.contract import Contract
    from app.repositories import user_repo
    async with AsyncSessionLocal() as verify_db:
        repo = ScanJobRepository(verify_db)
        job = await repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        contract = await verify_db.get(Contract, job.contract_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
            )
        user = await user_repo.get_user_by_clerk_id(verify_db, user_id)
        if not user or contract.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    generator = _sse_generator(
        job_id=job_id,
        user_id=str(user_id),
        contract_id=str(job.contract_id),
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
