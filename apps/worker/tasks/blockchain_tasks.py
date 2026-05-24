"""
Celery Beat tasks for blockchain maintenance:
  - confirm_blockchain_records  (every 5 min) — poll pending tx receipts
  - blockchain_health_monitor   (every 10 min) — connectivity + Prometheus metric
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from celery import shared_task

from services.api.app.services.blockchain_service import BlockchainService
from services.api.app.db.session import SessionLocal
from services.api.app.models.contract_blockchain_record import ContractBlockchainRecord
from services.api.app.models.audit_trail_event import AuditTrailEvent
from sqlalchemy import select
import asyncio

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.confirm_blockchain_records",
    max_retries=1,
    ignore_result=True,
)
def confirm_blockchain_records() -> None:
    """
    Poll the Polygon node for receipts on every 'pending' blockchain record.
    Updates registration_status to 'confirmed' and sets confirmed_at.
    Runs every 5 minutes via Celery Beat.
    """
    bc_svc = BlockchainService()
    if not bc_svc.connectivity_ok():
        logger.warning("[confirm_blockchain_records] RPC unreachable — skipping")
        return

    now = datetime.now(timezone.utc)

    async def _confirm():
        async with SessionLocal() as session:
            # Confirm pending contract_blockchain_records
            result = await session.execute(
                select(ContractBlockchainRecord).where(
                    ContractBlockchainRecord.registration_status == "pending"
                )
            )
            pending_recs = result.scalars().all()

            confirmed_count = 0
            for rec in pending_recs:
                if not rec.polygon_tx_hash:
                    continue
                try:
                    receipt = bc_svc.w3.eth.get_transaction_receipt(rec.polygon_tx_hash)
                    if receipt and receipt.get("blockNumber"):
                        rec.registration_status  = "confirmed"
                        rec.polygon_block_number = receipt["blockNumber"]
                        rec.confirmed_at         = now
                        confirmed_count += 1
                except Exception as exc:
                    logger.debug("Receipt not ready for tx=%s: %s", rec.polygon_tx_hash, exc)

            # Confirm pending audit_trail_events
            result_evts = await session.execute(
                select(AuditTrailEvent).where(
                    AuditTrailEvent.on_chain_status == "pending"
                )
            )
            pending_evts = result_evts.scalars().all()

            for evt in pending_evts:
                if not evt.polygon_tx_hash:
                    continue
                try:
                    receipt = bc_svc.w3.eth.get_transaction_receipt(evt.polygon_tx_hash)
                    if receipt and receipt.get("blockNumber"):
                        evt.on_chain_status      = "confirmed"
                        evt.polygon_block_number = receipt["blockNumber"]
                        evt.confirmed_at         = now
                except Exception as exc:
                    logger.debug("Audit event receipt not ready tx=%s: %s", evt.polygon_tx_hash, exc)

            await session.commit()
            return confirmed_count

    try:
        confirmed_count = asyncio.run(_confirm())
        logger.info("[confirm_blockchain_records] confirmed %d records", confirmed_count)
    except Exception as exc:
        logger.error("[confirm_blockchain_records] DB error: %s", exc)


@shared_task(
    name="tasks.blockchain_health_monitor",
    max_retries=1,
    ignore_result=True,
)
def blockchain_health_monitor() -> None:
    """
    Check Polygon RPC connectivity and ContractRegistry reachability.
    Publishes result to Redis key 'blockchain:health:status' (90s TTL).
    Runs every 10 minutes via Celery Beat.
    """
    import json, os, time
    import redis as redis_lib

    bc_svc  = BlockchainService()
    network = os.environ.get("BLOCKCHAIN_NETWORK", "testnet")
    status  = "offline"
    latency_ms = -1

    try:
        t0 = time.monotonic()
        if bc_svc.connectivity_ok():
            block_num  = bc_svc.w3.eth.block_number
            latency_ms = int((time.monotonic() - t0) * 1000)

            # Check ContractRegistry owner() call
            if bc_svc.registry:
                bc_svc.registry.functions.owner().call()
            status = "healthy"
            logger.info("[blockchain_health_monitor] healthy block=%s latency=%dms",
                        block_num, latency_ms)
        else:
            status = "offline"
            logger.warning("[blockchain_health_monitor] RPC unreachable")
    except Exception as exc:
        status = "degraded"
        logger.error("[blockchain_health_monitor] error: %s", exc)

    # Publish to Redis with 90-second TTL
    try:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = redis_lib.from_url(redis_url, decode_responses=True)
        r.setex(
            "blockchain:health:status",
            90,
            json.dumps({"status": status, "network": network, "latency_ms": latency_ms}),
        )
        # Track latest block
        if status == "healthy":
            r.set("blockchain:latest_block", bc_svc.w3.eth.block_number)
    except Exception as exc:
        logger.warning("[blockchain_health_monitor] Redis publish failed: %s", exc)
