import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("contracts.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plain_english: Mapped[str | None] = mapped_column(Text, nullable=True)
    worst_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    financial_exposure: Mapped[str | None] = mapped_column(String(255), nullable=True)
    negotiable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    contract = relationship("Contract", back_populates="clauses")
    counter_offers = relationship("CounterOffer", back_populates="clause")
    precedent_matches = relationship("PrecedentMatch", back_populates="clause")
