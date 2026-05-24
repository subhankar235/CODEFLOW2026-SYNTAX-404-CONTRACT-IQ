"""Clause model."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class Clause(Base):
    """Clause table — stores individual contract clauses and their risk analysis."""

    __tablename__ = "clauses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String, nullable=False
    )  # HIGH, MEDIUM, LOW, SAFE
    risk_category: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # indemnity, ip_assignment, etc.
    plain_english: Mapped[str | None] = mapped_column(Text, nullable=True)
    worst_case_scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    financial_exposure: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Dollar amount or "unlimited"
    negotiable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-1.0
    headline: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # 8-word worst-case summary
    scenario: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # 2-sentence story
    probability: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Low, Medium, High
    similar_case: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Real-world example headline
    requires_attorney_review: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    counter_offers = relationship(
        "CounterOffer", back_populates="clause", cascade="all, delete-orphan"
    )
    precedent_matches = relationship(
        "PrecedentMatch", back_populates="clause", cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "Embedding",
        foreign_keys="[Embedding.clause_id]",
        back_populates="clause",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Clause(id={self.id}, position={self.position_index}, risk_level={self.risk_level})>"
