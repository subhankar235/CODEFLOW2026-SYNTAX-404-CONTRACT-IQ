"""
services/ai/utils/validate_llm_response.py

Central utility for validating raw LLM JSON responses against Pydantic models.

Design contract
---------------
* Never raises on validation failure – always returns None instead.
* Always logs the raw response at ERROR level on failure so every bad
  response is auditable without crashing the pipeline.
* Accepts either a dict (already parsed JSON) or a str (raw LLM output).
* Strips markdown code fences automatically before attempting to parse.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Matches ```json ... ``` or ``` ... ``` wrappers
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    """Remove markdown code fences from an LLM response string."""
    return _FENCE_RE.sub("", text).strip()


def _to_dict(raw: str | dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Convert raw LLM output to a dict.
    Returns None if parsing fails.
    """
    if isinstance(raw, dict):
        return raw
    cleaned = _strip_fences(raw)
    try:
        result = json.loads(cleaned)
        if not isinstance(result, dict):
            logger.error(
                "LLM response parsed to %s, expected dict. raw=%s",
                type(result).__name__,
                cleaned[:200],
            )
            return None
        return result
    except json.JSONDecodeError as exc:
        logger.error(
            "LLM response JSON decode error: %s | raw=%s",
            exc,
            cleaned[:400],
        )
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_llm_response(
    model_class: Type[T],
    raw: str | dict[str, Any],
    *,
    context: Optional[str] = None,
) -> Optional[T]:
    """
    Validate a raw LLM response against a Pydantic model.

    Parameters
    ----------
    model_class : Pydantic model class to validate against
    raw         : raw LLM output – either a JSON string or already-parsed dict
    context     : optional context label for log messages (e.g. clause_id, job_id)

    Returns
    -------
    Validated model instance on success, or None on any failure.
    Never raises.
    """
    label = f"[{context}] " if context else ""

    # Step 1: parse to dict
    data = _to_dict(raw)
    if data is None:
        logger.error(
            "%svalidate_llm_response: JSON parse failed for model=%s",
            label,
            model_class.__name__,
        )
        return None

    # Step 2: Pydantic validation
    try:
        instance = model_class.model_validate(data)
        logger.debug(
            "%svalidate_llm_response: OK model=%s",
            label,
            model_class.__name__,
        )
        return instance

    except ValidationError as exc:
        logger.error(
            "%svalidate_llm_response: ValidationError for model=%s errors=%s raw_data=%s",
            label,
            model_class.__name__,
            exc.errors(),
            json.dumps(data)[:600],
        )
        return None

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "%svalidate_llm_response: Unexpected error for model=%s: %s",
            label,
            model_class.__name__,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Typed convenience wrappers – one per LLM response model
# (avoids passing model_class everywhere in pipeline code)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Typed convenience wrappers — one per LLM response model
# (avoids passing model_class everywhere in pipeline code)
# ---------------------------------------------------------------------------

def _make_validator(model_class: Type[T]):
    """Factory for typed validate_* helpers."""
    def _validate(
        raw: str | dict[str, Any],
        context: Optional[str] = None,
    ) -> Optional[T]:
        return validate_llm_response(model_class, raw, context=context)
    _validate.__name__ = f"validate_{model_class.__name__}"
    _validate.__doc__ = f"Validate raw LLM output as {model_class.__name__}. Returns None on failure."
    return _validate


# Import at bottom to avoid circular imports — use package-relative path
from .llm_responses import (  # noqa: E402
    LLMRiskAnalysis,
    LLMTypeDetection,
    LLMConsequence,
    LLMSummary,
    LLMPowerAsymmetry,
    LLMCounterOffer,
    LLMPrecedent,
)

validate_risk_analysis = _make_validator(LLMRiskAnalysis)
validate_type_detection = _make_validator(LLMTypeDetection)
validate_consequence = _make_validator(LLMConsequence)
validate_summary = _make_validator(LLMSummary)
validate_power_asymmetry = _make_validator(LLMPowerAsymmetry)
validate_counter_offer = _make_validator(LLMCounterOffer)
validate_precedent = _make_validator(LLMPrecedent)