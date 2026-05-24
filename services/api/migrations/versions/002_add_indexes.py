"""Add performance indexes on critical columns.

Revision ID: 002_add_indexes
Revises: 001_initial
Create Date: 2024-04-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002_add_indexes"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for frequently filtered columns
    
    # Clauses: filter by risk_level for analysis
    op.create_index("ix_clauses_risk_level", "clauses", ["risk_level"])
    
    # ScanJobs: filter by status for job polling
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])
    
    # ScanJobs: find latest scan for a contract
    op.create_index(
        "ix_scan_jobs_contract_created",
        "scan_jobs",
        ["contract_id", "created_at"],
    )
    
    # Embeddings: filter by embedding_type for retrieval
    op.create_index("ix_embeddings_type_contract", "embeddings", ["embedding_type", "contract_id"])
    
    # Embeddings: find embeddings for a clause
    op.create_index("ix_embeddings_clause_type", "embeddings", ["clause_id", "embedding_type"])
    
    # Reports: filter by expiry for cleanup job
    op.create_index("ix_reports_expires_at", "reports", ["share_expires_at"])


def downgrade() -> None:
    # Drop all indexes
    op.drop_index("ix_reports_expires_at", table_name="reports")
    op.drop_index("ix_embeddings_clause_type", table_name="embeddings")
    op.drop_index("ix_embeddings_type_contract", table_name="embeddings")
    op.drop_index("ix_scan_jobs_contract_created", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_status", table_name="scan_jobs")
    op.drop_index("ix_clauses_risk_level", table_name="clauses")
