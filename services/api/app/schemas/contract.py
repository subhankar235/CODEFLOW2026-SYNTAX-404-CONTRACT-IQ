# """
# Contract-related schemas for API requests and responses.
# """

# from __future__ import annotations

# from datetime import datetime
# from typing import Optional
# from uuid import UUID

# from pydantic import BaseModel, Field

# from app.schemas.response import ContractType, RiskLevel


# # ---------------------------------------------------------------------------
# # Contract Create/Update
# # ---------------------------------------------------------------------------


# class ContractCreate(BaseModel):
#     """Request to create a new contract."""

#     name: str = Field(..., min_length=1, max_length=255)
#     contract_type: Optional[ContractType] = None
#     file_path: Optional[str] = None
#     file_url: Optional[str] = None
#     party_a: Optional[str] = None
#     party_b: Optional[str] = None
#     metadata: Optional[dict] = None


# class ContractUpdate(BaseModel):
#     """Request to update an existing contract."""

#     name: Optional[str] = Field(None, min_length=1, max_length=255)
#     contract_type: Optional[ContractType] = None
#     party_a: Optional[str] = None
#     party_b: Optional[str] = None
#     metadata: Optional[dict] = None


# # ---------------------------------------------------------------------------
# # Contract Read
# # ---------------------------------------------------------------------------


# class ContractRead(BaseModel):
#     """Contract response model."""

#     id: UUID
#     name: str
#     contract_type: Optional[ContractType] = None

#     # File info
#     file_path: Optional[str] = None
#     file_url: Optional[str] = None
#     file_size: Optional[int] = None
#     mime_type: Optional[str] = None

#     # Party info
#     party_a: Optional[str] = None
#     party_b: Optional[str] = None

#     # Extracted content
#     extracted_text: Optional[str] = None
#     text_length: Optional[int] = None

#     # Analysis status
#     analysis_complete: bool = False
#     overall_risk_level: Optional[RiskLevel] = None

#     # Metadata
#     metadata: Optional[dict] = None

#     # Timestamps
#     created_at: datetime
#     updated_at: datetime

#     class Config:
#         from_attributes = True


# # ---------------------------------------------------------------------------
# # Contract List
# # ---------------------------------------------------------------------------


# class ContractListItem(BaseModel):
#     """Brief contract info for list views."""

#     id: UUID
#     name: str
#     contract_type: Optional[ContractType] = None
#     analysis_complete: bool
#     overall_risk_level: Optional[RiskLevel] = None
#     created_at: datetime

#     class Config:
#         from_attributes = True


# class ContractListResponse(BaseModel):
#     """Paginated contract list response."""

#     items: list[ContractListItem]
#     total: int
#     page: int
#     page_size: int
#     total_pages: int


# # ---------------------------------------------------------------------------
# # Contract Analysis Summary
# # ---------------------------------------------------------------------------


# class ContractAnalysisSummary(BaseModel):
#     """Summary of contract analysis results."""

#     total_clauses: int = 0
#     clauses_analyzed: int = 0

#     # Risk breakdown
#     critical_count: int = 0
#     high_count: int = 0
#     medium_count: int = 0
#     low_count: int = 0
#     none_count: int = 0

#     # Overall assessment
#     overall_risk_level: Optional[RiskLevel] = None
#     key_risks: list[str] = Field(default_factory=list)

#     # Feature completion
#     risk_analysis_complete: bool = False
#     type_detection_complete: bool = False
#     consequence_complete: bool = False
#     summary_complete: bool = False
#     power_asymmetry_complete: bool = False
#     counter_offer_complete: bool = False
#     precedent_complete: bool = False


"""
Contract-related schemas for API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.response import ContractType, RiskLevel


# ---------------------------------------------------------------------------
# Contract Create/Update
# ---------------------------------------------------------------------------


class ContractCreate(BaseModel):
    """Request to create a new contract."""

    file_url: str = Field(
        ..., description="Uploadthing URL of the encrypted uploaded file"
    )
    original_filename: str = Field(
        ..., description="Original filename of the uploaded file"
    )
    file_type: str = Field(..., description="File type (pdf or docx)")
    file_size_bytes: int = Field(..., description="Size of the file in bytes")
    name: Optional[str] = Field(
        None, description="Contract name (defaults to original filename)"
    )
    encryption_key: Optional[str] = Field(
        None, description="Encryption key for file decryption"
    )
    contract_type: Optional[ContractType] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    metadata: Optional[dict] = None


class ContractUpdate(BaseModel):
    """Request to update an existing contract."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contract_type: Optional[ContractType] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    metadata: Optional[dict] = None


# ---------------------------------------------------------------------------
# Contract Read
# ---------------------------------------------------------------------------


class ContractRead(BaseModel):
    """Contract response model."""

    id: UUID
    name: str
    contract_type: Optional[ContractType] = None

    # File info
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    # Party info
    party_a: Optional[str] = None
    party_b: Optional[str] = None

    # Extracted content
    extracted_text: Optional[str] = None
    text_length: Optional[int] = None

    # Analysis status
    analysis_complete: bool = False
    overall_risk_level: Optional[RiskLevel] = None

    # Metadata
    metadata: Optional[dict] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Contract List
# ---------------------------------------------------------------------------


class ContractListItem(BaseModel):
    """Brief contract info for list views."""

    id: UUID
    name: str
    contract_type: Optional[ContractType] = None
    analysis_complete: bool
    overall_risk_level: Optional[RiskLevel] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Paginated contract list response."""

    items: list[ContractListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Contract Analysis Summary
# ---------------------------------------------------------------------------


class ContractAnalysisSummary(BaseModel):
    """Summary of contract analysis results."""

    total_clauses: int = 0
    clauses_analyzed: int = 0

    # Risk breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    none_count: int = 0

    # Overall assessment
    overall_risk_level: Optional[RiskLevel] = None
    key_risks: list[str] = Field(default_factory=list)

    # Feature completion
    risk_analysis_complete: bool = False
    type_detection_complete: bool = False
    consequence_complete: bool = False
    summary_complete: bool = False
    power_asymmetry_complete: bool = False
    counter_offer_complete: bool = False
    precedent_complete: bool = False
