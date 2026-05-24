"""SQLAlchemy ORM model — audit_trail_events."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class AuditTrailEvent(Base):
    """Append-only audit log mirroring on-chain AuditTrail events."""

    __tablename__ = "audit_trail_events"

    id:                   Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id:          Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type:           Mapped[str]       = mapped_column(String(50), nullable=False)
    actor_user_id:        Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_wallet_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    payload:              Mapped[dict]      = mapped_column(JSON, nullable=False, default=dict)
    payload_hash:         Mapped[str]       = mapped_column(String(66), nullable=False)
    previous_event_hash:  Mapped[str | None] = mapped_column(String(66), nullable=True)
    polygon_tx_hash:      Mapped[str | None] = mapped_column(String(66), nullable=True)
    polygon_block_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    on_chain_status:      Mapped[str]       = mapped_column(String(20), nullable=False, default="pending")
    occurred_at:          Mapped[datetime]  = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    confirmed_at:         Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    contract = relationship("Contract", back_populates="audit_trail_events")

    def __repr__(self) -> str:
        return (f"<AuditTrailEvent(contract_id={self.contract_id}, "
                f"event_type={self.event_type}, status={self.on_chain_status})>")
