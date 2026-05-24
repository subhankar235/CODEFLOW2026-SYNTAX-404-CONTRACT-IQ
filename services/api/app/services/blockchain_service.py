"""
Blockchain Service — interact with ContractRegistry and AuditTrail on Polygon PoS.
Includes gas management, retry decorator, and pybreaker circuit breaker.
"""
from __future__ import annotations
import hashlib, json, logging, os, time
from dataclasses import dataclass
from enum import IntEnum
from functools import wraps
from pathlib import Path
from typing import Optional, Callable
import httpx

logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 not installed — BlockchainService stub mode active")

try:
    import pybreaker
    PYBREAKER_AVAILABLE = True
except ImportError:
    PYBREAKER_AVAILABLE = False

POLYGON_RPC_URL   = os.environ.get("POLYGON_RPC_URL", "https://rpc-mumbai.maticvigil.com")
PRIVATE_KEY       = os.environ.get("BLOCKCHAIN_PRIVATE_KEY", "")
NETWORK           = os.environ.get("BLOCKCHAIN_NETWORK", "testnet")
GAS_STATION_URL   = "https://gasstation.polygon.technology/v2"
ABI_DIR           = Path(__file__).resolve().parents[5] / "blockchain" / "abis"
DEPLOYMENTS_DIR   = Path(__file__).resolve().parents[5] / "blockchain" / "deployments"
TX_TIMEOUT        = 120


class AuditEventType(IntEnum):
    UPLOADED = 0; ANALYZED = 1; SIGNED = 2; COUNTER_OFFERED = 3; EXPORTED = 4


@dataclass
class BlockchainRegistrationResult:
    tx_hash: str; block_number: int; contract_hash: str
    metadata_hash: str; network: str; polygon_scan_url: str


@dataclass
class AuditEventResult:
    tx_hash: str; event_id: int; block_number: int; chain_hash: str


@dataclass
class OnChainRecord:
    contract_hash: str; metadata_hash: str; uploader_address: str
    timestamp: int; ipfs_cid: str; exists: bool


def blockchain_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    RETRYABLE = ("TransactionNotFound", "TimeExhausted", "ConnectionError", "TimeoutError")
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    wait = backoff_factor ** (attempt - 1)
                    logger.warning("[blockchain_retry] attempt %d/%d failed: %s — wait %.1fs",
                                   attempt, max_attempts, exc, wait)
                    time.sleep(wait)
            raise last_exc  # type: ignore
        return wrapper
    return decorator


def _make_circuit_breaker():
    if not PYBREAKER_AVAILABLE:
        return None
    return pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="polygon_rpc")


def _scan_url(tx_hash: str, network: str) -> str:
    bases = {"mainnet": "https://polygonscan.com/tx",
             "testnet": "https://amoy.polygonscan.com/tx",
             "local":   "http://localhost:8545/tx"}
    return f"{bases.get(network, bases['testnet'])}/{tx_hash}"


def _load_abi(name: str) -> list:
    path = ABI_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"ABI not found: {path}. Run npm run export:abis in blockchain/")
    return json.loads(path.read_text())


def _load_addresses(network: str) -> dict:
    path = DEPLOYMENTS_DIR / f"{network}.json"
    return json.loads(path.read_text()) if path.exists() else {}


class BlockchainService:
    _circuit_breaker = _make_circuit_breaker()

    def __init__(self) -> None:
        if not WEB3_AVAILABLE:
            self._stub = True
            return
        self._stub = False
        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL, request_kwargs={"timeout": 30}))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.account = Account.from_key(PRIVATE_KEY) if PRIVATE_KEY else None
        self._registry_abi    = _load_abi("ContractRegistry")
        self._audit_trail_abi = _load_abi("AuditTrail")
        addresses = _load_addresses(NETWORK)
        reg_addr = addresses.get("ContractRegistry")
        aud_addr = addresses.get("AuditTrail")
        self.registry   = (self.w3.eth.contract(
            address=Web3.to_checksum_address(reg_addr), abi=self._registry_abi)
            if reg_addr else None)
        self.audit_trail = (self.w3.eth.contract(
            address=Web3.to_checksum_address(aud_addr), abi=self._audit_trail_abi)
            if aud_addr else None)

    @blockchain_retry(max_attempts=3, backoff_factor=2.0)
    def register_contract(self, contract_id: str, pdf_bytes: bytes,
                          metadata: dict, ipfs_pdf_cid: str) -> BlockchainRegistrationResult:
        if self._stub:
            sha = hashlib.sha256(pdf_bytes).hexdigest()
            return BlockchainRegistrationResult(f"0x{'0'*64}", 0, sha,
                hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
                "stub", "")
        if not self.registry:
            raise RuntimeError("ContractRegistry not deployed")
        if not self.account:
            raise RuntimeError("No BLOCKCHAIN_PRIVATE_KEY set")

        contract_hash = self.w3.keccak(primitive=pdf_bytes)
        meta_json     = json.dumps({**metadata, "contract_id": contract_id}, sort_keys=True)
        metadata_hash = self.w3.keccak(text=meta_json)
        gas_price     = self._get_gas_price()
        nonce         = self.w3.eth.get_transaction_count(self.account.address)
        fn            = self.registry.functions.register(contract_hash, metadata_hash, ipfs_pdf_cid)
        gas           = fn.estimate_gas({"from": self.account.address})
        tx            = fn.build_transaction({"from": self.account.address, "nonce": nonce,
                                               "gas": int(gas * 1.15), "gasPrice": gas_price})
        signed   = self.account.sign_transaction(tx)
        tx_hash  = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt  = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=TX_TIMEOUT)
        logger.info("register_contract confirmed block=%s tx=%s", receipt["blockNumber"], tx_hash.hex())
        return BlockchainRegistrationResult(
            tx_hash=tx_hash.hex(), block_number=receipt["blockNumber"],
            contract_hash=contract_hash.hex(), metadata_hash=metadata_hash.hex(),
            network=NETWORK, polygon_scan_url=_scan_url(tx_hash.hex(), NETWORK))

    @blockchain_retry(max_attempts=3, backoff_factor=2.0)
    def log_audit_event(self, contract_id: str, pdf_bytes: bytes,
                        event_type: AuditEventType, actor_address: str,
                        payload: dict) -> AuditEventResult:
        if self._stub:
            return AuditEventResult(f"0x{'0'*64}", -1, 0, "0"*64)
        if not self.audit_trail or not self.account:
            raise RuntimeError("AuditTrail not deployed or no private key")
        contract_hash = self.w3.keccak(primitive=pdf_bytes)
        data_hash     = self.w3.keccak(
            text=json.dumps({**payload, "contract_id": contract_id}, sort_keys=True))
        actor         = Web3.to_checksum_address(actor_address)
        gas_price     = self._get_gas_price()
        nonce         = self.w3.eth.get_transaction_count(self.account.address)
        fn            = self.audit_trail.functions.logEvent(
            contract_hash, int(event_type), actor, data_hash)
        gas           = fn.estimate_gas({"from": self.account.address})
        tx            = fn.build_transaction({"from": self.account.address, "nonce": nonce,
                                               "gas": int(gas * 1.15), "gasPrice": gas_price})
        signed   = self.account.sign_transaction(tx)
        tx_hash  = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt  = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=TX_TIMEOUT)
        event_id = self._decode_event_id(receipt)
        chain_hash = self.audit_trail.functions.getLastEventHash(contract_hash).call()
        return AuditEventResult(tx_hash=tx_hash.hex(), event_id=event_id,
                                block_number=receipt["blockNumber"],
                                chain_hash=chain_hash.hex())

    def get_contract_record(self, pdf_bytes: bytes) -> Optional[OnChainRecord]:
        if self._stub or not self.registry:
            return None
        try:
            ch  = self.w3.keccak(primitive=pdf_bytes)
            rec = self.registry.functions.getContract(ch).call()
            return OnChainRecord(rec[0].hex(), rec[1].hex(), rec[2], rec[3], rec[4], rec[5])
        except Exception as exc:
            logger.warning("getContract failed: %s", exc)
            return None

    def get_audit_events(self, pdf_bytes: bytes) -> list[dict]:
        if self._stub or not self.audit_trail:
            return []
        try:
            ch = self.w3.keccak(primitive=pdf_bytes)
            evts = self.audit_trail.functions.getEvents(ch).call()
            return [{"contract_hash": e[0].hex(), "event_type": e[1],
                     "actor_address": e[2], "data_hash": e[3].hex(),
                     "previous_event_hash": e[4].hex(), "timestamp": e[5]} for e in evts]
        except Exception as exc:
            logger.warning("getEvents failed: %s", exc)
            return []

    def verify_signature(self, message: str, signature: str) -> str:
        if not WEB3_AVAILABLE:
            raise RuntimeError("web3 not available")
        from eth_account.messages import encode_defunct
        return Account.recover_message(encode_defunct(text=message), signature=signature)

    def compute_pdf_hash(self, pdf_bytes: bytes) -> str:
        if self._stub or not WEB3_AVAILABLE:
            return hashlib.sha256(pdf_bytes).hexdigest()
        return self.w3.keccak(primitive=pdf_bytes).hex()

    def connectivity_ok(self) -> bool:
        if self._stub:
            return False
        try:
            self.w3.eth.block_number
            return True
        except Exception:
            return False

    def _get_gas_price(self, priority: str = "standard") -> int:
        if NETWORK == "mainnet":
            try:
                with httpx.Client(timeout=5) as c:
                    d = c.get(GAS_STATION_URL).json()
                    gwei = d.get(priority, d.get("standard", {})).get("maxFee", 30)
                    return int(self.w3.to_wei(gwei, "gwei") * 1.2)
            except Exception as exc:
                logger.warning("Gas Station failed: %s", exc)
        return int(self.w3.eth.gas_price * 1.2)

    def _decode_event_id(self, receipt) -> int:
        if not self.audit_trail:
            return -1
        try:
            logs = self.audit_trail.events.AuditEventLogged().process_receipt(receipt)
            if logs:
                return logs[0]["args"]["eventId"]
        except Exception:
            pass
        return -1
