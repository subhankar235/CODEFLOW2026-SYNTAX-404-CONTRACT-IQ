"""SQLAlchemy ORM model — contract_blockchain_records."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, BigInteger, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.base import Base


class ContractBlockchainRecord(Base):
    """On-chain registration state for each contract."""

    __tablename__ = "contract_blockchain_records"

    id:                  Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    contract_id:         Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    ipfs_pdf_cid:        Mapped[str]       = mapped_column(String(100), nullable=False)
    ipfs_metadata_cid:   Mapped[str]       = mapped_column(String(100), nullable=False)
    pdf_sha256:          Mapped[str]       = mapped_column(String(64),  nullable=False)
    metadata_sha256:     Mapped[str]       = mapped_column(String(64),  nullable=False)
    polygon_tx_hash:     Mapped[str | None] = mapped_column(String(66), nullable=True)
    polygon_block_number: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    polygon_network:     Mapped[str]       = mapped_column(String(20), nullable=False, default="testnet")
    contract_address:    Mapped[str | None] = mapped_column(String(42), nullable=True)
    registration_status: Mapped[str]       = mapped_column(String(20), nullable=False, default="pending")
    confirmed_at:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:          Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    contract = relationship("Contract", back_populates="blockchain_record")

    def __repr__(self) -> str:
        return (f"<ContractBlockchainRecord(contract_id={self.contract_id}, "
                f"status={self.registration_status})>")
