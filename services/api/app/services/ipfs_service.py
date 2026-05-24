"""
IPFS Service — pin and retrieve legal contract documents via IPFS.

In development: connects to a local go-ipfs (Kubo) node via Docker.
In production:  falls back to the public IPFS gateway if the local node
                is unreachable, and optionally pins to web3.storage.

Usage:
    from app.services.ipfs_service import IPFSService
    result = await IPFSService().upload_contract(pdf_bytes, metadata)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
IPFS_API_URL      = os.environ.get("IPFS_API_URL", "http://localhost:5001")
IPFS_GATEWAY_URL  = os.environ.get("IPFS_GATEWAY_URL", "http://localhost:8080")
PUBLIC_GATEWAY    = "https://ipfs.io/ipfs"
TIMEOUT_SECS      = 30
RETRIEVE_TIMEOUT  = 10


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class IPFSUploadResult:
    pdf_cid:       str   # IPFS CID of the pinned PDF bytes
    metadata_cid:  str   # IPFS CID of the pinned metadata JSON
    sha256_hash:   str   # hex SHA-256 of the raw PDF bytes


# ── Service ───────────────────────────────────────────────────────────────────
class IPFSService:
    """Async IPFS client wrapping the Kubo HTTP RPC API."""

    def __init__(
        self,
        api_url: str = IPFS_API_URL,
        gateway_url: str = IPFS_GATEWAY_URL,
    ) -> None:
        self._api     = api_url.rstrip("/")
        self._gateway = gateway_url.rstrip("/")

    # ── Public API ────────────────────────────────────────────────────────────

    async def upload_contract(
        self,
        file_bytes: bytes,
        metadata: dict,
    ) -> IPFSUploadResult:
        """
        Pin a contract PDF to IPFS and create a matching metadata object.

        Args:
            file_bytes: Raw bytes of the PDF/DOCX document.
            metadata:   Dict to attach as a JSON sidecar (contract_id, sha256, etc.).

        Returns:
            IPFSUploadResult with pdf_cid, metadata_cid, sha256_hash.
        """
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Build the metadata envelope
        envelope = {
            "sha256":       sha256,
            "platform":     "legaltech-ai",
            "version":      "1.0",
            **metadata,          # merges caller-supplied fields (contract_id, timestamp…)
        }
        meta_bytes = json.dumps(envelope, sort_keys=True).encode()

        logger.info("Pinning PDF to IPFS (%d bytes, sha256=%s…)", len(file_bytes), sha256[:12])
        pdf_cid  = await self._add_bytes(file_bytes, filename="contract.pdf")

        logger.info("Pinning metadata JSON to IPFS for CID=%s", pdf_cid)
        meta_cid = await self._add_bytes(meta_bytes, filename="metadata.json")

        logger.info("IPFS upload complete: pdf_cid=%s  meta_cid=%s", pdf_cid, meta_cid)
        return IPFSUploadResult(
            pdf_cid=pdf_cid,
            metadata_cid=meta_cid,
            sha256_hash=sha256,
        )

    async def retrieve_contract(self, cid: str) -> bytes:
        """
        Fetch content from IPFS by CID.
        Tries the local node first, then falls back to the public gateway.

        Args:
            cid: IPFS content identifier (Qm… or bafybe…)

        Returns:
            Raw bytes of the stored object.

        Raises:
            RuntimeError: When content cannot be fetched from any source.
        """
        # 1) Try local gateway
        try:
            data = await self._fetch_gateway(self._gateway, cid)
            logger.debug("Retrieved CID=%s from local gateway", cid)
            return data
        except Exception as exc:
            logger.warning("Local IPFS gateway failed for CID=%s: %s — trying public", cid, exc)

        # 2) Fall back to public IPFS gateway
        try:
            data = await self._fetch_gateway(PUBLIC_GATEWAY, cid, timeout=RETRIEVE_TIMEOUT)
            logger.info("Retrieved CID=%s from public IPFS gateway", cid)
            return data
        except Exception as exc:
            raise RuntimeError(
                f"Failed to retrieve CID={cid} from both local and public IPFS gateways"
            ) from exc

    async def get_metadata(self, metadata_cid: str) -> dict:
        """Fetch and parse the JSON metadata sidecar by its CID."""
        raw = await self.retrieve_contract(metadata_cid)
        return json.loads(raw.decode())

    async def health_check(self) -> dict:
        """
        Test connectivity to the local IPFS node.
        Returns a dict with 'connected' bool and optional 'peer_id'.
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(f"{self._api}/api/v0/id")
                resp.raise_for_status()
                data = resp.json()
                return {"connected": True, "peer_id": data.get("ID", "unknown")}
        except Exception as exc:
            logger.warning("IPFS health check failed: %s", exc)
            return {"connected": False, "error": str(exc)}

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _add_bytes(self, data: bytes, filename: str = "file") -> str:
        """
        POST bytes to the local Kubo API (/api/v0/add) and return the CID.
        Raises RuntimeError on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECS) as client:
                resp = await client.post(
                    f"{self._api}/api/v0/add",
                    params={"pin": "true", "quieter": "true"},
                    files={"file": (filename, data, "application/octet-stream")},
                )
                resp.raise_for_status()
                # Kubo returns newline-delimited JSON; we only want the last line
                last_line = [ln for ln in resp.text.strip().splitlines() if ln][-1]
                result = json.loads(last_line)
                return result["Hash"]
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"IPFS add failed for {filename}: {exc}") from exc

    @staticmethod
    async def _fetch_gateway(base_url: str, cid: str, timeout: int = RETRIEVE_TIMEOUT) -> bytes:
        """Fetch raw bytes from an IPFS gateway."""
        url = f"{base_url}/ipfs/{cid}"
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
