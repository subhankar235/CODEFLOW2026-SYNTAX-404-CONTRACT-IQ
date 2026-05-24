"""
Report schemas — PRD Feature 12.

POST /api/v1/report/generate/{contractId}  → 202 Accepted
GET  /api/v1/report/{reportId}             → ReportRead
GET  /api/v1/report/share/{shareUuid}      → ReportRead (public, checks expiry)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    """Request body for generating a report (language selector)."""
    language: str = Field(
        default="en",
        description="BCP-47 language code: en | es | fr | de | pt | hi",
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class ReportRead(BaseModel):
    """Full report record returned to authenticated or share-link callers."""
    report_id: UUID
    contract_id: UUID

    # Share link — UUID v4, non-guessable (PRD Section 7.3)
    share_uuid: UUID
    share_url: str = Field(..., description="Full public share URL")

    # 48-hour expiry enforced by share endpoint
    expires_at: datetime
    language: str

    # PDF path present once the Celery task completes
    pdf_path: Optional[str] = None
    status: str = Field(..., description="processing | complete | failed")

    created_at: datetime

    class Config:
        from_attributes = True
