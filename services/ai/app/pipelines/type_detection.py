"""
Step 6.1 — Contract Type Detection Pipeline
Detects contract type from the first 1000 tokens of text using a fast LLM.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — use OpenRouter via our client
# ---------------------------------------------------------------------------
FAST_MODEL = os.getenv("FAST_MODEL", "anthropic/claude-3-haiku")

MAX_DETECTION_TOKENS = 1_000
CONFIDENCE_THRESHOLD = 0.80
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "type_detection.txt"


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class ContractType(str, Enum):
    EMPLOYMENT          = "Employment"
    NDA                 = "NDA"
    SERVICE_AGREEMENT   = "Service Agreement"
    VENDOR              = "Vendor"
    SAAS                = "SaaS"
    LEASE               = "Lease"
    PARTNERSHIP         = "Partnership"
    LOAN                = "Loan"
    IP_ASSIGNMENT       = "IP Assignment"
    SETTLEMENT          = "Settlement"
    UNKNOWN             = "Unknown"


class TypeDetectionResult(BaseModel):
    """Structured result returned by the type-detection pipeline."""

    type: ContractType = Field(..., description="Detected contract type")
    confidence: float  = Field(..., ge=0.0, le=1.0, description="Detection confidence 0–1")
    party_roles: List[str] = Field(default_factory=list, description="Roles of the signing parties")
    needs_manual_review: bool = Field(
        False,
        description="True when confidence < CONFIDENCE_THRESHOLD; the frontend should show the correction selector",
    )
    raw_excerpt: Optional[str] = Field(
        None,
        description="The first-1000-token excerpt sent to the model (for debugging)",
        exclude=True,
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.confidence < CONFIDENCE_THRESHOLD:
            object.__setattr__(self, 'needs_manual_review', True)


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _load_prompt_template() -> tuple[str, str]:
    """Load the prompt template, substitute placeholders, split into (system, user).

    Falls back to an inline default if the prompt file is missing.
    Returns
    -------
    (system_prompt, user_prompt) ready to pass to the LLM client.
    """
    if PROMPT_PATH.exists():
        raw = PROMPT_PATH.read_text(encoding="utf-8")
    else:
        raw = (
            "SYSTEM:\n"
            "You are a contract-classification assistant. "
            "Analyse the contract excerpt provided by the user and respond ONLY with a "
            "JSON object (no markdown fences) with these keys:\n"
            "  contract_type  – one of: Employment, NDA, Service Agreement, Vendor, SaaS, "
            "Lease, Partnership, Loan, IP Assignment, Settlement, Unknown\n"
            "  confidence_score  – float 0.0–1.0\n"
            "  detected_parties – array of short role strings (e.g. ['employer','employee'])\n"
            "Be concise and accurate.\n"
            "USER:\n"
            "{{contract_text}}"
        )

    from ..prompts.prompt_loader import split_system_user
    sys_prompt, user_prompt = split_system_user(raw)
    return sys_prompt, user_prompt


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Rough token truncation (4 chars ≈ 1 token)."""
    char_limit = max_tokens * 4
    return text[:char_limit]


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def detect_contract_type(
    contract_text: str,
    *,
    openrouter_client=None,
) -> TypeDetectionResult:
    """
    Sync wrapper — safe to call from both sync (Celery worker) and async contexts.

    When called from within an already-running event loop (e.g. Celery with gevent
    or from an async test), we spin up a dedicated thread so asyncio.run() gets a
    fresh loop instead of trying to nest inside the existing one.
    """
    import concurrent.futures

    try:
        # If there is already a running loop we MUST NOT call asyncio.run() here —
        # that would raise RuntimeError('This event loop is already running').
        asyncio.get_running_loop()
        _has_running_loop = True
    except RuntimeError:
        _has_running_loop = False

    if _has_running_loop:
        # Offload to a thread that has no running loop, then asyncio.run() safely.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                detect_contract_type_async(contract_text, openrouter_client=openrouter_client),
            )
            return future.result()
    else:
        return asyncio.run(
            detect_contract_type_async(contract_text, openrouter_client=openrouter_client)
        )


async def detect_contract_type_async(
    contract_text: str,
    *,
    openrouter_client=None,
) -> TypeDetectionResult:
    """Async variant for use inside async frameworks (FastAPI, etc.)."""
    # Use relative import — works regardless of how the package is installed.
    from ..models.openrouter_client import OpenRouterClient

    client = openrouter_client or OpenRouterClient()
    excerpt = _truncate_to_tokens(contract_text, MAX_DETECTION_TOKENS)
    system_prompt, user_prompt = _load_prompt_template()

    # Substitute placeholders in the user prompt
    user_prompt = user_prompt.replace("{{sample_length}}", str(len(excerpt)))
    user_prompt = user_prompt.replace("{{contract_text}}", excerpt)

    logger.debug("Sending %d chars to %s for type detection", len(excerpt), FAST_MODEL)

    try:
        # client.complete() is the correct method (chat_json does not exist).
        # json_mode=True forces a JSON object response from the LLM.
        raw_response = await client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=FAST_MODEL,
            json_mode=True,
        )
        # The OpenRouter response is: {"choices": [{"message": {"content": "..."}}]}
        content = raw_response["choices"][0]["message"].get("content", "{}")
        logger.debug("Raw type-detection response: %s", content)
        return _parse_response(content, excerpt)
    except Exception as exc:
        logger.error("Type detection LLM call failed: %s", exc)
        return TypeDetectionResult(
            type=ContractType.UNKNOWN,
            confidence=0.0,
            party_roles=[],
        )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_response(data, excerpt: str) -> TypeDetectionResult:
    """Parse the model's JSON response into a TypeDetectionResult."""
    if isinstance(data, str):
        cleaned = data.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Type-detection returned non-JSON; defaulting to Unknown. raw=%r", data)
            return TypeDetectionResult(
                type=ContractType.UNKNOWN,
                confidence=0.0,
                party_roles=[],
                raw_excerpt=excerpt,
            )
    elif isinstance(data, dict):
        payload = data
    else:
        logger.warning("Type-detection returned unexpected type; defaulting to Unknown.")
        return TypeDetectionResult(
            type=ContractType.UNKNOWN,
            confidence=0.0,
            party_roles=[],
            raw_excerpt=excerpt,
        )

    # Handle both prompt formats:
    # - type_detection.txt returns: contract_type, confidence_score, detected_parties
    # - expected legacy format: type, confidence, party_roles
    raw_type = payload.get("type") or payload.get("contract_type", "Unknown")
    try:
        contract_type = ContractType(raw_type)
    except ValueError:
        contract_type = _fuzzy_match_type(raw_type)

    confidence = float(payload.get("confidence") or payload.get("confidence_score", 0.0))
    confidence = max(0.0, min(1.0, confidence))

    roles = payload.get("party_roles") or payload.get("detected_parties", [])
    if not isinstance(roles, list):
        roles = [str(roles)]

    result = TypeDetectionResult(
        type=contract_type,
        confidence=confidence,
        party_roles=[str(r) for r in roles],
        raw_excerpt=excerpt,
    )
    logger.info(
        "Type detection: type=%s confidence=%.2f needs_review=%s roles=%s",
        result.type,
        result.confidence,
        result.needs_manual_review,
        result.party_roles,
    )
    return result


def _fuzzy_match_type(raw: str) -> ContractType:
    """Best-effort case-insensitive match to a known ContractType."""
    normalised = raw.strip().lower()
    for member in ContractType:
        if member.value.lower() == normalised:
            return member
    if "employ" in normalised:
        return ContractType.EMPLOYMENT
    if "non-disclos" in normalised or "nda" in normalised or "confidential" in normalised:
        return ContractType.NDA
    if "service" in normalised:
        return ContractType.SERVICE_AGREEMENT
    if "vendor" in normalised or "supplier" in normalised:
        return ContractType.VENDOR
    if "saas" in normalised or "software" in normalised or "subscription" in normalised:
        return ContractType.SAAS
    if "lease" in normalised or "rental" in normalised:
        return ContractType.LEASE
    if "partner" in normalised or "joint venture" in normalised:
        return ContractType.PARTNERSHIP
    if "loan" in normalised or "credit" in normalised or "promissory" in normalised:
        return ContractType.LOAN
    if "ip " in normalised or "intellectual property" in normalised or "patent" in normalised:
        return ContractType.IP_ASSIGNMENT
    if "settlement" in normalised or "release of claims" in normalised:
        return ContractType.SETTLEMENT
    return ContractType.UNKNOWN