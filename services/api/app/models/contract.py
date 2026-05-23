import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    file_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    contract_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_language: Mapped[str] = mapped_column(String(10), default="unknown")
    party_roles: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="contracts")
    clauses = relationship("Clause", back_populates="contract")
    scan_jobs = relationship("ScanJob", back_populates="contract")
    analysis_results = relationship("AnalysisResult", back_populates="contract")
    reports = relationship("Report", back_populates="contract")
    embeddings = relationship("Embedding", back_populates="contract")
