import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PrecedentMatch(Base):
    __tablename__ = "precedent_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    clause_id: Mapped[str] = mapped_column(String(36), ForeignKey("clauses.id"), nullable=False)
    precedent_summary: Mapped[str] = mapped_column(Text, nullable=False)
    enforcement_likelihood: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cited_cases: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    clause = relationship("Clause", back_populates="precedent_matches")
