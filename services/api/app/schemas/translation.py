"""
Translation schemas — PRD Feature 11.

POST /api/v1/translate/{contractId} → 202 Accepted with TranslationResponse.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Supported language codes (PRD Feature 11)
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = {"en", "es", "fr", "de", "pt", "hi"}


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class TranslationRequest(BaseModel):
    """Request body for POST /translate/{contractId}."""
    target_language: str = Field(
        ...,
        description="BCP-47 language code. Supported: en, es, fr, de, pt, hi",
    )

    def validate_language(self) -> "TranslationRequest":
        """Raises ValueError if the language code is not supported."""
        if self.target_language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language '{self.target_language}'. "
                f"Supported: {sorted(SUPPORTED_LANGUAGES)}"
            )
        return self


class TranslationResponse(BaseModel):
    """202 Accepted response after queuing a translation task."""
    contract_id: UUID
    target_language: str
    status: str = Field(default="queued", description="queued | processing | complete | failed")
    task_id: str | None = None
