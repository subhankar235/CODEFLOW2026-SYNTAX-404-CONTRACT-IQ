"""Report model."""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class Report(Base):
    """Report table — stores generated PDF reports and share links."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Path to PDF on storage
    share_uuid: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )  # UUID v4 for public sharing
    share_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract = relationship("Contract", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, contract_id={self.contract_id}, share_uuid={self.share_uuid})>"
