"""Pydantic v2 schemas for blockchain/IPFS endpoints."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Request bodies ────────────────────────────────────────────────────────────
class SignatureVerifyRequest(BaseModel):
    contract_id:    str = Field(..., description="Platform contract UUID")
    signature:      str = Field(..., description="Hex EIP-191 signature from MetaMask")
    wallet_address: str = Field(..., description="Wallet address that signed")
    message:        str = Field(..., description="Exact message that was signed")


# ── Response schemas ──────────────────────────────────────────────────────────
class IPFSHealthResponse(BaseModel):
    connected: bool
    peer_id:   Optional[str] = None
    error:     Optional[str] = None


class BlockchainHealthResponse(BaseModel):
    status:     str   # healthy | degraded | offline
    network:    str
    latency_ms: int


class BlockchainRecordResponse(BaseModel):
    contract_id:          str
    ipfs_pdf_cid:         str
    ipfs_metadata_cid:    str
    pdf_sha256:           str
    polygon_tx_hash:      Optional[str]
    polygon_block_number: Optional[int]
    polygon_network:      str
    registration_status:  str
    confirmed_at:         Optional[datetime]
    polygon_scan_url:     Optional[str]

    model_config = {"from_attributes": True}


class AuditEventResponse(BaseModel):
    id:                   str
    contract_id:          str
    event_type:           str
    actor_wallet_address: Optional[str]
    payload:              dict
    payload_hash:         str
    previous_event_hash:  Optional[str]
    polygon_tx_hash:      Optional[str]
    on_chain_status:      str
    occurred_at:          datetime
    confirmed_at:         Optional[datetime]
    polygon_scan_url:     Optional[str]

    model_config = {"from_attributes": True}


class AuditTrailResponse(BaseModel):
    contract_id:   str
    total_events:  int
    events:        list[AuditEventResponse]
    on_chain_events: list[dict] = Field(default_factory=list,
                                        description="Events fetched live from the blockchain")


class VerificationResponse(BaseModel):
    contract_id:          str
    verified:             bool
    tampered:             bool
    on_chain_match:       bool
    ipfs_match:           bool
    blockchain_timestamp: Optional[datetime]
    tx_hash:              str
    polygon_scan_url:     str
    sha256_provided:      str
    sha256_stored:        str
    verification_certificate: dict


class SignatureRegistrationResponse(BaseModel):
    contract_id:     str
    tx_hash:         str
    polygon_scan_url: str
    wallet_address:  str
    task_id:         Optional[str]
    status:          str


class CertificateResponse(BaseModel):
    contract_id:          str
    sha256:               str
    tx_hash:              str
    ipfs_cid:             str
    blockchain_timestamp: Optional[str]
    on_chain_match:       bool
    ipfs_match:           bool
    tampered:             bool
    verified:             bool
    generated_at:         str
