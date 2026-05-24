"""Counter offer model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class CounterOffer(Base):
    """Counter offer table — stores generated counter-offer versions for HIGH-risk clauses."""

    __tablename__ = "counter_offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    aggressive_version: Mapped[str] = mapped_column(Text, nullable=False)
    balanced_version: Mapped[str] = mapped_column(Text, nullable=False)
    conservative_version: Mapped[str] = mapped_column(Text, nullable=False)
    negotiation_email: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    clause = relationship("Clause", back_populates="counter_offers")

    def __repr__(self) -> str:
        return f"<CounterOffer(id={self.id}, clause_id={self.clause_id})>"
