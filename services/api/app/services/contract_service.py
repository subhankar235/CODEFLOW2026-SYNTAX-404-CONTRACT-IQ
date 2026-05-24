from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.repositories import contract_repo, scan_job_repo, user_repo
from app.schemas.contract import ContractCreate
from app.schemas.scan_job import ScanResponse, ScanStatus
from typing import Tuple, Optional
from fastapi import HTTPException


import logging

logger = logging.getLogger(__name__)


async def create_contract_and_job(
    db: AsyncSession, clerk_user_id: str, contract_data: ContractCreate
) -> Tuple[UUID, UUID, ScanStatus, Optional[str]]:
    """
    Business logic for creating a contract and its initial scan job.
    Returns: (job_id, contract_id, status, encryption_key)
    """
    logger.info(f"Processing upload for clerk_user_id: {clerk_user_id}")
    
    # 0. Look up user by Clerk ID to get internal UUID
    user = await user_repo.get_user_by_clerk_id(db, clerk_user_id)
    if not user:
        logger.info(f"User not found, creating new user: {clerk_user_id}")
        # Create user if doesn't exist
        user = await user_repo.create_user(
            session=db,
            clerk_user_id=clerk_user_id,
            email=f"{clerk_user_id}@placeholder.local",
        )
        await db.commit()
        # Refresh to get the created user with ID
        await db.refresh(user)
        logger.info(f"Created new user with ID: {user.id}")

    user_uuid = user.id

    # 1. Create the contract record
    contract = await contract_repo.create_contract(
        session=db,
        user_id=user_uuid,
        file_ref=str(contract_data.file_url),
        original_filename=contract_data.original_filename,
        file_type=contract_data.file_type,
        detected_language="unknown",
    )

    # 2. Create the scan job record
    scan_job = await scan_job_repo.create_scan_job(
        session=db, contract_id=contract.id, status="queued", progress_pct=0
    )

    # Return encryption key if provided
    return scan_job.id, contract.id, ScanStatus.QUEUED, contract_data.encryption_key
