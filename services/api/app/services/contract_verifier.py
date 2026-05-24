"""
Contract Verifier — multi-source integrity verification for legal contracts.

Checks:
  1. SHA-256 of provided bytes vs. stored database hash
  2. On-chain keccak256 hash from ContractRegistry (guards against DB tampering)
  3. IPFS metadata sidecar SHA-256 field

Returns a VerificationResult dataclass suitable for the API response.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
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
    verification_certificate: dict = field(default_factory=dict)


async def verify_contract_integrity(
    contract_id: str,
    pdf_bytes: bytes,
    db_record: dict,        # row from contract_blockchain_records (as dict)
    blockchain_svc,         # BlockchainService instance
    ipfs_svc,               # IPFSService instance
) -> VerificationResult:
    """
    Full three-source integrity verification.

    Args:
        contract_id:     Platform UUID.
        pdf_bytes:       Bytes from the user's uploaded file.
        db_record:       Dict with keys: pdf_sha256, polygon_tx_hash,
                         ipfs_metadata_cid, contract_address, polygon_network,
                         confirmed_at, polygon_block_number.
        blockchain_svc:  Initialized BlockchainService.
        ipfs_svc:        Initialized IPFSService.

    Returns:
        VerificationResult
    """
    sha256_provided = hashlib.sha256(pdf_bytes).hexdigest()
    sha256_stored   = db_record.get("pdf_sha256", "")

    # Step 1 — compare provided bytes hash vs stored hash
    tampered = sha256_provided != sha256_stored

    # Step 2 — query on-chain record
    on_chain_match = False
    blockchain_timestamp: Optional[datetime] = None
    try:
        on_chain = blockchain_svc.get_contract_record(pdf_bytes)
        if on_chain and on_chain.exists:
            stored_on_chain_hash = blockchain_svc.compute_pdf_hash(pdf_bytes)
            on_chain_match = (on_chain.contract_hash == stored_on_chain_hash)
            if on_chain.timestamp:
                blockchain_timestamp = datetime.fromtimestamp(
                    on_chain.timestamp, tz=timezone.utc
                )
    except Exception as exc:
        logger.warning("On-chain verification failed for %s: %s", contract_id, exc)

    # Step 3 — IPFS metadata check
    ipfs_match = False
    meta_cid   = db_record.get("ipfs_metadata_cid", "")
    if meta_cid:
        try:
            meta = await ipfs_svc.get_metadata(meta_cid)
            ipfs_match = meta.get("sha256", "") == sha256_stored
        except Exception as exc:
            logger.warning("IPFS metadata check failed for CID=%s: %s", meta_cid, exc)

    verified = (not tampered) and on_chain_match

    tx_hash          = db_record.get("polygon_tx_hash", "")
    polygon_scan_url = _build_scan_url(tx_hash, db_record.get("polygon_network", "testnet"))

    certificate = _build_certificate(
        contract_id          = contract_id,
        sha256               = sha256_provided,
        tx_hash              = tx_hash,
        ipfs_cid             = db_record.get("ipfs_pdf_cid", ""),
        blockchain_timestamp = blockchain_timestamp,
        on_chain_match       = on_chain_match,
        ipfs_match           = ipfs_match,
        tampered             = tampered,
    )

    return VerificationResult(
        contract_id          = contract_id,
        verified             = verified,
        tampered             = tampered,
        on_chain_match       = on_chain_match,
        ipfs_match           = ipfs_match,
        blockchain_timestamp = blockchain_timestamp,
        tx_hash              = tx_hash,
        polygon_scan_url     = polygon_scan_url,
        sha256_provided      = sha256_provided,
        sha256_stored        = sha256_stored,
        verification_certificate = certificate,
    )


def _build_scan_url(tx_hash: str, network: str) -> str:
    bases = {
        "mainnet": "https://polygonscan.com/tx",
        "testnet": "https://amoy.polygonscan.com/tx",
        "local":   "",
    }
    if not tx_hash:
        return ""
    base = bases.get(network, bases["testnet"])
    return f"{base}/{tx_hash}" if base else ""


def _build_certificate(
    contract_id: str,
    sha256: str,
    tx_hash: str,
    ipfs_cid: str,
    blockchain_timestamp: Optional[datetime],
    on_chain_match: bool,
    ipfs_match: bool,
    tampered: bool,
) -> dict:
    """Build the JSON verification certificate suitable for legal submission."""
    return {
        "platform":            "LegalTech AI Platform",
        "certificate_version": "1.0",
        "contract_id":         contract_id,
        "sha256":              sha256,
        "tx_hash":             tx_hash,
        "ipfs_cid":            ipfs_cid,
        "blockchain_timestamp": (
            blockchain_timestamp.isoformat() if blockchain_timestamp else None
        ),
        "on_chain_match":     on_chain_match,
        "ipfs_match":         ipfs_match,
        "tampered":           tampered,
        "verified":           (not tampered) and on_chain_match,
        "generated_at":       datetime.now(timezone.utc).isoformat(),
    }
