"""Analysis result model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class AnalysisResult(Base):
    """Analysis result table — stores overall scan results per contract."""

    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    overall_risk_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100
    one_liner: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # e.g. "Contract with 2 key concerns"
    should_sign: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # "Yes as-is", "Yes with changes", "No"
    top_concerns: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )  # Array of strings
    top_positives: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )  # Array of strings
    negotiating_power: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # "Strong", "Moderate", "Weak"
    power_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # -100 to +100
    power_label: Mapped[str | None] = mapped_column(String, nullable=True)
    leverage_points: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )  # Array of strings
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract = relationship("Contract", back_populates="analysis_result")

    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, contract_id={self.contract_id}, risk_score={self.overall_risk_score})>"
