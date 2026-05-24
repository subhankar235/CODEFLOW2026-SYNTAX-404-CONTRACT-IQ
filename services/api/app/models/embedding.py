"""Embedding model for RAG (Retrieval-Augmented Generation)."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from ..db.base import Base


class Embedding(Base):
    """Embedding table — stores vector embeddings for RAG (Q&A chat, counter-offer, precedent retrieval)."""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    clause_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clauses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    embedding_type: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )  # "contract_qa", "favorable_clause", "precedent"
    text: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # The original text being embedded
    embedding: Mapped[Vector] = mapped_column(
        Vector(384), nullable=False
    )  # all-MiniLM-L6-v2 uses 384 dimensions
    context_data: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )  # Additional context (clause_id, source, etc.)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract = relationship("Contract", back_populates="embeddings")
    clause = relationship(
        "Clause", back_populates="embeddings", foreign_keys=[clause_id]
    )

    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, type={self.embedding_type}, text_len={len(self.text)})>"
