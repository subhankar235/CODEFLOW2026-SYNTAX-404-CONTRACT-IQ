import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False)
    overall_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    should_sign: Mapped[str | None] = mapped_column(String(50), nullable=True)
    top_concerns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    top_positives: Mapped[list | None] = mapped_column(JSON, nullable=True)
    negotiating_power: Mapped[str | None] = mapped_column(String(20), nullable=True)
    power_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    leverage_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    contract = relationship("Contract", back_populates="analysis_results")
