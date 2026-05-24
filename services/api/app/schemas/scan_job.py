"""
Scan job schemas for processing contracts.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.response import ContractType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ScanStatus(str, Enum):
    """Status of a scan job."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Scan Request
# ---------------------------------------------------------------------------


class ScanFeatures(BaseModel):
    """Features to enable for scanning."""

    risk_analysis: bool = True
    type_detection: bool = True
    consequence: bool = True
    summary: bool = True
    power_asymmetry: bool = True
    counter_offer: bool = True
    precedent: bool = True


class ScanRequest(BaseModel):
    """Request to scan a contract."""

    contract_id: UUID
    features: ScanFeatures = Field(default_factory=ScanFeatures)
    priority: int = Field(default=0, ge=0, le=100)
    callback_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Scan Response
# ---------------------------------------------------------------------------


class ScanProgress(BaseModel):
    """Progress information for a scan job."""

    current_feature: Optional[str] = None
    clauses_processed: int = 0
    total_clauses: int = 0
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class ScanJobStatus(BaseModel):
    """Complete status of a scan job."""

    job_id: UUID
    contract_id: UUID
    status: ScanStatus
    progress: ScanProgress = Field(default_factory=ScanProgress)
    error_message: Optional[str] = None

    # Results
    summary: Optional[dict] = None

    # Timestamps
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    """Basic scan response."""

    job_id: UUID
    contract_id: UUID
    status: ScanStatus
    progress_pct: float = 0.0
    error_message: Optional[str] = None
    detected_language: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Scan Result
# ---------------------------------------------------------------------------


class ScanResultSummary(BaseModel):
    """Summary of scan results."""

    total_clauses: int = 0
    risk_analysis_count: int = 0
    type_detection_count: int = 0
    consequence_count: int = 0
    summary_count: int = 0
    power_asymmetry_count: int = 0
    counter_offer_count: int = 0
    precedent_count: int = 0


class ScanResult(BaseModel):
    """Complete scan result."""

    job_id: UUID
    contract_id: UUID
    status: ScanStatus
    summary: ScanResultSummary
    error_message: Optional[str] = None

    # Results storage
    results: Optional[dict] = None

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
