"""add blockchain tables

Revision ID: 003_blockchain_tables
Revises: 002_add_indexes
Create Date: 2026-05-19

Adds:
  - contract_blockchain_records  (IPFS CIDs, Polygon tx hashes, registration status)
  - audit_trail_events           (append-only, hash-chained lifecycle log)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003_blockchain_tables"
down_revision = "002_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── contract_blockchain_records ───────────────────────────────────────────
    op.create_table(
        "contract_blockchain_records",
        sa.Column("id",                   sa.UUID(),    primary_key=True),
        sa.Column("contract_id",          sa.UUID(),    sa.ForeignKey("contracts.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("ipfs_pdf_cid",         sa.String(100), nullable=False),
        sa.Column("ipfs_metadata_cid",    sa.String(100), nullable=False),
        sa.Column("pdf_sha256",           sa.String(64),  nullable=False),
        sa.Column("metadata_sha256",      sa.String(64),  nullable=False),
        sa.Column("polygon_tx_hash",      sa.String(66),  nullable=True),
        sa.Column("polygon_block_number", sa.BigInteger, nullable=True),
        sa.Column("polygon_network",      sa.String(20),  nullable=False, server_default="testnet"),
        sa.Column("contract_address",     sa.String(42),  nullable=True),
        sa.Column("registration_status",  sa.String(20),  nullable=False, server_default="pending"),
        sa.Column("confirmed_at",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",           sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_cbr_contract_id", "contract_blockchain_records", ["contract_id"])
    op.create_index("idx_cbr_status",      "contract_blockchain_records", ["registration_status"])

    # ── audit_trail_events ────────────────────────────────────────────────────
    op.create_table(
        "audit_trail_events",
        sa.Column("id",                   sa.UUID(),    primary_key=True),
        sa.Column("contract_id",          sa.UUID(),    sa.ForeignKey("contracts.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("event_type",           sa.String(50),  nullable=False),
        sa.Column("actor_user_id",        sa.UUID(),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_wallet_address", sa.String(42),  nullable=True),
        sa.Column("payload",              sa.JSON(),      nullable=False, server_default="{}"),
        sa.Column("payload_hash",         sa.String(66),  nullable=False),
        sa.Column("previous_event_hash",  sa.String(66),  nullable=True),
        sa.Column("polygon_tx_hash",      sa.String(66),  nullable=True),
        sa.Column("polygon_block_number", sa.BigInteger,  nullable=True),
        sa.Column("on_chain_status",      sa.String(20),  nullable=False, server_default="pending"),
        sa.Column("occurred_at",          sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("confirmed_at",         sa.DateTime(timezone=True), nullable=True),
    )
    # Partial index recommended in spec
    op.create_index(
        "idx_audit_trail_contract",
        "audit_trail_events",
        ["contract_id"],
        postgresql_where=sa.text("on_chain_status = 'confirmed'"),
    )
    op.create_index("idx_audit_trail_contract_all", "audit_trail_events", ["contract_id"])
    op.create_index("idx_audit_trail_status",       "audit_trail_events", ["on_chain_status"])


def downgrade() -> None:
    op.drop_table("audit_trail_events")
    op.drop_table("contract_blockchain_records")
