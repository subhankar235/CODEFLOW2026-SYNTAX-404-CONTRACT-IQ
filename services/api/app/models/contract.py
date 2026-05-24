"""Contract model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class Contract(Base):
    """Contract table — stores uploaded contracts."""

    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_ref: Mapped[str] = mapped_column(String, nullable=False)  # Uploadthing URL
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)  # "pdf" or "docx"
    contract_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Employment, NDA, etc.
    detected_language: Mapped[str] = mapped_column(
        String, default="unknown", nullable=False
    )
    party_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    clauses = relationship(
        "Clause", back_populates="contract", cascade="all, delete-orphan"
    )
    scan_jobs = relationship(
        "ScanJob", back_populates="contract", cascade="all, delete-orphan"
    )
    analysis_result = relationship(
        "AnalysisResult",
        back_populates="contract",
        cascade="all, delete-orphan",
        uselist=False,
    )
    embeddings = relationship(
        "Embedding", back_populates="contract", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="contract", cascade="all, delete-orphan"
    )
    blockchain_record = relationship(
        "ContractBlockchainRecord",
        back_populates="contract",
        cascade="all, delete-orphan",
        uselist=False,
    )
    audit_trail_events = relationship(
        "AuditTrailEvent", back_populates="contract", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, user_id={self.user_id}, filename={self.original_filename})>"
