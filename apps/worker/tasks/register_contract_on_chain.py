"""
Celery task — register_contract_on_chain
Queued by the upload endpoint after the contract is saved to the DB.
Calls IPFS + Polygon in sequence, updates contract_blockchain_records.
"""
from __future__ import annotations
import hashlib, json, logging, uuid
from datetime import datetime, timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="tasks.register_contract_on_chain",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def register_contract_on_chain(
    self,
    contract_id: str,
    file_url: str,
    user_id: str,
    actor_wallet: str = "",
) -> dict:
    """
    1. Download the contract file from Uploadthing/IPFS URL.
    2. Pin to local IPFS node.
    3. Register keccak256 hashes on ContractRegistry.
    4. Log an UPLOADED event on AuditTrail.
    5. Persist results to contract_blockchain_records and audit_trail_events.

    Args:
        contract_id:   Platform contract UUID.
        file_url:      Uploadthing URL of the stored file.
        user_id:       Clerk user UUID.
        actor_wallet:  Optional wallet address that signed; defaults to deployer.

    Returns:
        dict with tx_hash, ipfs_pdf_cid, pdf_sha256, status.
    """
    import asyncio
    import httpx

    from services.api.app.services.ipfs_service import IPFSService
    from services.api.app.services.blockchain_service import BlockchainService, AuditEventType
    from services.api.app.db.session import SessionLocal

    logger.info("[register_contract_on_chain] contract_id=%s", contract_id)

    # ── Step 1: download file ─────────────────────────────────────────────────
    try:
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(file_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as exc:
        logger.error("Download failed for %s: %s", file_url, exc)
        raise self.retry(exc=exc)

    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    metadata   = {
        "contract_id": contract_id,
        "user_id":     user_id,
        "file_url":    file_url,
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ── Step 2: pin to IPFS ───────────────────────────────────────────────────
    ipfs_svc = IPFSService()
    try:
        ipfs_result = asyncio.run(ipfs_svc.upload_contract(pdf_bytes, metadata))
    except Exception as exc:
        logger.warning("IPFS upload failed (non-fatal): %s", exc)
        return {"status": "skipped", "reason": f"IPFS unavailable: {exc}"}

    # ── Step 3: register on Polygon ───────────────────────────────────────────
    bc_svc = BlockchainService()
    try:
        reg_result = bc_svc.register_contract(
            contract_id  = contract_id,
            pdf_bytes    = pdf_bytes,
            metadata     = metadata,
            ipfs_pdf_cid = ipfs_result.pdf_cid,
        )
    except Exception as exc:
        logger.error("Blockchain registration failed: %s", exc)
        raise self.retry(exc=exc)

    # ── Step 4: log UPLOADED event on AuditTrail ─────────────────────────────
    wallet = actor_wallet or (bc_svc.account.address if bc_svc.account else "0x0")
    try:
        audit_result = bc_svc.log_audit_event(
            contract_id   = contract_id,
            pdf_bytes     = pdf_bytes,
            event_type    = AuditEventType.UPLOADED,
            actor_address = wallet,
            payload       = {"action": "upload", "file_url": file_url},
        )
    except Exception as exc:
        logger.warning("Audit log failed (non-fatal): %s", exc)
        audit_result = None

    # ── Step 5: persist to DB ─────────────────────────────────────────────────
    async def _persist():
        from services.api.app.models.contract_blockchain_record import ContractBlockchainRecord
        from services.api.app.models.audit_trail_event import AuditTrailEvent

        async with SessionLocal() as session:
            rec = ContractBlockchainRecord(
                id                   = uuid.uuid4(),
                contract_id          = uuid.UUID(contract_id),
                ipfs_pdf_cid         = ipfs_result.pdf_cid,
                ipfs_metadata_cid    = ipfs_result.metadata_cid,
                pdf_sha256           = pdf_sha256,
                metadata_sha256      = hashlib.sha256(
                    json.dumps(metadata, sort_keys=True).encode()
                ).hexdigest(),
                polygon_tx_hash      = reg_result.tx_hash,
                polygon_block_number = reg_result.block_number or None,
                polygon_network      = reg_result.network,
                registration_status  = "confirmed" if reg_result.block_number else "pending",
                confirmed_at         = datetime.now(timezone.utc) if reg_result.block_number else None,
            )
            session.add(rec)

            if audit_result:
                evt = AuditTrailEvent(
                    id                   = uuid.uuid4(),
                    contract_id          = uuid.UUID(contract_id),
                    event_type           = "UPLOADED",
                    actor_user_id        = uuid.UUID(user_id) if user_id else None,
                    actor_wallet_address = wallet,
                    payload              = {"action": "upload", "file_url": file_url},
                    payload_hash         = audit_result.chain_hash or "0x" + "0" * 64,
                    polygon_tx_hash      = audit_result.tx_hash,
                    polygon_block_number = audit_result.block_number or None,
                    on_chain_status      = "confirmed" if audit_result.block_number else "pending",
                )
                session.add(evt)

            await session.commit()

    try:
        asyncio.run(_persist())
    except Exception as exc:
        logger.error("DB persist failed: %s", exc)
        # Non-fatal — on-chain data is safe; DB can be repaired by confirm task

    logger.info("[register_contract_on_chain] complete: tx=%s ipfs=%s",
                reg_result.tx_hash, ipfs_result.pdf_cid)
    return {
        "tx_hash":      reg_result.tx_hash,
        "ipfs_pdf_cid": ipfs_result.pdf_cid,
        "pdf_sha256":   pdf_sha256,
        "status":       "confirmed" if reg_result.block_number else "pending",
    }
