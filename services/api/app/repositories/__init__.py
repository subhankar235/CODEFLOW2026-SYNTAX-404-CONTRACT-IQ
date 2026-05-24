"""Database repositories for query functions."""

from .user_repo import (
    create_user,
    get_user_by_id,
    get_user_by_clerk_id,
    update_user,
    delete_user,
)
from .contract_repo import (
    create_contract,
    get_contract_by_id,
    get_all_contracts_by_user_id,
    update_contract,
    delete_contract,
)
from .clause_repo import (
    create_clause,
    get_clause_by_id,
    get_all_clauses_by_contract_id,
    bulk_create_clauses,
    update_clause,
    delete_clause,
)
from .scan_job_repo import (
    create_scan_job,
    get_scan_job_by_id,
    get_scan_jobs_by_contract_id,
    update_status,
    update_progress,
    update_error,
    delete_scan_job,
)
from .report_repo import (
    create_report,
    get_report_by_id,
    get_report_by_share_uuid,
    get_report_by_contract_id,
    delete_report,
    delete_expired_reports,
)
from .precedent_repo import (
    create_precedent_match,
    get_precedent_match_by_id,
    get_precedent_matches_by_clause_id,
    delete_precedent_match,
)

__all__ = [
    # User
    "create_user",
    "get_user_by_id",
    "get_user_by_clerk_id",
    "update_user",
    "delete_user",
    # Contract
    "create_contract",
    "get_contract_by_id",
    "get_all_contracts_by_user_id",
    "update_contract",
    "delete_contract",
    # Clause
    "create_clause",
    "get_clause_by_id",
    "get_all_clauses_by_contract_id",
    "bulk_create_clauses",
    "update_clause",
    "delete_clause",
    # Scan Job
    "create_scan_job",
    "get_scan_job_by_id",
    "get_scan_jobs_by_contract_id",
    "update_status",
    "update_progress",
    "update_error",
    "delete_scan_job",
    # Report
    "create_report",
    "get_report_by_id",
    "get_report_by_share_uuid",
    "get_report_by_contract_id",
    "delete_report",
    "delete_expired_reports",
    # Precedent
    "create_precedent_match",
    "get_precedent_match_by_id",
    "get_precedent_matches_by_clause_id",
    "delete_precedent_match",
]
