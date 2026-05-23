"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-05-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("clerk_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(10), server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_ref", sa.String(512), nullable=False),
        sa.Column("contract_type", sa.String(100), nullable=True),
        sa.Column("detected_language", sa.String(10), server_default="unknown"),
        sa.Column("party_roles", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "clauses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("position_index", sa.Integer, nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("risk_category", sa.String(100), nullable=True),
        sa.Column("plain_english", sa.Text, nullable=True),
        sa.Column("worst_case", sa.Text, nullable=True),
        sa.Column("financial_exposure", sa.String(255), nullable=True),
        sa.Column("negotiable", sa.Boolean, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("progress_pct", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("overall_risk_score", sa.Integer, nullable=True),
        sa.Column("should_sign", sa.String(50), nullable=True),
        sa.Column("top_concerns", sa.JSON, nullable=True),
        sa.Column("top_positives", sa.JSON, nullable=True),
        sa.Column("negotiating_power", sa.String(20), nullable=True),
        sa.Column("power_score", sa.Integer, nullable=True),
        sa.Column("power_label", sa.String(50), nullable=True),
        sa.Column("leverage_points", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "counter_offers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("clause_id", sa.String(36), sa.ForeignKey("clauses.id"), nullable=False),
        sa.Column("aggressive_clause", sa.Text, nullable=False),
        sa.Column("balanced_clause", sa.Text, nullable=False),
        sa.Column("conservative_clause", sa.Text, nullable=False),
        sa.Column("negotiation_email", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "precedent_matches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("clause_id", sa.String(36), sa.ForeignKey("clauses.id"), nullable=False),
        sa.Column("precedent_summary", sa.Text, nullable=False),
        sa.Column("enforcement_likelihood", sa.String(30), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("cited_cases", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("pdf_path", sa.String(512), nullable=True),
        sa.Column("share_uuid", sa.String(36), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=True),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("embedding_type", sa.String(30), nullable=False),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_clauses_contract_id", "clauses", ["contract_id"])
    op.create_index("ix_scan_jobs_contract_id", "scan_jobs", ["contract_id"])
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])
    op.create_index("ix_embeddings_contract_id", "embeddings", ["contract_id"])
    op.create_index("ix_embeddings_embedding_type", "embeddings", ["embedding_type"])


def downgrade() -> None:
    op.drop_table("embeddings")
    op.drop_table("reports")
    op.drop_table("precedent_matches")
    op.drop_table("counter_offers")
    op.drop_table("analysis_results")
    op.drop_table("scan_jobs")
    op.drop_table("clauses")
    op.drop_table("contracts")
    op.drop_table("users")
