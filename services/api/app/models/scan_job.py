"""Scan job model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class ScanJob(Base):
    """Scan job table — tracks the status of contract analysis jobs."""

    __tablename__ = "scan_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # queued, processing, complete, failed
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    contract = relationship("Contract", back_populates="scan_jobs")

    def __repr__(self) -> str:
        return f"<ScanJob(id={self.id}, contract_id={self.contract_id}, status={self.status})>"
