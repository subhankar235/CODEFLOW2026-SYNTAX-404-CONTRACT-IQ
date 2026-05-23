import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CounterOffer(Base):
    __tablename__ = "counter_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clause_id: Mapped[str] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=False)
    aggressive_clause: Mapped[str] = mapped_column(Text, nullable=False)
    balanced_clause: Mapped[str] = mapped_column(Text, nullable=False)
    conservative_clause: Mapped[str] = mapped_column(Text, nullable=False)
    negotiation_email: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    clause = relationship("Clause", back_populates="counter_offers")
