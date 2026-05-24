from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_async_session
from app.core.security import get_current_user_id
from app.repositories import contract_repo, scan_job_repo, user_repo
from app.schemas.scan_job import ScanResponse, ScanStatus
from app.core.celery import celery_app

router = APIRouter()


@router.post("/{contractId}", response_model=ScanResponse)
async def trigger_scan(
    contractId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Manually trigger or retrigger a scan for a contract the user owns.
    If a scan is already complete, return the existing results.
    If failed, reset and requeue.
    """
    # 1. Get internal user
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get contract
    contract = await contract_repo.get_contract_by_id(db, contractId)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # 3. Verify ownership
    if contract.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to contract")

    # 4. Check for existing scan jobs
    jobs = await scan_job_repo.get_scan_jobs_by_contract_id(db, contract.id, user.id)

    if jobs:
        latest_job = jobs[0]  # Ordered by created_at desc

        if latest_job.status == "complete":
            return ScanResponse(
                job_id=latest_job.id,
                contract_id=contract.id,
                status=ScanStatus.COMPLETE,
                progress_pct=100.0,
                detected_language=contract.detected_language,
            )

        if latest_job.status == "processing":
            return ScanResponse(
                job_id=latest_job.id,
                contract_id=contract.id,
                status=ScanStatus.PROCESSING,
                progress_pct=latest_job.progress_pct,
                detected_language=contract.detected_language,
            )

    # 4. If no job or failed job, create/reset and trigger
    # Note: For simplicity, we always create a new job here if not complete/processing
    new_job = await scan_job_repo.create_scan_job(
        db, contract_id=contract.id, status="queued", progress_pct=0
    )

    # Trigger Celery task
    celery_app.send_task(
        "tasks.process_contract",
        kwargs={
            "contract_id_str": str(contract.id),
            "file_url": str(contract.file_ref),
            "user_id": str(user.id),
        },
    )

    return ScanResponse(
        job_id=new_job.id,
        contract_id=contract.id,
        status=ScanStatus.QUEUED,
        progress_pct=0.0,
        detected_language=contract.detected_language,
    )


@router.get("/{jobId}", response_model=ScanResponse)
async def get_scan_status(
    jobId: UUID,
    db: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Return the current ScanJobStatus (status, progress_pct, error_message).
    """
    # 1. Get internal user (auto-create if not exists)
    user = await user_repo.get_user_by_clerk_id(db, user_id)
    if not user:
        user = await user_repo.create_user(
            session=db,
            clerk_user_id=user_id,
            email=f"{user_id}@placeholder.local",
        )
        await db.commit()
        await db.refresh(user)

    # 2. Try to get the scan job
    job = await scan_job_repo.get_scan_job_by_id(db, jobId)
    
    if job:
        # Verify ownership
        contract = await contract_repo.get_contract_by_id(db, job.contract_id)
        if contract and contract.user_id == user.id:
            return ScanResponse(
                job_id=job.id,
                contract_id=job.contract_id,
                status=job.status,
                progress_pct=float(job.progress_pct),
                error_message=job.error_message,
                detected_language=contract.detected_language,
            )

    # 3. If no job or not authorized, return 404
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Scan job not found",
    )
