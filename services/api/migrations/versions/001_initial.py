"""Initial schema - create all 9 tables with pgvector extension.

Revision ID: 001_initial
Revises: 
Create Date: 2024-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clerk_user_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("preferred_language", sa.String(), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clerk_user_id"),
    )
    op.create_index(op.f("ix_users_clerk_user_id"), "users", ["clerk_user_id"], unique=True)

    # Create contracts table
    op.create_table(
        "contracts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("file_ref", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("contract_type", sa.String(), nullable=True),
        sa.Column("detected_language", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("party_roles", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contracts_user_id"), "contracts", ["user_id"])

    # Create clauses table
    op.create_table(
        "clauses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("risk_category", sa.String(), nullable=True),
        sa.Column("plain_english", sa.Text(), nullable=True),
        sa.Column("worst_case_scenario", sa.Text(), nullable=True),
        sa.Column("financial_exposure", sa.String(), nullable=True),
        sa.Column("negotiable", sa.Boolean(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("headline", sa.String(), nullable=True),
        sa.Column("scenario", sa.Text(), nullable=True),
        sa.Column("probability", sa.String(), nullable=True),
        sa.Column("similar_case", sa.String(), nullable=True),
        sa.Column("requires_attorney_review", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clauses_contract_id"), "clauses", ["contract_id"])

    # Create scan_jobs table
    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_jobs_contract_id"), "scan_jobs", ["contract_id"])

    # Create analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("overall_risk_score", sa.Integer(), nullable=True),
        sa.Column("should_sign", sa.String(), nullable=True),
        sa.Column("top_concerns", sa.JSON(), nullable=True),
        sa.Column("top_positives", sa.JSON(), nullable=True),
        sa.Column("negotiating_power", sa.String(), nullable=True),
        sa.Column("power_score", sa.Integer(), nullable=True),
        sa.Column("power_label", sa.String(), nullable=True),
        sa.Column("leverage_points", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contract_id"),
    )
    op.create_index(op.f("ix_analysis_results_contract_id"), "analysis_results", ["contract_id"], unique=True)

    # Create counter_offers table
    op.create_table(
        "counter_offers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clause_id", sa.UUID(), nullable=False),
        sa.Column("aggressive_version", sa.Text(), nullable=False),
        sa.Column("balanced_version", sa.Text(), nullable=False),
        sa.Column("conservative_version", sa.Text(), nullable=False),
        sa.Column("negotiation_email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_counter_offers_clause_id"), "counter_offers", ["clause_id"])

    # Create precedent_matches table
    op.create_table(
        "precedent_matches",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clause_id", sa.UUID(), nullable=False),
        sa.Column("case_name", sa.String(), nullable=False),
        sa.Column("case_year", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("enforcement_likelihood", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_precedent_matches_clause_id"), "precedent_matches", ["clause_id"])

    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("share_uuid", sa.String(), nullable=False),
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_uuid"),
    )
    op.create_index(op.f("ix_reports_contract_id"), "reports", ["contract_id"])
    op.create_index(op.f("ix_reports_share_uuid"), "reports", ["share_uuid"], unique=True)

    # Create embeddings table with pgvector Vector column
    op.create_table(
        "embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contract_id", sa.UUID(), nullable=True),
        sa.Column("clause_id", sa.UUID(), nullable=True),
        sa.Column("embedding_type", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clause_id"], ["clauses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_embeddings_contract_id"), "embeddings", ["contract_id"])
    op.create_index(op.f("ix_embeddings_clause_id"), "embeddings", ["clause_id"])
    op.create_index(op.f("ix_embeddings_embedding_type"), "embeddings", ["embedding_type"])


def downgrade() -> None:
    # Drop all tables in reverse order of creation (to respect foreign keys)
    op.drop_table("embeddings")
    op.drop_table("reports")
    op.drop_table("precedent_matches")
    op.drop_table("counter_offers")
    op.drop_table("analysis_results")
    op.drop_table("scan_jobs")
    op.drop_table("clauses")
    op.drop_table("contracts")
    op.drop_table("users")

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
