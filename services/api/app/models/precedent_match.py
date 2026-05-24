"""Precedent match model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Integer, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class PrecedentMatch(Base):
    """Precedent match table — stores legal precedent matches for HIGH-risk clauses."""

    __tablename__ = "precedent_matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clauses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    precedent_summary: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_likelihood: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "Very Likely", "Likely", "Uncertain", "Unlikely"
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    cited_cases: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    clause = relationship("Clause", back_populates="precedent_matches")

    def __repr__(self) -> str:
        return f"<PrecedentMatch(id={self.id}, clause_id={self.clause_id})>"
