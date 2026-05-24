"""
API Router for Blockchain and IPFS integrations.
Handles verification, audit trails, and digital signatures.
"""
from __future__ import annotations
import httpx
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.services.blockchain_service import BlockchainService, AuditEventType
from app.services.ipfs_service import IPFSService
from app.services.contract_verifier import verify_contract_integrity, VerificationResult
from app.schemas.blockchain import (
    SignatureVerifyRequest,
    IPFSHealthResponse,
    BlockchainHealthResponse,
    BlockchainRecordResponse,
    AuditTrailResponse,
    AuditEventResponse,
    VerificationResponse,
    SignatureRegistrationResponse,
    CertificateResponse,
)
from app.models.contract import Contract
from app.models.contract_blockchain_record import ContractBlockchainRecord
from app.models.audit_trail_event import AuditTrailEvent

router = APIRouter()


@router.get("/health", response_model=BlockchainHealthResponse)
async def check_blockchain_health() -> BlockchainHealthResponse:
    """Check connectivity to Polygon PoS node via BlockchainService."""
    svc = BlockchainService()
    if svc.connectivity_ok():
        return BlockchainHealthResponse(status="healthy", network=svc.w3.eth.chain_id, latency_ms=10)
    return BlockchainHealthResponse(status="offline", network="unknown", latency_ms=-1)


@router.get("/ipfs/health", response_model=IPFSHealthResponse)
async def check_ipfs_health() -> IPFSHealthResponse:
    """Check connectivity to local IPFS Kubo node."""
    svc = IPFSService()
    res = await svc.health_check()
    return IPFSHealthResponse(**res)


@router.get("/{contract_id}/record", response_model=BlockchainRecordResponse)
async def get_blockchain_record(
    contract_id: str,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """Get the current blockchain registration status (db row) for a contract."""
    stmt = select(ContractBlockchainRecord).where(
        ContractBlockchainRecord.contract_id == uuid.UUID(contract_id)
    )
    result = await db.execute(stmt)
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Blockchain record not found")
    
    # Optional URL generation
    from app.services.blockchain_service import NETWORK, _scan_url
    url = _scan_url(record.polygon_tx_hash, NETWORK) if record.polygon_tx_hash else None
    
    response = BlockchainRecordResponse.model_validate(record)
    response.polygon_scan_url = url
    return response


@router.get("/{contract_id}/verify", response_model=VerificationResponse)
async def verify_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Perform a 3-source integrity check:
    1. Re-hash the original uploaded file.
    2. Check IPFS metadata.
    3. Check on-chain keccak256 hash in ContractRegistry.
    """
    # 1. Load contract and DB record
    stmt = select(Contract).where(Contract.id == uuid.UUID(contract_id))
    contract = (await db.execute(stmt)).scalars().first()
    if not contract:
        raise HTTPException(404, "Contract not found")
        
    stmt_rec = select(ContractBlockchainRecord).where(
        ContractBlockchainRecord.contract_id == uuid.UUID(contract_id)
    )
    record = (await db.execute(stmt_rec)).scalars().first()
    if not record:
        raise HTTPException(404, "No blockchain record exists for this contract")

    # 2. Download the original PDF to verify it
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(contract.file_ref)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch original file: {exc}")

    # 3. Verify
    bc_svc = BlockchainService()
    ipfs_svc = IPFSService()
    
    db_dict = {
        "pdf_sha256": record.pdf_sha256,
        "polygon_tx_hash": record.polygon_tx_hash,
        "ipfs_metadata_cid": record.ipfs_metadata_cid,
        "ipfs_pdf_cid": record.ipfs_pdf_cid,
        "contract_address": record.contract_address,
        "polygon_network": record.polygon_network,
        "confirmed_at": record.confirmed_at,
        "polygon_block_number": record.polygon_block_number,
    }
    
    result = await verify_contract_integrity(
        contract_id=contract_id,
        pdf_bytes=pdf_bytes,
        db_record=db_dict,
        blockchain_svc=bc_svc,
        ipfs_svc=ipfs_svc,
    )
    
    return result


@router.get("/{contract_id}/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    contract_id: str,
    live_check: bool = False,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """Get the full chronological audit trail for a contract."""
    stmt = select(AuditTrailEvent).where(
        AuditTrailEvent.contract_id == uuid.UUID(contract_id)
    ).order_by(AuditTrailEvent.occurred_at.asc())
    
    db_events = (await db.execute(stmt)).scalars().all()
    
    events_out = []
    from app.services.blockchain_service import NETWORK, _scan_url
    for e in db_events:
        url = _scan_url(e.polygon_tx_hash, NETWORK) if e.polygon_tx_hash else None
        evt_resp = AuditEventResponse.model_validate(e)
        evt_resp.polygon_scan_url = url
        events_out.append(evt_resp)
        
    on_chain_events = []
    if live_check and db_events:
        # Fetch live from blockchain for strict verification
        bc_svc = BlockchainService()
        try:
            # Re-download the file to get the hash
            stmt_c = select(Contract).where(Contract.id == uuid.UUID(contract_id))
            c = (await db.execute(stmt_c)).scalars().first()
            if c:
                async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                    resp = await client.get(c.file_ref)
                    on_chain_events = bc_svc.get_audit_events(resp.content)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed live audit check: %s", exc)

    return AuditTrailResponse(
        contract_id=contract_id,
        total_events=len(events_out),
        events=events_out,
        on_chain_events=on_chain_events
    )


@router.post("/sign", response_model=SignatureRegistrationResponse)
async def register_signature(
    req: SignatureVerifyRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Verify an EIP-191 signature and append a SIGNED event to the on-chain AuditTrail.
    This links the user's wallet address cryptographically to the document.
    """
    bc_svc = BlockchainService()
    try:
        signer = bc_svc.verify_signature(req.message, req.signature)
    except Exception as exc:
        raise HTTPException(400, f"Invalid signature format: {exc}")
        
    if signer.lower() != req.wallet_address.lower():
        raise HTTPException(401, "Signature was not created by the provided wallet address")

    # Fetch file to compute hash for AuditTrail
    stmt = select(Contract).where(Contract.id == uuid.UUID(req.contract_id))
    contract = (await db.execute(stmt)).scalars().first()
    if not contract:
        raise HTTPException(404, "Contract not found")
        
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(contract.file_ref)
            pdf_bytes = resp.content
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch contract file: {exc}")

    # Log to blockchain
    try:
        audit_res = bc_svc.log_audit_event(
            contract_id=req.contract_id,
            pdf_bytes=pdf_bytes,
            event_type=AuditEventType.SIGNED,
            actor_address=signer,
            payload={"action": "signed", "message": req.message}
        )
    except Exception as exc:
        raise HTTPException(500, f"Blockchain tx failed: {exc}")

    # Persist event to DB
    evt = AuditTrailEvent(
        id=uuid.uuid4(),
        contract_id=uuid.UUID(req.contract_id),
        event_type="SIGNED",
        actor_user_id=uuid.UUID(user_id),
        actor_wallet_address=signer,
        payload={"action": "signed", "message": req.message},
        payload_hash=audit_res.chain_hash,
        polygon_tx_hash=audit_res.tx_hash,
        polygon_block_number=audit_res.block_number,
        on_chain_status="confirmed" if audit_res.block_number else "pending",
    )
    db.add(evt)
    await db.commit()

    from app.services.blockchain_service import NETWORK, _scan_url
    return SignatureRegistrationResponse(
        contract_id=req.contract_id,
        tx_hash=audit_res.tx_hash,
        polygon_scan_url=_scan_url(audit_res.tx_hash, NETWORK),
        wallet_address=signer,
        task_id=None,
        status="confirmed" if audit_res.block_number else "pending",
    )
